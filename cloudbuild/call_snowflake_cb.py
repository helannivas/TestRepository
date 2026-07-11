import snowflake.connector
from google.cloud import secretmanager

GCP_PROJECT       = "project-edaab515-4141-40a2-a68"
SECRET_PREFIX     = "SNOWFLAKE_SVC"
SNOWFLAKE_ACCOUNT = "HMTLBRJ-IY80390"


def get_azure_token():
    from google.auth.compute_engine import IDTokenCredentials
    import google.auth.transport.requests
    import requests

    AZURE_TENANT_ID        = "cef8c081-d201-48a9-be90-7f38ac978991"
    AZURE_CLIENT_ID        = "51a4cea1-294f-4b79-9fb0-24ce472ae3a3"
    SNOWFLAKE_RESOURCE_APP = "fea65ab4-0dbb-44f0-b7dd-8e80dba8395d"
    SA_EMAIL               = "snowflake-pipeline-sa@project-edaab515-4141-40a2-a68.iam.gserviceaccount.com"

    request = google.auth.transport.requests.Request()
    credentials = IDTokenCredentials(
        request,
        target_audience="api://AzureADTokenExchange",
        service_account_email=SA_EMAIL
    )
    credentials.refresh(request)
    gcp_id_token = credentials.token

    response = requests.post(
        f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token",
        data={
            "grant_type":            "client_credentials",
            "client_id":             AZURE_CLIENT_ID,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion":      gcp_id_token,
            "scope":                 f"api://{SNOWFLAKE_RESOURCE_APP}/.default"
        }
    )

    if response.status_code != 200:
        raise RuntimeError(f"Azure token exchange failed: {response.json()}")

    return response.json()["access_token"]


print("=" * 55)
print(" Snowflake Key Rotation (Cloud Build)")
print("=" * 55)

sm_client = secretmanager.SecretManagerServiceClient()

def get_secret(name):
    path = f"projects/{GCP_PROJECT}/secrets/{name}/versions/latest"
    return sm_client.access_secret_version(
        request={"name": path}
    ).payload.data.decode()

print("\n[1/3] Fetching public key from Secret Manager...")
public_key = get_secret(f"{SECRET_PREFIX}_PUBLIC_KEY")
print("      Public key fetched OK")

print("\n[2/3] Getting Azure token...")
azure_token = get_azure_token()
print("      Token obtained OK")

print("\n[3/3] Connecting to Snowflake and rotating key...")
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
    f"CALL SNOWFLAKE_PIPELINE_DB.PIPELINE_SCHEMA.rotate_svc_public_key('{public_key}')"
).fetchone()
print(f"      Result: {result[0]}")

if "ERROR" in result[0]:
    raise RuntimeError(f"Rotation failed: {result[0]}")

cur.close()
conn.close()

print("\n" + "=" * 55)
print(" Rotation COMPLETE ✓")
print("=" * 55)
