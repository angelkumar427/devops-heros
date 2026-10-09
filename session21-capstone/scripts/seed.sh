#!/usr/bin/env bash
# Load a realistic demo catalogue through the public API (so it exercises validation too).
#   ./scripts/seed.sh                      # docker compose  (http://localhost:8000)
#   API=http://stockpilot.local ./scripts/seed.sh   # through the Kubernetes Ingress
#   API=http://localhost HOST_HEADER=stockpilot.local ./scripts/seed.sh   # same, without editing /etc/hosts
set -euo pipefail
API="${API:-http://localhost:8000}"
CURL=(curl -sS); [ -n "${HOST_HEADER:-}" ] && CURL+=(-H "Host: $HOST_HEADER")
add() {  # sku name category qty reorder price  (JSON built by python, so quotes in names are safe)
  body=$(python3 -c 'import json,sys; s,n,c,q,r,p=sys.argv[1:]
print(json.dumps({"sku":s,"name":n,"category":c,"quantity":int(q),"reorder_level":int(r),"unit_price":p}))' "$@")
  "${CURL[@]}" -o /dev/null -w "  %{http_code}  $1\n" -X POST "$API/api/products" -H 'Content-Type: application/json' -d "$body"
}
adjust() {  # sku change reason
  id=$("${CURL[@]}" -f "$API/api/products?q=$1" | python3 -c "import json,sys; print(json.load(sys.stdin)[0]['id'])")
  "${CURL[@]}" -f -o /dev/null -w "  %{http_code}  $1 $2 ($3)\n" -X POST "$API/api/products/$id/adjust" \
    -H 'Content-Type: application/json' -d "{\"change\":$2,\"reason\":\"$3\"}"
}
echo "Seeding $API"
add LAP-AIR-13   "Laptop 13\" (16 GB / 512 GB)"  Computers    14  5  72990
add LAP-PRO-15   "Laptop 15\" Pro (32 GB / 1 TB)" Computers    4   5  134990
add MON-27-4K    "27\" 4K monitor"               Displays     22  8  28490
add MON-24-FHD   "24\" Full-HD monitor"          Displays     35 10  10990
add KB-MECH-TKL  "Mechanical keyboard, TKL"      Peripherals  48 15  5490
add MS-WL-ERGO   "Wireless ergonomic mouse"      Peripherals  9  12  2790
add HS-ANC-01    "Noise-cancelling headset"      Audio        17  6  8990
add SPK-BT-MINI  "Bluetooth speaker, mini"       Audio        0   5  2490
add CAB-USBC-1M  "USB-C cable, 1 m"              Cables       160 50 349
add CAB-HDMI-2M  "HDMI 2.1 cable, 2 m"           Cables       38 40 699
add DOCK-USBC-8  "USB-C dock, 8-in-1"            Accessories  26 10 6490
add SSD-NVME-1T  "NVMe SSD, 1 TB"                Storage      31 10 6990
adjust LAP-AIR-13  6   "PO-2041 received"
adjust MON-27-4K   -3  "Order #10482"
adjust KB-MECH-TKL -12 "Order #10490 (bulk)"
adjust CAB-USBC-1M -45 "Order #10495"
adjust HS-ANC-01   -2  "Order #10501"
