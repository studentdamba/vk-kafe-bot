# Database queries and operations
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Tuple
from models.models import User, Category, Item, CartItem, Order, OrderItem
from datetime import datetime, timedelta


# User operations
def get_or_create_user(session: Session, vk_id: int, name: str) -> User:
    """Get existing user or create new one"""
    user = session.query(User).filter(User.vk_id == vk_id).first()
    if not user:
        user = User(vk_id=vk_id, name=name)
        session.add(user)
        session.commit()
    return user

def update_user_consent(session: Session, vk_id: int, consent: bool = True) -> None:
    """Update user's 152-ФЗ consent"""
    user = session.query(User).filter(User.vk_id == vk_id).first()
    if user:
        user.consent_152 = consent
        session.commit()

def update_user_phone(session: Session, vk_id: int, phone: str) -> None:
    """Update user's phone number"""
    user = session.query(User).filter(User.vk_id == vk_id).first()
    if user:
        user.phone = phone
        session.commit()

def get_user_by_vk_id(session: Session, vk_id: int) -> Optional[User]:
    """Get user by VK ID"""
    return session.query(User).filter(User.vk_id == vk_id).first()


# Category operations
def get_active_categories(session: Session) -> List[Category]:
    """Get all active categories sorted by sort_order"""
    return session.query(Category).filter(
        Category.is_active == True
    ).order_by(Category.sort_order).all()

def get_category_by_id(session: Session, category_id: int) -> Optional[Category]:
    """Get category by ID"""
    return session.query(Category).filter(Category.id == category_id).first()


# Item operations
def get_active_items_by_category(session: Session, category_id: int) -> List[Item]:
    """Get all active items in a category (not in stop_list)"""
    return session.query(Item).filter(
        Item.category_id == category_id,
        Item.is_active == True,
        Item.stop_list == False
    ).all()

def get_item_by_id(session: Session, item_id: int) -> Optional[Item]:
    """Get item by ID"""
    return session.query(Item).filter(Item.id == item_id).first()

def get_all_active_items(session: Session) -> List[Item]:
    """Get all active items"""
    return session.query(Item).filter(
        Item.is_active == True,
        Item.stop_list == False
    ).all()

def add_item_to_db(session: Session, category_id: int, name: str, price: float, description: str) -> Item:
    """Add new item to database"""
    item = Item(
        category_id=category_id,
        name=name,
        price=price,
        description=description
    )
    session.add(item)
    session.commit()
    return item

def update_item_price(session: Session, item_id: int, new_price: float) -> bool:
    """Update item price"""
    item = session.query(Item).filter(Item.id == item_id).first()
    if item:
        item.price = new_price
        session.commit()
        return True
    return False

def toggle_item_stop_list(session: Session, item_id: int) -> Optional[Item]:
    """Toggle item stop_list status"""
    item = session.query(Item).filter(Item.id == item_id).first()
    if item:
        item.stop_list = not item.stop_list
        session.commit()
        return item
    return None


# Cart operations
def get_cart_items(session: Session, user_id: int) -> List[CartItem]:
    """Get all cart items for a user"""
    return session.query(CartItem).filter(CartItem.user_id == user_id).all()

def add_to_cart(session: Session, user_id: int, item_id: int, quantity: int = 1) -> CartItem:
    """Add item to cart or update quantity if exists"""
    cart_item = session.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.item_id == item_id
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
        if cart_item.quantity <= 0:
            session.delete(cart_item)
        else:
            cart_item.updated_at = datetime.utcnow()
    else:
        if quantity > 0:
            cart_item = CartItem(user_id=user_id, item_id=item_id, quantity=quantity)
            session.add(cart_item)
    
    session.commit()
    return cart_item

def clear_cart(session: Session, user_id: int) -> None:
    """Clear user's cart"""
    session.query(CartItem).filter(CartItem.user_id == user_id).delete()
    session.commit()

def calculate_cart_total(session: Session, user_id: int) -> float:
    """Calculate total cart amount"""
    cart_items = get_cart_items(session, user_id)
    total = 0.0
    for cart_item in cart_items:
        item = session.query(Item).filter(Item.id == cart_item.item_id).first()
        if item:
            total += item.price * cart_item.quantity
    return total


