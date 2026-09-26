"""
infrastructure/email/__init__.py
================================
Transactional Email Provider Abstraction for Task 8.20.
"""

from infrastructure.email.provider import (
    EmailEvent,
    EmailMessage,
    EmailProvider,
    DevelopmentEmailProvider,
    ProductionEmailProvider,
    get_email_provider,
    reset_email_provider,
)

__all__ = [
    "EmailEvent",
    "EmailMessage",
    "EmailProvider",
    "DevelopmentEmailProvider",
    "ProductionEmailProvider",
    "get_email_provider",
    "reset_email_provider",
]
