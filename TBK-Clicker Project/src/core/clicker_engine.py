"""
Сервис циклического выполнения кликов мыши на базе PyAutoGUI и threading.
"""

from typing import Callable, Optional, Tuple
import threading
import pyautogui

# Отключаем встроенную искусственную паузу PyAutoGUI между вызовами (по умолчанию 0.1 сек)
pyautogui.PAUSE = 0.0


class ClickerEngine:
    """
    Класс управления жизненным циклом автоматических кликов.
    Выполняет клики в отдельном фоновом потоке с возможностью мгновенной остановки
    через threading.Event.
    """

    def __init__(self) -> None:
        """Инициализация движка кликера."""
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._is_running: bool = False

        self._on_error: Optional[Callable[[str], None]] = None
        self._on_stopped: Optional[Callable[[], None]] = None

    @property
    def is_running(self) -> bool:
        """Возвращает текущее состояние работы кликера."""
        with self._lock:
            return self._is_running

    def start(
        self,
        interval: float,
        button: str = "left",
        coords: Optional[Tuple[int, int]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_stopped: Optional[Callable[[], None]] = None,
    ) -> bool:
        """
        Запускает фоновый поток циклического кликания.

        :param interval: Интервал между кликами в секундах.
        :param button: Кнопка мыши ('left' или 'right').
        :param coords: Кортеж (x, y) координат экрана или None для текущей позиции.
        :param on_error: Коллбек для передачи текста ошибки.
        :param on_stopped: Коллбек при завершении работы потока.
        :return: True, если поток успешно запущен, False если уже работал.
        """
        with self._lock:
            if self._is_running:
                return False

            self._stop_event.clear()
            self._is_running = True
            self._on_error = on_error
            self._on_stopped = on_stopped

            self._thread = threading.Thread(
                target=self._click_loop,
                args=(interval, button, coords),
                name="ClickerEngineThread",
                daemon=True,
            )
            self._thread.start()
            return True

    def stop(self) -> bool:
        """
        Останавливает цикл кликов и ожидает завершения потока.

        :return: True, если кликер был остановлен, False если он не работал.
        """
        with self._lock:
            if not self._is_running:
                return False
            self._stop_event.set()

        # Ожидание остановки потока без удержания блокировки
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        with self._lock:
            self._is_running = False
            self._thread = None

        return True

    def _click_loop(
        self,
        interval: float,
        button: str,
        coords: Optional[Tuple[int, int]],
    ) -> None:
        """
        Рабочий цикл кликера, выполняемый в изолированном потоке.

        :param interval: Задержка между кликами в секундах.
        :param button: Тип кнопки мыши ('left' или 'right').
        :param coords: Целевые координаты (X, Y) или None.
        """
        error_message: Optional[str] = None

        try:
            while not self._stop_event.is_set():
                # Выполнение клика в заданной точке или в текущей позиции курсора
                if coords is not None:
                    pyautogui.click(x=coords[0], y=coords[1], button=button)
                else:
                    pyautogui.click(button=button)

                # Точная пауза с мгновенным пробуждением при сигнале остановки
                # Если сработал stop_event, wait вернет True и цикл немедленно прервется
                if self._stop_event.wait(timeout=max(0.0001, interval)):
                    break

        except pyautogui.FailSafeException:
            # Срабатывание встроенной защиты FailSafe (курсор переведен в угол экрана)
            error_message = "Защита PyAutoGUI: курсор в углу экрана. Кликер остановлен."
        except Exception as exc:
            error_message = f"Ошибка в потоке кликера: {exc}"
        finally:
            with self._lock:
                self._is_running = False

            if error_message and self._on_error:
                self._on_error(error_message)

            if self._on_stopped:
                self._on_stopped()