# Order operations
def create_order(
    session: Session,
    user_id: int,
    total: float,
    delivery_type: str,
    address: Optional[str],
    phone: str,
    comment: Optional[str]
) -> Order:
    """Create new order from cart"""
    order = Order(
        user_id=user_id,
        total=total,
        delivery_type=delivery_type,
        address=address,
        phone=phone,
        comment=comment,
        status="pending"
    )
    session.add(order)
    session.flush()  # Get order ID
    
    # Add order items from cart
    cart_items = get_cart_items(session, user_id)
    for cart_item in cart_items:
        item = session.query(Item).filter(Item.id == cart_item.item_id).first()
        if item:
            order_item = OrderItem(
                order_id=order.id,
                item_id=item.id,
                quantity=cart_item.quantity,
                price_at_order=item.price
            )
            session.add(order_item)
    
    # Clear cart
    clear_cart(session, user_id)
    session.commit()
    return order

def get_order_by_id(session: Session, order_id: int) -> Optional[Order]:
    """Get order by ID"""
    return session.query(Order).filter(Order.id == order_id).first()

def get_orders_by_user(session: Session, user_id: int) -> List[Order]:
    """Get all orders for a user"""
    return session.query(Order).filter(
        Order.user_id == user_id
    ).order_by(Order.created_at.desc()).all()

def update_order_status(session: Session, order_id: int, new_status: str) -> bool:
    """Update order status"""
    order = session.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = new_status
        session.commit()
        return True
    return False

def get_orders_filtered(
    session: Session,
    filter_type: str = "all",
    limit: int = 20
) -> List[Order]:
    """Get orders with filtering"""
    query = session.query(Order)
    
    if filter_type == "today":
        today = datetime.utcnow().date()
        query = query.filter(func.date(Order.created_at) == today)
    elif filter_type == "pending":
        query = query.filter(Order.status.in_(["pending", "confirmed", "preparing"]))
    
    return query.order_by(Order.created_at.desc()).limit(limit).all()

def get_order_with_items(session: Session, order_id: int) -> Optional[Tuple[Order, List[OrderItem]]]:
    """Get order with its items"""
    order = get_order_by_id(session, order_id)
    if order:
        items = session.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        return order, items
    return None


# Stats operations
def get_stats(session: Session) -> dict:
    """Get basic statistics"""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    
    # Orders count
    orders_today = session.query(Order).filter(Order.created_at >= today_start).count()
    orders_week = session.query(Order).filter(Order.created_at >= week_start).count()
    orders_total = session.query(Order).count()
    
    # Revenue
    revenue_today = session.query(func.sum(Order.total)).filter(
        Order.created_at >= today_start,
        Order.status.notin_(["cancelled"])
    ).scalar() or 0.0
    
    revenue_week = session.query(func.sum(Order.total)).filter(
        Order.created_at >= week_start,
        Order.status.notin_(["cancelled"])
    ).scalar() or 0.0
    
    # Top items
    top_items_query = session.query(
        Item.name,
        func.sum(OrderItem.quantity).label("total_qty")
    ).join(OrderItem).join(Order).filter(
        Order.created_at >= week_start
    ).group_by(Item.id).order_by(func.sum(OrderItem.quantity).desc()).limit(3)
    
    top_items = top_items_query.all()
    
    return {
        "orders_today": orders_today,
        "orders_week": orders_week,
        "orders_total": orders_total,
        "revenue_today": revenue_today,
        "revenue_week": revenue_week,
        "top_items": top_items
    }


# Admin operations
def get_menu_list(session: Session) -> List[Tuple[Category, List[Item]]]:
    """Get full menu list for admin"""
    categories = get_active_categories(session)
    result = []
    for category in categories:
        items = session.query(Item).filter(Item.category_id == category.id).all()
        result.append((category, items))
    return result

def export_orders_csv(session: Session, start_date: datetime, end_date: datetime) -> str:
    """Export orders to CSV format"""
    orders = session.query(Order).filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date
    ).order_by(Order.created_at.desc()).all()
    
    lines = ["ID;Дата;Статус;Тип доставки;Адрес;Телефон;Сумма;Комментарий"]
    for order in orders:
        lines.append(
            f"{order.id};"
            f"{order.created_at.strftime('%Y-%m-%d %H:%M')};"
            f"{order.status};"
            f"{order.delivery_type};"
            f"{order.address or '-'};"
            f"{order.phone};"
            f"{order.total};"
            f"{order.comment or '-'}"
        )
    
    return "\n".join(lines)
