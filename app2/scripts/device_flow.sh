#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: $0 <keycloak_base_url> <realm> <client_id> [scope]" >&2
  exit 1
fi

BASE_URL="$1"
REALM="$2"
CLIENT_ID="$3"
SCOPE="${4:-openid profile demo2.projects.read demo2.reports.read demo2.users.read}"

DEVICE_ENDPOINT="${BASE_URL%/}/realms/${REALM}/protocol/openid-connect/auth/device"
TOKEN_ENDPOINT="${BASE_URL%/}/realms/${REALM}/protocol/openid-connect/token"

DEVICE_JSON=$(curl -fsS -X POST   -H "Content-Type: application/x-www-form-urlencoded"   --data-urlencode "client_id=${CLIENT_ID}"   --data-urlencode "scope=${SCOPE}"   "$DEVICE_ENDPOINT")

export DEVICE_JSON
DEVICE_CODE=$(python3 -c 'import json, os; print(json.loads(os.environ["DEVICE_JSON"])["device_code"])')
USER_CODE=$(python3 -c 'import json, os; print(json.loads(os.environ["DEVICE_JSON"])["user_code"])')
VERIFICATION_URI=$(python3 -c 'import json, os; payload=json.loads(os.environ["DEVICE_JSON"]); print(payload.get("verification_uri_complete") or payload["verification_uri"])')
INTERVAL=$(python3 -c 'import json, os; print(json.loads(os.environ["DEVICE_JSON"]).get("interval", 5))')

printf "User code: %s
" "$USER_CODE"
printf "Open this URL and complete login:
%s

" "$VERIFICATION_URI"
printf "Polling token endpoint every %s seconds...
" "$INTERVAL"

while true; do
  set +e
  TOKEN_JSON=$(curl -sS -X POST     -H "Content-Type: application/x-www-form-urlencoded"     --data-urlencode "grant_type=urn:ietf:params:oauth:grant-type:device_code"     --data-urlencode "client_id=${CLIENT_ID}"     --data-urlencode "device_code=${DEVICE_CODE}"     "$TOKEN_ENDPOINT")
  STATUS=$?
  set -e

  if [ $STATUS -ne 0 ]; then
    echo "Token request failed; retrying in ${INTERVAL}s" >&2
    sleep "$INTERVAL"
    continue
  fi

  export TOKEN_JSON
  STATUS_NAME=$(python3 -c 'import json, os; payload=json.loads(os.environ["TOKEN_JSON"]); print("success" if "access_token" in payload else payload.get("error", "unknown_error"))')

  if [ "$STATUS_NAME" = "success" ]; then
    ACCESS_TOKEN=$(python3 -c 'import json, os; print(json.loads(os.environ["TOKEN_JSON"])["access_token"])')
    REFRESH_TOKEN=$(python3 -c 'import json, os; payload=json.loads(os.environ["TOKEN_JSON"]); print(payload.get("refresh_token", ""))')
    printf "
Access token:
%s
" "$ACCESS_TOKEN"
    if [ -n "$REFRESH_TOKEN" ]; then
      printf "
Refresh token:
%s
" "$REFRESH_TOKEN"
    fi
    printf "
Example:
"
    printf 'curl -H "Authorization: Bearer %s" https://your-api-host/api/demo2/projects
' "$ACCESS_TOKEN"
    exit 0
  fi

  case "$STATUS_NAME" in
    authorization_pending)
      sleep "$INTERVAL"
      ;;
    slow_down)
      INTERVAL=$((INTERVAL + 5))
      sleep "$INTERVAL"
      ;;
    *)
      printf "Device flow failed: %s
" "$TOKEN_JSON" >&2
      exit 1
      ;;
  esac
done
