"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from types import SimpleNamespace

import oci
import pytest
from oracle.oci_registry_mcp_server.models import (
    ContainerRepository,
    ContainerRepositoryReadme,
    Request,
    Response,
    _oci_to_dict,
    map_container_repository,
    map_container_repository_readme,
    map_request,
    map_response,
)


class TestContainerRepositoryReadme:
    def test_map_container_repository_readme_none(self) -> None:
        assert map_container_repository_readme(None) is None

    def test_map_container_repository_readme_values(self) -> None:
        readme = SimpleNamespace(content="# Repo", format="TEXT_MARKDOWN")
        mapped = map_container_repository_readme(readme)
        assert isinstance(mapped, ContainerRepositoryReadme)
        assert mapped.content == "# Repo"
        assert mapped.format == "TEXT_MARKDOWN"


class TestContainerRepositoryMapping:
    def test_map_container_repository_full(self) -> None:
        ts_created = datetime(2024, 1, 1, 0, 0, 0)
        ts_last = datetime(2024, 1, 2, 0, 0, 0)
        repo_input = SimpleNamespace(
            compartment_id="ocid1.compartment.oc1..xyz",
            created_by="ocid1.user.oc1..user",
            display_name="my/repo",
            id="ocid1.repo.oc1..abc",
            image_count=10,
            is_immutable=True,
            is_public=False,
            layer_count=42,
            layers_size_in_bytes=1000,
            lifecycle_state="AVAILABLE",
            readme=SimpleNamespace(content="hello", format="TEXT_PLAIN"),
            time_created=ts_created,
            time_last_pushed=ts_last,
            billable_size_in_gbs=3,
            namespace="mytenancy",
            freeform_tags={"env": "dev"},
            defined_tags={"Ops": {"CostCenter": "42"}},
            system_tags={"orcl-cloud": {"free-tier-retain": True}},
        )

        mapped = map_container_repository(repo_input)
        assert isinstance(mapped, ContainerRepository)
        assert mapped.compartment_id == "ocid1.compartment.oc1..xyz"
        assert mapped.created_by == "ocid1.user.oc1..user"
        assert mapped.display_name == "my/repo"
        assert mapped.id == "ocid1.repo.oc1..abc"
        assert mapped.image_count == 10
        assert mapped.is_immutable is True
        assert mapped.is_public is False
        assert mapped.layer_count == 42
        assert mapped.layers_size_in_bytes == 1000
        assert mapped.lifecycle_state == "AVAILABLE"
        assert mapped.readme is not None
        assert mapped.readme.content == "hello"
        assert mapped.readme.format == "TEXT_PLAIN"
        assert mapped.time_created == ts_created
        assert mapped.time_last_pushed == ts_last
        assert mapped.billable_size_in_gbs == 3
        assert mapped.namespace == "mytenancy"
        assert mapped.freeform_tags == {"env": "dev"}
        assert mapped.defined_tags == {"Ops": {"CostCenter": "42"}}
        assert mapped.system_tags == {"orcl-cloud": {"free-tier-retain": True}}


class TestRequestAndResponseMapping:
    def test_map_request_none(self) -> None:
        assert map_request(None) is None

    def test_map_request_values(self) -> None:
        req = SimpleNamespace(
            method="GET",
            url="https://example.com",
            query_params={"a": 1},
            header_params={"h": "v"},
            body=None,
            response_type="json",
            enforce_content_headers=True,
        )
        mapped = map_request(req)
        assert isinstance(mapped, Request)
        assert mapped.method == "GET"
        assert mapped.url == "https://example.com"
        assert mapped.query_params == {"a": 1}
        assert mapped.header_params == {"h": "v"}
        assert mapped.response_type == "json"
        assert mapped.enforce_content_headers is True

    def test_map_response_none(self) -> None:
        assert map_response(None) is None

    def test_map_response_with_header_derivation_and_repo_data(self) -> None:
        class FakeResponse:
            pass

        resp = FakeResponse()
        resp.status = 200
        # Provide headers that should derive next_page and request_id
        resp.headers = {"opc-next-page": "np-1", "opc-request-id": "req-123"}
        # next_page property absent -> should be derived from headers
        resp.data = oci.artifacts.models.ContainerRepository(
            display_name="repo1",
            id="ocid1.repo.oc1..abc",
            is_public=False,
            compartment_id="ocid1.compartment.oc1..xyz",
        )
        resp.request = SimpleNamespace(method="GET", url="u")

        mapped = map_response(resp)
        assert isinstance(mapped, Response)
        assert mapped.status == 200
        assert mapped.next_page == "np-1"
        assert mapped.request_id == "req-123"
        assert mapped.has_next_page is True
        # Data should be mapped to ContainerRepository model
        assert isinstance(mapped.data, ContainerRepository)
        assert mapped.data.display_name == "repo1"

    def test_map_response_with_list_data(self) -> None:
        class FakeResponse:
            pass

        sdk_repo = oci.artifacts.models.ContainerRepository(
            display_name="repo2",
            id="ocid1.repo.oc1..def",
            is_public=True,
            compartment_id="ocid1.compartment.oc1..xyz",
        )
        resp = FakeResponse()
        resp.status = 200
        resp.headers = {}
        resp.data = [sdk_repo, "x", 1]
        resp.request = None

        mapped = map_response(resp)
        assert isinstance(mapped, Response)
        assert isinstance(mapped.data, list)
        # First element should be mapped to our Pydantic model
        assert isinstance(mapped.data[0], ContainerRepository)
        assert mapped.data[0].display_name == "repo2"
        # Other primitive elements should pass through
        assert mapped.data[1] == "x"
        assert mapped.data[2] == 1

    def test_map_response_headers_fallback_via_oci_to_dict(self, monkeypatch) -> None:
        class WeirdHeaders:
            def __init__(self) -> None:
                self.k = "v"

        # Force _oci_to_dict path to be exercised so that __dict__ fallback runs
        import oci.util as oci_util  # type: ignore

        def raise_from_oci_to_dict(_: object):
            raise RuntimeError("force fallback")

        monkeypatch.setattr(oci_util, "to_dict", raise_from_oci_to_dict, raising=True)

        # Monkeypatch to ensure dict(headers) path fails and fallback is used
        class FakeResponse:
            pass

        resp = FakeResponse()
        resp.status = 200
        headers_obj = WeirdHeaders()
        resp.headers = headers_obj
        resp.data = None
        resp.request = None

        # Use monkeypatch to make dict() raise when called on headers_obj
        # We cannot patch builtins.dict, so ensure _oci_to_dict handles __dict__
        mapped = map_response(resp)
        assert isinstance(mapped, Response)
        assert mapped.headers == {"k": "v"}


class TestOciToDict:
    def test_oci_to_dict_none(self) -> None:
        assert _oci_to_dict(None) is None

    def test_oci_to_dict_passthrough(self) -> None:
        data = {"a": 1}
        assert _oci_to_dict(data) == {"a": 1}

    def test_oci_to_dict_fallback_filters_private(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class Dummy:
            def __init__(self) -> None:
                self.a = 1
                self._private = 2

        def raise_from_oci_to_dict(_: object):
            raise RuntimeError("force fallback")

        import oci.util as oci_util  # type: ignore

        monkeypatch.setattr(oci_util, "to_dict", raise_from_oci_to_dict, raising=True)

        out = _oci_to_dict(Dummy())
        assert out == {"a": 1}
