echo "=== Test 1: Karnak Temple (inside Egypt) ==="
curl -s "http://localhost:8000/api/v1/context?lat=25.7159&lon=32.6579&radius=500" | jq

echo -e "\n=== Test 2: Outside Egypt (New York) ==="
curl -s "http://localhost:8000/api/v1/context?lat=40.7128&lon=-74.0060" | jq

echo -e "\n=== Test 3: Inside Restricted Zone (Military Area) ==="
curl -s "http://localhost:8000/api/v1/context?lat=29.77973&lon=31.19933" | jq

echo -e "\n=== Test 4: Karnak Temple (Custom Radius: 5000m) ==="
curl -s "http://localhost:8000/api/v1/context?lat=25.7159&lon=32.6579&radius=5000" | jq
