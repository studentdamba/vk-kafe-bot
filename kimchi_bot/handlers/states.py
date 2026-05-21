# User states for FSM (Finite State Machine)
from enum import Enum


class UserState(Enum):
    """User interaction states"""
    NONE = "none"
    
    # Checkout states
    CHECKOUT_PHONE = "checkout_phone"
    CHECKOUT_DELIVERY_TYPE = "checkout_delivery_type"
    CHECKOUT_ADDRESS = "checkout_address"
    CHECKOUT_COMMENT = "checkout_comment"
    CHECKOUT_CONFIRM = "checkout_confirm"
    
    # Admin states
    ADMIN_ADD_ITEM_CATEGORY = "admin_add_item_category"
    ADMIN_ADD_ITEM_NAME = "admin_add_item_name"
    ADMIN_ADD_ITEM_PRICE = "admin_add_item_price"
    ADMIN_ADD_ITEM_DESC = "admin_add_item_desc"
    
    ADMIN_EDIT_PRICE_ITEM = "admin_edit_price_item"
    ADMIN_EDIT_PRICE_VALUE = "admin_edit_price_value"
    
    ADMIN_STOP_LIST_ITEM = "admin_stop_list_item"
    
    # Support state
    SUPPORT_MESSAGE = "support_message"


class CheckoutState(Enum):
    """Checkout process states"""
    PHONE = "phone"
    DELIVERY_TYPE = "delivery_type"
    ADDRESS = "address"
    COMMENT = "comment"
    CONFIRM = "confirm"


class AdminState(Enum):
    """Admin operation states"""
    ADD_ITEM = "add_item"
    EDIT_PRICE = "edit_price"
    STOP_LIST = "stop_list"
    CHANGE_STATUS = "change_status"
