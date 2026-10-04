"""
Модуль управления глобальными горячими клавишами и динамического захвата клавиш.
Построен на базе pynput.keyboard для глобального перехвата в любых приложениях и играх.
"""

from typing import Callable, Optional
import threading
from pynput import keyboard


def get_key_vk(key: keyboard.Key | keyboard.KeyCode) -> Optional[int]:
    """
    Извлекает целочисленный Virtual Key (VK) код Windows для любой клавиши pynput.

    :param key: Объект клавиши pynput.
    :return: Целочисленный код клавиши или None.
    """
    if isinstance(key, keyboard.Key):
        if hasattr(key.value, "vk") and key.value.vk is not None:
            return int(key.value.vk)
    elif isinstance(key, keyboard.KeyCode):
        if key.vk is not None:
            return int(key.vk)
        if key.char:
            char_upper = key.char.upper()
            if "A" <= char_upper <= "Z" or "0" <= char_upper <= "9":
                return ord(char_upper)
    return None


class KeybindManager:
    """
    Класс управления горячей клавишей-переключателем (Start/Stop Toggle)
    и динамического захвата любых клавиш для бинда или клавиатурного спамера.
    """

    def __init__(self, default_key: keyboard.Key | keyboard.KeyCode = keyboard.Key.f6) -> None:
        """
        Инициализация менеджера хоткеев.

        :param default_key: Клавиша по умолчанию (F6).
        """
        self._current_key: keyboard.Key | keyboard.KeyCode = default_key
        self._listener: Optional[keyboard.Listener] = None
        self._on_toggle: Optional[Callable[[], None]] = None

        # Универсальный режим захвата одной клавиши (для хоткея или спама)
        self._capture_callback: Optional[Callable[[keyboard.Key | keyboard.KeyCode, str, int], None]] = None

        self._lock = threading.RLock()

    @property
    def is_listening(self) -> bool:
        """Проверяет активность фонового слушателя клавиатуры."""
        with self._lock:
            return self._listener is not None and self._listener.is_alive()

    @property
    def is_capturing(self) -> bool:
        """Возвращает True, если менеджер ожидает нажатия клавиши."""
        with self._lock:
            return self._capture_callback is not None

    def get_current_key_name(self) -> str:
        """Возвращает понятное строковое имя текущей назначенной клавиши."""
        with self._lock:
            return self._key_to_name(self._current_key)

    def start(self, on_toggle: Callable[[], None]) -> None:
        """
        Запускает фоновый глобальный слушатель клавиатурных событий.

        :param on_toggle: Функция обратного вызова при нажатии хоткея (Start/Stop).
        """
        self.stop()

        with self._lock:
            self._on_toggle = on_toggle
            self._listener = keyboard.Listener(on_press=self._on_key_press)
            self._listener.daemon = True
            self._listener.start()

    def stop(self) -> None:
        """Останавливает глобальный слушатель клавиатуры без блокировки потока."""
        with self._lock:
            self._capture_callback = None

            if self._listener is not None:
                listener = self._listener
                self._listener = None
                try:
                    threading.Thread(target=listener.stop, daemon=True).start()
                except Exception:
                    pass

    def start_capture(
        self,
        callback: Callable[[keyboard.Key | keyboard.KeyCode, str, int], None],
    ) -> None:
        """
        Переводит менеджер в режим перехвата ровно одного следующего нажатия клавиши.

        :param callback: Коллбек(key_obj, key_name, vk_code).
        """
        with self._lock:
            self._capture_callback = callback

    def cancel_capture(self) -> None:
        """Отменяет режим ожидания нажатия клавиши."""
        with self._lock:
            self._capture_callback = None

    def set_hotkey(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        """Устанавливает активную клавишу Start/Stop."""
        with self._lock:
            self._current_key = key

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        """
        Внутренний обработчик нажатия клавиши от pynput.

        :param key: Объект нажатой клавиши.
        """
        if key is None:
            return

        # 1. Режим перехвата клавиши (для назначения хоткея или спама)
        callback = None
        with self._lock:
            if self._capture_callback is not None:
                callback = self._capture_callback
                self._capture_callback = None

        if callback is not None:
            name = self._key_to_name(key)
            vk = get_key_vk(key) or 0
            callback(key, name, vk)
            return

        # 2. Обычный рабочий режим: проверка совпадения с хоткеем Start/Stop
        toggle_callback = None
        with self._lock:
            if self._keys_match(key, self._current_key):
                toggle_callback = self._on_toggle

        if toggle_callback is not None:
            toggle_callback()

    def _keys_match(
        self,
        key1: keyboard.Key | keyboard.KeyCode,
        key2: keyboard.Key | keyboard.KeyCode,
    ) -> bool:
        """
        Проверяет совпадение двух клавиш с учетом регистра и виртуальных кодов Windows.
        """
        if isinstance(key1, keyboard.Key) and isinstance(key2, keyboard.Key):
            return key1 == key2

        if isinstance(key1, keyboard.KeyCode) and isinstance(key2, keyboard.KeyCode):
            if key1.vk is not None and key2.vk is not None:
                return key1.vk == key2.vk
            if key1.char and key2.char:
                return key1.char.lower() == key2.char.lower()

        return key1 == key2

    def _key_to_name(self, key: keyboard.Key | keyboard.KeyCode) -> str:
        """
        Преобразует объект клавиши pynput в аккуратное читаемое имя.
        """
        if isinstance(key, keyboard.Key):
            name = key.name
            return name.upper() if name else str(key)

        if isinstance(key, keyboard.KeyCode):
            if key.char:
                return key.char.upper()
            if key.vk:
                if 112 <= key.vk <= 123:
                    return f"F{key.vk - 111}"
                if 65 <= key.vk <= 90:
                    return chr(key.vk)
                if key.vk == 13:
                    return "ENTER"
                if key.vk == 32:
                    return "SPACE"
                return f"VK_{key.vk}"

        return str(key).replace("Key.", "").upper()
