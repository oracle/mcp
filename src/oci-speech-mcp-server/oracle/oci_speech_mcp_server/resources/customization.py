"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP

CUSTOMIZATIONS_GUIDE = """# Speech customizations

Customizations improve how the Oracle ASR model transcribes domain-specific
words and phrases in Realtime Speech. Typical targets include acronyms, proper
nouns, medications, product names, locations, or a desired written replacement
for a spoken form. They are managed as OCI resources through create, get, list,
update, delete, and change-compartment operations.

## Entities and pronunciations

An entity's `value` is the exact output text wanted in the transcript. Each
entity can have multiple `sounds_like` strings and one Object Storage audio
pronunciation list. Examples include an acronym whose sounds-like form spells
its syllables, a person's canonical name with several spoken nicknames, or a
domain phrase with an uploaded example pronunciation. Use weights only when the
dataset design calls for a deliberate relative bias; do not assign arbitrary
weights to every entity.

## Entity lists and reuse

An entity list groups entities under an `entity_type`, such as `medication`,
`person`, or `city`. A populated list can include an optional alias. During
creation, every populated entity list becomes a reusable entity customization.

Instead of resending entities, a list may reference an existing reusable entity
customization. Set the list's `entities=[]` and provide exactly one of
`customization_id` or `alias`, along with the entity type for the new context.
The referenced customization must be usable as an entity source and must not be
in FAILED state. Do not rely on an exposed "type" property: the external
GetCustomization response has no customization-type field.

## Reference examples and relationships

Reference examples describe common sentence patterns and use placeholders that
match entity types, for example:

```text
patient name is <PERSON>
<PERSON> was prescribed <MEDICATION>
take <MEDICATION> twice daily
```

Multiple entity types can appear in one dataset and in one sentence. Every
placeholder must match an entity type supplied by an entity list; an unknown
placeholder causes training to fail, so the input model validates this before
the API call.

When reference examples are present, the API creates a contextual customization
whose default entity sources correspond to the supplied lists. Populated lists
also create reusable entity customizations. When the dataset has one populated
entity list and no reference examples, the result is a reusable entity
customization rather than a contextual one.

## Realtime inference

Enable an ACTIVE contextual customization in the Oracle Realtime client to use
its default entity sources. An application can override the source for a given
entity type at inference time with another ACTIVE reusable entity customization
OCID. This lets one sentence-pattern customization serve different customers,
departments, product catalogs, or name lists without retraining the contextual
patterns. Keep `should_ignore_invalid_customizations=False` when silently using
the base model would be unsafe.

## Review checklist

1. Use the exact target output in `value` and realistic pronunciation variants.
2. Keep each entity type semantically consistent and reusable.
3. Make placeholders and entity types match case-insensitively.
4. Prefer representative sentence patterns over exhaustive prose.
5. Confirm Object Storage access for audio pronunciations and managed datasets.
6. Review the proposed dataset before create/update because both start training.
7. Wait for lifecycle state ACTIVE before inference; inspect lifecycle details on
   FAILED rather than retrying an unchanged dataset.

For large managed datasets, use the Object Storage dataset form with at most
1,024 object names.
"""


def customizations_guide() -> str:
    return CUSTOMIZATIONS_GUIDE


def register_resources(mcp: FastMCP) -> None:
    mcp.resource(
        "speech://guides/customizations",
        description="OCI Speech entities, reusable entity lists, and contextual datasets.",
    )(customizations_guide)

