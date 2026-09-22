# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""Stable public tool catalog."""

from __future__ import annotations

TOOL_NAMES = (
    "detect_dominant_language",
    "detect_language_text_classification",
    "detect_language_entities",
    "detect_language_key_phrases",
    "detect_language_sentiments",
    "detect_language_pii_entities",
    "translate_language_text",
)

TOOL_ARGUMENTS = {
    "detect_dominant_language": frozenset(
        {
            "documents",
            "compartment_id",
            "should_ignore_transliteration",
            "chars_to_consider",
            "options",
        }
    ),
    "detect_language_text_classification": frozenset(
        {"documents", "compartment_id", "options"}
    ),
    "detect_language_entities": frozenset(
        {"documents", "compartment_id", "options"}
    ),
    "detect_language_key_phrases": frozenset(
        {"documents", "compartment_id", "options"}
    ),
    "detect_language_sentiments": frozenset(
        {"documents", "compartment_id", "levels", "options"}
    ),
    "detect_language_pii_entities": frozenset(
        {"documents", "compartment_id", "masking", "options"}
    ),
    "translate_language_text": frozenset(
        {
            "documents",
            "compartment_id",
            "target_language_code",
            "no_translate",
            "options",
        }
    ),
}
