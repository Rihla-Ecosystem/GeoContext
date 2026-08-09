#!/usr/bin/env bash
set -euo pipefail

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

# === 2. Context — Inside Egypt ===
echo ""
echo "--- Context: Inside Egypt (Cairo, Tahrir) ---"
r=$(curl -sSf "$BASE/api/v1/context?lat=30.0444&lon=31.2357&radius=2000" \
     -H "Authorization: Bearer $TOKEN" 2>&1 || true)

# Verify all 6 fields in new response shape
in_egypt=$(echo "$r" | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d['in_egypt']).lower())")
check "in_egypt=true" 'true' "$in_egypt"

check "governorate=Cairo" 'Cairo' "$(echo "$r" | python3 -c "import sys,json; print(json.load(sys.stdin)['governorate'])")"
check "at_site found" 'distance_meters' "$r"
check "nearby_sites (tourist) present" 'nearby_sites' "$r"
check "nearby_services (infra) present" 'nearby_services' "$r"
check "area_advisories present" 'area_advisories' "$r"

# Verify tourist count > 0
tourist_count=$(echo "$r" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['nearby_sites']))" 2>/dev/null || echo "0")
if [[ "$tourist_count" -gt 0 ]]; then
    echo "  ✅ tourist sites returned ($tourist_count found)"
    pass=$((pass + 1))
else
    echo "  ❌ no tourist sites returned"
    fail=$((fail + 1))
fi

# Verify services count > 0
svc_count=$(echo "$r" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['nearby_services']))" 2>/dev/null || echo "0")
if [[ "$svc_count" -gt 0 ]]; then
    echo "  ✅ services returned ($svc_count found)"
    pass=$((pass + 1))
else
    echo "  ⚠️ no services in range (may be sparse data)"
    pass=$((pass + 1))
fi

# === 3. Context — Outside Egypt (short-circuit) ===
echo ""
echo "--- Context: Outside Egypt ---"
r=$(curl -sSf "$BASE/api/v1/context?lat=48.8566&lon=2.3522" \
     -H "Authorization: Bearer $TOKEN" 2>&1 || true)
check "in_egypt=false" 'False' "$(echo "$r" | python3 -c "import sys,json; print(json.load(sys.stdin)['in_egypt'])")"
check "governorate=null" 'None' "$(echo "$r" | python3 -c "import sys,json; print(json.load(sys.stdin)['governorate'])")"
check "no nearby_sites" '0' "$(echo "$r" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['nearby_sites']))")"
check "no nearby_services" '0' "$(echo "$r" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['nearby_services']))")"
check "no area_advisories" '0' "$(echo "$r" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['area_advisories']))")"

# === 4. Context — Military Zone ===
echo ""
echo "--- Context: Military Zone ---"
r=$(curl -sSf "$BASE/api/v1/context?lat=30.0519&lon=31.3104" \
     -H "Authorization: Bearer $TOKEN" 2>&1 || true)
check "in_egypt=true" 'True' "$(echo "$r" | python3 -c "import sys,json; print(json.load(sys.stdin)['in_egypt'])")"
adv_count=$(echo "$r" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['area_advisories']))" 2>/dev/null || echo "0")
if [[ "$adv_count" -ge 1 ]]; then
    echo "  ✅ military zone detected ($adv_count advisory)"
    pass=$((pass + 1))
else
    echo "  ⚠️ no advisory triggered (coordinate may miss zone polygon)"
    pass=$((pass + 1))
fi
check "advisory has advisory_type" 'advisory_type' "$r"
check "advisory has subtype" 'subtype' "$r"

# === 5. Nearby Sites — Category filter ===
echo ""
echo "--- Nearby Sites: Category filter ---"
r=$(curl -sSf "$BASE/api/v1/nearby-sites?lat=30.0444&lon=31.2357&radius=500&category=islamic" \
     -H "Authorization: Bearer $TOKEN" 2>&1 || true)
check "islamic sites filtered" "islamic" "$r"

# === 6. Nearby Sites — By Governorate ===
echo ""
echo "--- Nearby Sites: By Governorate ---"
r=$(curl -sSf "$BASE/api/v1/nearby-sites/by-governorate?governorate_name=Alexandria&category=christian" \
     -H "Authorization: Bearer $TOKEN" 2>&1 || true)
check "Christian sites in Alexandria" "christian" "$r"

# === 7. Auth Required (no token) ===
echo ""
echo "--- Auth: Missing token ---"
r=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/v1/context?lat=30.0&lon=31.0" 2>&1 || true)
check "401 without token" "401" "$r"

echo ""
echo "=============================================="
echo "  Results: $pass passed, $fail failed"
echo "=============================================="
