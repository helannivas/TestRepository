from google.cloud import secretmanager
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key, Encoding, PrivateFormat, NoEncryption
)
import snowflake.connector

GCP_PROJECT   = "project-edaab515-4141-40a2-a68"
SECRET_PREFIX = "SNOWFLAKE_SVC"
SF_ACCOUNT    = "HMTLBRJ-IY80390"
SF_USER       = "SSVC_SAS_VIYA"
SF_WAREHOUSE  = "COMPUTE_WH"
SF_DATABASE   = "SNOWFLAKE_PIPELINE_DB"
SF_ROLE       = "PIPELINE_ADMIN_ROLE"

print("=" * 55)
print(" Key Pair Validation Test (Cloud Build)")
print("=" * 55)

client = secretmanager.SecretManagerServiceClient()

def get_secret(name):
    path = f"projects/{GCP_PROJECT}/secrets/{name}/versions/latest"
    return client.access_secret_version(
        request={"name": path}
    ).payload.data.decode()

print("\n[1/3] Fetching private key from Secret Manager...")
private_key_pem = get_secret(f"{SECRET_PREFIX}_PRIVATE_KEY")
passphrase       = get_secret(f"{SECRET_PREFIX}_PASSPHRASE")
print("      Private key + passphrase fetched OK")

print("\n[2/3] Decrypting private key...")
private_key = load_pem_private_key(
    private_key_pem.encode(),
    password=passphrase.encode(),
    backend=default_backend()
)
private_key_bytes = private_key.private_bytes(
    encoding=Encoding.DER,
    format=PrivateFormat.PKCS8,
    encryption_algorithm=NoEncryption()
)
print("      Private key decrypted OK")

print("\n[3/3] Connecting to Snowflake using key-pair auth...")
conn = snowflake.connector.connect(
    account     = SF_ACCOUNT,
    user        = SF_USER,
    private_key = private_key_bytes,
    warehouse   = SF_WAREHOUSE,
    database    = SF_DATABASE,
    role        = SF_ROLE
)

cur = conn.cursor()
cur.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE()")
row = cur.fetchone()
print(f"      Connected as  : {row[0]}")
print(f"      Role          : {row[1]}")
print(f"      Warehouse     : {row[2]}")
cur.close()
conn.close()

print("\n" + "=" * 55)
print(" Key pair validation PASSED ✓")
print("=" * 55)
