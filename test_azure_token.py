import os
import json
import base64
from azure.identity import DefaultAzureCredential

AZURE_CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
AZURE_TENANT_ID = os.environ["AZURE_TENANT_ID"]

print("=" * 50)
print("Azure Token POC")
print("=" * 50)

# ── get token ─────────────────────────────────────
print("\n[1/2] Getting Azure token...")

try:
    credential = DefaultAzureCredential()

    # user.read scope format for Microsoft Graph
    token_obj  = credential.get_token(
        "https://graph.microsoft.com/.default"
    )
    token = token_obj.token
    print("      Token obtained OK")
    print(f"      Expires at: {token_obj.expires_on}")

except Exception as e:
    print(f"      FAILED: {e}")
    exit(1)

# ── decode and print claims ───────────────────────
print("\n[2/2] Decoding token claims...")

try:
    payload  = token.split(".")[1]
    payload += "=" * (4 - len(payload) % 4)
    claims   = json.loads(base64.b64decode(payload))

    print(f"\n      iss   : {claims.get('iss',   'NOT FOUND')}")
    print(f"      appid : {claims.get('appid', 'NOT FOUND')}")
    print(f"      sub   : {claims.get('sub',   'NOT FOUND')}")
    print(f"      aud   : {claims.get('aud',   'NOT FOUND')}")
    print(f"      scp   : {claims.get('scp',   'NOT FOUND')}")

except Exception as e:
    print(f"      FAILED to decode: {e}")
    exit(1)

print("\n" + "=" * 50)
print("POC PASSED — token retrieved successfully")
print("=" * 50)
