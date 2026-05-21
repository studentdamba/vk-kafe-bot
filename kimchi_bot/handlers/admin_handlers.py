# Admin handlers - Menu management, orders, stats
from vk_api.bot_longpoll import VkBotMessageEvent
from datetime import datetime, timedelta
from database import (
    get_or_create_user, get_active_categories, get_category_by_id,
    get_all_active_items, add_item_to_db, update_item_price, toggle_item_stop_list,
    get_orders_filtered, get_order_by_id, update_order_status, get_stats,
    get_menu_list, export_orders_csv, get_item_by_id
)
from utils import (
    logger, create_admin_keyboard, create_admin_menu_keyboard,
    create_order_status_keyboard, create_orders_list_keyboard, create_back_keyboard,
    create_main_keyboard, format_price, validate_price
)
from config import settings
from handlers.states import UserState


# In-memory state storage for admin operations
admin_states = {}
admin_data = {}


def is_admin(vk_id: int) -> bool:
    """Check if user is admin"""
    return vk_id in settings.ADMIN_IDS


def check_admin_access(vk, event: VkBotMessageEvent):
    """Check admin access and send error if not authorized"""
    if not is_admin(event.from_id):
        vk.messages.send(
            peer_id=event.peer_id,
            message="❌ Доступ ограничен. Только для администраторов.",
            random_id=0
        )
        return False
    return True


def handle_admin_command(vk, event: VkBotMessageEvent, session):
    """Handle /admin command"""
    if not check_admin_access(vk, event):
        return
    
    vk_id = event.from_id
    user = get_or_create_user(session, vk_id, str(vk_id))
    
    msg = (
        "🔧 **Режим администратора**\n\n"
        "Доступные команды:\n"
        "• /menu_list - показать всё меню\n"
        "• /add_item - добавить товар\n"
        "• /edit_price - изменить цену\n"
        "• /stop_list - стоп-лист товара\n"
        "• /orders - список заказов\n"
        "• /status - изменить статус заказа\n"
        "• /stats - статистика\n"
        "• /export - экспорт заказов\n\n"
        "Или используйте кнопки:"
    )
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_admin_keyboard(),
        random_id=0
    )


def handle_menu_list(vk, event: VkBotMessageEvent, session):
    """Show full menu list for admin"""
    if not check_admin_access(vk, event):
        return
    
    menu = get_menu_list(session)
    
    msg = "📖 **Полное меню:**\n\n"
    
    for category, items in menu:
        status_icon = "✅" if category.is_active else "❌"
        msg += f"\n{status_icon} **{category.name}**\n"
        
        for item in items:
            stop_icon = "🚫" if item.stop_list else ""
            msg += f"  • {item.name} - {format_price(item.price)} {stop_icon}\n"
    
    if len(msg) > 4096:
        # Split long message
        parts = [msg[i:i+4096] for i in range(0, len(msg), 4096)]
        for part in parts:
            vk.messages.send(
                peer_id=event.peer_id,
                message=part,
                random_id=0
            )
    else:
        vk.messages.send(
            peer_id=event.peer_id,
            message=msg,
            keyboard=create_admin_menu_keyboard(),
            random_id=0
        )


def handle_add_item_start(vk, event: VkBotMessageEvent, session):
    """Start add item process"""
    if not check_admin_access(vk, event):
        return
    
    categories = get_active_categories(session)
    
    msg = (
        "➕ **Добавление товара**\n\n"
        "Выберите категорию для нового товара:"
    )
    
    keyboard = VkKeyboard(one_time=False, inline=False)
    for cat in categories:
        keyboard.add_button(cat.name, color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
    keyboard.add_button("❌ Отмена", color=VkKeyboardColor.NEGATIVE)
    
    admin_states[event.from_id] = "add_item_category"
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=keyboard.get_keyboard(),
        random_id=0
    )


