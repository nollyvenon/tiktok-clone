"""
Tests for Monetization (Module 18): earnings ledger and payout requests,
built on top of the already-real Creator Fund and Creator Shop records.

Written HTTP-level from the start (via test_client), per the rule
established since Module 10. NOTE: written but not yet run - the user
paused test/build verification mid-session (2026-08-03) until the whole
app is declared complete; these will be run in that deferred pass.
"""

import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4

from app.models import User, UserRole


async def _register(test_client: AsyncClient, register_user_data, email, username):
    data = dict(register_user_data)
    data["email"] = email
    data["username"] = username
    response = await test_client.post("/api/auth/register", json=data)
    return response.json()["access_token"], response.json()["user"]["id"]


async def _make_admin(test_db, user_id: str):
    user = await test_db.get(User, UUID(user_id))
    user.role = UserRole.ADMIN
    await test_db.commit()


async def _earn_via_fund(test_client, test_db, admin_token, creator_token, award_amount=50000):
    """Approve a fund application for creator_token, crediting an Earning"""
    program_response = await test_client.post(
        "/api/creator-fund/programs",
        json={"name": "Monetization Fund", "award_amount": award_amount},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    program_id = program_response.json()["id"]
    apply_response = await test_client.post(
        f"/api/creator-fund/programs/{program_id}/apply",
        headers={"Authorization": f"Bearer {creator_token}"},
    )
    application_id = apply_response.json()["id"]
    await test_client.post(
        f"/api/creator-fund/admin/applications/{application_id}/decide",
        json={"status": "approved"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )


async def _earn_via_shop(test_client, seller_token, buyer_token, price=1000):
    """Fulfill a shop order for seller_token, crediting an Earning"""
    await test_client.post(
        "/api/shop/me", json={"name": "Earnings Shop"}, headers={"Authorization": f"Bearer {seller_token}"}
    )
    product_response = await test_client.post(
        "/api/shop/products",
        json={"name": "Widget", "price": price},
        headers={"Authorization": f"Bearer {seller_token}"},
    )
    product_id = product_response.json()["id"]
    order_response = await test_client.post(
        f"/api/shop/products/{product_id}/order",
        json={"quantity": 1},
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    order_id = order_response.json()["id"]
    await test_client.post(
        f"/api/shop/orders/{order_id}/fulfill", headers={"Authorization": f"Bearer {seller_token}"}
    )


@pytest.mark.asyncio
async def test_summary_zero_when_no_earnings(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "noearnings@example.com", "noearningsuser")
    response = await test_client.get("/api/monetization/summary", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_earned"] == 0
    assert data["available_balance"] == 0
    assert data["earnings"] == []


@pytest.mark.asyncio
async def test_fund_approval_credits_earning(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "monfundadmin@example.com", "monfundadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, _ = await _register(test_client, register_user_data, "monfundcreator@example.com", "monfundcreatoruser")

    await _earn_via_fund(test_client, test_db, admin_token, creator_token, award_amount=75000)

    response = await test_client.get(
        "/api/monetization/summary", headers={"Authorization": f"Bearer {creator_token}"}
    )
    data = response.json()
    assert data["total_earned"] == 75000
    assert data["available_balance"] == 75000
    assert len(data["earnings"]) == 1
    assert data["earnings"][0]["source_type"] == "creator_fund"


@pytest.mark.asyncio
async def test_shop_fulfillment_credits_earning(test_client: AsyncClient, register_user_data):
    seller_token, _ = await _register(test_client, register_user_data, "monshopseller@example.com", "monshopselleruser")
    buyer_token, _ = await _register(test_client, register_user_data, "monshopbuyer@example.com", "monshopbuyeruser")

    await _earn_via_shop(test_client, seller_token, buyer_token, price=2500)

    response = await test_client.get(
        "/api/monetization/summary", headers={"Authorization": f"Bearer {seller_token}"}
    )
    data = response.json()
    assert data["total_earned"] == 2500
    assert data["earnings"][0]["source_type"] == "shop_order"


@pytest.mark.asyncio
async def test_request_payout_within_balance(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "payoutokadmin@example.com", "payoutokadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, _ = await _register(test_client, register_user_data, "payoutokcreator@example.com", "payoutokcreatoruser")
    await _earn_via_fund(test_client, test_db, admin_token, creator_token, award_amount=10000)

    response = await test_client.post(
        "/api/monetization/payouts", json={"amount": 5000}, headers={"Authorization": f"Bearer {creator_token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"

    summary = await test_client.get(
        "/api/monetization/summary", headers={"Authorization": f"Bearer {creator_token}"}
    )
    assert summary.json()["available_balance"] == 5000
    assert summary.json()["pending_payout_total"] == 5000


@pytest.mark.asyncio
async def test_request_payout_exceeding_balance_rejected(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "payoutoverdraft@example.com", "payoutoverdraftuser")
    response = await test_client.post(
        "/api/monetization/payouts", json={"amount": 100}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_pending_payout_reduces_available_balance_for_second_request(
    test_client: AsyncClient, test_db, register_user_data
):
    admin_token, admin_id = await _register(test_client, register_user_data, "doublepayoutadmin@example.com", "doublepayoutadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, _ = await _register(test_client, register_user_data, "doublepayoutcreator@example.com", "doublepayoutcreatoruser")
    await _earn_via_fund(test_client, test_db, admin_token, creator_token, award_amount=10000)

    first = await test_client.post(
        "/api/monetization/payouts", json={"amount": 8000}, headers={"Authorization": f"Bearer {creator_token}"}
    )
    assert first.status_code == 200

    second = await test_client.post(
        "/api/monetization/payouts", json={"amount": 5000}, headers={"Authorization": f"Bearer {creator_token}"}
    )
    assert second.status_code == 400


@pytest.mark.asyncio
async def test_admin_can_complete_payout(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "completepayoutadmin@example.com", "completepayoutadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, _ = await _register(test_client, register_user_data, "completepayoutcreator@example.com", "completepayoutcreatoruser")
    await _earn_via_fund(test_client, test_db, admin_token, creator_token, award_amount=10000)

    payout_response = await test_client.post(
        "/api/monetization/payouts", json={"amount": 4000}, headers={"Authorization": f"Bearer {creator_token}"}
    )
    payout_id = payout_response.json()["id"]

    decide_response = await test_client.post(
        f"/api/monetization/admin/payouts/{payout_id}/decide",
        json={"status": "completed", "notes": "Paid via bank transfer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert decide_response.status_code == 200
    assert decide_response.json()["status"] == "completed"

    summary = await test_client.get(
        "/api/monetization/summary", headers={"Authorization": f"Bearer {creator_token}"}
    )
    assert summary.json()["total_paid_out"] == 4000
    assert summary.json()["pending_payout_total"] == 0
    assert summary.json()["available_balance"] == 6000


@pytest.mark.asyncio
async def test_cannot_decide_payout_twice(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "twicepayoutadmin@example.com", "twicepayoutadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, _ = await _register(test_client, register_user_data, "twicepayoutcreator@example.com", "twicepayoutcreatoruser")
    await _earn_via_fund(test_client, test_db, admin_token, creator_token, award_amount=10000)

    payout_response = await test_client.post(
        "/api/monetization/payouts", json={"amount": 1000}, headers={"Authorization": f"Bearer {creator_token}"}
    )
    payout_id = payout_response.json()["id"]

    await test_client.post(
        f"/api/monetization/admin/payouts/{payout_id}/decide",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    second = await test_client.post(
        f"/api/monetization/admin/payouts/{payout_id}/decide",
        json={"status": "cancelled"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert second.status_code == 400


@pytest.mark.asyncio
async def test_non_admin_cannot_list_or_decide_payouts(test_client: AsyncClient, register_user_data):
    token, _ = await _register(test_client, register_user_data, "notadminpayouts@example.com", "notadminpayoutsuser")

    list_response = await test_client.get(
        "/api/monetization/admin/payouts", headers={"Authorization": f"Bearer {token}"}
    )
    assert list_response.status_code == 403

    decide_response = await test_client.post(
        f"/api/monetization/admin/payouts/{uuid4()}/decide",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert decide_response.status_code == 403


@pytest.mark.asyncio
async def test_list_my_payouts(test_client: AsyncClient, test_db, register_user_data):
    admin_token, admin_id = await _register(test_client, register_user_data, "listpayoutadmin@example.com", "listpayoutadminuser")
    await _make_admin(test_db, admin_id)
    creator_token, _ = await _register(test_client, register_user_data, "listpayoutcreator@example.com", "listpayoutcreatoruser")
    await _earn_via_fund(test_client, test_db, admin_token, creator_token, award_amount=5000)

    await test_client.post(
        "/api/monetization/payouts", json={"amount": 2000}, headers={"Authorization": f"Bearer {creator_token}"}
    )

    response = await test_client.get(
        "/api/monetization/payouts/me", headers={"Authorization": f"Bearer {creator_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_monetization_endpoints_require_auth(test_client: AsyncClient):
    response = await test_client.get("/api/monetization/summary")
    assert response.status_code == 401

    response = await test_client.post("/api/monetization/payouts", json={"amount": 100})
    assert response.status_code == 401
