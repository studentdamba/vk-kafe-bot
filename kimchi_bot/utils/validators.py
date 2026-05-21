# Validators and utilities
import re
from typing import Optional


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Check if it matches Russian phone format
    pattern = r'^(\+7|8|7)?\d{10}$'
    
    if re.match(pattern, cleaned):
        return True
    
    # Also accept format with spaces/dashes
    pattern_flexible = r'^[\d\s\-\+\(\)]{10,20}$'
    if re.match(pattern_flexible, phone) and len(re.sub(r'\D', '', phone)) >= 10:
        return True
    
    return False


def normalize_phone(phone: str) -> str:
    """Normalize phone number to +7XXXXXXXXXX format"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Handle different formats
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    elif len(digits) == 10:
        digits = '7' + digits
    elif len(digits) == 12 and digits.startswith('7'):
        pass  # Already correct
    else:
        return phone  # Return as is if we can't normalize
    
    return f"+{digits}"


def validate_price(price_str: str) -> Optional[float]:
    """Validate and parse price"""
    try:
        price = float(price_str.replace(',', '.'))
        if 0 < price <= 9999:
            return price
    except (ValueError, AttributeError):
        pass
    return None


def format_price(price: float) -> str:
    """Format price for display"""
    return f"{int(price)}₽" if price == int(price) else f"{price:.2f}₽"


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def parse_callback_data(data: str) -> dict:
    """Parse callback data from button payload"""
    result = {}
    if not data:
        return result
    
    parts = data.split(':')
    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            result[key] = value
    
    return result
