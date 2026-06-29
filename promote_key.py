import snowflake.connector
from azure.identity import DefaultAzureCredential
from google.cloud import secretmanager

# ── config ────────────────────────────────────────
SNOWFLAKE_RESOURCE_APP = "fea65ab4-0dbb-44f0-b7dd-8e80dba8395d"
SNOWFLAKE_ACCOUNT      = "HMTLBRJ-IY80390"
GCP_PROJECT            = "project-edaab515-4141-40a2-a68"
SECRET_PREFIX          = "SNOWFLAKE_SVC"

print("=" * 55)
print(" Promote RSA_2 → RSA_1")
print("=" * 55)

# ── step 1: fetch public key ──────────────────────
print("\n[1/3] Fetching public key from Secret Manager...")
sm_client = secretmanager.SecretManagerServiceClient()
path      = f"projects/{GCP_PROJECT}/secrets/{SECRET_PREFIX}_PUBLIC_KEY/versions/latest"
public_key = sm_client.access_secret_version(
    request={"name": path}
).payload.data.decode()
print(f"      Public key fetched OK")

# ── step 2: get Azure token ───────────────────────
print("\n[2/3] Getting Azure token...")
credential  = DefaultAzureCredential()
azure_token = credential.get_token(
    f"api://{SNOWFLAKE_RESOURCE_APP}/.default"
).token
print("      Token obtained OK")

# ── step 3: connect + call promote procedure ──────
print("\n[3/3] Connecting to Snowflake and promoting key...")
try:
    conn = snowflake.connector.connect(
        account       = SNOWFLAKE_ACCOUNT,
        authenticator = "oauth",
        token         = azure_token,
        warehouse     = "COMPUTE_WH",
        database      = "SNOWFLAKE_PIPELINE_DB",
        schema        = "PIPELINE_SCHEMA",
        role          = "PIPELINE_ADMIN_ROLE"
    )
    print("      Connected OK")

    cur    = conn.cursor()
    result = cur.execute(
        f"CALL SNOWFLAKE_PIPELINE_DB.PIPELINE_SCHEMA.promote_svc_public_key('{public_key}')"
    ).fetchone()

    print(f"      Result: {result[0]}")

    if "ERROR" in result[0]:
        raise RuntimeError(f"Promote failed: {result[0]}")

    cur.close()
    conn.close()

    print("\n" + "=" * 55)
    print(" Promotion COMPLETE ✓")
    print(" RSA_1 = new key")
    print(" RSA_2 = empty (ready for next rotation)")
    print("=" * 55)

except Exception as e:
    print(f"\n[ERROR] {e}")
    raise
