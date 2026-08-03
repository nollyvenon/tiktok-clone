"""
Creator Shop service - storefronts, products, and orders.

Orders are recorded transactions only. No real payment processor exists
anywhere in this app (consistent with Creator Fund and Collaborations),
so placing an order and fulfilling it are both just status changes on a
row - no money actually moves.
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Shop, ShopProduct, ShopOrder, ShopOrderStatus

logger = logging.getLogger(__name__)


class ShopService:
    """Service for creator shops, products, and orders"""

    @staticmethod
    async def get_shop_by_user(db: AsyncSession, user_id: UUID) -> Optional[Shop]:
        result = await db.execute(select(Shop).where(Shop.user_id == user_id))
        return result.scalar()

    @staticmethod
    async def upsert_my_shop(db: AsyncSession, user_id: UUID, name: str, description: Optional[str]) -> Shop:
        shop = await ShopService.get_shop_by_user(db, user_id)
        if shop:
            shop.name = name
            shop.description = description
        else:
            shop = Shop(user_id=user_id, name=name, description=description)
            db.add(shop)
        await db.commit()
        await db.refresh(shop)
        return shop

    @staticmethod
    async def get_shop_with_products_by_user(db: AsyncSession, user_id: UUID) -> Tuple[Shop, List[ShopProduct]]:
        shop = await ShopService.get_shop_by_user(db, user_id)
        if not shop or not shop.is_active:
            raise ValueError("This creator doesn't have a shop")
        return await ShopService.get_shop_with_products(db, shop.id)

    @staticmethod
    async def get_shop_with_products(db: AsyncSession, shop_id: UUID) -> Tuple[Shop, List[ShopProduct]]:
        shop = await db.get(Shop, shop_id)
        if not shop or not shop.is_active:
            raise ValueError("Shop not found")

        result = await db.execute(
            select(ShopProduct).where(
                and_(
                    ShopProduct.shop_id == shop_id,
                    ShopProduct.is_active == True,
                    ShopProduct.deleted_at.is_(None),
                )
            ).order_by(desc(ShopProduct.created_at))
        )
        return shop, list(result.scalars().all())

    @staticmethod
    async def create_product(
        db: AsyncSession, user_id: UUID, name: str, description: Optional[str],
        price: int, image_url: Optional[str], stock_quantity: Optional[int],
    ) -> ShopProduct:
        shop = await ShopService.get_shop_by_user(db, user_id)
        if not shop:
            raise ValueError("Create a shop before adding products")

        product = ShopProduct(
            shop_id=shop.id, name=name, description=description,
            price=price, image_url=image_url, stock_quantity=stock_quantity,
        )
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def update_product(db: AsyncSession, user_id: UUID, product_id: UUID, updates: dict) -> ShopProduct:
        product = await db.get(ShopProduct, product_id)
        if not product or product.deleted_at is not None:
            raise ValueError("Product not found")

        shop = await db.get(Shop, product.shop_id)
        if not shop or shop.user_id != user_id:
            raise ValueError("Not authorized")

        for field, value in updates.items():
            if value is not None:
                setattr(product, field, value)
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def delete_product(db: AsyncSession, user_id: UUID, product_id: UUID) -> None:
        product = await db.get(ShopProduct, product_id)
        if not product or product.deleted_at is not None:
            raise ValueError("Product not found")

        shop = await db.get(Shop, product.shop_id)
        if not shop or shop.user_id != user_id:
            raise ValueError("Not authorized")

        product.deleted_at = datetime.utcnow()
        product.is_active = False
        await db.commit()

    @staticmethod
    async def place_order(db: AsyncSession, buyer_id: UUID, product_id: UUID, quantity: int) -> ShopOrder:
        product = await db.get(ShopProduct, product_id)
        if not product or not product.is_active or product.deleted_at is not None:
            raise ValueError("Product not found or no longer available")

        shop = await db.get(Shop, product.shop_id)
        if not shop or not shop.is_active:
            raise ValueError("Shop not found or no longer active")
        if shop.user_id == buyer_id:
            raise ValueError("You can't order your own product")

        if product.stock_quantity is not None:
            if product.stock_quantity < quantity:
                raise ValueError("Not enough stock available")
            product.stock_quantity -= quantity

        order = ShopOrder(
            product_id=product_id,
            shop_id=shop.id,
            buyer_id=buyer_id,
            quantity=quantity,
            total_amount=product.price * quantity,
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        logger.info(f"Order {order.id} placed by {buyer_id} for product {product_id}")
        return order

    @staticmethod
    async def list_my_orders(db: AsyncSession, buyer_id: UUID) -> List[ShopOrder]:
        result = await db.execute(
            select(ShopOrder).where(ShopOrder.buyer_id == buyer_id).order_by(desc(ShopOrder.created_at))
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_received_orders(db: AsyncSession, user_id: UUID) -> List[ShopOrder]:
        shop = await ShopService.get_shop_by_user(db, user_id)
        if not shop:
            return []
        result = await db.execute(
            select(ShopOrder).where(ShopOrder.shop_id == shop.id).order_by(desc(ShopOrder.created_at))
        )
        return list(result.scalars().all())

    @staticmethod
    async def _get_order_for_seller(db: AsyncSession, user_id: UUID, order_id: UUID) -> ShopOrder:
        order = await db.get(ShopOrder, order_id)
        if not order:
            raise ValueError("Order not found")
        shop = await db.get(Shop, order.shop_id)
        if not shop or shop.user_id != user_id:
            raise ValueError("Not authorized")
        return order

    @staticmethod
    async def fulfill_order(db: AsyncSession, user_id: UUID, order_id: UUID) -> ShopOrder:
        order = await ShopService._get_order_for_seller(db, user_id, order_id)
        if order.status != ShopOrderStatus.PENDING:
            raise ValueError("Only pending orders can be fulfilled")

        order.status = ShopOrderStatus.FULFILLED
        order.fulfilled_at = datetime.utcnow()
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def cancel_order(db: AsyncSession, user_id: UUID, order_id: UUID) -> ShopOrder:
        order = await ShopService._get_order_for_seller(db, user_id, order_id)
        if order.status != ShopOrderStatus.PENDING:
            raise ValueError("Only pending orders can be cancelled")

        product = await db.get(ShopProduct, order.product_id)
        if product and product.stock_quantity is not None:
            product.stock_quantity += order.quantity

        order.status = ShopOrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()
        await db.commit()
        await db.refresh(order)
        return order
