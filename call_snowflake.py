import snowflake.connector
from azure.identity import DefaultAzureCredential
from google.cloud import secretmanager

# ── hardcoded config ──────────────────────────────
AZURE_CLIENT_ID   = "51a4cea1-294f-4b79-9fb0-24ce472ae3a3"
SNOWFLAKE_ACCOUNT = "HMTLBRJ-IY80390"
GCP_PROJECT       = "project-edaab515-4141-40a2-a68"
SECRET_PREFIX     = "SNOWFLAKE_SVC"

print("=" * 55)
print(" Snowflake Key Rotation")
print("=" * 55)

# ── step 1: fetch public key from GCP Secret Manager ─
print("\n[1/3] Fetching public key from GCP Secret Manager...")
sm_client  = secretmanager.SecretManagerServiceClient()
secret_path = f"projects/{GCP_PROJECT}/secrets/{SECRET_PREFIX}_PUBLIC_KEY/versions/latest"
public_key  = sm_client.access_secret_version(
    request={"name": secret_path}
).payload.data.decode()
print("      Public key fetched OK")
print(f"      Key length: {len(public_key)} chars")

# ── step 2: get Azure token ───────────────────────
print("\n[2/3] Getting Azure token...")
credential  = DefaultAzureCredential()
azure_token = credential.get_token(
    f"api://{AZURE_CLIENT_ID}/.default"
).token
print("      Token obtained OK")

# ── step 3: connect to Snowflake ──────────────────
print("\n[3/3] Connecting to Snowflake and calling procedure...")
conn = snowflake.connector.connect(
    account       = SNOWFLAKE_ACCOUNT,
    user          = "SSVC_PIPELINE_USER",
    authenticator = "oauth",
    token         = azure_token,
    database      = "SNOWFLAKE_PIPELINE_DB",
    schema        = "PIPELINE_SCHEMA",
    role          = "PIPELINE_ADMIN_ROLE"
)
print("      Connected to Snowflake OK")

# ── step 4: call stored procedure ─────────────────
cur    = conn.cursor()
result = cur.execute(
    "CALL SNOWFLAKE_PIPELINE_DB.PIPELINE_SCHEMA.rotate_svc_public_key(%s)",
    (public_key,)
).fetchone()

print(f"      Procedure result: {result[0]}")

if "ERROR" in result[0]:
    raise RuntimeError(f"Procedure failed: {result[0]}")

cur.close()
conn.close()

print("\n" + "=" * 55)
print(" Key rotation COMPLETE ✓")
print("=" * 55)
