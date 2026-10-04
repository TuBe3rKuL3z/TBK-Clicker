"""
Модуль плавающего визуального маркера точки клика.
Реализован на базе прозрачного безрамочного окна tkinter.Toplevel с поддержкой Drag & Drop.
"""

from typing import Callable, Optional, Tuple
import tkinter as tk


class ClickMarker(tk.Toplevel):
    """
    Плавающий круглый маркер на экране.
    Окно поверх всех окон (topmost) без системных рамок, прозрачное за пределами круга,
    с возможностью свободного перетаскивания мышью в любую точку экрана.
    """

    def __init__(
        self,
        master: tk.Misc,
        initial_x: int = 600,
        initial_y: int = 400,
        size: int = 56,
        on_move_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """
        Инициализация окна маркера.

        :param master: Родительский виджет Tkinter.
        :param initial_x: Начальная экранная координата X левого верхнего угла.
        :param initial_y: Начальная экранная координата Y левого верхнего угла.
        :param size: Диаметр маркера в пикселях.
        :param on_move_callback: Функция обратного вызова при перемещении (x_center, y_center).
        """
        super().__init__(master)

        self.size = size
        self.radius = size // 2
        self.on_move_callback = on_move_callback

        # Скрываем стандартные рамки и заголовок окна Windows
        self.overrideredirect(True)

        # Окно всегда находится поверх всех приложений и полноэкранных окон
        self.wm_attributes("-topmost", True)

        # Ключ прозрачности для ОС Windows: все пиксели заданного цвета становятся 100% прозрачными
        self._trans_color = "#000001"
        self.config(bg=self._trans_color)
        try:
            self.wm_attributes("-transparentcolor", self._trans_color)
        except Exception:
            # Запасной вариант для окружений без поддержки transparentcolor
            self.wm_attributes("-alpha", 0.9)

        # Установка размера и начальной позиции
        self.geometry(f"{self.size}x{self.size}+{initial_x}+{initial_y}")

        # Холст для рисования круглого прицела
        self.canvas = tk.Canvas(
            self,
            width=self.size,
            height=self.size,
            bg=self._trans_color,
            highlightthickness=0,
            cursor="fleur",  # Четырехнаправленный курсор перемещения
        )
        self.canvas.pack(fill="both", expand=True)

        # Отрисовка видоискателя / кружка
        self._draw_marker()

        # Смещения мыши для плавного Drag & Drop
        self._drag_offset_x: int = 0
        self._drag_offset_y: int = 0

        # Привязка событий перетаскивания мышью
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)

        # Уведомляем вызывающую сторону о начальных координатах центра
        if self.on_move_callback is not None:
            self.on_move_callback(initial_x + self.radius, initial_y + self.radius)

    def _draw_marker(self) -> None:
        """Отрисовывает неоновый высококонтрастный круглый маркер с прицелом."""
        pad = 3
        cx = self.radius
        cy = self.radius

        # Основной кружок (темная подложка с неоновой бирюзовой обводкой)
        self.canvas.create_oval(
            pad,
            pad,
            self.size - pad,
            self.size - pad,
            fill="#1E1E2E",
            outline="#00E5FF",
            width=2.5,
        )

        # Внутреннее перекрестие прицела
        self.canvas.create_line(
            cx, pad + 5, cx, self.size - pad - 5,
            fill="#00E5FF", width=1.5
        )
        self.canvas.create_line(
            pad + 5, cy, self.size - pad - 5, cy,
            fill="#00E5FF", width=1.5
        )

        # Центральная контрастная красная точка клика
        point_r = 3
        self.canvas.create_oval(
            cx - point_r,
            cy - point_r,
            cx + point_r,
            cy + point_r,
            fill="#FF2A6D",
            outline="#FFFFFF",
            width=1,
        )

    def _on_drag_start(self, event: tk.Event) -> None:
        """
        Фиксация смещения точки клика относительно окна при начале перетаскивания.
        Используются event.x_root и event.y_root для абсолютно плавного Drag & Drop.
        """
        self._drag_offset_x = event.x_root - self.winfo_x()
        self._drag_offset_y = event.y_root - self.winfo_y()

    def _on_drag_motion(self, event: tk.Event) -> None:
        """
        Перемещение окна маркера вслед за курсором в реальном времени.
        """
        new_x = event.x_root - self._drag_offset_x
        new_y = event.y_root - self._drag_offset_y
        self.geometry(f"{self.size}x{self.size}+{new_x}+{new_y}")

        # Передаем координаты центра в главное окно
        if self.on_move_callback is not None:
            center_x = new_x + self.radius
            center_y = new_y + self.radius
            self.on_move_callback(center_x, center_y)

    def _on_drag_end(self, event: tk.Event) -> None:
        """Завершение перетаскивания маркера."""
        if self.on_move_callback is not None:
            center_x = self.winfo_x() + self.radius
            center_y = self.winfo_y() + self.radius
            self.on_move_callback(center_x, center_y)

    def get_center_coords(self) -> Tuple[int, int]:
        """
        Возвращает точные координаты центра маркера в экранных пикселях.

        :return: Кортеж (X, Y).
        """
        return self.winfo_x() + self.radius, self.winfo_y() + self.radius
