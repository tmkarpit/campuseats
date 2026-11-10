#!/usr/bin/env bash
# Task 6 demo — run with the server already started (npm start) in another terminal.
BASE=${BASE:-http://localhost:3000}

step() { echo; echo "=================================================================="; echo "$1"; echo "=================================================================="; }

step "CASE 1: GET /items with NO token  -> expect 401"
echo "\$ curl -i $BASE/items"
curl -s -i "$BASE/items"; echo

step "CASE 2: POST /login (bob, restaurant) -> expect 200 + token"
echo "\$ curl -i -X POST $BASE/login -H 'Content-Type: application/json' -d '{\"username\":\"bob\",\"password\":\"bob123\"}'"
curl -s -i -X POST "$BASE/login" -H 'Content-Type: application/json' -d '{"username":"bob","password":"bob123"}'; echo
BOB=$(curl -s -X POST "$BASE/login" -H 'Content-Type: application/json' -d '{"username":"bob","password":"bob123"}' | node -pe 'JSON.parse(require("fs").readFileSync(0)).token')
ALICE=$(curl -s -X POST "$BASE/login" -H 'Content-Type: application/json' -d '{"username":"alice","password":"alice123"}' | node -pe 'JSON.parse(require("fs").readFileSync(0)).token')

step "CASE 2b: POST /login with WRONG password -> expect 401"
echo "\$ curl -i -X POST $BASE/login -H 'Content-Type: application/json' -d '{\"username\":\"bob\",\"password\":\"wrong\"}'"
curl -s -i -X POST "$BASE/login" -H 'Content-Type: application/json' -d '{"username":"bob","password":"wrong"}'; echo

step "CASE 3: GET /items WITH token (alice, customer) -> expect 200"
echo "\$ curl -i $BASE/items -H \"Authorization: Bearer \$ALICE\""
curl -s -i "$BASE/items" -H "Authorization: Bearer $ALICE"; echo

step "CASE 4: POST /items as restaurant (bob) -> expect 201"
echo "\$ curl -i -X POST $BASE/items -H \"Authorization: Bearer \$BOB\" -H 'Content-Type: application/json' -d '{\"name\":\"Masala Dosa\",\"price\":149}'"
curl -s -i -X POST "$BASE/items" -H "Authorization: Bearer $BOB" -H 'Content-Type: application/json' -d '{"name":"Masala Dosa","price":149}'; echo

step "CASE 5: POST /items as customer (alice) -> expect 403"
echo "\$ curl -i -X POST $BASE/items -H \"Authorization: Bearer \$ALICE\" -H 'Content-Type: application/json' -d '{\"name\":\"Free Food\",\"price\":0}'"
curl -s -i -X POST "$BASE/items" -H "Authorization: Bearer $ALICE" -H 'Content-Type: application/json' -d '{"name":"Free Food","price":0}'; echo

step "EXTRA: GET /items with a TAMPERED token -> expect 401"
echo "\$ curl -i $BASE/items -H \"Authorization: Bearer \${ALICE}x\""
curl -s -i "$BASE/items" -H "Authorization: Bearer ${ALICE}x"; echo
