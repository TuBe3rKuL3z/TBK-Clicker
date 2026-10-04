"""
Сервис фонового захвата координат курсора с экрана с использованием pynput.mouse.
"""

from typing import Callable, Optional
import threading
from pynput import mouse


class CoordinatePicker:
    """
    Класс для перехвата координат точки на экране в фоновом режиме.
    Использует глобальный слушатель pynput.mouse.Listener для регистрации
    первого же клика мыши в любой точке экрана.
    """

    def __init__(self) -> None:
        """Инициализация сервиса захвата координат."""
        self._listener: Optional[mouse.Listener] = None
        self._callback: Optional[Callable[[int, int], None]] = None
        self._lock = threading.Lock()
        self._is_active: bool = False

    @property
    def is_active(self) -> bool:
        """Возвращает текущий статус активности слушателя."""
        return self._is_active

    def start(self, callback: Callable[[int, int], None]) -> None:
        """
        Запускает фоновый слушатель клика мыши.

        :param callback: Функция обратного вызова, принимающая координаты (x, y).
        """
        with self._lock:
            # Если уже слушает, сначала останавливаем предыдущий
            self.stop()

            self._callback = callback
            self._is_active = True
            self._listener = mouse.Listener(on_click=self._on_click)
            self._listener.daemon = True
            self._listener.start()

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> bool:
        """
        Внутренний обработчик событий клика от pynput.mouse.

        :param x: Координата X курсора в пикселях.
        :param y: Координата Y курсора в пикселях.
        :param button: Нажатая кнопка мыши.
        :param pressed: Флаг нажатия (True - нажата, False - отпущена).
        :return: False для завершения работы слушателя pynput.
        """
        # Срабатываем только на нажатие (pressed=True)
        if pressed:
            callback_to_call = None
            with self._lock:
                self._is_active = False
                callback_to_call = self._callback
                self._callback = None

            if callback_to_call is not None:
                # Передаем целочисленные координаты экрана
                callback_to_call(int(x), int(y))

            # Возврат False в pynput приводит к безопасному отключению слушателя
            return False

        return True

    def stop(self) -> None:
        """Принудительно останавливает фоновый слушатель мыши, если он активен."""
        with self._lock:
            self._is_active = False
            self._callback = None
            if self._listener is not None:
                try:
                    self._listener.stop()
                except Exception:
                    pass
                self._listener = None
