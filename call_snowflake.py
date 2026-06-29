import json
import base64
import snowflake.connector
from azure.identity import DefaultAzureCredential
from google.cloud import secretmanager

# ── hardcoded config ──────────────────────────────
AZURE_CLIENT_ID        = "51a4cea1-294f-4b79-9fb0-24ce472ae3a3"
SNOWFLAKE_RESOURCE_APP = "fea65ab4-0dbb-44f0-b7dd-8e80dba8395d"
SNOWFLAKE_ACCOUNT      = "HMTLBRJ-IY80390"
GCP_PROJECT            = "project-edaab515-4141-40a2-a68"
SECRET_PREFIX          = "SNOWFLAKE_SVC"

print("=" * 55)
print(" Snowflake Key Rotation — DEBUG MODE")
print("=" * 55)

# ── step 1: fetch public key ──────────────────────
print("\n[1/3] Fetching public key from Secret Manager...")
sm_client   = secretmanager.SecretManagerServiceClient()
secret_path = f"projects/{GCP_PROJECT}/secrets/{SECRET_PREFIX}_PUBLIC_KEY/versions/latest"
public_key  = sm_client.access_secret_version(
    request={"name": secret_path}
).payload.data.decode()
print(f"      Public key fetched OK — length: {len(public_key)}")

# ── step 2: get Azure token ───────────────────────
print("\n[2/3] Getting Azure token...")
credential  = DefaultAzureCredential()
azure_token = credential.get_token(
    f"api://{SNOWFLAKE_RESOURCE_APP}/.default"
).token
print("      Token obtained OK")

# ── decode and print ALL claims ───────────────────
print("\n[DEBUG] Full token claims:")
payload  = azure_token.split(".")[1]
payload += "=" * (4 - len(payload) % 4)
claims   = json.loads(base64.b64decode(payload))

for key, value in claims.items():
    print(f"  {key:20} : {value}")

# ── step 3: connect to Snowflake ──────────────────
print("\n[3/3] Connecting to Snowflake...")
try:
    conn = snowflake.connector.connect(
        account       = SNOWFLAKE_ACCOUNT,
        user          = "SSVC_PIPELINE_USER",
        authenticator = "oauth",
        token         = azure_token,
        database      = "SNOWFLAKE_PIPELINE_DB",
        schema        = "PIPELINE_SCHEMA",
        role          = "PIPELINE_ADMIN_ROLE"
    )
    print("      Connected OK")

    cur    = conn.cursor()
    result = cur.execute(
        "CALL SNOWFLAKE_PIPELINE_DB.PIPELINE_SCHEMA.rotate_svc_public_key(%s)",
        (public_key,)
    ).fetchone()
    print(f"      Result: {result[0]}")
    cur.close()
    conn.close()

except Exception as e:
    print(f"\n[ERROR] {e}")
    raise
