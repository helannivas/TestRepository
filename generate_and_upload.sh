#!/bin/bash
set -euo pipefail

echo "=================================================="
echo " Key Pair Generation + GCP Secret Manager Upload"
echo "=================================================="

# ── hardcoded config ──────────────────────────────────
GCP_PROJECT="project-edaab515-4141-40a2-a68"
SECRET_PREFIX="SNOWFLAKE_SVC"

# ── step 1: generate random passphrase ───────────────
echo ""
echo "[1/5] Generating random passphrase..."
PASSPHRASE=$(openssl rand -base64 32)
echo "      Passphrase generated OK"

# ── step 2: create temp directory ────────────────────
KEY_DIR=$(mktemp -d)
RSA_PATH="$KEY_DIR/rsa.pem"
PRIVATE_PATH="$KEY_DIR/snowflake_key.p8"
PUBLIC_PATH="$KEY_DIR/snowflake_key.pub"

# always clean up temp files on exit
cleanup() {
  rm -rf "$KEY_DIR"
  echo "      Temp files deleted"
}
trap cleanup EXIT

# ── step 3: generate RSA 2048 key ────────────────────
echo ""
echo "[2/5] Generating RSA 2048 key..."
openssl genrsa \
  -out "$RSA_PATH" \
  2048 2>/dev/null
echo "      RSA key generated OK"

echo ""
echo "[3/5] Converting to encrypted PKCS8 (.p8)..."
openssl pkcs8 \
  -topk8 \
  -v2 aes-256-cbc \
  -in      "$RSA_PATH" \
  -out     "$PRIVATE_PATH" \
  -passout "pass:$PASSPHRASE"
echo "      PKCS8 conversion OK"

echo ""
echo "[4/5] Extracting public key..."
openssl rsa \
  -in     "$PRIVATE_PATH" \
  -passin "pass:$PASSPHRASE" \
  -pubout \
  -out    "$PUBLIC_PATH" 2>/dev/null
echo "      Public key extracted OK"

# strip headers for Snowflake ALTER USER
PUBLIC_KEY_STRIPPED=$(grep -v '\-\-\-\-\-' "$PUBLIC_PATH" | tr -d '\n')

# ── step 5: upload to GCP Secret Manager ─────────────
echo ""
echo "[5/5] Uploading secrets to GCP Secret Manager..."

echo "      Uploading ${SECRET_PREFIX}_PRIVATE_KEY..."
gcloud secrets versions add "${SECRET_PREFIX}_PRIVATE_KEY" \
  --project="$GCP_PROJECT" \
  --data-file="$PRIVATE_PATH"
echo "      ${SECRET_PREFIX}_PRIVATE_KEY uploaded OK"

echo "      Uploading ${SECRET_PREFIX}_PASSPHRASE..."
printf '%s' "$PASSPHRASE" | \
gcloud secrets versions add "${SECRET_PREFIX}_PASSPHRASE" \
  --project="$GCP_PROJECT" \
  --data-file=-
echo "      ${SECRET_PREFIX}_PASSPHRASE uploaded OK"

echo "      Uploading ${SECRET_PREFIX}_PUBLIC_KEY..."
printf '%s' "$PUBLIC_KEY_STRIPPED" | \
gcloud secrets versions add "${SECRET_PREFIX}_PUBLIC_KEY" \
  --project="$GCP_PROJECT" \
  --data-file=-
echo "      ${SECRET_PREFIX}_PUBLIC_KEY uploaded OK"

echo ""
echo "=================================================="
echo " COMPLETE"
echo " Project : $GCP_PROJECT"
echo " Secrets :"
echo "   ${SECRET_PREFIX}_PRIVATE_KEY"
echo "   ${SECRET_PREFIX}_PASSPHRASE"
echo "   ${SECRET_PREFIX}_PUBLIC_KEY"
echo "=================================================="
