#!/usr/bin/env bash
# Regenerates transcript.txt:  bash make_transcript.sh
PORT=3000; H="localhost:$PORT"; OUT=transcript.txt
PORT=$PORT node server.js >/dev/null 2>server.log & PID=$!
sleep 1; : > $OUT
J='Content-Type: application/json'
run() { echo "\$ $*" >> $OUT; eval "$@" >> $OUT 2>&1; printf '\n\n' >> $OUT; }
sec() { printf '\n==================== %s ====================\n\n' "$1" >> $OUT; }

sec "D1  SUCCESS PATH"
run "curl -si -X POST $H/orders -H '$J' -d '{\"items\":[{\"sku\":\"widget\",\"qty\":2},{\"sku\":\"gadget\",\"qty\":1}],\"address\":\"12 Ring Road, Surat\"}'"
run "curl -si $H/orders/ord_1001"
run "curl -si -X PATCH $H/orders/ord_1001 -H '$J' -d '{\"status\":\"shipped\"}'"

sec "D2  FAILURES"
echo "--- empty cart" >> $OUT
run "curl -si -X POST $H/orders -H '$J' -d '{\"items\":[],\"address\":\"x\"}'"
echo "--- qty <= 0" >> $OUT
run "curl -si -X POST $H/orders -H '$J' -d '{\"items\":[{\"sku\":\"widget\",\"qty\":0}],\"address\":\"x\"}'"
echo "--- two bad fields at once (qty and address)" >> $OUT
run "curl -si -X POST $H/orders -H '$J' -d '{\"items\":[{\"sku\":\"widget\",\"qty\":-1}],\"address\":\"\"}'"
echo "--- unknown id" >> $OUT
run "curl -si $H/orders/ord_9999"
echo "--- illegal transition (shipped -> paid)" >> $OUT
run "curl -si -X PATCH $H/orders/ord_1001 -H '$J' -d '{\"status\":\"paid\"}'"
echo "--- item unavailable (out of stock)" >> $OUT
run "curl -si -X POST $H/orders -H '$J' -d '{\"items\":[{\"sku\":\"gizmo\",\"qty\":1}],\"address\":\"x\"}'"
echo "--- payment declined" >> $OUT
run "curl -si -X POST $H/orders -H '$J' -d '{\"items\":[{\"sku\":\"widget\",\"qty\":1}],\"address\":\"x\",\"payment_token\":\"tok_decline\"}'"
echo "--- malformed JSON" >> $OUT
run "curl -si -X POST $H/orders -H '$J' -d '{oops'"
echo "--- payment provider timeout -> 503 + Retry-After" >> $OUT
run "curl -si -X POST $H/orders -H '$J' -d '{\"items\":[{\"sku\":\"widget\",\"qty\":1}],\"address\":\"x\",\"payment_token\":\"tok_slow\"}'"
echo "--- internal error is hidden (simulated DB failure)" >> $OUT
run "curl -si $H/orders/ord_1001 -H 'X-Simulate-Fault: db'"
echo "--- rate limit: 30 quick requests as client 'burst' (status codes only), then the 31st in full" >> $OUT
echo "\$ for i in \$(seq 1 30); do curl -s -o /dev/null -w '%{http_code} ' $H/orders -H 'X-Client-Id: burst'; done" >> $OUT
for i in $(seq 1 30); do curl -s -o /dev/null -w '%{http_code} ' $H/orders -H 'X-Client-Id: burst' >> $OUT; done; printf '\n\n' >> $OUT
run "curl -si $H/orders -H 'X-Client-Id: burst'"

sec "D3  CONTENT NEGOTIATION"
run "curl -si $H/orders/ord_1001 -H 'Accept: application/json'"
run "curl -si $H/orders/ord_1001 -H 'Accept: application/xml'"
echo "--- cannot produce -> 406" >> $OUT
run "curl -si $H/orders/ord_1001 -H 'Accept: text/html'"

sec "D4  NO REGRESSIONS (A5: idempotency + timeouts)"
echo "--- same Idempotency-Key twice: same order, second one flagged as replay" >> $OUT
run "curl -si -X POST $H/orders -H '$J' -H 'Idempotency-Key: demo-1' -d '{\"items\":[{\"sku\":\"widget\",\"qty\":1}],\"address\":\"x\"}'"
run "curl -si -X POST $H/orders -H '$J' -H 'Idempotency-Key: demo-1' -d '{\"items\":[{\"sku\":\"widget\",\"qty\":1}],\"address\":\"x\"}'"
echo "--- timeout (above, tok_slow) was not cached: the same key succeeds on retry" >> $OUT
run "curl -si -X POST $H/orders -H '$J' -H 'Idempotency-Key: demo-2' -d '{\"items\":[{\"sku\":\"widget\",\"qty\":1}],\"address\":\"x\",\"payment_token\":\"tok_slow\"}'"
run "curl -si -X POST $H/orders -H '$J' -H 'Idempotency-Key: demo-2' -d '{\"items\":[{\"sku\":\"widget\",\"qty\":1}],\"address\":\"x\"}'"
echo "--- DELETE" >> $OUT
run "curl -si -X DELETE $H/orders/ord_1001"
run "curl -si -X DELETE $H/orders/ord_1002"
kill $PID
