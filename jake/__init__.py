"""
RuneScape Bot Package

A comprehensive bot framework for RuneScape automation with human-like mouse movements.
"""

__version__ = "2.0.0"
__author__ = "Jake"

from .bots.attack_bot import AttackBot
from .bots.buy_iron_bot import BuyIronBot
from .bots.fishing_bot import FishingBot
from . import path

__all__ = [
    'AttackBot',
    'BuyIronBot',
    'FishingBot',
    'path',
] 