import json
import base64
import google.auth
import google.auth.transport.requests
import requests

AZURE_TENANT_ID        = "cef8c081-d201-48a9-be90-7f38ac978991"
AZURE_CLIENT_ID        = "51a4cea1-294f-4b79-9fb0-24ce472ae3a3"
SNOWFLAKE_RESOURCE_APP = "fea65ab4-0dbb-44f0-b7dd-8e80dba8395d"

print("=" * 55)
print(" Cloud Build → Azure Token Test")
print("=" * 55)

# ── step 1: get GCP identity token ───────────────
print("\n[1/3] Getting GCP identity token...")
credentials, project = google.auth.default()
credentials.refresh(google.auth.transport.requests.Request())
gcp_token = credentials.token
print("      GCP token obtained OK")

# ── step 2: exchange for Azure token ─────────────
print("\n[2/3] Exchanging GCP token for Azure token...")
response = requests.post(
    f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token",
    data={
        "grant_type":            "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "client_id":             AZURE_CLIENT_ID,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion":      gcp_token,
        "scope":                 f"api://{SNOWFLAKE_RESOURCE_APP}/.default",
        "requested_token_use":   "on_behalf_of"
    }
)

if response.status_code != 200:
    print(f"      FAILED: {response.json()}")
    exit(1)

azure_token = response.json()["access_token"]
print("      Azure token obtained OK")

# ── step 3: decode and print claims ──────────────
print("\n[3/3] Token claims:")
parts    = azure_token.split(".")
payload  = parts[1]
payload += "=" * (4 - len(payload) % 4)
claims   = json.loads(base64.b64decode(payload))

print(f"  iss   : {claims.get('iss')}")
print(f"  aud   : {claims.get('aud')}")
print(f"  sub   : {claims.get('sub')}")
print(f"  appid : {claims.get('appid')}")
print(f"  roles : {claims.get('roles')}")

print("\n" + "=" * 55)
print(" Cloud Build Azure token test PASSED ✓")
print("=" * 55)
