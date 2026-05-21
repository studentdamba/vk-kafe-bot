#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VK Bot for Kimchi Cafe
Main entry point using vk_api + VkBotLongpoll
"""

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboardColor
from vk_api.utils import sjson_dumps

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from database import get_engine, init_db, get_session_factory, seed_database
from utils import logger, create_main_keyboard
from handlers import (
    handle_start, show_main_menu, handle_menu, handle_category_select,
    handle_item_select, handle_cart, handle_clear_cart, handle_my_orders,
    handle_support, start_checkout, handle_checkout_phone, handle_delivery_type,
    handle_address, handle_comment, handle_checkout_confirm,
    get_user_state, clear_user_state, UserState, user_checkout_data,
    is_admin, handle_admin_command, handle_menu_list, handle_orders_list,
    handle_show_orders, handle_stats, handle_export_orders, handle_admin_cancel,
    admin_states, admin_data
)


def parse_button_text(text: str) -> dict:
    """Parse button text to determine action"""
    text_lower = text.lower()
    
    # Main menu buttons
    if "меню" in text_lower and "назад" not in text_lower:
        return {"action": "menu"}
    elif "корзина" in text_lower:
        return {"action": "cart"}
    elif "заказы" in text_lower or "мои заказы" in text_lower:
        return {"action": "my_orders"}
    elif "поддержка" in text_lower:
        return {"action": "support"}
    
    # Cart buttons
    elif "оформить" in text_lower:
        return {"action": "checkout_start"}
    elif "очистить" in text_lower or "удалить" in text_lower:
        return {"action": "clear_cart"}
    
    # Navigation
    elif "назад" in text_lower:
        return {"action": "back"}
    elif "отмена" in text_lower or "cancel" in text_lower:
        return {"action": "cancel"}
    
    # Checkout
    elif "самовывоз" in text_lower:
        return {"action": "delivery_pickup"}
    elif "доставка" in text_lower:
        return {"action": "delivery_delivery"}
    elif "да, подтверждаю" in text_lower or "подтверждаю" in text_lower:
        return {"action": "confirm_order"}
    
    # Admin buttons
    elif "список заказов" in text_lower:
        return {"action": "admin_orders"}
    elif "управление меню" in text_lower:
        return {"action": "admin_menu"}
    elif "статистика" in text_lower:
        return {"action": "admin_stats"}
    elif "экспорт заказов" in text_lower:
        return {"action": "admin_export"}
    elif "выйти из режима" in text_lower or "выйти" in text_lower:
        return {"action": "admin_exit"}
    elif "показать всё меню" in text_lower:
        return {"action": "admin_menu_list"}
    elif "добавить товар" in text_lower:
        return {"action": "admin_add_item"}
    elif "изменить цену" in text_lower:
        return {"action": "admin_edit_price"}
    elif "стоп-лист" in text_lower:
        return {"action": "admin_stop_list"}
    elif "за сегодня" in text_lower:
        return {"action": "orders_today"}
    elif "активные заказы" in text_lower:
        return {"action": "orders_pending"}
    elif "все заказы" in text_lower:
        return {"action": "orders_all"}
    
    # Order status buttons
    elif "подтверждён" in text_lower:
        return {"action": "status_confirmed"}
    elif "готовится" in text_lower:
        return {"action": "status_preparing"}
    elif "готов к выдаче" in text_lower or "готов" in text_lower:
        return {"action": "status_ready"}
    elif "выдан" in text_lower or "доставлен" in text_lower:
        return {"action": "status_delivered"}
    elif "отменён" in text_lower:
        return {"action": "status_cancelled"}
    
    return {"action": "unknown", "text": text}


def main():
    """Main bot loop"""
    
    logger.info("Starting Kimchi Bot...")
    
    # Initialize database
    logger.info("Initializing database...")
    engine = get_engine()
    init_db(engine)
    session_factory = get_session_factory(engine)
    
    with session_factory() as session:
        seed_database(session)
    logger.info("Database initialized successfully")
    
    # Initialize VK API
    if not settings.VK_TOKEN or settings.VK_TOKEN == "your_vk_token_here":
        logger.error("VK_TOKEN not set in .env file!")
        print("❌ Ошибка: VK_TOKEN не настроен в файле .env")
        print("Скопируйте .env.example в .env и укажите ваш токен VK")
        sys.exit(1)
    
    vk_session = vk_api.VkApi(token=settings.VK_TOKEN)
    vk = vk_session.get_api()
    
    # Get bot info
    try:
        bot_info = vk.groups.getById()
        logger.info(f"Bot started for group: {bot_info[0]['name']}")
        print(f"✅ Бот запущен для группы: {bot_info[0]['name']}")
        group_id = bot_info[0]['id']
    except Exception as e:
        logger.error(f"Failed to get bot info: {e}")
        print("⚠️ Не удалось получить информацию о группе")
        print(f"Ошибка: {e}")
        print("\n🔑 Проверьте VK_TOKEN в файле .env")
        print("Получить токен можно в управлении сообществом VK → Работа с API → Создать ключ")
        print("\n❌ Бот не может работать без корректного токена. Остановка.")
        sys.exit(1)
    
    # Initialize Long Poll
    longpoll = VkBotLongPoll(vk_session, group_id)
    logger.info("Long Poll initialized")
    
    print("\n🤖 Бот работает. Нажмите Ctrl+C для остановки.\n")
    
    # Main event loop
    try:
        for event in longpoll.listen():
            try:
                if event.type == VkBotEventType.MESSAGE_NEW:
                    # Get message object from event
                    message = event.obj.message
                    vk_id = message['from_id']
                    peer_id = message['peer_id']
                    text = message.get('text', '').strip()
                    
                    with session_factory() as session:
                        # Handle user state first (for checkout and admin operations)
                        user_state = get_user_state(vk_id)
                        
                        # Check if in checkout flow
                        if user_state != UserState.NONE:
                            logger.debug(f"User {vk_id} in state: {user_state}")
                            
                            if user_state == UserState.CHECKOUT_PHONE:
                                handle_checkout_phone(vk, event, session, text)
                            elif user_state == UserState.CHECKOUT_DELIVERY_TYPE:
                                handle_delivery_type(vk, event, session, text)
                            elif user_state == UserState.CHECKOUT_ADDRESS:
                                handle_address(vk, event, session, text)
                            elif user_state == UserState.CHECKOUT_COMMENT:
                                handle_comment(vk, event, session, text)
                            elif user_state == UserState.CHECKOUT_CONFIRM:
                                confirmed = "да" in text.lower() or "подтверждаю" in text.lower()
                                handle_checkout_confirm(vk, event, session, confirmed)
                            
                            continue
                        
                        # Check for admin state
                        if vk_id in admin_states:
                            admin_state = admin_states[vk_id]
                            logger.debug(f"Admin {vk_id} in state: {admin_state}")
                            # Admin state handling would go here
                            # For MVP, we'll handle via commands
                            
                        # Handle commands
                        if text.startswith('/'):
                            command = text.lower().split()[0]
                            
                            if command in ['/start', 'начать']:
                                handle_start(vk, event, session)
                            elif command == '/admin':
                                handle_admin_command(vk, event, session)
                            elif command == '/menu_list':
                                handle_menu_list(vk, event, session)
                            elif command == '/orders':
                                filter_type = "all"
                                if len(text.split()) > 1:
                                    filter_type = text.split()[1]
                                handle_show_orders(vk, event, session, filter_type)
                            elif command == '/stats':
                                handle_stats(vk, event, session)
                            elif command == '/export':
                                handle_export_orders(vk, event, session)
                            else:
                                vk.messages.send(
                                    peer_id=peer_id,
                                    message=f"❌ Неизвестная команда: {command}\nИспользуйте /start или /admin",
                                    random_id=0
                                )
                            continue
                        
                        # Handle button clicks (text-based for MVP)
                        if text:
                            parsed = parse_button_text(text)
                            action = parsed.get("action")
                            
                            if action == "menu":
                                handle_menu(vk, event, session)
                            elif action == "cart":
                                handle_cart(vk, event, session)
                            elif action == "my_orders":
                                handle_my_orders(vk, event, session)
                            elif action == "support":
                                handle_support(vk, event)
                            elif action == "checkout_start":
                                start_checkout(vk, event, session)
                            elif action == "clear_cart":
                                handle_clear_cart(vk, event, session)
                            elif action == "back":
                                show_main_menu(vk, event)
                            elif action == "cancel":
                                clear_user_state(vk_id)
                                if vk_id in admin_states:
                                    del admin_states[vk_id]
                                if vk_id in admin_data:
                                    del admin_data[vk_id]
                                show_main_menu(vk, event)
                            elif action == "delivery_pickup":
                                handle_delivery_type(vk, event, session, "pickup")
                            elif action == "delivery_delivery":
                                handle_delivery_type(vk, event, session, "delivery")
                            elif action == "confirm_order":
                                handle_checkout_confirm(vk, event, session, True)
                            elif action == "admin_orders":
                                handle_orders_list(vk, event, session)
                            elif action == "admin_menu":
                                msg = "📖 Управление меню\nВыберите действие:"
                                from utils import create_admin_menu_keyboard
                                vk.messages.send(
                                    peer_id=peer_id,
                                    message=msg,
                                    keyboard=create_admin_menu_keyboard(),
                                    random_id=0
                                )
                            elif action == "admin_stats":
                                handle_stats(vk, event, session)
                            elif action == "admin_export":
                                handle_export_orders(vk, event, session)
                            elif action == "admin_exit":
                                if vk_id in admin_states:
                                    del admin_states[vk_id]
                                if vk_id in admin_data:
                                    del admin_data[vk_id]
                                show_main_menu(vk, event)
                            elif action == "admin_menu_list":
                                handle_menu_list(vk, event, session)
                            elif action == "orders_today":
                                handle_show_orders(vk, event, session, "today")
                            elif action == "orders_pending":
                                handle_show_orders(vk, event, session, "pending")
                            elif action == "orders_all":
                                handle_show_orders(vk, event, session, "all")
                            elif action.startswith("status_"):
                                status_map = {
                                    "status_confirmed": "confirmed",
                                    "status_preparing": "preparing",
                                    "status_ready": "ready",
                                    "status_delivered": "delivered",
                                    "status_cancelled": "cancelled"
                                }
                                new_status = status_map.get(action, action.replace("status_", ""))
                                # Would need order_id from context - simplified for MVP
                                vk.messages.send(
                                    peer_id=peer_id,
                                    message=f"ℹ️ Для смены статуса используйте команду:\n/status <order_id> <status>",
                                    random_id=0
                                )
                            elif action == "unknown":
                                # Try to match category or item
                                # Check if it's a category
                                from database import get_active_categories
                                categories = get_active_categories(session)
                                matched = False
                                
                                for cat in categories:
                                    if cat.name in text:
                                        handle_category_select(vk, event, session, cat.name)
                                        matched = True
                                        break
                                
                                if not matched:
                                    # Check if it's an item
                                    from database import get_all_active_items
                                    items = get_all_active_items(session)
                                    for item in items:
                                        if item.name in text:
                                            handle_item_select(vk, event, session, item.name)
                                            matched = True
                                            break
                                
                                if not matched:
                                    # Unknown input
                                    vk.messages.send(
                                        peer_id=peer_id,
                                        message="🤔 Используйте кнопки меню или команду /start",
                                        keyboard=create_main_keyboard(),
                                        random_id=0
                                    )
                
                elif event.type == VkBotEventType.MESSAGE_TYPING_STATE:
                    # User is typing - could be used for analytics
                    pass
                    
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
                
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n👋 Бот остановлен")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
