"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP

TEXT_TO_SPEECH_GUIDE = """# Text-to-speech

Call `list_voices` before synthesis when the required voice is not known.
`TTS_1_STANDARD` requires a voice ID. `TTS_2_NATURAL` additionally accepts a
language code. Text may be plain `TEXT` or `SSML` and is limited to 10,000
characters. Read `speech://guides/ssml` before composing or modifying SSML.
Output formats are MP3, PCM, OGG, and JSON; JSON is useful for requested WORD or
SENTENCE speech marks.

Text-to-speech is routed to `us-phoenix-1`. Synthesized content is streamed to a
contained local output file rather than returned through the MCP conversation.
"""

SSML_GUIDE = """# OCI Speech SSML composition guide

## Eligibility and validation

OCI Speech supports SSML only for selected English (United States) voices; it is
not supported by voices in other languages. The current OCI table lists SSML for
the standard voices Brian, Annabelle, Bob, Stacy, Phil, and Cindy, and for the
natural voices Brian, Annabelle, Bob, Stacy, Phil, Cindy, Brad, and Richard.
Voice availability can change, so call `list_voices` and confirm the current OCI
documentation before synthesis.

Every SSML request must be well-formed XML with one `<speak>` root and must set
`text_type="SSML"`. The complete request, including tags, is limited to 10,000
characters. Escape literal `&`, `<`, and `>` as `&amp;`, `&lt;`, and `&gt;`.
The `synthesize_speech` tool rejects malformed XML, a missing `<speak>` root,
and tags outside OCI's supported set before sending the request.

## Supported tags

- `<speak>`: required root; standard and natural voices.
- `<break>`: insert a pause. Use `time="500ms"` or `time="1s"`, or strength
  `none`, `x-weak`, `weak`, `medium`, `strong`, or `x-strong`.
- `<s>`: mark sentence boundaries and sentence-length pauses.
- `<p>`: mark paragraphs and longer paragraph pauses.
- `<say-as>`: control rendering of dates, times, fractions, digits, cardinal or
  ordinal numbers, units, currency, or spelled-out text. Dates need a `format`
  such as `ymd`; units must immediately follow their values, such as `25°C`.
- `<sub alias="...">`: pronounce an abbreviation or symbol using an alias.
- `<phoneme alphabet="ipa|x-sampa" ph="...">`: supply an exact pronunciation.
- `<prosody>`: adjust rate, volume, or pitch. This tag is supported only by
  `TTS_1_STANDARD` voices. Rate accepts named speeds or a relative percentage;
  volume accepts named levels or relative dB; pitch accepts named levels.
- `<voice name="...">`: switch among compatible voices inside one request.

All tags except `<prosody>` are documented for both supported standard and
natural voices.

## Composition examples

Pauses, an expanded acronym, and a date:

```xml
<speak>
  Welcome to <sub alias="Oracle Cloud Infrastructure">OCI</sub>.
  <break time="400ms"/>
  Your appointment is <say-as interpret-as="date" format="ymd">2026-08-21</say-as>.
</speak>
```

Digits, units, and an explicit pronunciation:

```xml
<speak>
  Reference <say-as interpret-as="digits">2048</say-as>.
  The package weighs <say-as interpret-as="unit">5kg</say-as>.
  Say <phoneme alphabet="ipa" ph="ˈɔːrəkəl">Oracle</phoneme> clearly.
</speak>
```

Standard-voice delivery control:

```xml
<speak>
  <p>
    <s><prosody rate="-15%">This sentence is slower.</prosody></s>
    <s><prosody volume="+4dB" pitch="high">This is brighter and louder.</prosody></s>
  </p>
</speak>
```

Two supported voices in one request:

```xml
<speak>
  <voice name="Bob">Welcome to the demonstration.</voice>
  <voice name="Cindy">Thank you. Let us begin.</voice>
</speak>
```

## Agent workflow

When a user asks to customize delivery, first preserve the exact meaning and
identify only the requested goals: pauses, sentence structure, expansion,
pronunciation, speaking rate, volume, pitch, or speaker changes. Compose the
smallest supported SSML needed, show it for review, call `list_voices` when voice
support is uncertain, and then invoke `synthesize_speech` with `text_type=SSML`.
Do not invent pronunciations for names; ask for a sounds-like form or IPA when
the intended pronunciation is unclear. Do not use unsupported web-standard SSML
tags such as `<audio>`, `<emphasis>`, or `<mark>`.

Official SSML and voice-support reference:
https://docs.oracle.com/en-us/iaas/Content/speech/using/using-tts.htm
"""


def text_to_speech_guide() -> str:
    return TEXT_TO_SPEECH_GUIDE


def ssml_guide() -> str:
    return SSML_GUIDE


def register_resources(mcp: FastMCP) -> None:
    mcp.resource(
        "speech://guides/text-to-speech",
        description="OCI Speech voices, synthesis models, and output formats.",
    )(text_to_speech_guide)
    mcp.resource(
        "speech://guides/ssml",
        description="Supported OCI Speech SSML tags, constraints, and examples.",
    )(ssml_guide)

