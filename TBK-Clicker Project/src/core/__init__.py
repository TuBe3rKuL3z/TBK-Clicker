"""
Ядро бизнес-логики приложения TBK-Clicker.
Содержит службы симуляции мыши и менеджер глобальных биндов клавиатуры.
"""

from src.core.clicker_engine import ClickerEngine
from src.core.keybind_manager import KeybindManager

__all__ = [
    "ClickerEngine",
    "KeybindManager",
]
