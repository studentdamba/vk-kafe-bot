# Checkout handlers - Order placement flow
from vk_api.bot_longpoll import VkBotMessageEvent
from database import (
    get_or_create_user, get_cart_items, calculate_cart_total, create_order,
    update_user_phone, clear_cart, get_item_by_id
)
from utils import (
    logger, create_delivery_type_keyboard, create_confirm_keyboard,
    create_main_keyboard, create_cancel_keyboard, validate_phone, normalize_phone,
    format_price
)
from handlers.states import UserState


# Simple in-memory state storage (for MVP)
# In production, use Redis or database
user_states = {}
user_checkout_data = {}


def get_user_state(vk_id: int) -> UserState:
    """Get user's current state"""
    return user_states.get(vk_id, UserState.NONE)


def set_user_state(vk_id: int, state: UserState):
    """Set user's state"""
    user_states[vk_id] = state


def clear_user_state(vk_id: int):
    """Clear user's state"""
    if vk_id in user_states:
        del user_states[vk_id]
    if vk_id in user_checkout_data:
        del user_checkout_data[vk_id]


def start_checkout(vk, event: VkBotMessageEvent, session):
    """Start checkout process"""
    vk_id = event.from_id
    user = get_or_create_user(session, vk_id, str(vk_id))
    
    cart_items = get_cart_items(session, user.id)
    
    if not cart_items:
        vk.messages.send(
            peer_id=event.peer_id,
            message="❌ Ваша корзина пуста. Добавьте товары перед оформлением.",
            keyboard=create_main_keyboard(),
            random_id=0
        )
        return
    
    total = calculate_cart_total(session, user.id)
    
    msg = (
        "🛒 **Оформление заказа**\n\n"
        f"В корзине товаров на сумму: {format_price(total)}\n\n"
        "Для оформления заказа введите ваш номер телефона.\n"
        "Формат: +7XXXXXXXXXX или 8XXXXXXXXXX"
    )
    
    set_user_state(vk_id, UserState.CHECKOUT_PHONE)
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_cancel_keyboard(),
        random_id=0
    )


def handle_checkout_phone(vk, event: VkBotMessageEvent, session, phone: str):
    """Handle phone input during checkout"""
    vk_id = event.from_id
    
    if not validate_phone(phone):
        vk.messages.send(
            peer_id=event.peer_id,
            message="❌ Неверный формат телефона.\nПожалуйста, введите номер в формате +7XXXXXXXXXX",
            keyboard=create_cancel_keyboard(),
            random_id=0
        )
        return
    
    normalized_phone = normalize_phone(phone)
    
    # Save phone to checkout data
    if vk_id not in user_checkout_data:
        user_checkout_data[vk_id] = {}
    user_checkout_data[vk_id]["phone"] = normalized_phone
    
    # Update user's phone in DB
    user = get_or_create_user(session, vk_id, str(vk_id))
    update_user_phone(session, vk_id, normalized_phone)
    
    msg = (
        f"✅ Телефон принят: {normalized_phone}\n\n"
        "Выберите тип получения заказа:"
    )
    
    set_user_state(vk_id, UserState.CHECKOUT_DELIVERY_TYPE)
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_delivery_type_keyboard(),
        random_id=0
    )


def handle_delivery_type(vk, event: VkBotMessageEvent, session, delivery_type: str):
    """Handle delivery type selection"""
    vk_id = event.from_id
    
    if vk_id not in user_checkout_data:
        vk.messages.send(
            peer_id=event.peer_id,
            message="❌ Ошибка оформления. Начните сначала.",
            keyboard=create_main_keyboard(),
            random_id=0
        )
        clear_user_state(vk_id)
        return
    
    is_delivery = "доставка" in delivery_type.lower()
    user_checkout_data[vk_id]["delivery_type"] = "delivery" if is_delivery else "pickup"
    
    if is_delivery:
        msg = (
            "🚗 Вы выбрали доставку.\n\n"
            "Введите адрес доставки:\n"
            "(улица, дом, квартира, подъезд, этаж)"
        )
        set_user_state(vk_id, UserState.CHECKOUT_ADDRESS)
    else:
        msg = (
            "🚶 Вы выбрали самовывоз.\n\n"
            "Адрес самовывоза: ул. Примерная, д. 1\n"
            "Время работы: 10:00 - 22:00\n\n"
            "Добавить комментарий к заказу? (или напишите «нет»)"
        )
        set_user_state(vk_id, UserState.CHECKOUT_COMMENT)
        user_checkout_data[vk_id]["address"] = None
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_cancel_keyboard(),
        random_id=0
    )