def handle_edit_price_start(vk, event: VkBotMessageEvent, session):
    """Start edit price process"""
    if not check_admin_access(vk, event):
        return
    
    items = get_all_active_items(session)
    
    msg = (
        "✏️ **Изменение цены**\n\n"
        "Выберите товар для изменения цены:"
    )
    
    keyboard = VkKeyboard(one_time=False, inline=False)
    for item in items[:20]:  # Limit to 20 items
        keyboard.add_button(f"{item.name} - {format_price(item.price)}", color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
    keyboard.add_button("❌ Отмена", color=VkKeyboardColor.NEGATIVE)
    
    admin_states[event.from_id] = "edit_price_item"
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=keyboard.get_keyboard(),
        random_id=0
    )


def handle_stop_list_start(vk, event: VkBotMessageEvent, session):
    """Start stop list toggle process"""
    if not check_admin_access(vk, event):
        return
    
    items = get_all_active_items(session)
    
    msg = (
        "🚫 **Стоп-лист**\n\n"
        "Выберите товар для переключения статуса:\n"
        "(товар в стоп-листе не показывается в меню)"
    )
    
    keyboard = VkKeyboard(one_time=False, inline=False)
    for item in items[:20]:
        stop_status = "🚫 В стоп-листе" if item.stop_list else "✅ Активен"
        keyboard.add_button(f"{item.name} ({stop_status})", color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
    keyboard.add_button("❌ Отмена", color=VkKeyboardColor.NEGATIVE)
    
    admin_states[event.from_id] = "stop_list_item"
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=keyboard.get_keyboard(),
        random_id=0
    )


def handle_orders_list(vk, event: VkBotMessageEvent, session):
    """Show orders list"""
    if not check_admin_access(vk, event):
        return
    
    msg = (
        "📋 **Управление заказами**\n\n"
        "Выберите фильтр:"
    )
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_orders_list_keyboard([]),
        random_id=0
    )


def handle_show_orders(vk, event: VkBotMessageEvent, session, filter_type: str = "all"):
    """Show filtered orders"""
    if not check_admin_access(vk, event):
        return
    
    orders = get_orders_filtered(session, filter_type)
    
    if not orders:
        vk.messages.send(
            peer_id=event.peer_id,
            message=f"❌ Заказы ({filter_type}) не найдены.",
            keyboard=create_admin_keyboard(),
            random_id=0
        )
        return
    
    status_emoji = {
        "pending": "⏳",
        "confirmed": "✅",
        "preparing": "👨‍🍳",
        "ready": "🔔",
        "delivered": "📦",
        "cancelled": "❌"
    }
    
    msg = f"📋 **Заказы ({filter_type}):**\n\n"
    
    for order in orders[:15]:
        emoji = status_emoji.get(order.status, "📋")
        delivery_info = "🚗 Доставка" if order.delivery_type == "delivery" else "🚶 Самовывоз"
        msg += (
            f"{emoji} **Заказ #{order.id}**\n"
            f"Дата: {order.created_at.strftime('%d.%m %H:%M')}\n"
            f"Статус: {order.status}\n"
            f"{delivery_info}\n"
            f"Телефон: {order.phone}\n"
            f"Сумма: {format_price(order.total)}\n\n"
        )
    
    if len(msg) > 4096:
        parts = [msg[i:i+4096] for i in range(0, len(msg), 4096)]
        for i, part in enumerate(parts):
            vk.messages.send(
                peer_id=event.peer_id,
                message=part,
                random_id=0
            )
    else:
        vk.messages.send(
            peer_id=event.peer_id,
            message=msg,
            keyboard=create_admin_keyboard(),
            random_id=0
        )


def handle_change_status_start(vk, event: VkBotMessageEvent, session, order_id: int):
    """Start change order status process"""
    if not check_admin_access(vk, event):
        return
    
    order = get_order_by_id(session, order_id)
    
    if not order:
        vk.messages.send(
            peer_id=event.peer_id,
            message=f"❌ Заказ #{order_id} не найден.",
            random_id=0
        )
        return
    
    msg = (
        f"📦 **Заказ #{order_id}**\n\n"
        f"Текущий статус: {order.status}\n"
        f"Клиент: {order.phone}\n"
        f"Сумма: {format_price(order.total)}\n\n"
        "Выберите новый статус:"
    )
    
    admin_data[event.from_id] = {"order_id": order_id}
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_order_status_keyboard(order_id),
        random_id=0
    )


