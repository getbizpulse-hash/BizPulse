import urllib.parse
from typing import Optional
import random
import string


def generate_coupon_code(prefix: str = "BIZ", length: int = 6) -> str:
    """Generate a random coupon code."""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix}{suffix}"


def build_email_link(
    to_email: str,
    subject: str,
    body: str
) -> str:
    """Build a mailto: link."""
    params = urllib.parse.urlencode({
        "subject": subject,
        "body": body
    }, quote_via=urllib.parse.quote)
    return f"mailto:{to_email}?{params}"


def build_whatsapp_link(phone: str, message: str) -> str:
    """Build a wa.me link for WhatsApp."""
    # Clean phone number (remove non-digits except +)
    clean_phone = ''.join(c for c in str(phone) if c.isdigit() or c == '+')
    if clean_phone.startswith('+'):
        clean_phone = clean_phone[1:]

    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded_message}"


def generate_upgrade_message(
    customer_name: str,
    visits: int,
    target_visits: int,
    coupon_code: str,
    business_name: str = "us"
) -> str:
    """Generate personalized upgrade message."""
    remaining = target_visits - visits

    return f"""Hi {customer_name}!

You've visited {business_name} {visits} times this year — just {remaining} more to reach VIP status!

Book your next appointment and use code {coupon_code} for 15% off.

We appreciate your loyalty!"""


def generate_winback_message(
    customer_name: str,
    coupon_code: str,
    business_name: str = "us"
) -> str:
    """Generate win-back message for lapsed customers."""
    return f"""Hi {customer_name},

We miss you! It's been a while since your last visit to {business_name}.

As a thank you for being a valued customer, here's 20% off your next appointment. Use code {coupon_code}.

We'd love to see you again soon!"""


def generate_explorer_message(
    customer_name: str,
    coupon_code: str,
    business_name: str = "us"
) -> str:
    """Generate message for one-time visitors."""
    return f"""Hi {customer_name},

We'd love to see you again at {business_name}!

Here's 10% off your next appointment — use code {coupon_code} when you book.

Hope to see you soon!"""
