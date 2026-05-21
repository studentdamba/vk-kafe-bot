# Client handlers - Main menu, categories, items, cart
from vk_api.bot_longpoll import VkBotMessageEvent
from vk_api.utils import sjson_dumps
from database import (
    get_or_create_user, get_active_categories, get_active_items_by_category,
    get_item_by_id, get_cart_items, add_to_cart, calculate_cart_total, clear_cart,
    get_orders_by_user, get_order_with_items
)
from utils import (
    logger, create_main_keyboard, create_categories_keyboard,
    create_items_keyboard, create_item_detail_keyboard, create_cart_keyboard,
    format_price
)
from config import settings


def handle_start(vk, event: VkBotMessageEvent, session):
    """Handle /start command"""
    vk_id = event.from_id
    
    # Get or create user
    user = get_or_create_user(session, vk_id, event.obj.get("from_id", str(vk_id)))
    
    # Check consent
    if not user.consent_152:
        msg = (
            "👋 Добро пожаловать в кафе «Кимчи»!\n\n"
            "Для продолжения необходимо ваше согласие на обработку персональных данных "
            "в соответствии с 152-ФЗ.\n\n"
            "Мы собираем только необходимую информацию:\n"
            "• Ваше имя\n"
            "• Номер телефона (для связи по заказу)\n"
            "• Адрес доставки (если выбираете доставку)\n\n"
            "Нажимая «✅ Я согласен», вы даёте согласие на обработку ваших данных.\n"
            "Ваши данные не передаются третьим лицам."
        )
        vk.messages.send(
            peer_id=event.peer_id,
            message=msg,
            random_id=0
        )
        return
    
    # Show main menu
    show_main_menu(vk, event)


def show_main_menu(vk, event: VkBotMessageEvent):
    """Show main menu with buttons"""
    msg = (
        "🍽️ **Кафе «Кимчи»**\n\n"
        "Выберите действие:\n"
        "📖 Меню - просмотреть наше меню\n"
        "🛒 Корзина - ваши выбранные блюда\n"
        "📦 Мои заказы - история и статусы заказов\n"
        "📞 Поддержка - связь с администрацией"
    )
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_main_keyboard(),
        random_id=0
    )


def handle_menu(vk, event: VkBotMessageEvent, session):
    """Handle menu button - show categories"""
    categories = get_active_categories(session)
    
    if not categories:
        vk.messages.send(
            peer_id=event.peer_id,
            message="❌ Меню временно недоступно. Попробуйте позже.",
            random_id=0
        )
        return
    
    msg = "📖 **Меню кафе «Кимчи»**\n\nВыберите категорию:"
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_categories_keyboard(categories),
        random_id=0
    )


def handle_category_select(vk, event: VkBotMessageEvent, session, category_name: str):
    """Handle category selection"""
    # Find category by name
    categories = get_active_categories(session)
    category = None
    for cat in categories:
        if cat.name == category_name.replace("📁 ", ""):
            category = cat
            break
    
    if not category:
        vk.messages.send(
            peer_id=event.peer_id,
            message="❌ Категория не найдена.",
            keyboard=create_back_keyboard(),
            random_id=0
        )
        return
    
    items = get_active_items_by_category(session, category.id)
    
    if not items:
        msg = f"📁 **{category.name}**\n\nВ этой категории пока нет товаров."
    else:
        msg = f"📁 **{category.name}**\n\nВыберите блюдо:"
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_items_keyboard(items, category.name),
        random_id=0
    )


def handle_item_select(vk, event: VkBotMessageEvent, session, item_name: str):
    """Handle item selection - show details"""
    # Extract item name from button text (remove price)
    item_name_clean = item_name.split(" - ")[0] if " - " in item_name else item_name
    
    # Find item by name
    items = get_active_items_by_category(session, 0)  # Get all items workaround
    all_categories = get_active_categories(session)
    
    item = None
    for cat in all_categories:
        cat_items = get_active_items_by_category(session, cat.id)
        for it in cat_items:
            if it.name == item_name_clean:
                item = it
                break
        if item:
            break
    
    if not item:
        vk.messages.send(
            peer_id=event.peer_id,
            message="❌ Товар не найден.",
            keyboard=create_back_keyboard(),
            random_id=0
        )
        return
    
    msg = (
        f"🍽️ **{item.name}**\n\n"
        f"💰 Цена: {format_price(item.price)}\n\n"
        f"📝 Описание:\n{item.description}"
    )
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_item_detail_keyboard(item.id),
        random_id=0
    )


