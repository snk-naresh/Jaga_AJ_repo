def test_login_and_reject_bad_password(client):
    bad = client.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    assert bad.status_code == 401
    ok = client.post("/api/auth/login", json={"username": "staff", "password": "ChangeMe_123!"})
    assert ok.status_code == 200
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {ok.json()['access_token']}"})
    assert me.json()["role"] == "STAFF"


def test_customer_crud_and_search(client, auth):
    created = client.post("/api/customers", headers=auth, json={"name": "Anita Sharma", "phone": "90000 01001", "whatsapp_opt_in": True})
    assert created.status_code == 200, created.text
    customer_id = created.json()["id"]
    assert created.json()["phone"] == "9000001001"
    short = client.post("/api/customers", headers=auth, json={"name": "Short Number", "phone": "900000100"})
    assert short.status_code == 422
    assert short.json()["detail"] == "enter valid ph. no."
    low = client.post("/api/customers", headers=auth, json={"name": "Low Number", "phone": "5999999999"})
    assert low.status_code == 422
    missing = client.post("/api/customers", headers=auth, json={"phone": "9000001008"})
    assert missing.status_code == 422
    duplicate = client.post("/api/customers", headers=auth, json={"name": "Other", "phone": "9000001001"})
    assert duplicate.status_code == 409
    found = client.get("/api/customers", headers=auth, params={"q": "9000001001"})
    assert found.status_code == 200
    assert found.json()["total"] == 1
    edited = client.patch(f"/api/customers/{customer_id}", headers=auth, json={"notes": "Prefers gold"})
    assert edited.status_code == 200
    assert edited.json()["notes"] == "Prefers gold"


def test_order_items_inventory_and_notification(client, auth):
    stock = client.post("/api/inventory", headers=auth, json={
        "sku": "GLD-1", "name": "22K chain", "category": "Gold", "quantity": 2, "low_stock_threshold": 1, "purity": "22K"
    })
    assert stock.status_code == 200, stock.text
    sku_id = stock.json()["id"]
    customer = client.post("/api/customers", headers=auth, json={"name": "Priya Nair", "phone": "9000002002", "whatsapp_opt_in": True}).json()
    created = client.post("/api/orders", headers=auth, json={
        "customer_id": customer["id"],
        "expected_delivery_date": "2026-12-01",
        "notes": "Wedding set",
        "items": [
            {"item_type": "Chain", "description": "22 inch", "quantity": 1, "inventory_item_id": sku_id},
            {"item_type": "Bangle", "description": "Set of 4", "quantity": 1},
        ],
    })
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["status"] == "OPEN"
    assert len(body["items"]) == 2
    assert body["order_number"].startswith("ANJ-")
    chain = next(item for item in body["items"] if item["item_type"] == "Chain")
    moved = client.patch(f"/api/orders/items/{chain['id']}/status", headers=auth, json={"status": "IN_PROGRESS"})
    assert moved.status_code == 200, moved.text
    assert moved.json()["status"] == "IN_PROGRESS"
    ready = client.patch(f"/api/orders/items/{chain['id']}/status", headers=auth, json={"status": "READY"})
    assert ready.status_code == 200, ready.text
    notes = client.get("/api/notifications", headers=auth, params={"order_id": body["id"]})
    assert notes.status_code == 200
    assert notes.json()["total"] >= 1
    assert notes.json()["items"][0]["status"] == "SENT"
    invalid = client.patch(f"/api/orders/items/{chain['id']}/status", headers=auth, json={"status": "PENDING"})
    assert invalid.status_code == 400
    short = client.post("/api/inventory", headers=auth, json={"sku": "DIA-1", "name": "Solitaire", "category": "Diamond", "quantity": 0})
    blocked = client.post("/api/orders", headers=auth, json={
        "customer_id": customer["id"],
        "items": [{"item_type": "Diamond Ring", "quantity": 1, "inventory_item_id": short.json()["id"]}],
    })
    assert blocked.status_code == 409
    staff = client.post("/api/auth/login", json={"username": "staff", "password": "ChangeMe_123!"}).json()["access_token"]
    staff_headers = {"Authorization": f"Bearer {staff}"}
    forbidden = client.get("/api/users", headers=staff_headers)
    assert forbidden.status_code == 403
    blocked_edit = client.patch(f"/api/orders/items/{chain['id']}/status", headers=staff_headers, json={"status": "DELIVERED"})
    assert blocked_edit.status_code == 403
    blocked_customer = client.patch(f"/api/customers/{customer['id']}", headers=staff_headers, json={"notes": "staff edit"})
    assert blocked_customer.status_code == 403
    created_by_staff = client.post("/api/customers", headers=staff_headers, json={"name": "New Walk In", "phone": "9123456780"})
    assert created_by_staff.status_code == 200, created_by_staff.text
    from app.db.session import SessionLocal
    from app.models.customer import Customer
    db = SessionLocal()
    legacy = Customer(name="Old Card", phone="12345", whatsapp_opt_in=False)
    db.add(legacy)
    db.commit()
    legacy_id = legacy.id
    db.close()
    fixed = client.patch(f"/api/customers/{legacy_id}", headers=staff_headers, json={"phone": "9876543210"})
    assert fixed.status_code == 200, fixed.text
    assert fixed.json()["phone"] == "9876543210"
    hidden = client.get("/api/access", headers=staff_headers)
    assert hidden.status_code == 403
    security = client.get("/api/access", headers=auth)
    assert security.status_code == 200
    edits = security.json()["edits"]
    assert any(row["previous_phone"] == "12345" and row["phone"] == "9876543210" and row["customer"] == "Old Card" for row in edits)
    dashboard = client.get("/api/dashboard", headers=auth)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_customers"] >= 1
    report = client.get("/api/reports", headers=auth, params={"preset": "30d"})
    assert report.status_code == 200
