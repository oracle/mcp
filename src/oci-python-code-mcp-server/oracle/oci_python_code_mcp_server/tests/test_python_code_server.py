from types import ModuleType
from unittest.mock import patch

import pytest
from fastmcp import Client

from oracle.oci_python_code_mcp_server import server as server_module
from oracle.oci_python_code_mcp_server.compiler import (
    OciSdkCompileError,
    ResultReference,
    compile_oci_sdk_call,
    compile_oci_sdk_program,
    compile_oci_sdk_procedure,
)
from oracle.oci_python_code_mcp_server.server import mcp


def _client_entry(runtime_client_fqn: str, public_client: str) -> dict[str, str]:
    module_name, class_name = runtime_client_fqn.rsplit(".", 1)
    return {
        "client": public_client,
        "service_module": public_client.rsplit(".", 1)[0],
        "runtime_client_fqn": runtime_client_fqn,
        "runtime_module": module_name,
        "class": class_name,
    }


@pytest.fixture(autouse=True)
def _clear_server_caches():
    server_module._discover_oci_clients.cache_clear()
    server_module._discover_operation_catalog.cache_clear()
    yield
    server_module._discover_oci_clients.cache_clear()
    server_module._discover_operation_catalog.cache_clear()


class TestCompiler:
    def test_compiles_natural_client_code_with_setup_boilerplate(self, monkeypatch):
        class IdentityClient:
            def get_tenancy(self, tenancy_id):  # noqa: ARG002
                return None

        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        monkeypatch.setattr(
            "oracle.oci_python_code_mcp_server.compiler.import_module",
            lambda name: fake_public_module if name == "oci.fake" else None,
        )

        payload = compile_oci_sdk_call(
            """
import oci
config = oci.config.from_file()
client = oci.fake.IdentityClient(config, signer=signer)
client.get_tenancy("ocid1.tenancy...")
            """.strip()
        )

        assert payload == {
            "client_fqn": "oci.fake.IdentityClient",
            "operation": "get_tenancy",
            "params": {"tenancy_id": "ocid1.tenancy..."},
        }

    def test_compiles_result_reference_in_procedure(self, monkeypatch):
        class IdentityClient:
            def get_tenancy(self, tenancy_id):  # noqa: ARG002
                return None

            def list_region_subscriptions(self, tenancy_id):  # noqa: ARG002
                return None

        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        monkeypatch.setattr(
            "oracle.oci_python_code_mcp_server.compiler.import_module",
            lambda name: fake_public_module if name == "oci.fake" else None,
        )

        plan = compile_oci_sdk_procedure(
            """
from oci.fake import IdentityClient
tenancy = IdentityClient().get_tenancy("ocid1.tenancy...")
IdentityClient().list_region_subscriptions(tenancy_id=tenancy["id"])
            """.strip()
        )

        assert len(plan["steps"]) == 2
        assert plan["steps"][0]["label"] == "tenancy"
        assert plan["steps"][1]["params"]["tenancy_id"] == ResultReference(
            "tenancy", (("key", "id"),)
        )

    def test_rejects_reserved_internal_metadata_keys(self, monkeypatch):
        class NetworkClient:
            def create_vcn(self, vcn_details):  # noqa: ARG002
                return None

        fake_public_module = ModuleType("oci.fake")
        fake_public_module.NetworkClient = NetworkClient
        monkeypatch.setattr(
            "oracle.oci_python_code_mcp_server.compiler.import_module",
            lambda name: fake_public_module if name == "oci.fake" else None,
        )

        with pytest.raises(OciSdkCompileError, match="reserved for internal metadata"):
            compile_oci_sdk_call(
                """
from oci.fake import NetworkClient
NetworkClient().create_vcn(
    vcn_details={"__model_fqn": "oci.core.models.CreateVcnDetails"}
)
                """.strip()
            )

    def test_compiles_setup_value_reference_for_api_argument(self, monkeypatch):
        class IdentityClient:
            def list_compartments(self, compartment_id, **kwargs):  # noqa: ARG002
                return None

        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        monkeypatch.setattr(
            "oracle.oci_python_code_mcp_server.compiler.import_module",
            lambda name: fake_public_module if name == "oci.fake" else None,
        )

        program = compile_oci_sdk_program(
            """
import oci
config = oci.config.from_file()
client = oci.fake.IdentityClient(config)
client.list_compartments(compartment_id=config["tenancy"])
            """.strip()
        )

        assert program["steps"][0]["params"]["compartment_id"] == ResultReference(
            "config", (("key", "tenancy"),)
        )
        assert program["setup_bindings"] == {"config": "oci.config.from_file()"}

    def test_procedure_limit_and_destructive_policy(self, monkeypatch):
        class ComputeClient:
            def get_instance(self, instance_id):  # noqa: ARG002
                return None

            def terminate_instance(self, instance_id):  # noqa: ARG002
                return None

        fake_public_module = ModuleType("oci.fake")
        fake_public_module.ComputeClient = ComputeClient
        monkeypatch.setattr(
            "oracle.oci_python_code_mcp_server.compiler.import_module",
            lambda name: fake_public_module if name == "oci.fake" else None,
        )

        with pytest.raises(OciSdkCompileError, match="at most 3 steps"):
            compile_oci_sdk_procedure(
                """
from oci.fake import ComputeClient
ComputeClient().get_instance(instance_id="1")
ComputeClient().get_instance(instance_id="2")
ComputeClient().get_instance(instance_id="3")
ComputeClient().get_instance(instance_id="4")
                """.strip()
            )

        with pytest.raises(OciSdkCompileError, match="final step"):
            compile_oci_sdk_procedure(
                """
from oci.fake import ComputeClient
ComputeClient().terminate_instance(instance_id="1")
ComputeClient().get_instance(instance_id="1")
                """.strip()
            )


