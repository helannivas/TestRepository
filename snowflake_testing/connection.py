import snowflake.connector
from azure.identity import DefaultAzureCredential

# ── config ────────────────────────────────────────
SNOWFLAKE_RESOURCE_APP = "fea65ab4-0dbb-44f0-b7dd-8e80dba8395d"
SNOWFLAKE_ACCOUNT      = "HMTLBRJ-IY80390"

print("=" * 50)
print(" Snowflake Connection Test")
print("=" * 50)

# get Azure token
print("\n[1/2] Getting Azure token...")
credential  = DefaultAzureCredential()
azure_token = credential.get_token(
    f"api://{SNOWFLAKE_RESOURCE_APP}/.default"
).token
print("      Token OK")

# print raw token parts
parts = azure_token.split(".")
print("\n[RAW TOKEN]")
print(f"Part1.Part2.Part3 for jwt.ms:")
print(f"{parts[0]}.{parts[1]}.{parts[2]}")

# connect to Snowflake
print("\n[2/2] Connecting to Snowflake...")
conn = snowflake.connector.connect(
    account       = SNOWFLAKE_ACCOUNT,
    user          = "SSVC_PIPELINE_USER",
    authenticator = "oauth",
    token         = azure_token
)

cur = conn.cursor()
cur.execute("SELECT CURRENT_USER(), CURRENT_ROLE()")
row = cur.fetchone()
print(f"      Connected as : {row[0]}")
print(f"      Role         : {row[1]}")
cur.close()
conn.close()

print("\n" + "=" * 50)
print(" Connection PASSED ✓")
print("=" * 50)
