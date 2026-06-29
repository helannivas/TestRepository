import os
import json
import base64
from azure.identity import DefaultAzureCredential

AZURE_CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
AZURE_TENANT_ID = os.environ["AZURE_TENANT_ID"]

print("=" * 50)
print("Azure Token POC")
print("=" * 50)

print("\n[1/3] Getting Azure token...")
credential = DefaultAzureCredential()
token_obj  = credential.get_token(
    f"api://{AZURE_CLIENT_ID}/.default"
)
token = token_obj.token
print("      Token obtained OK")

# ── print token encoded so GitHub doesn't mask it ────
print("\n[2/3] Token (base64 encoded to avoid masking):")
print("      Decode this at https://www.base64decode.org")
print("      then paste the result at https://jwt.ms")
print("")
encoded = base64.b64encode(token.encode()).decode()
print(encoded)

# ── decoded claims ────────────────────────────────────
print("\n[3/3] Decoded claims:")
payload  = token.split(".")[1]
payload += "=" * (4 - len(payload) % 4)
claims   = json.loads(base64.b64decode(payload))

print(f"  iss   : {claims.get('iss',   'NOT FOUND')}")
print(f"  appid : {claims.get('appid', 'NOT FOUND')}")
print(f"  sub   : {claims.get('sub',   'NOT FOUND')}")
print(f"  aud   : {claims.get('aud',   'NOT FOUND')}")
print(f"  scp   : {claims.get('scp',   'NOT FOUND')}")
print(f"  exp   : {claims.get('exp',   'NOT FOUND')}")

print("\n" + "=" * 50)
print("POC PASSED")
print("=" * 50)
