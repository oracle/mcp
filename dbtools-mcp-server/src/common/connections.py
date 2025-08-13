import oci
from oci.signer import Signer
from src.common.config import *

profile_name = os.getenv("OCI_PROFILE", "DEFAULT")

config = oci.config.from_file(profile_name=profile_name)

identity_client = oci.identity.IdentityClient(config)

search_client = oci.resource_search.ResourceSearchClient(config)
database_client = oci.database.DatabaseClient(config)
dbtools_client = oci.database_tools.DatabaseToolsClient(config)
vault_client = oci.vault.VaultsClient(config)
secrets_client = oci.secrets.SecretsClient(config)
ords_endpoint = dbtools_client.base_client._endpoint.replace("https://", "https://sql.")

auth_signer = Signer(
    tenancy=config['tenancy'],
    user=config['user'],
    fingerprint=config['fingerprint'],
    private_key_file_location=config['key_file'],
    pass_phrase=config['pass_phrase']
)
tenancy_id = os.getenv("TENANCY_ID_OVERRIDE", config['tenancy'])