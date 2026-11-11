from oracle.oci_cloud_mcp_server.server import (
    _import_models_module_from_client_fqn,
    _resolve_model_class,
    _serialize_oci_data,
    _snake_to_camel,
)

from oracle.oci_cloud_mcp_server.tests.sdk_fixtures import sdk_models


class TestSnakeToCamel:
    def test_basic_conversion(self):
        assert _snake_to_camel("create_vcn_details") == "CreateVcnDetails"
        assert _snake_to_camel("update_instance_configuration") == "UpdateInstanceConfiguration"

    def test_ignores_empty_segments(self):
        # leading/trailing/multiple underscores produce empty parts which should be skipped
        assert _snake_to_camel("__x__y") == "XY"
        assert _snake_to_camel("___") == ""


class TestImportModelsModuleFromClientFqn:
    def test_success_returns_module(self):
        import oci

        assert _import_models_module_from_client_fqn("oci.core.compute_client.ComputeClient") is oci.core.models

    def test_invalid_client_is_rejected(self):
        import pytest

        with pytest.raises(ValueError, match="Unknown OCI SDK service"):
            _import_models_module_from_client_fqn("oci.not_a_service.MissingClient")


class TestResolveModelClass:
    def test_not_found_returns_none(self):
        mm = sdk_models()
        assert _resolve_model_class(mm, "Missing") is None


class TestSerializeOciData:
    def test_handles_nested_primitives_and_tuples(self):
        data = {"a": [1, {"b": 2}, (3, 4)], "c": ("x", "y")}
        out = _serialize_oci_data(data)
        # tuples should be converted to lists, dictionaries preserved
        assert out["a"][2] == [3, 4]
        assert out["c"] == ["x", "y"]
        assert out["a"][1] == {"b": 2}

    def test_when_to_dict_raises_uses_fallback_and_str_for_non_jsonable(self, monkeypatch):
        # force oci.util.to_dict to raise to hit exception path
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        def boom(obj):  # noqa: ARG001
            raise Exception("no to_dict")

        monkeypatch.setattr(_oci.util, "to_dict", boom, raising=False)

        class P:
            pass

        out = _serialize_oci_data(P())
        # should be stringified
        assert isinstance(out, str)
        assert "P" in out
