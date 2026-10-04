"""
Сервис циклического выполнения кликов мыши и нажатий клавиш клавиатуры
на базе низкоуровневого Windows API (ctypes).
Обеспечивает надежный кликер мыши (Single/Double, LMB/RMB) и циклический спамер клавиш (Key Presser).
"""

from typing import Callable, Optional, Tuple
import ctypes
import threading
import time

# Низкоуровневые константы Windows API mouse_event
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

# Низкоуровневые константы Windows API keybd_event
KEYEVENTF_KEYUP = 0x0002


class ClickerEngine:
    """
    Класс управления фоновым циклом автоматизации (мышь или клавиатура).
    Выполняет симуляцию нажатий через ctypes.windll.user32 в изолированном потоке,
    поддерживая одиночные/двойные клики мыши, спам клавиш и мгновенную остановку.
    """

    def __init__(self) -> None:
        """Инициализация движка кликера."""
        self._user32 = ctypes.windll.user32
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._is_running: bool = False

        self._on_error: Optional[Callable[[str], None]] = None
        self._on_stopped: Optional[Callable[[], None]] = None

    @property
    def is_running(self) -> bool:
        """Возвращает флаг активности фонового цикла."""
        with self._lock:
            return self._is_running

    def start(
        self,
        interval: float,
        mode: str = "mouse",
        button: str = "left",
        click_type: str = "single",
        coords_provider: Optional[Callable[[], Optional[Tuple[int, int]]]] = None,
        target_vk: Optional[int] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_stopped: Optional[Callable[[], None]] = None,
    ) -> bool:
        """
        Запускает фоновый поток циклического кликания или спама клавиши.

        :param interval: Интервал между действиями в секундах.
        :param mode: Режим работы ('mouse' или 'keyboard').
        :param button: Кнопка мыши ('left' или 'right').
        :param click_type: Тип клика ('single' или 'double').
        :param coords_provider: Функция, возвращающая текущие (X, Y) маркера или None.
        :param target_vk: Virtual Key код для режима клавиатуры.
        :param on_error: Коллбек при ошибке.
        :param on_stopped: Коллбек при остановке.
        :return: True, если поток запущен, False если уже работал.
        """
        with self._lock:
            if self._is_running:
                return False

            self._stop_event.clear()
            self._is_running = True
            self._on_error = on_error
            self._on_stopped = on_stopped

            self._thread = threading.Thread(
                target=self._run_loop,
                args=(mode, interval, button, click_type, coords_provider, target_vk),
                name="TBKAutomationThread",
                daemon=True,
            )
            self._thread.start()
            return True

    def stop(self) -> bool:
        """
        Мгновенно останавливает цикл автоматизации и дожидается завершения потока.

        :return: True, если движок был остановлен, False если он не работал.
        """
        with self._lock:
            if not self._is_running:
                return False
            self._stop_event.set()

        # Ожидание остановки потока без захвата блокировки
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.6)

        with self._lock:
            self._is_running = False
            self._thread = None

        return True

    def _run_loop(
        self,
        mode: str,
        interval: float,
        button: str,
        click_type: str,
        coords_provider: Optional[Callable[[], Optional[Tuple[int, int]]]],
        target_vk: Optional[int],
    ) -> None:
        """
        Рабочий цикл, выполняемый в изолированном фоновом потоке.
        """
        error_msg: Optional[str] = None

        # Подготовка флагов мыши
        if button == "right":
            down_flag = MOUSEEVENTF_RIGHTDOWN
            up_flag = MOUSEEVENTF_RIGHTUP
        else:
            down_flag = MOUSEEVENTF_LEFTDOWN
            up_flag = MOUSEEVENTF_LEFTUP

        try:
            if mode == "keyboard":
                # Режим циклического спама клавиши клавиатуры
                vk_code = int(target_vk) if target_vk else 13  # Default ENTER
                while not self._stop_event.is_set():
                    self._user32.keybd_event(vk_code, 0, 0, 0)
                    time.sleep(0.01)
                    self._user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)

                    if self._stop_event.wait(timeout=max(0.0001, interval)):
                        break
            else:
                # Режим кликера мыши
                while not self._stop_event.is_set():
                    coords = coords_provider() if coords_provider else None

                    if coords is not None:
                        self._user32.SetCursorPos(int(coords[0]), int(coords[1]))

                    if click_type == "double":
                        self._user32.mouse_event(down_flag, 0, 0, 0, 0)
                        self._user32.mouse_event(up_flag, 0, 0, 0, 0)
                        time.sleep(0.04)
                        self._user32.mouse_event(down_flag, 0, 0, 0, 0)
                        self._user32.mouse_event(up_flag, 0, 0, 0, 0)
                    else:
                        self._user32.mouse_event(down_flag, 0, 0, 0, 0)
                        self._user32.mouse_event(up_flag, 0, 0, 0, 0)

                    if self._stop_event.wait(timeout=max(0.0001, interval)):
                        break

        except Exception as exc:
            error_msg = f"Ошибка в потоке автоматизации: {exc}"
        finally:
            with self._lock:
                self._is_running = False

            if error_msg and self._on_error:
                self._on_error(error_msg)

            if self._on_stopped:
                self._on_stopped()
