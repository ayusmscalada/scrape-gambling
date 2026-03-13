"""Manager module for automation worker console server."""
from app.manager.registry import SiteRegistry
from app.manager.server import AutomationManager
from app.manager.commands import CommandHandler
from app.manager.puppeteer_client import PuppeteerClient

__all__ = [
    'SiteRegistry',
    'AutomationManager',
    'CommandHandler',
    'PuppeteerClient',
]
