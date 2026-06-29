#!/bin/bash
set -euo pipefail

echo "=================================================="
echo " Key Pair Generation + GCP Secret Manager Upload"
echo "=================================================="

GCP_PROJECT="project-edaab515-4141-40a2-a68"
SECRET_PREFIX="SNOWFLAKE_SVC"

echo ""
echo "[1/5] Generating random passphrase..."
PASSPHRASE=$(openssl rand -base64 32)
echo "      Passphrase generated OK"

KEY_DIR=$(mktemp -d)
RSA_PATH="$KEY_DIR/rsa.pem"
PRIVATE_PATH="$KEY_DIR/snowflake_key.p8"
PUBLIC_PATH="$KEY_DIR/snowflake_key.pub"

cleanup() {
  rm -rf "$KEY_DIR"
  echo "      Temp files deleted"
}
trap cleanup EXIT

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

# strip headers — not printed in log
PUBLIC_KEY_STRIPPED=$(grep -v '\-\-\-\-\-' "$PUBLIC_PATH" | tr -d '\n')

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

# ── disable old versions ──────────────────────────
echo ""
echo "[6/5] Disabling old secret versions..."

disable_old_versions() {
  SECRET_NAME="$1"

  # get version numbers only (not full paths)
  VERSIONS=$(gcloud secrets versions list "$SECRET_NAME" \
    --project="$GCP_PROJECT" \
    --filter="state=ENABLED" \
    --sort-by="createTime" \
    --format="value(name.basename())")

  TOTAL=$(echo "$VERSIONS" | grep -c . || true)

  if [ "$TOTAL" -le 1 ]; then
    echo "      $SECRET_NAME — only 1 version, nothing to disable"
    return
  fi

  # get all except latest (last line)
  OLD_VERSIONS=$(echo "$VERSIONS" | head -n -1)

  for VERSION in $OLD_VERSIONS; do
    gcloud secrets versions disable "$VERSION" \
      --secret="$SECRET_NAME" \
      --project="$GCP_PROJECT" \
      --quiet
    echo "      Disabled version: $VERSION"
  done

  echo "      $SECRET_NAME — old versions disabled OK"
}

disable_old_versions "${SECRET_PREFIX}_PRIVATE_KEY"
disable_old_versions "${SECRET_PREFIX}_PASSPHRASE"
disable_old_versions "${SECRET_PREFIX}_PUBLIC_KEY"

echo ""
echo "=================================================="
echo " ALL DONE"
echo " Keys generated and uploaded"
echo " Old versions disabled"
echo "=================================================="
