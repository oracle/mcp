# OCI Speech MCP Server

`oracle.oci-speech-mcp-server` is a local, stdio MCP server for OCI Speech. It
provides transcription job and task management, an end-to-end local-file
transcription workflow, text-to-speech, Speech customizations, and OCI Events
and Notifications setup.

The server also publishes detailed MCP resources and workflow prompts so an MCP
client can plan a safe operation before invoking tools. Realtime Speech is
documented as a client-side WebSocket integration; this server does not expose
session tokens or keep WebSockets open across MCP calls.

> This project is a reference implementation and is not intended for production use.

## Capabilities

### Tools

| Area | Tools |
| --- | --- |
| Transcription jobs | `create_transcription_job`, `get_transcription_job`, `list_transcription_jobs`, `update_transcription_job`, `delete_transcription_job`, `cancel_transcription_job`, `change_transcription_job_compartment` |
| Transcription tasks | `list_transcription_tasks`, `get_transcription_task`, `cancel_transcription_task` |
| Local workflow | `transcribe_local_file`, `download_transcription_results` |
| Text-to-speech | `list_voices`, `synthesize_speech` |
| Customizations | `create_customization`, `get_customization`, `list_customizations`, `update_customization`, `delete_customization`, `change_customization_compartment` |
| Events and Notifications | `setup_transcription_notifications` |

List operations automatically follow OCI pagination but stop at the caller's
bounded `max_items` value. Mutating operations return a consistent envelope with
OCI data, status, ETag, request ID, and workflow notes where applicable.

### Resources

Read these with any MCP client that supports resources:

- `speech://guides/index`
- `speech://guides/prerequisites`
- `speech://guides/policies`
- `speech://guides/service-limits`
- `speech://guides/transcription`
- `speech://guides/local-files`
- `speech://guides/text-to-speech`
- `speech://guides/ssml`
- `speech://guides/customizations`
- `speech://guides/notifications`
- `speech://guides/realtime`

### Prompts

- `transcribe_local_audio`
- `manage_transcription_job`
- `synthesize_narration`
- `customize_tts_with_ssml`
- `build_speech_customization`
- `plan_speech_policies`
- `setup_job_notifications`
- `troubleshoot_speech_job`
- `plan_realtime_integration`

## Prerequisites

