"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP

REALTIME_GUIDE = """# Realtime Speech SDK runbook

## Architecture boundary

OCI Realtime Speech uses a long-lived WebSocket. An MCP call is a bounded
request/response operation, so the audio-producing application—not this MCP
server—must own the microphone, WebSocket, transcript callbacks, and reconnect
loop. Do not expose signed headers, session credentials, or raw audio through
the model conversation. Use this MCP server separately to create and inspect
Speech customizations.

## Install the supported client

Create a separate application environment and install the official package:

```bash
python -m pip install "oci-ai-speech-realtime>=2.2.0,<3"
python -m pip install "pyaudio>=0.2.14"  # only for microphone capture
```

The Realtime SDK depends on the OCI Python SDK and `websockets`. Its official
repository contains synchronous-listener/async-client examples. PyAudio may
also require the platform's PortAudio development package. Keep the capture
application separate from the MCP server so audio-device dependencies are not
added to every MCP client.

## Build the endpoint and authentication safely

Use the selected OCI region to construct:

`wss://realtime.aiservice.<region>.oci.oraclecloud.com`

Pass this endpoint explicitly: the current Realtime client does not derive a
default endpoint. Accept only known OCI region identifiers; never accept an
arbitrary WebSocket host from an agent. Pass normal OCI SDK `config` and
`signer` values. When the application shares this repository's environment,
use `oracle_mcp_common.build_auth_context()` so profile, security-token, and
principal authentication follow the same rules as this MCP server.

## Choose model and audio parameters

- OCI currently documents a default limit of 10 concurrent Live Transcribe
  sessions per tenancy. Use a client-side session limiter and request a service
  limit increase before designing for more concurrency.
- Use mono audio. The official microphone example uses signed 16-bit PCM,
  16 kHz, and 96 ms buffers. `audio/raw;rate=8000` is also supported, as are
  8 kHz mu-law and A-law encodings. The bytes sent must exactly match the
  declared `encoding`.
- `ORACLE` supports partial results, `GENERIC` and `MEDICAL` domains,
  customizations, silence thresholds, and partial-result stabilization.
- `WHISPER` supports many locale-agnostic language codes and `auto` language
  detection. Do not design a Whisper UI around partial results.
- Oracle-model language codes are locale-specific, such as `en-US`; Whisper
  codes are language-only, such as `en`, or `auto`.
- Partial silence is 0–2000 ms and final silence is 0–5000 ms. Lower values
  reduce latency but may create more fragments. Stabilization is `NONE`, `LOW`,
  `MEDIUM`, or `HIGH` and applies only to Oracle partial results.
- Punctuation is `NONE`, `AUTO`, or `SPOKEN`. `SPOKEN` is limited to the Oracle
  Medical model.
- Enable `is_ack_enabled` when the application needs delivery telemetry.
  Keep `should_ignore_invalid_customizations=False` when silently dropping a
  requested customization would be unsafe.

## Minimal asynchronous session pattern

The listener methods are synchronous callbacks. Keep them fast: publish results
to an application queue or UI and return. `on_connect` means the socket opened;
wait for `on_connect_message` before considering authentication complete.

```python
import asyncio

from oci.ai_speech.models import RealtimeParameters
from oci_ai_speech_realtime import RealtimeSpeechClient, RealtimeSpeechClientListener
from oracle_mcp_common import build_auth_context


class Listener(RealtimeSpeechClientListener):
    def __init__(self, authenticated, final_received, result_sink):
        self.authenticated = authenticated
        self.final_received = final_received
        self.result_sink = result_sink

    def on_connect(self):
        pass

    def on_connect_message(self, message):
        self.authenticated.set()

    def on_result(self, result):
        for item in result.get("transcriptions", []):
            self.result_sink(item["transcription"], item["isFinal"])
            if item["isFinal"]:
                self.final_received.set()

    def on_ack_message(self, message):
        pass

    def on_network_event(self, message):
        pass

    def on_error(self, error):
        self.result_sink(f"Realtime service error: {error}", True)

    def on_close(self, code, reason):
        self.result_sink(f"Realtime session closed: {code} {reason}", True)


async def transcribe_stream(audio_chunks, compartment_id, region, result_sink):
    auth = build_auth_context()
    parameters = RealtimeParameters(
        language_code="en-US",
        model_type="ORACLE",
        model_domain=RealtimeParameters.MODEL_DOMAIN_GENERIC,
        encoding="audio/raw;rate=16000",
        is_ack_enabled=True,
        partial_silence_threshold_in_ms=0,
        final_silence_threshold_in_ms=2000,
        stabilize_partial_results=RealtimeParameters.STABILIZE_PARTIAL_RESULTS_LOW,
        punctuation=RealtimeParameters.PUNCTUATION_AUTO,
        should_ignore_invalid_customizations=False,
    )
    authenticated = asyncio.Event()
    final_received = asyncio.Event()
    client = RealtimeSpeechClient(
        config=auth.config,
        signer=auth.signer,
        compartment_id=compartment_id,
        service_endpoint=f"wss://realtime.aiservice.{region}.oci.oraclecloud.com",
        realtime_speech_parameters=parameters,
        listener=Listener(authenticated, final_received, result_sink),
    )
    connection = asyncio.create_task(client.connect())
    try:
        await asyncio.wait_for(authenticated.wait(), timeout=15)
        async for chunk in audio_chunks:
            await client.send_data(chunk)
        await client.request_final_result()
        await asyncio.wait_for(final_received.wait(), timeout=10)
    finally:
        client.close()
        await connection
```

Call `request_final_result()` before closing and wait for the corresponding
final callback. `connect()` processes inbound messages until closure, so run it
as a task while the producer sends audio.

## Microphone capture and backpressure

PyAudio invokes its callback outside the asyncio consumer flow. Transfer chunks
onto the event loop with `loop.call_soon_threadsafe`, and use a bounded queue.
If the queue fills, record the overload and drop stale live audio or stop the
session; never allow an unbounded queue to increase latency and memory use.
At 16 kHz mono 16-bit PCM, a 96 ms chunk contains 1,536 frames and 3,072 bytes.
Do not send a WAV file header when the declared encoding is raw PCM.

## Customizations

Customizations apply only to the Oracle model. Supply typed
`CustomizationInference` values with the customization OCID, compartment OCID,
and optional entity mappings. Confirm the customization is ACTIVE before the
session. With `should_ignore_invalid_customizations=False`, a load failure ends
the session instead of silently falling back to the base model.

## Reconnect and shutdown

- Treat `on_error` and unexpected `on_close` as session failures. Create a new
  `RealtimeSpeechClient` for each retry; a closed client retains its close flag.
- Retry only transient failures, with capped exponential backoff and jitter.
  Re-resolve authentication before a retry so rotated tokens are observed.
- Do not replay old microphone audio after reconnect unless the product
  explicitly requires it; stale audio undermines the meaning of "live."
- Stop capture, request the last final result, wait briefly for it, close the
  client, cancel the producer, close the audio stream, and terminate PyAudio.
- Keep callbacks non-blocking and send transcript events to downstream consumers
  through a bounded queue. Distinguish partial text from final text in the UI;
  replace partial text rather than appending it as a second transcript.
- Measure connection/authentication time, queued audio duration, acknowledgement
  delay, final-result latency, reconnect count, and close/error codes. Never log
  signed headers, credentials, or raw audio.

## Troubleshooting order

1. Verify Speech IAM access, the compartment OCID, selected region, and the
   region-specific `wss://realtime...` endpoint.
2. Confirm the microphone format exactly matches `encoding`, including sample
   rate, channel count, sample width, and codec.
3. Check `on_connect_message` before sending; a socket-open callback alone does
   not prove Speech authentication succeeded.
4. Remove customizations to isolate model connectivity, then restore only ACTIVE
   customization OCIDs.
5. Compare Oracle/Whisper parameters: do not send Oracle-only silence,
   stabilization, Medical, or customization settings to Whisper.
6. Inspect bounded-queue depth and acknowledgement timing for producer/network
   backpressure before increasing silence thresholds.

Official sources:
- https://github.com/oracle/oci-ai-speech-realtime-python-sdk
- https://pypi.org/project/oci-ai-speech-realtime/
- https://oracle-livelabs.github.io/analytics-ai/oci-artificial-intelligence/ai-speech/workshops/freetier/index.html?lab=transcribe-live-audio
"""


def realtime_guide() -> str:
    return REALTIME_GUIDE


def register_resources(mcp: FastMCP) -> None:
    mcp.resource(
        "speech://guides/realtime",
        description="Safe client-side OCI Realtime Speech WebSocket integration guidance.",
    )(realtime_guide)

