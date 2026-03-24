import pytest
from pydantic import ValidationError

from oracle.oci_ag_mcp_server.models import (
    map_identity,
    map_identity_collection,
    map_access_bundle,
    map_orchestrated_system,
    map_access_request,
    Identity,
    IdentityCollection,
    AccessBundle,
    OrchestratedSystem,
    AccessRequest
)


class TestAGModels:

    # ---------- Identity ----------

    def test_map_identity(self):
        data = {"id": "id1", "name": "User1"}

        result = map_identity(data)

        assert isinstance(result, Identity)
        assert result.id == "id1"
        assert result.name == "User1"


    # ---------- IdentityCollection ----------

    def test_map_identity_collection(self):
        data = {"id": "col1", "name": "Collection1"}

        result = map_identity_collection(data)

        assert isinstance(result, IdentityCollection)
        assert result.id == "col1"
        assert result.name == "Collection1"


    # ---------- Access Bundle ----------

    def test_map_access_bundle(self):
        data = {"id": "b1", "displayName": "Bundle1"}

        result = map_access_bundle(data)
        assert isinstance(result, AccessBundle)
        assert result.id == "b1"
        assert result.name == "Bundle1"


    # ---------- Orchestrated System ----------

    def test_map_orchestrated_system(self):
        data = {"id": "sys1", "displayName": "System1", "type": "APP"}

        result = map_orchestrated_system(data)

        assert isinstance(result, OrchestratedSystem)
        assert result.id == "sys1"
        assert result.name == "System1"
        assert result.type == "APP"


    # ---------- Access Request ----------

    def test_map_access_request(self):
        data = {
            "id": "req1",
            "justification": "testing",
            "requestStatus": "PENDING",
            "timeCreated": "2025-03-20",
            "timeUpdated": "2025-03-20"
        }

        result = map_access_request(data)

        assert isinstance(result, AccessRequest)

        assert result.id == "req1"
        assert result.justification == "testing"
        assert result.requestStatus == "PENDING"
        assert result.timeCreated == "2025-03-20"
        assert result.timeUpdated == "2025-03-20"