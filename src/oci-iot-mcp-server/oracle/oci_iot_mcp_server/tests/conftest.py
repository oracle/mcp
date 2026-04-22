import pytest

from oracle.oci_iot_mcp_server.client import clear_iot_client_cache


@pytest.fixture(autouse=True)
def reset_iot_client_cache():
    clear_iot_client_cache()
    yield
    clear_iot_client_cache()
