"""
Сервис регистрации и обработки глобальных горячих клавиш на базе pynput.keyboard.
"""

from typing import Callable, Optional
import threading
from pynput import keyboard


class HotkeyManager:
    """
    Класс управления глобальными горячими клавишами приложения.
    Перехватывает нажатия F5 (Старт) и F6 (Стоп) в фоновом режиме,
    в том числе при свернутом окне и в полноэкранных приложениях.
    """

    def __init__(self) -> None:
        """Инициализация менеджера горячих клавиш."""
        self._listener: Optional[keyboard.Listener] = None
        self._on_start: Optional[Callable[[], None]] = None
        self._on_stop: Optional[Callable[[], None]] = None
        self._lock = threading.Lock()

    @property
    def is_listening(self) -> bool:
        """Проверяет активность слушателя клавиатуры."""
        with self._lock:
            return self._listener is not None and self._listener.is_alive()

    def start(
        self,
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
    ) -> None:
        """
        Запускает фоновый слушатель клавиатурных событий.

        :param on_start: Коллбек при нажатии F5 (Запуск).
        :param on_stop: Коллбек при нажатии F6 (Остановка).
        """
        with self._lock:
            self.stop()

            self._on_start = on_start
            self._on_stop = on_stop

            self._listener = keyboard.Listener(on_press=self._on_key_press)
            self._listener.daemon = True
            self._listener.start()

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        """
        Внутренний обработчик нажатия клавиш pynput.

        :param key: Объект нажатой клавиши.
        """
        try:
            if key == keyboard.Key.f5:
                start_cb = None
                with self._lock:
                    start_cb = self._on_start
                if start_cb is not None:
                    start_cb()

            elif key == keyboard.Key.f6:
                stop_cb = None
                with self._lock:
                    stop_cb = self._on_stop
                if stop_cb is not None:
                    stop_cb()

        except Exception:
            # Игнорируем непредвиденные системные исключения в хуке ввода
            pass

    def stop(self) -> None:
        """Безопасно останавливает фоновый слушатель клавиатуры."""
        with self._lock:
            self._on_start = None
            self._on_stop = None

            if self._listener is not None:
                try:
                    self._listener.stop()
                except Exception:
                    pass
                self._listener = None