class TestRunOciSdkCode:
    @pytest.mark.asyncio
    async def test_executes_natural_client_code(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-123"}

        class IdentityClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_tenancy(self, tenancy_id):
                return FakeResponse({"id": tenancy_id, "name": "demo"})

        IdentityClient.__module__ = "oci.fake.identity_client"
        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        fake_runtime_module = ModuleType("oci.fake.identity_client")
        fake_runtime_module.IdentityClient = IdentityClient

        def importer(name):
            if name == "oci.fake":
                return fake_public_module
            if name == "oci.fake.identity_client":
                return fake_runtime_module
            raise ImportError(name)

        source = """
import oci
config = oci.config.from_file()
identity = oci.fake.IdentityClient(config, signer=signer)
identity.get_tenancy("ocid1.tenancy...")
        """.strip()

        with (
            patch("oracle.oci_python_code_mcp_server.compiler.import_module", side_effect=importer),
            patch("oracle.oci_python_code_mcp_server.server.import_module", side_effect=importer),
            patch(
                "oracle.oci_python_code_mcp_server.server._discover_oci_clients",
                return_value=(
                    _client_entry(
                        "oci.fake.identity_client.IdentityClient",
                        "oci.fake.IdentityClient",
                    ),
                ),
            ),
            patch("oracle.oci_python_code_mcp_server.server._get_config_and_signer") as mock_cfg,
        ):
            mock_cfg.return_value = ({}, object())
            async with Client(mcp) as client:
                result = (await client.call_tool("run_oci_sdk_code", {"source": source})).data

        assert result["method_ref"] == "oci.fake.IdentityClient.get_tenancy"
        assert result["data"] == {"id": "ocid1.tenancy...", "name": "demo"}
        assert result["source"] == source

    @pytest.mark.asyncio
    async def test_dry_run_returns_python_oriented_preview(self, monkeypatch):
        class IdentityClient:
            def get_tenancy(self, tenancy_id):  # noqa: ARG002
                return None

        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        monkeypatch.setattr(
            "oracle.oci_python_code_mcp_server.compiler.import_module",
            lambda name: fake_public_module if name == "oci.fake" else None,
        )
        monkeypatch.setattr(
            "oracle.oci_python_code_mcp_server.server._discover_oci_clients",
            lambda: (
                _client_entry(
                    "oci.fake.identity_client.IdentityClient",
                    "oci.fake.IdentityClient",
                ),
            ),
        )

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "run_oci_sdk_code",
                    {
                        "source": """
from oci.fake import IdentityClient
client = IdentityClient()
client.get_tenancy("ocid1.tenancy...")
                        """.strip(),
                        "execute": False,
                    },
                )
            ).data

        assert result["executed"] is False
        assert result["preview_steps"] == [
            {
                "step": 1,
                "method_ref": "oci.fake.IdentityClient.get_tenancy",
                "argument_names": ["tenancy_id"],
            }
        ]

    @pytest.mark.asyncio
    async def test_executes_nested_model_constructor(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-model"}

        class CreateVcnDetails:
            def __init__(self, **kwargs):
                self.kwargs = dict(kwargs)

        class NetworkClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def create_vcn(self, create_vcn_details):
                assert isinstance(create_vcn_details, CreateVcnDetails)
                return FakeResponse({"display_name": create_vcn_details.kwargs["display_name"]})

        NetworkClient.__module__ = "oci.fake.network_client"
        CreateVcnDetails.__module__ = "oci.fake.models"

        fake_public_module = ModuleType("oci.fake")
        fake_public_module.NetworkClient = NetworkClient
        fake_runtime_module = ModuleType("oci.fake.network_client")
        fake_runtime_module.NetworkClient = NetworkClient
        fake_models_module = ModuleType("oci.fake.models")
        fake_models_module.CreateVcnDetails = CreateVcnDetails

        def compiler_import(name):
            if name == "oci.fake":
                return fake_public_module
            if name == "oci.fake.models":
                return fake_models_module
            raise ImportError(name)

        def server_import(name):
            if name == "oci.fake":
                return fake_public_module
            if name == "oci.fake.network_client":
                return fake_runtime_module
            if name == "oci.fake.models":
                return fake_models_module
            raise ImportError(name)

        source = """
from oci.fake import NetworkClient
from oci.fake.models import CreateVcnDetails
network = NetworkClient(config)
network.create_vcn(
    vcn_details=CreateVcnDetails(display_name="demo-vcn")
)
        """.strip()

        with (
            patch("oracle.oci_python_code_mcp_server.compiler.import_module", side_effect=compiler_import),
            patch("oracle.oci_python_code_mcp_server.server.import_module", side_effect=server_import),
            patch(
                "oracle.oci_python_code_mcp_server.server._discover_oci_clients",
                return_value=(
                    _client_entry("oci.fake.network_client.NetworkClient", "oci.fake.NetworkClient"),
                ),
            ),
            patch("oracle.oci_python_code_mcp_server.server._get_config_and_signer") as mock_cfg,
        ):
            mock_cfg.return_value = ({}, object())
            async with Client(mcp) as client:
                result = (await client.call_tool("run_oci_sdk_code", {"source": source})).data

        assert result["method_ref"] == "oci.fake.NetworkClient.create_vcn"
        assert result["data"]["display_name"] == "demo-vcn"

    @pytest.mark.asyncio
    async def test_accepts_trailing_expression_and_derived_assignment(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-regions"}

        class IdentityClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def list_regions(self):
                return FakeResponse(
                    [
                        {"name": "us-ashburn-1"},
                        {"name": "us-phoenix-1"},
                    ]
                )

        IdentityClient.__module__ = "oci.fake.identity_client"
        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        fake_runtime_module = ModuleType("oci.fake.identity_client")
        fake_runtime_module.IdentityClient = IdentityClient

        def importer(name):
            if name == "oci.fake":
                return fake_public_module
            if name == "oci.fake.identity_client":
                return fake_runtime_module
            raise ImportError(name)

        source = """
import oci
config = oci.config.from_file()
identity = oci.fake.IdentityClient(config)
regions = identity.list_regions()
region_names = [region.name for region in regions.data]
region_names
        """.strip()

        with (
            patch("oracle.oci_python_code_mcp_server.compiler.import_module", side_effect=importer),
            patch("oracle.oci_python_code_mcp_server.server.import_module", side_effect=importer),
            patch(
                "oracle.oci_python_code_mcp_server.server._discover_oci_clients",
                return_value=(
                    _client_entry(
                        "oci.fake.identity_client.IdentityClient",
                        "oci.fake.IdentityClient",
                    ),
                ),
            ),
            patch("oracle.oci_python_code_mcp_server.server._get_config_and_signer") as mock_cfg,
        ):
            mock_cfg.return_value = ({}, object())
            async with Client(mcp) as client:
                result = (await client.call_tool("run_oci_sdk_code", {"source": source})).data

        assert result["method_ref"] == "oci.fake.IdentityClient.list_regions"
        assert result["output"] == ["us-ashburn-1", "us-phoenix-1"]
        assert result["data"] == [{"name": "us-ashburn-1"}, {"name": "us-phoenix-1"}]

    @pytest.mark.asyncio
    async def test_procedure_uses_prior_step_results_and_derived_bindings(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-proc"}

        class IdentityClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_tenancy(self, tenancy_id):
                return FakeResponse({"id": tenancy_id, "name": "demo"})

            def list_region_subscriptions(self, tenancy_id):
                return FakeResponse({"tenancy_id": tenancy_id, "count": 3})

        IdentityClient.__module__ = "oci.fake.identity_client"
        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        fake_runtime_module = ModuleType("oci.fake.identity_client")
        fake_runtime_module.IdentityClient = IdentityClient

        def importer(name):
            if name == "oci.fake":
                return fake_public_module
            if name == "oci.fake.identity_client":
                return fake_runtime_module
            raise ImportError(name)

        source = """
from oci.fake import IdentityClient
identity = IdentityClient(config)
tenancy = identity.get_tenancy("ocid1.tenancy...")
tenancy_id = tenancy.data["id"]
identity.list_region_subscriptions(tenancy_id=tenancy_id)
        """.strip()

        with (
            patch("oracle.oci_python_code_mcp_server.compiler.import_module", side_effect=importer),
            patch("oracle.oci_python_code_mcp_server.server.import_module", side_effect=importer),
            patch(
                "oracle.oci_python_code_mcp_server.server._discover_oci_clients",
                return_value=(
                    _client_entry(
                        "oci.fake.identity_client.IdentityClient",
                        "oci.fake.IdentityClient",
                    ),
                ),
            ),
            patch("oracle.oci_python_code_mcp_server.server._get_config_and_signer") as mock_cfg,
        ):
            mock_cfg.return_value = ({}, object())
            async with Client(mcp) as client:
                result = (await client.call_tool("run_oci_sdk_code", {"source": source})).data

        assert result["mode"] == "procedure"
        assert result["completed_steps"] == 2
        assert result["results"][0]["label"] == "tenancy"
        assert result["results"][0]["method_ref"] == "oci.fake.IdentityClient.get_tenancy"
        assert result["results"][1]["method_ref"] == "oci.fake.IdentityClient.list_region_subscriptions"
        assert result["results"][1]["data"] == {"tenancy_id": "ocid1.tenancy...", "count": 3}

    @pytest.mark.asyncio
    async def test_executes_setup_derived_api_argument_and_builtin_output(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-compartments"}

        class IdentityClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def list_compartments(self, compartment_id, **kwargs):  # noqa: ARG002
                return FakeResponse(
                    [
                        {"name": "console-ai-test", "lifecycle_state": "ACTIVE", "parent": compartment_id},
                    ]
                )

        IdentityClient.__module__ = "oci.fake.identity_client"
        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        fake_runtime_module = ModuleType("oci.fake.identity_client")
        fake_runtime_module.IdentityClient = IdentityClient

        def importer(name):
            if name == "oci.fake":
                return fake_public_module
            if name == "oci.fake.identity_client":
                return fake_runtime_module
            raise ImportError(name)

        source = """
import oci
config = oci.config.from_file()
identity = oci.fake.IdentityClient(config)
compartments = identity.list_compartments(
    compartment_id=config["tenancy"],
    compartment_id_in_subtree=True,
    access_level="ANY",
)
[{"name": comp.name, "lifecycle_state": str(comp.lifecycle_state)} for comp in compartments.data]
        """.strip()

        with (
            patch("oracle.oci_python_code_mcp_server.compiler.import_module", side_effect=importer),
            patch("oracle.oci_python_code_mcp_server.server.import_module", side_effect=importer),
            patch(
                "oracle.oci_python_code_mcp_server.server._discover_oci_clients",
                return_value=(
                    _client_entry(
                        "oci.fake.identity_client.IdentityClient",
                        "oci.fake.IdentityClient",
                    ),
                ),
            ),
            patch("oracle.oci_python_code_mcp_server.server._get_config_and_signer") as mock_cfg,
        ):
            mock_cfg.return_value = ({"tenancy": "ocid1.tenancy.oc1..demo"}, object())
            async with Client(mcp) as client:
                result = (await client.call_tool("run_oci_sdk_code", {"source": source})).data

        assert result["method_ref"] == "oci.fake.IdentityClient.list_compartments"
        assert result["data"][0]["parent"] == "ocid1.tenancy.oc1..demo"
        assert result["output"] == [{"name": "console-ai-test", "lifecycle_state": "ACTIVE"}]

    @pytest.mark.asyncio
    async def test_does_not_execute_setup_helper_code(self, monkeypatch):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-regions"}

        class IdentityClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def list_regions(self):
                return FakeResponse([{"name": "us-ashburn-1"}])

        IdentityClient.__module__ = "oci.fake.identity_client"
        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        fake_runtime_module = ModuleType("oci.fake.identity_client")
        fake_runtime_module.IdentityClient = IdentityClient

        def importer(name):
            if name == "oci.fake":
                return fake_public_module
            if name == "oci.fake.identity_client":
                return fake_runtime_module
            raise ImportError(name)

        def should_not_run():
            raise AssertionError("setup helper should not be executed during translation")

        source = """
import oci
config = oci.config.from_file()
signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
identity = oci.fake.IdentityClient(config, signer=signer)
identity.list_regions()
        """.strip()

        with (
            patch("oracle.oci_python_code_mcp_server.compiler.import_module", side_effect=importer),
            patch("oracle.oci_python_code_mcp_server.server.import_module", side_effect=importer),
            patch(
                "oracle.oci_python_code_mcp_server.server._discover_oci_clients",
                return_value=(
                    _client_entry(
                        "oci.fake.identity_client.IdentityClient",
                        "oci.fake.IdentityClient",
                    ),
                ),
            ),
            patch("oracle.oci_python_code_mcp_server.server._get_config_and_signer") as mock_cfg,
        ):
            mock_cfg.return_value = ({"tenancy": "ocid1.tenancy.oc1..demo"}, object())
            monkeypatch.setattr(
                "oracle.oci_python_code_mcp_server.server.oci.auth.signers.InstancePrincipalsSecurityTokenSigner",
                should_not_run,
            )
            async with Client(mcp) as client:
                result = (await client.call_tool("run_oci_sdk_code", {"source": source})).data

        assert result["method_ref"] == "oci.fake.IdentityClient.list_regions"
        assert result["data"] == [{"name": "us-ashburn-1"}]

    @pytest.mark.asyncio
    async def test_does_not_substitute_explicit_from_file_profile(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-compartments"}

        class IdentityClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def list_compartments(self, compartment_id, **kwargs):  # noqa: ARG002
                return FakeResponse([{"parent": compartment_id}])

        IdentityClient.__module__ = "oci.fake.identity_client"
        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        fake_runtime_module = ModuleType("oci.fake.identity_client")
        fake_runtime_module.IdentityClient = IdentityClient

        def importer(name):
            if name == "oci.fake":
                return fake_public_module
            if name == "oci.fake.identity_client":
                return fake_runtime_module
            raise ImportError(name)

        source = """
import oci
config = oci.config.from_file(profile_name="OTHER")
identity = oci.fake.IdentityClient(config)
identity.list_compartments(compartment_id=config["tenancy"])
        """.strip()

        with (
            patch("oracle.oci_python_code_mcp_server.compiler.import_module", side_effect=importer),
            patch("oracle.oci_python_code_mcp_server.server.import_module", side_effect=importer),
            patch(
                "oracle.oci_python_code_mcp_server.server._discover_oci_clients",
                return_value=(
                    _client_entry(
                        "oci.fake.identity_client.IdentityClient",
                        "oci.fake.IdentityClient",
                    ),
                ),
            ),
            patch("oracle.oci_python_code_mcp_server.server._get_config_and_signer") as mock_cfg,
        ):
            mock_cfg.return_value = ({"tenancy": "ocid1.tenancy.oc1..active"}, object())
            async with Client(mcp) as client:
                result = (await client.call_tool("run_oci_sdk_code", {"source": source})).data

        assert result["error"] == "Bound value 'config' is not available yet"

    @pytest.mark.asyncio
    async def test_single_call_error_is_not_masked_by_output_expression(self):
        class IdentityClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def list_compartments(self, compartment_id, **kwargs):  # noqa: ARG002
                raise RuntimeError("boom")

        IdentityClient.__module__ = "oci.fake.identity_client"
        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        fake_runtime_module = ModuleType("oci.fake.identity_client")
        fake_runtime_module.IdentityClient = IdentityClient

        def importer(name):
            if name == "oci.fake":
                return fake_public_module
            if name == "oci.fake.identity_client":
                return fake_runtime_module
            raise ImportError(name)

        source = """
import oci
config = oci.config.from_file()
identity = oci.fake.IdentityClient(config)
compartments = identity.list_compartments(compartment_id=config["tenancy"])
[comp.name for comp in compartments.data]
        """.strip()

        with (
            patch("oracle.oci_python_code_mcp_server.compiler.import_module", side_effect=importer),
            patch("oracle.oci_python_code_mcp_server.server.import_module", side_effect=importer),
            patch(
                "oracle.oci_python_code_mcp_server.server._discover_oci_clients",
                return_value=(
                    _client_entry(
                        "oci.fake.identity_client.IdentityClient",
                        "oci.fake.IdentityClient",
                    ),
                ),
            ),
            patch("oracle.oci_python_code_mcp_server.server._get_config_and_signer") as mock_cfg,
        ):
            mock_cfg.return_value = ({"tenancy": "ocid1.tenancy.oc1..demo"}, object())
            async with Client(mcp) as client:
                result = (await client.call_tool("run_oci_sdk_code", {"source": source})).data

        assert result["method_ref"] == "oci.fake.IdentityClient.list_compartments"
        assert result["error"] == "boom"

    @pytest.mark.asyncio
    async def test_compile_error_is_model_facing(self):
        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "run_oci_sdk_code",
                    {"source": "import oci\nlambda x: x"},
                )
            ).data

        assert result["error_type"] == "compile_error"
        assert "translate this OCI Python snippet" in result["error"]
        assert "Expr" not in result["error"]

    @pytest.mark.asyncio
    async def test_ignores_unsupported_non_invocation_python_when_call_plan_is_valid(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-regions"}

        class IdentityClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def list_regions(self):
                return FakeResponse([{"name": "us-ashburn-1"}])

        IdentityClient.__module__ = "oci.fake.identity_client"
        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        fake_runtime_module = ModuleType("oci.fake.identity_client")
        fake_runtime_module.IdentityClient = IdentityClient

        def importer(name):
            if name == "oci.fake":
                return fake_public_module
            if name == "oci.fake.identity_client":
                return fake_runtime_module
            raise ImportError(name)

        source = """
import oci
config = oci.config.from_file()
identity = oci.fake.IdentityClient(config)
regions = identity.list_regions()
set(region.name for region in regions.data)
        """.strip()

        with (
            patch("oracle.oci_python_code_mcp_server.compiler.import_module", side_effect=importer),
            patch("oracle.oci_python_code_mcp_server.server.import_module", side_effect=importer),
            patch(
                "oracle.oci_python_code_mcp_server.server._discover_oci_clients",
                return_value=(
                    _client_entry(
                        "oci.fake.identity_client.IdentityClient",
                        "oci.fake.IdentityClient",
                    ),
                ),
            ),
            patch("oracle.oci_python_code_mcp_server.server._get_config_and_signer") as mock_cfg,
        ):
            mock_cfg.return_value = ({}, object())
            async with Client(mcp) as client:
                result = (await client.call_tool("run_oci_sdk_code", {"source": source})).data

        assert result["method_ref"] == "oci.fake.IdentityClient.list_regions"
        assert result["data"] == [{"name": "us-ashburn-1"}]
        assert "translation_warnings" in result


class TestDiscoverySurface:
    @pytest.mark.asyncio
    async def test_help_write_oci_sdk_code_returns_method_refs_and_call_stubs(self):
        class IdentityClient:
            def list_regions(self):  # noqa: ARG002
                """List all regions."""
                return None

            def get_tenancy(self, tenancy_id):  # noqa: ARG002
                """Get tenancy."""
                return None

        IdentityClient.__module__ = "oci.fake.identity_client"
        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        fake_runtime_module = ModuleType("oci.fake.identity_client")
        fake_runtime_module.IdentityClient = IdentityClient

        def importer(name):
            if name == "oci.fake":
                return fake_public_module
            if name == "oci.fake.identity_client":
                return fake_runtime_module
            raise ImportError(name)

        with (
            patch("oracle.oci_python_code_mcp_server.server.import_module", side_effect=importer),
            patch(
                "oracle.oci_python_code_mcp_server.server._discover_oci_clients",
                return_value=(
                    _client_entry(
                        "oci.fake.identity_client.IdentityClient",
                        "oci.fake.IdentityClient",
                    ),
                ),
            ),
        ):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool("help_write_oci_sdk_code", {"query": "list regions"})
                ).data

        assert result["count"] >= 1
        assert result["matches"][0]["method_ref"] == "oci.fake.IdentityClient.list_regions"
        assert result["matches"][0]["call_stub"].startswith("oci.fake.IdentityClient.list_regions(")
        assert "score" not in result["matches"][0]
        assert result["matches"][0]["required_params"] == []

    @pytest.mark.asyncio
    async def test_help_write_oci_sdk_code_accepts_natural_code(self):
        class IdentityClient:
            def list_region_subscriptions(self, tenancy_id, **kwargs):  # noqa: ARG002
                """List region subscriptions."""
                expected_kwargs = ["retry_strategy"]  # noqa: F841
                return None

        IdentityClient.__module__ = "oci.fake.identity_client"
        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        fake_runtime_module = ModuleType("oci.fake.identity_client")
        fake_runtime_module.IdentityClient = IdentityClient

        def importer(name):
            if name == "oci.fake":
                return fake_public_module
            if name == "oci.fake.identity_client":
                return fake_runtime_module
            raise ImportError(name)

        source = """
import oci
config = oci.config.from_file()
identity = oci.fake.IdentityClient(config)
identity.list_region_subscriptions()
        """.strip()

        with (
            patch("oracle.oci_python_code_mcp_server.compiler.import_module", side_effect=importer),
            patch("oracle.oci_python_code_mcp_server.server.import_module", side_effect=importer),
            patch(
                "oracle.oci_python_code_mcp_server.server._discover_oci_clients",
                return_value=(
                    _client_entry(
                        "oci.fake.identity_client.IdentityClient",
                        "oci.fake.IdentityClient",
                    ),
                ),
            ),
        ):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool("help_write_oci_sdk_code", {"query": source})
                ).data

        assert result["count"] == 1
        assert result["matches"][0]["method_ref"] == "oci.fake.IdentityClient.list_region_subscriptions"
        assert result["matches"][0]["required_params"] == ["tenancy_id"]
        assert result["matches"][0]["accepted_kwargs"] == ["retry_strategy"]

    @pytest.mark.asyncio
    async def test_help_write_oci_sdk_code_uses_last_sdk_call_in_snippet(self):
        class IdentityClient:
            def list_compartments(self, compartment_id, **kwargs):  # noqa: ARG002
                """List compartments."""
                expected_kwargs = ["access_level", "compartment_id_in_subtree"]  # noqa: F841
                return None

        IdentityClient.__module__ = "oci.fake.identity_client"
        fake_public_module = ModuleType("oci.fake")
        fake_public_module.IdentityClient = IdentityClient
        fake_runtime_module = ModuleType("oci.fake.identity_client")
        fake_runtime_module.IdentityClient = IdentityClient

        def importer(name):
            if name == "oci.fake":
                return fake_public_module
            if name == "oci.fake.identity_client":
                return fake_runtime_module
            raise ImportError(name)

        source = """
import oci
config = oci.config.from_file()
identity = oci.fake.IdentityClient(config)
compartments = identity.list_compartments(compartment_id=config["tenancy"])
[comp.name for comp in compartments.data]
        """.strip()

        with (
            patch("oracle.oci_python_code_mcp_server.compiler.import_module", side_effect=importer),
            patch("oracle.oci_python_code_mcp_server.server.import_module", side_effect=importer),
            patch(
                "oracle.oci_python_code_mcp_server.server._discover_oci_clients",
                return_value=(
                    _client_entry(
                        "oci.fake.identity_client.IdentityClient",
                        "oci.fake.IdentityClient",
                    ),
                ),
            ),
        ):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool("help_write_oci_sdk_code", {"query": source})
                ).data

        assert result["count"] == 1
        assert result["matches"][0]["method_ref"] == "oci.fake.IdentityClient.list_compartments"
        assert result["matches"][0]["required_params"] == ["compartment_id"]

    @pytest.mark.asyncio
    async def test_public_tools_are_minimal(self):
        async with Client(mcp) as client:
            tools = await client.list_tools()

        assert {tool.name for tool in tools} == {
            "run_oci_sdk_code",
            "help_write_oci_sdk_code",
        }


class TestPaginationBehavior:
    def test_uses_bounded_auto_pagination(self, monkeypatch):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-page"}

        def list_compartments(**kwargs):  # noqa: ARG001
            return FakeResponse(["direct"])

        seen = {}

        def fake_paginator(method, record_limit, page_size, **params):
            seen["method"] = method
            seen["record_limit"] = record_limit
            seen["page_size"] = page_size
            seen["params"] = params
            return FakeResponse(["paged"])

        monkeypatch.setattr(
            "oracle.oci_python_code_mcp_server.server.oci.pagination.list_call_get_up_to_limit",
            fake_paginator,
        )
        monkeypatch.setattr(
            "oracle.oci_python_code_mcp_server.server._should_auto_paginate",
            lambda method, params, operation_name: True,
        )

        data, opc_request_id = server_module._call_with_pagination_if_applicable(
            list_compartments,
            {},
            "list_compartments",
        )

        assert data == ["paged"]
        assert opc_request_id == "req-page"
        assert seen["record_limit"] == server_module.AUTO_PAGINATION_MAX_RESULTS
        assert seen["page_size"] == server_module.AUTO_PAGINATION_PAGE_SIZE
        assert seen["params"] == {}

    def test_list_operation_without_page_or_limit_is_not_inferred_paginated(self):
        class IdentityClient:
            def list_regions(self, **kwargs):  # noqa: ARG002
                expected_kwargs = ["retry_strategy"]  # noqa: F841
                return None

        assert server_module._supports_pagination(IdentityClient.list_regions, "list_regions") is False
