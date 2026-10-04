"""
Сервис циклического выполнения кликов мыши на базе низкоуровневого Windows API (ctypes).
Обеспечивает максимальную надежность кликов в Windows, играх и полноэкранных приложениях.
"""

from typing import Callable, Optional, Tuple
import ctypes
import threading

# Низкоуровневые константы Windows API mouse_event
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010


class ClickerEngine:
    """
    Класс управления жизненным циклом автоматических кликов.
    Выполняет симуляцию нажатий через ctypes.windll.user32 в изолированном потоке,
    поддерживая динамическое считывание координат центра маркера и мгновенную остановку.
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
        """Возвращает флаг активности фонового цикла кликов."""
        with self._lock:
            return self._is_running

    def start(
        self,
        interval: float,
        button: str = "left",
        coords_provider: Optional[Callable[[], Optional[Tuple[int, int]]]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_stopped: Optional[Callable[[], None]] = None,
    ) -> bool:
        """
        Запускает фоновый поток циклического кликания.

        :param interval: Интервал между кликами в секундах.
        :param button: Кнопка мыши ('left' или 'right').
        :param coords_provider: Функция, возвращающая текущие (X, Y) маркера или None.
        :param on_error: Коллбек при возникновении ошибки.
        :param on_stopped: Коллбек при штатной остановке потока.
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
                target=self._click_loop,
                args=(interval, button, coords_provider),
                name="TBKClickerThread",
                daemon=True,
            )
            self._thread.start()
            return True

    def stop(self) -> bool:
        """
        Мгновенно останавливает цикл кликов и дожидается завершения потока.

        :return: True, если кликер был остановлен, False если он не работал.
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

    def _click_loop(
        self,
        interval: float,
        button: str,
        coords_provider: Optional[Callable[[], Optional[Tuple[int, int]]]],
    ) -> None:
        """
        Рабочий цикл кликов, выполняемый в изолированном фоновом потоке.

        :param interval: Задержка между кликами в секундах.
        :param button: Кнопка ('left' или 'right').
        :param coords_provider: Провайдер координат цели.
        """
        error_msg: Optional[str] = None

        # Определение флагов нажатия/отпускания кнопки
        if button == "right":
            down_flag = MOUSEEVENTF_RIGHTDOWN
            up_flag = MOUSEEVENTF_RIGHTUP
        else:
            down_flag = MOUSEEVENTF_LEFTDOWN
            up_flag = MOUSEEVENTF_LEFTUP

        try:
            while not self._stop_event.is_set():
                # Получаем актуальные координаты маркера (динамически при каждом клике)
                coords = coords_provider() if coords_provider else None

                if coords is not None:
                    # Перемещаем курсор точно в центр маркера
                    self._user32.SetCursorPos(int(coords[0]), int(coords[1]))

                # Отправка низкоуровневых событий нажатия и отпускания кнопки мыши
                self._user32.mouse_event(down_flag, 0, 0, 0, 0)
                self._user32.mouse_event(up_flag, 0, 0, 0, 0)

                # Точная задержка с мгновенным пробуждением при сигнале остановки
                if self._stop_event.wait(timeout=max(0.0001, interval)):
                    break

        except Exception as exc:
            error_msg = f"Ошибка в потоке кликов: {exc}"
        finally:
            with self._lock:
                self._is_running = False

            if error_msg and self._on_error:
                self._on_error(error_msg)

            if self._on_stopped:
                self._on_stopped()
