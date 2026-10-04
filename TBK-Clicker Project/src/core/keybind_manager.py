"""
Модуль управления глобальными горячими клавишами и динамического бинда клавиш.
Построен на базе pynput.keyboard для глобального перехвата в любых приложениях и играх.
"""

from typing import Callable, Optional
import threading
from pynput import keyboard


class KeybindManager:
    """
    Класс управления горячей клавишей-переключателем (Start/Stop Toggle).
    Поддерживает динамический перехват любой нажатой пользователем клавиши
    и ее назначение в качестве активного хоткея.
    """

    def __init__(self, default_key: keyboard.Key | keyboard.KeyCode = keyboard.Key.f6) -> None:
        """
        Инициализация менеджера хоткеев.

        :param default_key: Клавиша по умолчанию (F6).
        """
        self._current_key: keyboard.Key | keyboard.KeyCode = default_key
        self._listener: Optional[keyboard.Listener] = None
        self._on_toggle: Optional[Callable[[], None]] = None

        self._is_binding: bool = False
        self._on_key_bound: Optional[Callable[[str], None]] = None

        self._lock = threading.RLock()

    @property
    def is_listening(self) -> bool:
        """Проверяет активность фонового слушателя клавиатуры."""
        with self._lock:
            return self._listener is not None and self._listener.is_alive()

    @property
    def is_binding(self) -> bool:
        """Возвращает True, если менеджер ожидает нажатия клавиши для назначения."""
        with self._lock:
            return self._is_binding

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
            self._is_binding = False
            self._on_key_bound = None

            if self._listener is not None:
                listener = self._listener
                self._listener = None
                try:
                    # Останавливаем в отдельном потоке, исключая подвисания Windows хука
                    threading.Thread(target=listener.stop, daemon=True).start()
                except Exception:
                    pass

    def start_binding(self, on_key_bound: Callable[[str], None]) -> None:
        """
        Переводит менеджер в режим перехвата следующей нажатой клавиши.

        :param on_key_bound: Коллбек, принимающий строковое название назначенной клавиши.
        """
        with self._lock:
            self._is_binding = True
            self._on_key_bound = on_key_bound

    def cancel_binding(self) -> None:
        """Отменяет режим ожидания нажатия клавиши."""
        with self._lock:
            self._is_binding = False
            self._on_key_bound = None

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        """
        Внутренний обработчик нажатия клавиши от pynput.

        :param key: Объект нажатой клавиши.
        """
        if key is None:
            return

        # 1. Режим назначения новой клавиши (Binding mode)
        binding_callback: Optional[Callable[[str], None]] = None
        key_name: str = ""

        with self._lock:
            if self._is_binding:
                self._is_binding = False
                self._current_key = key
                key_name = self._key_to_name(key)
                binding_callback = self._on_key_bound
                self._on_key_bound = None

        if binding_callback is not None:
            binding_callback(key_name)
            return

        # 2. Обычный рабочий режим: проверка совпадения с активным хоткеем
        toggle_callback: Optional[Callable[[], None]] = None
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
        # Сравнение специальных клавиш (Key.f1 .. Key.f12, Key.space и др.)
        if isinstance(key1, keyboard.Key) and isinstance(key2, keyboard.Key):
            return key1 == key2

        # Сравнение символьных клавиш
        if isinstance(key1, keyboard.KeyCode) and isinstance(key2, keyboard.KeyCode):
            # Сравнение по Virtual Key коду (не зависит от языка раскладки клавиатуры)
            if key1.vk is not None and key2.vk is not None:
                return key1.vk == key2.vk
            if key1.char and key2.char:
                return key1.char.lower() == key2.char.lower()

        # Прямое равенство объектов
        return key1 == key2

    def _key_to_name(self, key: keyboard.Key | keyboard.KeyCode) -> str:
        """
        Преобразует объект клавиши pynput в аккуратное читаемое имя.
        """
        if isinstance(key, keyboard.Key):
            name = key.name
            # Приводим к общепринятому верхнему регистру
            return name.upper() if name else str(key)

        if isinstance(key, keyboard.KeyCode):
            if key.char:
                return key.char.upper()
            if key.vk:
                # Популярные функциональные клавиши через VK кодировку
                if 112 <= key.vk <= 123:
                    return f"F{key.vk - 111}"
                if 65 <= key.vk <= 90:
                    return chr(key.vk)
                return f"VK_{key.vk}"

        return str(key).replace("Key.", "").upper()
