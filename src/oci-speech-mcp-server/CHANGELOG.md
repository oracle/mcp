# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## 1.0.0

### Added

- Initial release of the local, stdio OCI Speech MCP server.
- Transcription job and task tools for creating, retrieving, listing, updating,
  canceling, deleting, and moving supported resources between compartments.
- Secure local-file transcription workflow that uploads media to OCI Object
  Storage without replacing existing objects, creates and monitors a
  transcription job, performs ETag-guarded cleanup after job-creation failures,
  reports recovery state for failures after remote side effects begin, and
  downloads completed results to a restricted local output directory.
- Voice discovery and text-to-speech synthesis with private, atomic local output
  handling, SSML structure validation, and OCI-supported SSML composition
  guidance.
- Speech customization tools for inline entities, pronunciations, reference
  examples, Object Storage datasets, and reusable entity customizations.
- OCI Events and Notifications setup for transcription job completion and
  failure events, including structured resource identifiers after partial setup
  failures.
- MCP resources and prompts for prerequisites, IAM policies, service limits,
  transcription and diarization, text-to-speech and SSML, customizations,
  notifications, troubleshooting, and Realtime Speech.
- Realtime Speech SDK guidance covering installation, model and audio settings,
  listener lifecycle, bounded streaming, finalization, reconnection,
  customizations, observability, and troubleshooting.
- OCI SDK authentication through `oracle-mcp-common` with package-derived
  `oci-speech-mcp/1.0.0` client telemetry.
- Truthful MCP tool safety annotations, hard-capped OCI pagination, and
  sanitized service and transport errors.
- Validation and guidance for OCI-supported customization names and current
  Whisper model identifiers.
