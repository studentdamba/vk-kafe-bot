# Keyboards and buttons utility
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json


def create_main_keyboard() -> str:
    """Create main menu keyboard"""
    keyboard = VkKeyboard(one_time=False, inline=False)
    
    keyboard.add_button("📖 Меню", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("🛒 Корзина", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("📦 Мои заказы", color=VkKeyboardColor.SECONDARY)
    keyboard.add_button("📞 Поддержка", color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()


def create_back_keyboard() -> str:
    """Create back button keyboard"""
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button("⬅️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def create_categories_keyboard(categories: list) -> str:
    """Create categories list keyboard"""
    keyboard = VkKeyboard(one_time=False, inline=False)
    
    for category in categories:
        keyboard.add_button(f"📁 {category.name}", color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
    
    keyboard.add_button("⬅️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def create_items_keyboard(items: list, category_name: str = "") -> str:
    """Create items list keyboard with descriptions"""
    keyboard = VkKeyboard(one_time=False, inline=False)
    
    if category_name:
        keyboard.add_button(f"📁 {category_name}", color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
    
    for item in items:
        # Button shows name and price
        btn_text = f"{item.name} - {int(item.price)}₽"
        keyboard.add_button(btn_text, color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
    
    keyboard.add_button("⬅️ Назад в меню", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def create_item_detail_keyboard(item_id: int) -> str:
    """Create keyboard for item detail view"""
    keyboard = VkKeyboard(one_time=False, inline=False)
    
    keyboard.add_button("➕ Добавить в корзину", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("⬅️ Назад к списку", color=VkKeyboardColor.SECONDARY)
    
    return keyboard.get_keyboard()


def create_cart_keyboard(has_items: bool = True) -> str:
    """Create cart keyboard"""
    keyboard = VkKeyboard(one_time=False, inline=False)
    
    if has_items:
        keyboard.add_button("✅ Оформить заказ", color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button("🗑️ Очистить корзину", color=VkKeyboardColor.NEGATIVE)
    
    keyboard.add_line()
    keyboard.add_button("⬅️ Назад в меню", color=VkKeyboardColor.SECONDARY)
    
    return keyboard.get_keyboard()


def create_delivery_type_keyboard() -> str:
    """Create delivery type selection keyboard"""
    keyboard = VkKeyboard(one_time=False, inline=False)
    
    keyboard.add_button("🚶 Самовывоз", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🚗 Доставка", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("❌ Отмена", color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()


def create_confirm_keyboard() -> str:
    """Create yes/no confirmation keyboard"""
    keyboard = VkKeyboard(one_time=False, inline=False)
    
    keyboard.add_button("✅ Да, подтверждаю", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("❌ Отмена", color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()


def create_cancel_keyboard() -> str:
    """Create cancel keyboard"""
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button("❌ Отмена", color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()


def create_admin_keyboard() -> str:
    """Create admin menu keyboard"""
    keyboard = VkKeyboard(one_time=False, inline=False)
    
    keyboard.add_button("📋 Список заказов", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📖 Управление меню", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📊 Статистика", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("📥 Экспорт заказов", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("⬅️ Выйти из режима админа", color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()


def create_admin_menu_keyboard() -> str:
    """Create admin menu management keyboard"""
    keyboard = VkKeyboard(one_time=False, inline=False)
    
    keyboard.add_button("📝 Показать всё меню", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("➕ Добавить товар", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("✏️ Изменить цену", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("🚫 Стоп-лист", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("⬅️ Назад", color=VkKeyboardColor.SECONDARY)
    
    return keyboard.get_keyboard()


def create_order_status_keyboard(order_id: int) -> str:
    """Create order status change keyboard for admin"""
    keyboard = VkKeyboard(one_time=False, inline=False)
    
    keyboard.add_button("✅ Подтверждён", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("👨‍🍳 Готовится", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🔔 Готов к выдаче", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("📦 Выдан/Доставлен", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("❌ Отменён", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("⬅️ Назад", color=VkKeyboardColor.SECONDARY)
    
    return keyboard.get_keyboard()


def create_orders_list_keyboard(orders: list) -> str:
    """Create orders list keyboard"""
    keyboard = VkKeyboard(one_time=False, inline=False)
    
    keyboard.add_button("📅 За сегодня", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("⏳ Активные заказы", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("📋 Все заказы", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("⬅️ Назад", color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()