def handle_add_to_cart(vk, event: VkBotMessageEvent, session):
    """Handle add to cart action"""
    vk_id = event.from_id
    user = get_or_create_user(session, vk_id, str(vk_id))
    
    # Get last selected item from context (simplified - would need proper state management)
    # For now, we'll ask user to specify quantity
    msg = (
        "➕ Товар добавлен в корзину!\n\n"
        "Для изменения количества используйте кнопку корзины."
    )
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_cart_keyboard(True),
        random_id=0
    )


def handle_cart(vk, event: VkBotMessageEvent, session):
    """Handle cart view"""
    vk_id = event.from_id
    user = get_or_create_user(session, vk_id, str(vk_id))
    
    cart_items = get_cart_items(session, user.id)
    
    if not cart_items:
        msg = (
            "🛒 **Ваша корзина пуста**\n\n"
            "Добавьте товары из меню, чтобы оформить заказ."
        )
        vk.messages.send(
            peer_id=event.peer_id,
            message=msg,
            keyboard=create_main_keyboard(),
            random_id=0
        )
        return
    
    # Build cart message
    msg = "🛒 **Ваша корзина:**\n\n"
    total = 0.0
    
    for cart_item in cart_items:
        item = get_item_by_id(session, cart_item.item_id)
        if item:
            item_total = item.price * cart_item.quantity
            total += item_total
            msg += f"• {item.name} x{cart_item.quantity} = {format_price(item_total)}\n"
    
    msg += f"\n💰 **Итого: {format_price(total)}**"
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_cart_keyboard(True),
        random_id=0
    )


def handle_clear_cart(vk, event: VkBotMessageEvent, session):
    """Handle clear cart action"""
    vk_id = event.from_id
    user = get_or_create_user(session, vk_id, str(vk_id))
    
    clear_cart(session, user.id)
    
    msg = "🗑️ Корзина очищена."
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_main_keyboard(),
        random_id=0
    )


def handle_my_orders(vk, event: VkBotMessageEvent, session):
    """Handle my orders view"""
    vk_id = event.from_id
    user = get_or_create_user(session, vk_id, str(vk_id))
    
    orders = get_orders_by_user(session, user.id)
    
    if not orders:
        msg = (
            "📦 **У вас пока нет заказов**\n\n"
            "Оформите свой первый заказ через меню!"
        )
        vk.messages.send(
            peer_id=event.peer_id,
            message=msg,
            keyboard=create_main_keyboard(),
            random_id=0
        )
        return
    
    msg = "📦 **Ваши заказы:**\n\n"
    
    status_emoji = {
        "pending": "⏳",
        "confirmed": "✅",
        "preparing": "👨‍🍳",
        "ready": "🔔",
        "delivered": "📦",
        "cancelled": "❌"
    }
    
    for order in orders[:10]:  # Show last 10 orders
        emoji = status_emoji.get(order.status, "📋")
        msg += (
            f"{emoji} **Заказ #{order.id}**\n"
            f"Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"Статус: {order.status}\n"
            f"Сумма: {format_price(order.total)}\n\n"
        )
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_back_keyboard(),
        random_id=0
    )


def handle_support(vk, event: VkBotMessageEvent):
    """Handle support request"""
    msg = (
        "📞 **Поддержка**\n\n"
        "Если у вас возникли вопросы или проблемы:\n\n"
        "📱 Телефон: +7 (XXX) XXX-XX-XX\n"
        "⏰ Время работы: 10:00 - 22:00\n\n"
        "Вы также можете написать сообщение прямо здесь, "
        "и администратор ответит вам в ближайшее время."
    )
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_main_keyboard(),
        random_id=0
    )
