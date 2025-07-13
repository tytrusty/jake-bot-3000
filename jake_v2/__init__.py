"""
RuneScape Bot Package

A comprehensive bot framework for RuneScape automation with human-like mouse movements.
"""

__version__ = "2.0.0"
__author__ = "Jake"

# Import main components for easy access
try:
    from .runescape_bot import RuneScapeBot
    from .path.human_path_finder import HumanPath
except ImportError:
    # Handle case where dependencies might not be available
    pass

__all__ = [
    'RuneScapeBot',
    'HumanPath',
] 