- Python 3.13 and [`uv`](https://docs.astral.sh/uv/)
- An OCI tenancy with OCI Speech enabled in the target region
- An OCI SDK credential source described below
- Object Storage access for transcription inputs and outputs
- For text-to-speech, access to `us-phoenix-1`, where the API is currently
  available

OCI service limits still apply. A transcription media file may be at most 2 GB
or four hours, a job may include at most 100 tasks, and job metadata is retained
for 90 days. Text-to-speech input is limited to 10,000 characters. Live
Transcribe supports 10 concurrent sessions per tenancy by default; request a
limit increase through Oracle Support before designing for more.

### Authentication

Credentials are resolved through the repository's shared `oracle-mcp-common`
library. Credentials are never accepted as MCP tool arguments.

For a normal local OCI profile:

```sh
export OCI_CONFIG_PROFILE=DEFAULT
export OCI_REGION=us-ashburn-1
```

Set `OCI_MCP_AUTH_TYPE` when you need a specific credential mode. Supported
values are `auto`, `api_key`, `security_token`, `identity_domain_upst`,
`instance_principal`, `resource_principal`,
`instance_principal_delegation`, `resource_principal_delegation`, and
`oke_workload_identity`. See the repository's
[shared authentication guide](../common/README.md#authentication-module) for
the complete environment-variable matrix.

### IAM policy examples

Adapt these examples to your tenancy's compartments and least-privilege model:

```text
allow group SpeechUsers to manage ai-service-speech-family in compartment SpeechCompartment
allow group SpeechUsers to manage object-family in compartment SpeechCompartment
```

For a group that needs only text-to-speech, use the individual synthesis
resource types instead of the aggregate Speech family:

```text
allow group SpeechTTSUsers to manage ai-service-speech-synthesize-voice in compartment SpeechCompartment
allow group SpeechTTSUsers to manage ai-service-speech-synthesize in compartment SpeechCompartment
```

The `speech://guides/policies` resource and `plan_speech_policies` prompt explain
where to create the policy, tenancy versus compartment scope, tag permissions,
and authorization troubleshooting. This MCP server does not create IAM policies;
an administrator must review and apply them.

Only add the following capabilities for users who will run the notification
setup tool:

```text
allow group SpeechNotificationAdmins to manage ons-family in compartment SpeechCompartment
allow group SpeechNotificationAdmins to manage cloudevents-rules in compartment SpeechCompartment
allow service cloudEvents to use ons-topic in compartment SpeechCompartment
```

Review the current [Speech IAM policy reference](https://docs.oracle.com/en-us/iaas/Content/speech/using/policies.htm),
[Notifications policy reference](https://docs.oracle.com/en-us/iaas/Content/Notification/Concepts/notificationoverview.htm),
and [Events policy reference](https://docs.oracle.com/en-us/iaas/Content/Events/Concepts/eventspolicy.htm)
before applying policy statements.

## Run from an MCP client

Once the package is published, the minimal configuration is:

```json
{
  "mcpServers": {
    "oracle-oci-speech": {
      "command": "uvx",
      "args": ["oracle.oci-speech-mcp-server@1.0.0"],
      "env": {
        "OCI_CONFIG_PROFILE": "<profile_name>",
        "OCI_REGION": "<speech_region>",
        "OCI_SPEECH_INPUT_ROOT": "<directory-containing-approved-media>",
        "OCI_SPEECH_OUTPUT_ROOT": "<directory-for-speech-outputs>",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

`OCI_SPEECH_INPUT_ROOT` is needed only for `transcribe_local_file`. If it is not
set, all other tools remain available. `OCI_SPEECH_OUTPUT_ROOT` defaults to
`~/.oci-speech-mcp/outputs`.

For a repository checkout, replace the command and arguments with:

```json
{
  "command": "uv",
  "args": [
    "--directory",
    "/absolute/path/to/mcp/src/oci-speech-mcp-server",
    "run",
    "oracle.oci-speech-mcp-server"
  ]
}
```

The server is deliberately stdio-only. Keep standard output reserved for MCP
protocol messages and send diagnostics to standard error through normal logging.

## End-to-end local transcription

`transcribe_local_file` performs this bounded workflow:

1. Resolve the requested file and confirm it is a regular supported media file
   inside `OCI_SPEECH_INPUT_ROOT`.
2. Reject credential/operating-system secret locations and files larger than 2
   GiB.
3. Upload the media to the selected Object Storage bucket.
4. Create an OCI Speech transcription job with a generated output prefix.
5. Optionally wait for a terminal lifecycle state.
6. For a successful job, discover task output objects and stream them into
   `OCI_SPEECH_OUTPUT_ROOT`.

The uploaded input is not automatically deleted. Use Object Storage lifecycle
rules or an explicit governance process to control retention. Local output paths
must be relative, cannot escape the configured root, and do not overwrite files
unless `overwrite` is explicitly enabled.

Supported media suffixes are AAC, AC3, AMR, AU, FLAC, M4A, MKV, MP3, MP4, OGA,
OGG, OPUS, WAV, and WEBM.

## Transcription models

The default model is Oracle `ORACLE`, domain `GENERIC`, language `en-US`.
Diarization can be enabled with 2–16 speakers. If the user says the recording
has multiple speakers, the agent should enable it; if the exact count is unknown,
the count can remain unset. When no speaker context is provided, the agent should
ask rather than infer from the file—the server validates the local file but does
not listen to it or run speaker detection. Diarization produces speaker labels,
not people's identities. Both Oracle ASR and OCI Whisper support it.

SRT can be requested as an additional output format. The model type remains an
explicit string so model names enabled for the tenancy—including supported
Whisper variants—can be used without a server release. Whisper prompts are
limited to 4,000 characters.

Use `MEDICAL` only where supported for the chosen capability and tenancy.
Always verify current model and language availability in the
[OCI Speech documentation](https://docs.oracle.com/en-us/iaas/Content/speech/home.htm).

## Text-to-speech

Call `list_voices` to select a voice, then `synthesize_speech`. The server routes
only these calls to `us-phoenix-1` and writes streamed output locally. Supported
formats are MP3, PCM, OGG, and JSON. JSON is intended for WORD and SENTENCE
speech marks. `TTS_1_STANDARD` accepts a voice; `TTS_2_NATURAL` additionally
accepts a language code. Input can be plain text or SSML.

SSML is available only for selected `en-US` voices. The server validates a
single `<speak>` root and the OCI-supported tags `<break>`, `<s>`, `<p>`,
`<say-as>`, `<sub>`, `<phoneme>`, `<prosody>`, and `<voice>` before synthesis;
`<prosody>` is standard-voice only. The `speech://guides/ssml` resource includes
examples for pauses, acronyms, dates, digits, units, pronunciations, delivery
rate/volume/pitch, and multi-voice dialogue. The `customize_tts_with_ssml`
prompt helps an agent preserve the user's text, inject the smallest necessary
markup, show it for review, and synthesize with `text_type=SSML`.

## Customizations

Customization tools support inline entity-list datasets and Object Storage
datasets. Inline entities can carry:

- a value and optional weight;
- one or more sounds-like pronunciations;
- audio pronunciation objects from one declared Object Storage namespace and
  bucket;
- reference examples containing entity-type placeholders.

Every populated entity list creates a reusable entity customization. A list can
instead reuse an existing entity customization by supplying its OCID or alias
with an empty `entities` field. Reference examples may contain multiple entity
types; every `<PLACEHOLDER>` must match a supplied `entity_type`, which the input
model validates before the API call. Reference examples plus entity lists create
a contextual customization that points to default reusable entity sources. A
Realtime application can use those defaults or override one entity type with a
different ACTIVE reusable customization.

The external API does not expose a customization-type field, so clients should
work from the returned relationships rather than depend on internal categories.
The create and update calls start training. Review the generated dataset and
check for ACTIVE lifecycle state before using it with the Oracle Realtime model.
Object Storage datasets and audio pronunciation lists accept at most 1,024
object names.

## Events and Notifications

`setup_transcription_notifications` accepts either an existing topic OCID or a
new topic name. It can optionally create a subscription and then creates an
enabled Events rule targeting the topic. By default the rule selects:

- `com.oraclecloud.aiservicespeech.completedtranscriptionjob`
- `com.oraclecloud.aiservicespeech.failedtranscriptionjob`

Supplying a transcription job OCID narrows the event condition by resource ID.
Email subscriptions remain pending until the recipient confirms them. If setup
stops after creating one resource, the exception is reported without silently
deleting that resource; inspect the returned OCI state before retrying.

## Realtime Speech

Realtime Speech uses a long-lived WebSocket and application listener callbacks.
An MCP tool invocation is a request/response boundary, so this server does not
hold a realtime socket open and does not return realtime session tokens to the
model. Use the official
[`oci-ai-speech-realtime`](https://pypi.org/project/oci-ai-speech-realtime/)
client in the audio-producing application and use this MCP server separately to
manage customizations.

Install the current compatible major version in the application environment:

```sh
python -m pip install "oci-ai-speech-realtime>=2.2.0,<3"
python -m pip install "pyaudio>=0.2.14"  # only for microphone capture
```

The SDK is asynchronous and based on WebSockets. Construct the region-specific
endpoint as `wss://realtime.aiservice.<region>.oci.oraclecloud.com`, pass OCI SDK
configuration and a signer, create a `RealtimeSpeechClientListener`, and run
`RealtimeSpeechClient.connect()` as a task while another coroutine sends audio
with `send_data()`.

OCI currently documents a default maximum of 10 concurrent Live Transcribe
sessions per tenancy. Add an application-side session limiter and obtain an OCI
service-limit increase before attempting greater concurrency.

Every listener must implement `on_result`, `on_ack_message`, `on_connect`,
`on_connect_message`, `on_network_event`, and `on_error`; `on_close` is the
cleanup hook. Treat `on_connect_message` as the authentication-ready signal.
Callbacks should quickly publish events to a bounded application queue and must
not block the WebSocket receive loop. Separate partial results from final
results in the UI: replace the current partial text and append only final text.

### Realtime parameter guide

| Setting | Guidance |
| --- | --- |
| Audio | Mono audio whose bytes exactly match `encoding`. Supported encodings include 16 kHz or 8 kHz raw PCM and 8 kHz mu-law/A-law. The official microphone example uses signed 16-bit PCM, 16 kHz, and 96 ms chunks. |
| Oracle model | Uses locale-specific languages such as `en-US`. Supports partial results, Generic/Medical domains, silence thresholds, stabilization, and customizations. |
| Whisper model | Uses language-only codes such as `en`, or `auto` detection. Do not depend on partial results or send Oracle-only parameters. |
| Silence | Oracle-only partial threshold: 0–2000 ms; final threshold: 0–5000 ms. Tune against latency and transcript fragmentation. |
| Stability | Oracle-only `NONE`, `LOW`, `MEDIUM`, or `HIGH`. Higher stability delays changing partial tokens. |
| Punctuation | `NONE`, `AUTO`, or `SPOKEN`; spoken punctuation is limited to the Oracle Medical model. |
| Acknowledgements | Enable `is_ack_enabled` when the application needs audio-delivery telemetry. |
| Customizations | Oracle-only. Prefer `should_ignore_invalid_customizations=False` so a requested customization is not silently dropped. |

For microphone capture, move data from the audio callback onto the asyncio event
loop with `loop.call_soon_threadsafe` and use a bounded queue. An unbounded queue
turns network slowdown into rising memory usage and increasingly stale
transcription. At 16 kHz mono 16-bit PCM, a 96 ms chunk is 1,536 frames or 3,072
bytes. Raw PCM must not include a WAV header.

Before a normal shutdown, stop accepting new audio, call
`request_final_result()`, wait for the final-result callback, and then call
`close()`. On a transient disconnect, create a new client, re-resolve
authentication, and retry with capped exponential backoff and jitter. Do not
replay stale microphone audio after reconnect. Track queue depth,
acknowledgement delay, final-result latency, reconnects, and close/error codes,
but never log signed headers, credentials, or raw audio.

The `speech://guides/realtime` resource contains a complete asynchronous session
pattern, safe capture/backpressure guidance, customization setup, reconnect and
shutdown rules, and a troubleshooting sequence. The
`plan_realtime_integration` prompt turns those rules into an application design.
See the official
[Realtime SDK repository](https://github.com/oracle/oci-ai-speech-realtime-python-sdk)
and the
[live-transcription LiveLab](https://oracle-livelabs.github.io/analytics-ai/oci-artificial-intelligence/ai-speech/workshops/freetier/index.html?lab=transcribe-live-audio)
for maintained examples.

## Source layout

The package uses capability folders without forcing every capability into the
same template:

- `tools/` contains transcription, customization, TTS, and Notifications tool
  modules;
- `prompts/` contains explicit prompt functions grouped by workflow—there is no
  duplicate prompt-template dictionary;
- `resources/` contains explicit guide functions for administration,
  transcription, customization, TTS, Notifications, and Realtime;
- `models.py` is the single source for shared Pydantic models and constrained
  Speech types;
- `utils/` contains OCI client construction, safe path handling, pagination,
  response envelopes, error handling, and streamed-file helpers.

Each folder's `__init__.py` explicitly registers its modules. The package root
therefore stays limited to metadata, the central models, and the `server.py`
entry point. Realtime remains guidance-first because its WebSocket belongs in
the audio-producing application rather than a bounded stdio tool call.

## Development and validation

From the repository root:

```sh
make test project=oci-speech-mcp-server
make lint
```

The package enforces at least 90% unit-test coverage in `pyproject.toml`.

## References

- [OCI Speech documentation](https://docs.oracle.com/en-us/iaas/Content/speech/home.htm)
- [OCI Speech API reference](https://docs.oracle.com/en-us/iaas/api/#/en/speech/20220101/)
- [OCI Speech IAM policies](https://docs.oracle.com/en-us/iaas/Content/speech/using/policies.htm)
- [OCI Speech limits](https://docs.oracle.com/en-us/iaas/Content/speech/using/speech.htm#ser-limits)
- [OCI Speech TTS and SSML](https://docs.oracle.com/en-us/iaas/Content/speech/using/using-tts.htm)
- [OCI Speech LiveLab](https://livelabs.oracle.com/ords/r/dbpm/livelabs/run-workshop?p210_wid=3135)
- [OCI Python SDK Speech API](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/ai_speech/client/oci.ai_speech.AIServiceSpeechClient.html)
- [OCI Realtime Speech Python SDK](https://github.com/oracle/oci-ai-speech-realtime-python-sdk)
- [OCI Realtime Speech package on PyPI](https://pypi.org/project/oci-ai-speech-realtime/)
