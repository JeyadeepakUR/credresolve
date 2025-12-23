import requests, json

BASE = "http://localhost:3000/api"
s = requests.Session()

def pp(label, resp):
    print(f"\n== {label} ({resp.status_code})")
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)

# Register users
u1 = s.post(f"{BASE}/auth/register", json={"name": "Alice", "email": "alice@test.com", "password": "pass"}); pp("register u1", u1)
u2 = s.post(f"{BASE}/auth/register", json={"name": "Bob", "email": "bob@test.com", "password": "pass"}); pp("register u2", u2)
t1 = u1.json()["token"]; t2 = u2.json()["token"]

# Auth headers per user
h1 = {"Authorization": f"Bearer {t1}"}
h2 = {"Authorization": f"Bearer {t2}"}

# Create group as Alice
g = s.post(f"{BASE}/groups", json={"name": "Trip", "description": "Test", "createdBy": u1.json()["user"]["id"]}, headers=h1); pp("create group", g)
gid = g.json()["id"]

# Add Bob to group
add = s.post(f"{BASE}/groups/{gid}/members", json={"userId": u2.json()["user"]["id"]}, headers=h1); pp("add member", add)

# Add expense: Alice pays $100, split equally
exp = s.post(f"{BASE}/expenses", headers=h1, json={
    "groupId": gid,
    "description": "Dinner",
    "totalAmount": 100,
    "paidBy": u1.json()["user"]["id"],
    "splitType": "EQUAL",
    "splits": [
        {"userId": u1.json()["user"]["id"]},
        {"userId": u2.json()["user"]["id"]}
    ]
}); pp("add expense", exp)

# Check balances in group
bal = s.get(f"{BASE}/groups/{gid}/balances", headers=h1); pp("group balances", bal)

# Simplified balances
simp = s.get(f"{BASE}/groups/{gid}/balances/simplified", headers=h1); pp("simplified balances", simp)

# Per-user balances
bal_u1 = s.get(f"{BASE}/users/{u1.json()['user']['id']}/balances", headers=h1); pp("u1 balances", bal_u1)
bal_u2 = s.get(f"{BASE}/users/{u2.json()['user']['id']}/balances", headers=h2); pp("u2 balances", bal_u2)