def handle_status_change(vk, event: VkBotMessageEvent, session, new_status: str):
    """Handle order status change"""
    if not check_admin_access(vk, event):
        return
    
    vk_id = event.from_id
    
    if vk_id not in admin_data or "order_id" not in admin_data[vk_id]:
        vk.messages.send(
            peer_id=event.peer_id,
            message="❌ Ошибка. Начните выбор заказа заново.",
            keyboard=create_admin_keyboard(),
            random_id=0
        )
        return
    
    order_id = admin_data[vk_id]["order_id"]
    
    # Map button text to status
    status_map = {
        "подтверждён": "confirmed",
        "готовится": "preparing",
        "готов к выдаче": "ready",
        "выдан/доставлен": "delivered",
        "отменён": "cancelled"
    }
    
    actual_status = status_map.get(new_status.lower(), new_status)
    
    if update_order_status(session, order_id, actual_status):
        msg = f"✅ Статус заказа #{order_id} изменён на: {actual_status}"
        
        # TODO: Send notification to customer
        logger.info(f"Order #{order_id} status changed to {actual_status} by admin {vk_id}")
    else:
        msg = f"❌ Не удалось изменить статус заказа #{order_id}"
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_admin_keyboard(),
        random_id=0
    )
    
    # Clear admin data
    if vk_id in admin_data:
        del admin_data[vk_id]


def handle_stats(vk, event: VkBotMessageEvent, session):
    """Show statistics"""
    if not check_admin_access(vk, event):
        return
    
    stats = get_stats(session)
    
    msg = (
        "📊 **Статистика**\n\n"
        f"**Заказы:**\n"
        f"• Сегодня: {stats['orders_today']}\n"
        f"• За неделю: {stats['orders_week']}\n"
        f"• Всего: {stats['orders_total']}\n\n"
        f"**Выручка:**\n"
        f"• Сегодня: {format_price(stats['revenue_today'])}\n"
        f"• За неделю: {format_price(stats['revenue_week'])}\n\n"
    )
    
    if stats['top_items']:
        msg += "**Топ товаров за неделю:**\n"
        for i, (name, qty) in enumerate(stats['top_items'], 1):
            msg += f"{i}. {name} ({qty} шт.)\n"
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_admin_keyboard(),
        random_id=0
    )


def handle_export_orders(vk, event: VkBotMessageEvent, session):
    """Export orders to CSV"""
    if not check_admin_access(vk, event):
        return
    
    # Export last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    csv_content = export_orders_csv(session, start_date, end_date)
    
    # Save to file and send
    filename = f"orders_{end_date.strftime('%Y%m%d')}.csv"
    
    with open(f"logs/{filename}", "w", encoding="utf-8") as f:
        f.write(csv_content)
    
    msg = (
        f"📥 **Экспорт заказов**\n\n"
        f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n"
        f"Файл сохранён: logs/{filename}\n\n"
        "В продакшене файл будет отправлен в чат."
    )
    
    vk.messages.send(
        peer_id=event.peer_id,
        message=msg,
        keyboard=create_admin_keyboard(),
        random_id=0
    )


def handle_admin_cancel(vk, event: VkBotMessageEvent, session):
    """Cancel admin operation"""
    vk_id = event.from_id
    
    if vk_id in admin_states:
        del admin_states[vk_id]
    if vk_id in admin_data:
        del admin_data[vk_id]
    
    vk.messages.send(
        peer_id=event.peer_id,
        message="❌ Операция отменена.",
        keyboard=create_main_keyboard(),
        random_id=0
    )


# Import VkKeyboard for admin handlers
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
