#!/usr/bin/env bash
set -euo pipefail

# GeoContext API Manual Test Script
# Requires: API running at localhost:8000, PostGIS DB with ingested data
# Uses ADMIN_BOOTSTRAP_SECRET for auth bypass (dev only)

TOKEN="${ADMIN_BOOTSTRAP_SECRET:-local-dev-bootstrap-secret}"
BASE="http://localhost:8000"

pass=0
fail=0

check() {
    local desc="$1" expected="$2" actual="$3"
    if [[ "$actual" == *"$expected"* ]]; then
        echo "  ✅ $desc"
        pass=$((pass + 1))
    else
        echo "  ❌ $desc"
        echo "     expected: $expected"
        echo "     got:      $(echo "$actual" | head -c 200)"
        fail=$((fail + 1))
    fi
}

echo "=============================================="
echo "  GeoContext API — Manual Test Suite"
echo "=============================================="
echo ""

# === 1. Health Probes ===
echo "--- Health Probes ---"
r=$(curl -sSf "$BASE/healthz" 2>&1 || true)
check "Liveness (/healthz)" "ok" "$r"

r=$(curl -sSf "$BASE/readyz" 2>&1 || true)
check "Readiness (/readyz)" "ready" "$r"

# === 2. Context — Inside Egypt (Cairo, Tahrir Square) ===
echo ""
echo "--- Context: Inside Egypt ---"
r=$(curl -sSf "$BASE/api/v1/context?lat=30.0444&lon=31.2357&radius=2000" \
     -H "Authorization: Bearer $TOKEN" 2>&1 || true)
in_egypt=$(echo "$r" | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d['in_egypt']).lower())")
check "in_egypt=true" 'true' "$in_egypt"
check "governorate=Cairo" 'Cairo' "$(echo "$r" | python3 -c "import sys,json; print(json.load(sys.stdin)['governorate'])")"
check "at_site found" 'distance_meters' "$r"
check "zone_warnings present" 'zone_warnings' "$r"

# === 3. Context — Outside Egypt (short-circuit) ===
echo ""
echo "--- Context: Outside Egypt (short-circuit) ---"
r=$(curl -sSf "$BASE/api/v1/context?lat=48.8566&lon=2.3522" \
     -H "Authorization: Bearer $TOKEN" 2>&1 || true)
check "in_egypt=false" 'False' "$(echo "$r" | python3 -c "import sys,json; print(json.load(sys.stdin)['in_egypt'])")"
check "governorate=null" 'None' "$(echo "$r" | python3 -c "import sys,json; print(json.load(sys.stdin)['governorate'])")"
check "no nearby_sites" '0' "$(echo "$r" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['nearby_sites']))")"

# === 4. Nearby Sites — Category filter ===
echo ""
echo "--- Nearby Sites: Category filter ---"
r=$(curl -sSf "$BASE/api/v1/nearby-sites?lat=30.0444&lon=31.2357&radius=500&category=islamic" \
     -H "Authorization: Bearer $TOKEN" 2>&1 || true)
count=$(echo "$r" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
check "islamic sites in 500m radius (count=$count)" "islamic" "$r"

# === 5. Nearby Sites — By Governorate ===
echo ""
echo "--- Nearby Sites: By Governorate ---"
r=$(curl -sSf "$BASE/api/v1/nearby-sites/by-governorate?governorate_name=Alexandria&category=christian" \
     -H "Authorization: Bearer $TOKEN" 2>&1 || true)
check "Christian sites in Alexandria" "christian" "$r"

# === 6. Submit Report ===
echo ""
echo "--- Reports: Submit ---"
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/v1/reports" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"report_type":"hazard","description":"Broken glass on path","severity":"medium","lat":30.0444,"lon":31.2357}' 2>&1 || true)
if [[ "$http_code" == "201" ]]; then
    echo "  ✅ report created (HTTP 201)"
    pass=$((pass + 1))
elif [[ "$http_code" == "429" ]]; then
    echo "  ⚠️ report rate-limited (HTTP 429 — expected if tested recently)"
    pass=$((pass + 1))
else
    echo "  ❌ report submission returned HTTP $http_code"
    fail=$((fail + 1))
fi

# === 7. Auth Required (no token) ===
echo ""
echo "--- Auth: Missing token ---"
r=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/v1/context?lat=30.0&lon=31.0" 2>&1 || true)
check "401 without token" "401" "$r"

# === 8. Rate Limit (POST /reports — 5/min) ===
echo ""
echo "--- Rate Limit: /reports (5/min) ---"
hits=0
for i in $(seq 1 6); do
    code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/v1/reports" \
         -H "Authorization: Bearer $TOKEN" \
         -H "Content-Type: application/json" \
         -d "{\"report_type\":\"hazard\",\"description\":\"rate test $i\",\"lat\":30.0,\"lon\":31.0}" 2>&1 || true)
    if [[ "$code" == "429" ]]; then
        hits=$((hits + 1))
    fi
done
if [[ "$hits" -ge 1 ]]; then
    echo "  ✅ rate limiter triggered ($hits requests got 429)"
    pass=$((pass + 1))
else
    echo "  ❌ rate limiter not triggered (0 requests got 429)"
    fail=$((fail + 1))
fi

echo ""
echo "=============================================="
echo "  Results: $pass passed, $fail failed"
echo "=============================================="
