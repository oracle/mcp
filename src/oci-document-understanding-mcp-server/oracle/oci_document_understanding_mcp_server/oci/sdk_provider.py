"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime, timezone
from typing import Any

from oracle.oci_document_understanding_mcp_server import __project__, __version__
from oracle.oci_document_understanding_mcp_server.models import ClassificationRequest, DocumentSource, ExtractionRequest, RawOciDocumentResult
from oracle.oci_document_understanding_mcp_server.oci.config import OciDocumentUnderstandingConfig
from oracle.oci_document_understanding_mcp_server.oci.request_mapper import classification_config, extraction_configs

_user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
_ADDITIONAL_UA = f"{_user_agent_name}/{__version__}"


class OciSdkDocumentUnderstandingProvider:
    """OCI SDK-backed provider for local and production calls."""

    def __init__(self, config: OciDocumentUnderstandingConfig) -> None:
        self.config = config
        self.oci, self.client = self._create_client()

    def extract(self, request: ExtractionRequest) -> RawOciDocumentResult:
        """Submits an extraction request to OCI Document Understanding."""
        response = self._analyze_document(request, operation="extract", feature_types=request.features)
        payload = self._response_to_payload(response)
        payload.setdefault("provider", "oci-sdk")
        payload.setdefault("requestConfigs", extraction_configs(request, self.config))
        return RawOciDocumentResult(
            request_id=self._request_id(response),
            operation="extract",
            received_at=datetime.now(timezone.utc),
            payload=payload,
        )

    def classify(self, request: ClassificationRequest) -> RawOciDocumentResult:
        """Submits a classification request to OCI Document Understanding."""
        response = self._analyze_document(request, operation="classify", feature_types=["DOCUMENT_CLASSIFICATION"])
        payload = self._response_to_payload(response)
        payload.setdefault("provider", "oci-sdk")
        payload.setdefault("requestConfig", classification_config(request, self.config))
        return RawOciDocumentResult(
            request_id=self._request_id(response),
            operation="classify",
            received_at=datetime.now(timezone.utc),
            payload=payload,
        )

    def _create_client(self) -> tuple[Any, Any]:
        """Initializes the OCI Python SDK client for the configured auth mode."""
        try:
            import oci
        except ImportError as exc:
            raise RuntimeError("oci Python SDK is required for local/prod modes. Install with: pip install -e .") from exc

        if self.config.auth_mode == "instance-principal":
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            client_config = {
                "region": self.config.region,
                "additional_user_agent": _ADDITIONAL_UA,
            }
            client = oci.ai_document.AIServiceDocumentClient(client_config, signer=signer)
        elif self.config.auth_mode == "session-token":
            client_config = oci.config.from_file(self.config.config_file_path or oci.config.DEFAULT_LOCATION, self.config.profile)
            client_config["additional_user_agent"] = _ADDITIONAL_UA
            token_file = client_config.get("security_token_file")
            if not token_file:
                raise RuntimeError("session-token auth requires security_token_file in the OCI config profile")
            with open(token_file, encoding="utf-8") as token:
                security_token = token.read()
            private_key = oci.signer.load_private_key_from_file(client_config["key_file"])
            signer = oci.auth.signers.SecurityTokenSigner(security_token, private_key)
            client = oci.ai_document.AIServiceDocumentClient(client_config, signer=signer)
        elif self.config.auth_mode == "api-key":
            client_config = oci.config.from_file(self.config.config_file_path or oci.config.DEFAULT_LOCATION, self.config.profile)
            client_config["additional_user_agent"] = _ADDITIONAL_UA
            client = oci.ai_document.AIServiceDocumentClient(client_config)
        else:
            raise RuntimeError(f"Unsupported OCI auth mode for SDK provider: {self.config.auth_mode}")

        if self.config.endpoint:
            client.base_client.set_endpoint(self.config.endpoint)
        return oci, client

    def _analyze_document(self, request: ExtractionRequest | ClassificationRequest, operation: str, feature_types: list[str]) -> Any:
        """Builds an OCI AnalyzeDocument request and sends it with the SDK client."""
        details = self._build_analyze_document_details(request, operation, feature_types)
        return self.client.analyze_document(analyze_document_details=details)

    def _build_analyze_document_details(self, request: ExtractionRequest | ClassificationRequest, operation: str, feature_types: list[str]) -> Any:
        """Creates SDK model objects for AnalyzeDocument."""
        if not self.config.default_compartment_id:
            raise RuntimeError("OCI_COMPARTMENT_ID is required for OCI Document Understanding requests")
        models = self.oci.ai_document.models
        document = self._document_model(request.document_source)
        features = [self._feature_model(feature_type) for feature_type in feature_types]

        kwargs: dict[str, Any] = {
            "compartment_id": self.config.default_compartment_id,
            "document": document,
            "features": features,
        }
        language = request.options.language
        if language:
            kwargs["language"] = language

        if operation == "classify" and isinstance(request, ClassificationRequest) and request.document_type_hint:
            kwargs["document_type"] = request.document_type_hint

        return models.AnalyzeDocumentDetails(**kwargs)

    def _document_model(self, source: DocumentSource) -> Any:
        """Maps the normalized document source to the OCI SDK document model."""
        models = self.oci.ai_document.models
        page_range = source.page_range

        if source.source_type == "INLINE_BASE64":
            kwargs: dict[str, Any] = {"data": source.document}
            if page_range:
                kwargs["page_range"] = page_range
            return models.InlineDocumentDetails(**kwargs)

        kwargs = {
            "namespace_name": source.namespace_name,
            "bucket_name": source.bucket_name,
            "object_name": source.object_name,
        }
        if page_range:
            kwargs["page_range"] = page_range
        return models.ObjectStorageDocumentDetails(**kwargs)

    def _feature_model(self, feature_type: str) -> Any:
        """Maps public feature names to OCI SDK feature model objects."""
        models = self.oci.ai_document.models
        return {
            "TEXT": models.DocumentTextExtractionFeature,
            "KEY_VALUE": models.DocumentKeyValueExtractionFeature,
            "TABLE": models.DocumentTableExtractionFeature,
            "ELEMENT": models.DocumentElementsExtractionFeature,
            "DOCUMENT_CLASSIFICATION": models.DocumentClassificationFeature,
        }[feature_type]()

    def _response_to_payload(self, response: Any) -> dict[str, Any]:
        """Converts the SDK response object into a JSON-ready payload."""
        data = getattr(response, "data", response)
        if hasattr(data, "to_dict"):
            return data.to_dict()
        if isinstance(data, dict):
            return data
        return {"raw": str(data)}

    def _request_id(self, response: Any) -> str:
        """Extracts the OCI request id used as job_id in the MCP response."""
        headers = getattr(response, "headers", {}) or {}
        return headers.get("opc-request-id") or headers.get("Opc-Request-Id") or "unknown"