def handle_address(vk, event: VkBotMessageEvent, session, address: str):
    """Handle address input"""
    vk_id = event.from_id
    
    if vk_id not in user_checkout_data:
        vk.messages.send(
            peer_id=event.peer_id,
            message="❌ Ошибка оформления. Начните сначала.",
            keyboard=create_main_keyboard(),
            random_id=0
        )
        clear_user_state(vk_id)
        return
    
    user_checkout_data[vk_id]["address"] = address
    
    msg = (
        f"✅ Адрес сохранён: {address}\n\n"
        "Добавить комментарий к заказу? (или напишите «нет»)"
    )
    
    set_user_state(vk_id, UserState.CHECKOUT_COMMENT)
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_cancel_keyboard(),
        random_id=0
    )


def handle_comment(vk, event: VkBotMessageEvent, session, comment: str):
    """Handle comment input"""
    vk_id = event.from_id
    
    if vk_id not in user_checkout_data:
        vk.messages.send(
            peer_id=event.peer_id,
            message="❌ Ошибка оформления. Начните сначала.",
            keyboard=create_main_keyboard(),
            random_id=0
        )
        clear_user_state(vk_id)
        return
    
    # Save comment (or None if "no")
    if comment.lower() in ["нет", "no", "-"]:
        comment = None
    
    user_checkout_data[vk_id]["comment"] = comment
    
    # Show order summary for confirmation
    user = get_or_create_user(session, vk_id, str(vk_id))
    cart_items = get_cart_items(session, user.id)
    total = calculate_cart_total(session, user.id)
    
    checkout = user_checkout_data[vk_id]
    
    msg = (
        "📋 **Подтверждение заказа**\n\n"
        "**Состав заказа:**\n"
    )
    
    for cart_item in cart_items:
        item = get_item_by_id(session, cart_item.item_id)
        if item:
            msg += f"• {item.name} x{cart_item.quantity}\n"
    
    msg += (
        f"\n💰 **Итого: {format_price(total)}**\n\n"
        f"📞 Телефон: {checkout['phone']}\n"
        f"🚚 Тип: {'Доставка' if checkout['delivery_type'] == 'delivery' else 'Самовывоз'}\n"
    )
    
    if checkout.get('address'):
        msg += f"📍 Адрес: {checkout['address']}\n"
    
    if checkout.get('comment'):
        msg += f"📝 Комментарий: {checkout['comment']}\n"
    
    msg += "\nПодтверждаете заказ?"
    
    set_user_state(vk_id, UserState.CHECKOUT_CONFIRM)
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_confirm_keyboard(),
        random_id=0
    )


def handle_checkout_confirm(vk, event: VkBotMessageEvent, session, confirmed: bool):
    """Handle order confirmation"""
    vk_id = event.from_id
    
    if vk_id not in user_checkout_data or not confirmed:
        msg = "❌ Заказ отменён."
        vk.messages.send(
            peer_id=event.peer_id,
            message=msg,
            keyboard=create_main_keyboard(),
            random_id=0
        )
        clear_user_state(vk_id)
        return
    
    user = get_or_create_user(session, vk_id, str(vk_id))
    checkout = user_checkout_data[vk_id]
    total = calculate_cart_total(session, user.id)
    
    # Create order
    order = create_order(
        session=session,
        user_id=user.id,
        total=total,
        delivery_type=checkout['delivery_type'],
        address=checkout.get('address'),
        phone=checkout['phone'],
        comment=checkout.get('comment')
    )
    
    msg = (
        f"✅ **Заказ #{order.id} принят!**\n\n"
        "Ожидайте подтверждения от администратора.\n"
        "Мы уведомим вас об изменении статуса заказа."
    )
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_main_keyboard(),
        random_id=0
    )
    
    # Log for admin notification (in production, send to admin chat)
    logger.info(f"New order #{order.id} from user {vk_id}")
    
    clear_user_state(vk_id)
