"""
Creator Shop API routes - storefronts, products, and orders
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.database import get_db
from app.routes.auth import get_current_user
from app.models import User
from app.services.shop import ShopService
from app.schemas import (
    ShopUpsertRequest, ShopResponse, ShopWithProductsResponse,
    ShopProductCreate, ShopProductUpdate, ShopProductResponse,
    ShopOrderCreate, ShopOrderResponse, ShopOrderListResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shop", tags=["Creator Shop"])


@router.post("/me", response_model=ShopResponse)
async def upsert_my_shop(
    request: ShopUpsertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update your own shop"""
    shop = await ShopService.upsert_my_shop(db, current_user.id, request.name, request.description)
    return ShopResponse.model_validate(shop)


@router.get("/me", response_model=ShopResponse, responses={404: {"model": ErrorResponse}})
async def get_my_shop(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get your own shop"""
    shop = await ShopService.get_shop_by_user(db, current_user.id)
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You don't have a shop yet")
    return ShopResponse.model_validate(shop)


@router.get(
    "/orders/me",
    response_model=ShopOrderListResponse,
)
async def list_my_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Orders you've placed as a buyer"""
    orders = await ShopService.list_my_orders(db, current_user.id)
    return ShopOrderListResponse(orders=[ShopOrderResponse.model_validate(o) for o in orders])


@router.get(
    "/orders/received",
    response_model=ShopOrderListResponse,
)
async def list_received_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Orders placed against your shop, as the seller"""
    orders = await ShopService.list_received_orders(db, current_user.id)
    return ShopOrderListResponse(orders=[ShopOrderResponse.model_validate(o) for o in orders])


@router.post(
    "/orders/{order_id}/fulfill",
    response_model=ShopOrderResponse,
    responses={400: {"model": ErrorResponse}},
)
async def fulfill_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Seller: mark a pending order fulfilled"""
    try:
        order = await ShopService.fulfill_order(db, current_user.id, order_id)
        return ShopOrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/orders/{order_id}/cancel",
    response_model=ShopOrderResponse,
    responses={400: {"model": ErrorResponse}},
)
async def cancel_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Seller: cancel a pending order, restocking the product"""
    try:
        order = await ShopService.cancel_order(db, current_user.id, order_id)
        return ShopOrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/products",
    response_model=ShopProductResponse,
    responses={400: {"model": ErrorResponse}},
)
async def create_product(
    request: ShopProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a product to your shop"""
    try:
        product = await ShopService.create_product(
            db, current_user.id, request.name, request.description,
            request.price, request.image_url, request.stock_quantity,
        )
        return ShopProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/products/{product_id}",
    response_model=ShopProductResponse,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def update_product(
    product_id: UUID,
    request: ShopProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update your own product"""
    try:
        product = await ShopService.update_product(
            db, current_user.id, product_id, request.model_dump(exclude_unset=True)
        )
        return ShopProductResponse.model_validate(product)
    except ValueError as e:
        code = status.HTTP_403_FORBIDDEN if str(e) == "Not authorized" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(e))


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def delete_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove your own product (soft delete)"""
    try:
        await ShopService.delete_product(db, current_user.id, product_id)
        return {"message": "Product removed"}
    except ValueError as e:
        code = status.HTTP_403_FORBIDDEN if str(e) == "Not authorized" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(e))


@router.post(
    "/products/{product_id}/order",
    response_model=ShopOrderResponse,
    responses={400: {"model": ErrorResponse}},
)
async def order_product(
    product_id: UUID,
    request: ShopOrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Place an order for a product"""
    try:
        order = await ShopService.place_order(db, current_user.id, product_id, request.quantity)
        return ShopOrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/user/{user_id}",
    response_model=ShopWithProductsResponse,
    responses={400: {"model": ErrorResponse}},
)
async def get_shop_by_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """View a creator's shop and its active products, by their user id"""
    try:
        shop, products = await ShopService.get_shop_with_products_by_user(db, user_id)
        return ShopWithProductsResponse(
            shop=ShopResponse.model_validate(shop),
            products=[ShopProductResponse.model_validate(p) for p in products],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{shop_id}",
    response_model=ShopWithProductsResponse,
    responses={400: {"model": ErrorResponse}},
)
async def get_shop(
    shop_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """View a shop and its active products"""
    try:
        shop, products = await ShopService.get_shop_with_products(db, shop_id)
        return ShopWithProductsResponse(
            shop=ShopResponse.model_validate(shop),
            products=[ShopProductResponse.model_validate(p) for p in products],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
