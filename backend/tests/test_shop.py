"""
Tests for Creator Shop (Module 16): storefronts, products, and orders.

Written HTTP-level from the start (via test_client), per the rule
established since Module 10. NOTE: written but not yet run - the user
paused test/build verification mid-session (2026-08-03) until the whole
app is declared complete; these will be run in that deferred pass.
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


async def _register(test_client: AsyncClient, register_user_data, email, username):
    data = dict(register_user_data)
    data["email"] = email
    data["username"] = username
    response = await test_client.post("/api/auth/register", json=data)
    return response.json()["access_token"], response.json()["user"]["id"]


async def _make_shop_with_product(test_client, register_user_data, email, username, stock=None):
    token, user_id = await _register(test_client, register_user_data, email, username)
    await test_client.post(
        "/api/shop/me", json={"name": f"{username}'s shop", "description": "Handmade goods"},
        headers={"Authorization": f"Bearer {token}"},
    )
    product_response = await test_client.post(
        "/api/shop/products",
        json={"name": "Sticker pack", "price": 500, "stock_quantity": stock},
        headers={"Authorization": f"Bearer {token}"},
    )
    return token, user_id, product_response.json()


@pytest.mark.asyncio
async def test_create_and_get_my_shop(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "shopowner1@example.com", "shopowner1user")

    create_response = await test_client.post(
        "/api/shop/me", json={"name": "My Shop", "description": "Cool stuff"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 200
    assert create_response.json()["name"] == "My Shop"

    get_response = await test_client.get("/api/shop/me", headers={"Authorization": f"Bearer {token}"})
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "My Shop"


@pytest.mark.asyncio
async def test_get_my_shop_404_when_none(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "shopless@example.com", "shoplessuser")
    response = await test_client.get("/api/shop/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upsert_shop_updates_existing(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "shopupdate@example.com", "shopupdateuser")
    await test_client.post(
        "/api/shop/me", json={"name": "First name"}, headers={"Authorization": f"Bearer {token}"}
    )
    response = await test_client.post(
        "/api/shop/me", json={"name": "Second name"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Second name"


@pytest.mark.asyncio
async def test_create_product_requires_shop(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "noshopproduct@example.com", "noshopproductuser")
    response = await test_client.post(
        "/api/shop/products",
        json={"name": "Test", "price": 100},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_view_shop_with_products(test_client: AsyncClient, register_user_data):
    _, _, product = await _make_shop_with_product(
        test_client, register_user_data, "shopview@example.com", "shopviewuser"
    )
    response = await test_client.get(f"/api/shop/{product['shop_id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["shop"]["id"] == product["shop_id"]
    assert any(p["id"] == product["id"] for p in data["products"])


@pytest.mark.asyncio
async def test_view_shop_by_user_id(test_client: AsyncClient, register_user_data):
    _, user_id, product = await _make_shop_with_product(
        test_client, register_user_data, "shopbyuser@example.com", "shopbyuseruser"
    )
    response = await test_client.get(f"/api/shop/user/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["shop"]["user_id"] == user_id
    assert any(p["id"] == product["id"] for p in data["products"])


@pytest.mark.asyncio
async def test_view_shop_by_user_id_404_when_none(test_client: AsyncClient, register_user_data):
    _, user_id = await _register(test_client, register_user_data, "noshopbyuser@example.com", "noshopbyuseruser")
    response = await test_client.get(f"/api/shop/user/{user_id}")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_product_requires_ownership(test_client: AsyncClient, register_user_data):
    _, _, product = await _make_shop_with_product(
        test_client, register_user_data, "productowner@example.com", "productowneruser"
    )
    intruder_token, _ = await _register(
        test_client, register_user_data, "productintruder@example.com", "productintruderuser"
    )
    response = await test_client.put(
        f"/api/shop/products/{product['id']}",
        json={"price": 999},
        headers={"Authorization": f"Bearer {intruder_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_product(test_client: AsyncClient, register_user_data):
    token, _, product = await _make_shop_with_product(
        test_client, register_user_data, "productdelete@example.com", "productdeleteuser"
    )
    response = await test_client.delete(
        f"/api/shop/products/{product['id']}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    shop_response = await test_client.get(f"/api/shop/{product['shop_id']}")
    assert not any(p["id"] == product["id"] for p in shop_response.json()["products"])


@pytest.mark.asyncio
async def test_place_order_decrements_stock(test_client: AsyncClient, register_user_data):
    _, _, product = await _make_shop_with_product(
        test_client, register_user_data, "stockowner@example.com", "stockowneruser", stock=10
    )
    buyer_token, _ = await _register(test_client, register_user_data, "stockbuyer@example.com", "stockbuyeruser")

    response = await test_client.post(
        f"/api/shop/products/{product['id']}/order",
        json={"quantity": 3},
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 3
    assert data["total_amount"] == 1500
    assert data["status"] == "pending"

    shop_response = await test_client.get(f"/api/shop/{product['shop_id']}")
    updated_product = next(p for p in shop_response.json()["products"] if p["id"] == product["id"])
    assert updated_product["stock_quantity"] == 7


@pytest.mark.asyncio
async def test_place_order_rejects_insufficient_stock(test_client: AsyncClient, register_user_data):
    _, _, product = await _make_shop_with_product(
        test_client, register_user_data, "lowstockowner@example.com", "lowstockowneruser", stock=1
    )
    buyer_token, _ = await _register(test_client, register_user_data, "lowstockbuyer@example.com", "lowstockbuyeruser")

    response = await test_client.post(
        f"/api/shop/products/{product['id']}/order",
        json={"quantity": 5},
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_unlimited_stock_product_always_orderable(test_client: AsyncClient, register_user_data):
    _, _, product = await _make_shop_with_product(
        test_client, register_user_data, "unlimitedowner@example.com", "unlimitedowneruser", stock=None
    )
    buyer_token, _ = await _register(test_client, register_user_data, "unlimitedbuyer@example.com", "unlimitedbuyeruser")

    response = await test_client.post(
        f"/api/shop/products/{product['id']}/order",
        json={"quantity": 100},
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_cannot_order_own_product(test_client: AsyncClient, register_user_data):
    token, _, product = await _make_shop_with_product(
        test_client, register_user_data, "selfbuy@example.com", "selfbuyuser"
    )
    response = await test_client.post(
        f"/api/shop/products/{product['id']}/order",
        json={"quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_order_nonexistent_product_rejected(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "orderghost@example.com", "orderghostuser")
    response = await test_client.post(
        f"/api/shop/products/{uuid4()}/order",
        json={"quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_seller_can_fulfill_order(test_client: AsyncClient, register_user_data):
    seller_token, _, product = await _make_shop_with_product(
        test_client, register_user_data, "fulfillseller@example.com", "fulfillselleruser"
    )
    buyer_token, _ = await _register(test_client, register_user_data, "fulfillbuyer@example.com", "fulfillbuyeruser")

    order_response = await test_client.post(
        f"/api/shop/products/{product['id']}/order",
        json={"quantity": 1},
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    order_id = order_response.json()["id"]

    fulfill_response = await test_client.post(
        f"/api/shop/orders/{order_id}/fulfill", headers={"Authorization": f"Bearer {seller_token}"}
    )
    assert fulfill_response.status_code == 200
    assert fulfill_response.json()["status"] == "fulfilled"


@pytest.mark.asyncio
async def test_buyer_cannot_fulfill_order(test_client: AsyncClient, register_user_data):
    _, _, product = await _make_shop_with_product(
        test_client, register_user_data, "nofulfillseller@example.com", "nofulfillselleruser"
    )
    buyer_token, _ = await _register(test_client, register_user_data, "nofulfillbuyer@example.com", "nofulfillbuyeruser")

    order_response = await test_client.post(
        f"/api/shop/products/{product['id']}/order",
        json={"quantity": 1},
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    order_id = order_response.json()["id"]

    response = await test_client.post(
        f"/api/shop/orders/{order_id}/fulfill", headers={"Authorization": f"Bearer {buyer_token}"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cancel_order_restocks_product(test_client: AsyncClient, register_user_data):
    seller_token, _, product = await _make_shop_with_product(
        test_client, register_user_data, "cancelseller@example.com", "cancelselleruser", stock=5
    )
    buyer_token, _ = await _register(test_client, register_user_data, "cancelbuyer@example.com", "cancelbuyeruser")

    order_response = await test_client.post(
        f"/api/shop/products/{product['id']}/order",
        json={"quantity": 2},
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    order_id = order_response.json()["id"]

    cancel_response = await test_client.post(
        f"/api/shop/orders/{order_id}/cancel", headers={"Authorization": f"Bearer {seller_token}"}
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    shop_response = await test_client.get(f"/api/shop/{product['shop_id']}")
    updated_product = next(p for p in shop_response.json()["products"] if p["id"] == product["id"])
    assert updated_product["stock_quantity"] == 5


@pytest.mark.asyncio
async def test_cannot_fulfill_already_decided_order(test_client: AsyncClient, register_user_data):
    seller_token, _, product = await _make_shop_with_product(
        test_client, register_user_data, "twicedecideseller@example.com", "twicedecidselleruser"
    )
    buyer_token, _ = await _register(test_client, register_user_data, "twicedecidebuyer@example.com", "twicedecidebuyeruser")

    order_response = await test_client.post(
        f"/api/shop/products/{product['id']}/order",
        json={"quantity": 1},
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    order_id = order_response.json()["id"]

    await test_client.post(
        f"/api/shop/orders/{order_id}/fulfill", headers={"Authorization": f"Bearer {seller_token}"}
    )
    second = await test_client.post(
        f"/api/shop/orders/{order_id}/cancel", headers={"Authorization": f"Bearer {seller_token}"}
    )
    assert second.status_code == 400


@pytest.mark.asyncio
async def test_list_my_orders_and_received_orders(test_client: AsyncClient, register_user_data):
    seller_token, _, product = await _make_shop_with_product(
        test_client, register_user_data, "listseller@example.com", "listselleruser"
    )
    buyer_token, _ = await _register(test_client, register_user_data, "listbuyer@example.com", "listbuyeruser")

    await test_client.post(
        f"/api/shop/products/{product['id']}/order",
        json={"quantity": 1},
        headers={"Authorization": f"Bearer {buyer_token}"},
    )

    my_orders = await test_client.get("/api/shop/orders/me", headers={"Authorization": f"Bearer {buyer_token}"})
    received_orders = await test_client.get(
        "/api/shop/orders/received", headers={"Authorization": f"Bearer {seller_token}"}
    )
    assert len(my_orders.json()["orders"]) == 1
    assert len(received_orders.json()["orders"]) == 1


@pytest.mark.asyncio
async def test_shop_endpoints_require_auth(test_client: AsyncClient):
    response = await test_client.post("/api/shop/me", json={"name": "X"})
    assert response.status_code == 401

    response = await test_client.get("/api/shop/orders/me")
    assert response.status_code == 401
