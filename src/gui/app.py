"""
Модуль главного окна графического интерфейса автокликера.
Построен на библиотеке CustomTkinter в современном темном стиле.
"""

from typing import Optional, Any, Tuple
import customtkinter as ctk

from src.core.coordinate_picker import CoordinatePicker
from src.core.clicker_engine import ClickerEngine
from src.core.hotkey_manager import HotkeyManager


class AutoClickerApp(ctk.CTk):
    """
    Главный класс графического интерфейса приложения TBK-Clicker.
    Наследуется от ctk.CTk и инкапсулирует в себе все элементы управления,
    разметку секций, синхронизацию скорости, захват координат с экрана,
    фоновый цикл кликов и глобальные горячие клавиши.
    """

    def __init__(self) -> None:
        """Инициализация главного окна, сервисов и построение интерфейса."""
        super().__init__()

        # Настройка глобальной темы CustomTkinter
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Конфигурация параметров окна
        self.title("TBK-Clicker — Автокликер")
        self.geometry("450x600")
        self.resizable(False, False)

        # Флаг блокировки взаимного обновления полей скорости (защита от рекурсии)
        self._sync_lock: bool = False

        # Сервисы ядра приложения
        self._coord_picker: CoordinatePicker = CoordinatePicker()
        self._clicker_engine: ClickerEngine = ClickerEngine()
        self._hotkey_manager: HotkeyManager = HotkeyManager()

        # Построение графических компонентов
        self._setup_ui()

        # Настройка слушателей событий и валидации
        self._setup_bindings()

        # Активация глобальных горячих клавиш (F5 - старт, F6 - стоп)
        self._start_global_hotkeys()

        # Привязка протокола корректного закрытия окна
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_ui(self) -> None:
        """Инициализация и размещение всех секций пользовательского интерфейса."""
        # Главный контейнер
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=16)

        # Построение секций интерфейса
        self._create_header_section()
        self._create_click_type_section()
        self._create_timing_section()
        self._create_coords_section()
        self._create_controls_section()
        self._create_status_bar()

    def _create_header_section(self) -> None:
        """Секция заголовка: название приложения и текущий статус работы."""
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 12))

        # Название программы
        title_label = ctk.CTkLabel(
            header_frame,
            text="TBK-Clicker",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
        )
        title_label.pack(side="left")

        # Индикатор статуса приложения
        self.status_badge = ctk.CTkLabel(
            header_frame,
            text="● Остановлен",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#F85149",  # Красный оттенок в спокойном состоянии
        )
        self.status_badge.pack(side="right")

    def _create_click_type_section(self) -> None:
        """Секция выбора типа клика (Левая кнопка / Правая кнопка мыши)."""
        card = ctk.CTkFrame(self.main_container, corner_radius=8)
        card.pack(fill="x", pady=(0, 10), padx=0)

        label = ctk.CTkLabel(
            card,
            text="Тип клика:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        label.pack(side="left", padx=(14, 10), pady=10)

        # Выпадающий список кнопок мыши
        self.combo_click_type = ctk.CTkComboBox(
            card,
            values=["Левая кнопка (LMB)", "Правая кнопка (RMB)"],
            state="readonly",
            width=230,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.combo_click_type.set("Левая кнопка (LMB)")
        self.combo_click_type.pack(side="right", padx=(0, 14), pady=10)

    def _create_timing_section(self) -> None:
        """Секция настройки скорости: интервал в секундах и CPS (кликов/сек)."""
        card = ctk.CTkFrame(self.main_container, corner_radius=8)
        card.pack(fill="x", pady=(0, 10))

        # Заголовок карточки
        card_title = ctk.CTkLabel(
            card,
            text="Скорость кликов",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        card_title.pack(anchor="w", padx=14, pady=(10, 8))

        # Сетка для полей ввода (Интервал и CPS)
        grid_frame = ctk.CTkFrame(card, fg_color="transparent")
        grid_frame.pack(fill="x", padx=14, pady=(0, 12))
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        # Колонка 1: Интервал (сек)
        lbl_interval = ctk.CTkLabel(
            grid_frame,
            text="Интервал (сек):",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        lbl_interval.grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 4))

        self.entry_interval = ctk.CTkEntry(
            grid_frame,
            placeholder_text="0.1",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.entry_interval.insert(0, "0.1")
        self.entry_interval.grid(row=1, column=0, sticky="ew", padx=(0, 6))

        # Колонка 2: Кликов/сек (CPS)
        lbl_cps = ctk.CTkLabel(
            grid_frame,
            text="Кликов/сек (CPS):",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        lbl_cps.grid(row=0, column=1, sticky="w", padx=(6, 0), pady=(0, 4))

        self.entry_cps = ctk.CTkEntry(
            grid_frame,
            placeholder_text="10.0",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.entry_cps.insert(0, "10.0")
        self.entry_cps.grid(row=1, column=1, sticky="ew", padx=(6, 0))

    def _create_coords_section(self) -> None:
        """Секция выбора координат клика: ввод X/Y и кнопка захвата с экрана."""
        card = ctk.CTkFrame(self.main_container, corner_radius=8)
        card.pack(fill="x", pady=(0, 10))

        # Заголовок карточки
        card_title = ctk.CTkLabel(
            card,
            text="Координаты клика",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        card_title.pack(anchor="w", padx=14, pady=(10, 8))

        # Поля ввода X и Y
        coords_frame = ctk.CTkFrame(card, fg_color="transparent")
        coords_frame.pack(fill="x", padx=14, pady=(0, 8))
        coords_frame.columnconfigure(0, weight=1)
        coords_frame.columnconfigure(1, weight=1)

        # Координата X
        lbl_x = ctk.CTkLabel(
            coords_frame,
            text="Позиция X (px):",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        lbl_x.grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 4))

        self.entry_x = ctk.CTkEntry(
            coords_frame,
            placeholder_text="Текущая позиция",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.entry_x.grid(row=1, column=0, sticky="ew", padx=(0, 6))

        # Координата Y
        lbl_y = ctk.CTkLabel(
            coords_frame,
            text="Позиция Y (px):",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        lbl_y.grid(row=0, column=1, sticky="w", padx=(6, 0), pady=(0, 4))

        self.entry_y = ctk.CTkEntry(
            coords_frame,
            placeholder_text="Текущая позиция",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.entry_y.grid(row=1, column=1, sticky="ew", padx=(6, 0))

        # Кнопки захвата и сброса координат
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=14, pady=(4, 6))
        btn_frame.columnconfigure(0, weight=3)
        btn_frame.columnconfigure(1, weight=1)

        self.btn_pick_coords = ctk.CTkButton(
            btn_frame,
            text="🎯 Выбрать точку на экране",
            fg_color="#1F6AA5",
            hover_color="#144870",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.on_pick_coordinates,
        )
        self.btn_pick_coords.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.btn_clear_coords = ctk.CTkButton(
            btn_frame,
            text="Очистить",
            fg_color="#3A3D40",
            hover_color="#4E5256",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.on_clear_coordinates,
        )
        self.btn_clear_coords.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # Подсказка для пользователя
        lbl_hint = ctk.CTkLabel(
            card,
            text="💡 Если поля X и Y пусты — клик выполняется в текущей позиции курсора",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#8B949E",
            wraplength=380,
            justify="left",
        )
        lbl_hint.pack(anchor="w", padx=14, pady=(2, 10))

    def _create_controls_section(self) -> None:
        """Секция запуска, остановки и информации о глобальных горячих клавишах."""
        controls_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(4, 6))
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)

        # Кнопка «Старт»
        self.btn_start = ctk.CTkButton(
            controls_frame,
            text="▶ Старт (F5)",
            height=40,
            fg_color="#2EA043",
            hover_color="#238636",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.on_start_clicker,
        )
        self.btn_start.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        # Кнопка «Стоп»
        self.btn_stop = ctk.CTkButton(
            controls_frame,
            text="⏹ Стоп (F6)",
            height=40,
            fg_color="#DA3633",
            hover_color="#B62324",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.on_stop_clicker,
        )
        self.btn_stop.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # Информационная плашка горячих клавиш
        hotkey_info = ctk.CTkLabel(
            self.main_container,
            text="Глобальные клавиши: [F5] — Старт  |  [F6] — Стоп",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8B949E",
        )
        hotkey_info.pack(pady=(6, 4))

    def _create_status_bar(self) -> None:
        """Нижняя панель (Status bar) с детальным описанием текущего состояния."""
        self.status_bar = ctk.CTkLabel(
            self.main_container,
            text="Готов к работе",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#6E7681",
            anchor="w",
        )
        self.status_bar.pack(fill="x", side="bottom", pady=(6, 0))

    # --------------------------------------------------------------------------
    # Привязка событий и синхронизация полей
    # --------------------------------------------------------------------------

    def _setup_bindings(self) -> None:
        """Настройка биндингов для интерактивного пересчета скорости."""
        self.entry_interval.bind("<KeyRelease>", self._on_interval_changed)
        self.entry_interval.bind("<FocusOut>", self._on_interval_changed)

        self.entry_cps.bind("<KeyRelease>", self._on_cps_changed)
        self.entry_cps.bind("<FocusOut>", self._on_cps_changed)

    def _on_interval_changed(self, event: Optional[Any] = None) -> None:
        """
        Слушатель изменения поля 'Интервал'.
        Пересчитывает и обновляет поле CPS: CPS = 1 / Interval.
        """
        if self._sync_lock:
            return

        raw_val = self.entry_interval.get().strip().replace(",", ".")
        if not raw_val:
            return

        try:
            interval = float(raw_val)
            if interval <= 0:
                return

            cps = 1.0 / interval
            formatted_cps = f"{round(cps, 3):g}"

            self._sync_lock = True
            try:
                self.entry_cps.delete(0, "end")
                self.entry_cps.insert(0, formatted_cps)
            finally:
                self._sync_lock = False

        except (ValueError, ZeroDivisionError):
            pass

    def _on_cps_changed(self, event: Optional[Any] = None) -> None:
        """
        Слушатель изменения поля 'CPS'.
        Пересчитывает и обновляет поле Интервал: Interval = 1 / CPS.
        """
        if self._sync_lock:
            return

        raw_val = self.entry_cps.get().strip().replace(",", ".")
        if not raw_val:
            return

        try:
            cps = float(raw_val)
            if cps <= 0:
                return

            interval = 1.0 / cps
            formatted_interval = f"{round(interval, 4):g}"

            self._sync_lock = True
            try:
                self.entry_interval.delete(0, "end")
                self.entry_interval.insert(0, formatted_interval)
            finally:
                self._sync_lock = False

        except (ValueError, ZeroDivisionError):
            pass

    # --------------------------------------------------------------------------
    # Логика захвата координат с экрана (pynput.mouse)
    # --------------------------------------------------------------------------

    def on_pick_coordinates(self) -> None:
        """Запуск фонового слушателя для фиксации клика в любой точке монитора."""
        if self._coord_picker.is_active:
            self._coord_picker.stop()
            self._reset_pick_button()
            self.status_bar.configure(text="Выбор координат отменен")
            return

        self.btn_pick_coords.configure(
            text="⏳ Кликните в любой точке экрана...",
            fg_color="#D97706",
            hover_color="#B45309",
        )
        self.status_bar.configure(
            text="Переместите курсор в нужную точку и сделайте клик мышью для сохранения..."
        )

        self.after(200, self._arm_coordinate_picker)

    def _arm_coordinate_picker(self) -> None:
        """Активирует слушатель мыши после завершения текущего клика по GUI."""
        self._coord_picker.start(callback=self._on_coordinates_captured)

    def _on_coordinates_captured(self, x: int, y: int) -> None:
        """Коллбек pynput: потокобезопасно направляет координаты в GUI."""
        self.after(0, lambda: self._apply_picked_coordinates(x, y))

    def _apply_picked_coordinates(self, x: int, y: int) -> None:
        """Применяет полученные координаты в поля X и Y в главном потоке."""
        self.entry_x.delete(0, "end")
        self.entry_x.insert(0, str(x))

        self.entry_y.delete(0, "end")
        self.entry_y.insert(0, str(y))

        self._reset_pick_button()
        self.status_bar.configure(text=f"Координаты зафиксированы: X={x}, Y={y}")

    def _reset_pick_button(self) -> None:
        """Возвращает кнопку выбора координат в исходное состояние."""
        self.btn_pick_coords.configure(
            text="🎯 Выбрать точку на экране",
            fg_color="#1F6AA5",
            hover_color="#144870",
        )

    def on_clear_coordinates(self) -> None:
        """Очистка полей ввода координат X и Y."""
        if self._coord_picker.is_active:
            self._coord_picker.stop()
            self._reset_pick_button()

        self.entry_x.delete(0, "end")
        self.entry_y.delete(0, "end")
        self.status_bar.configure(text="Координаты очищены. Клики будут выполняться в позиции курсора.")

    # --------------------------------------------------------------------------
    # Глобальные горячие клавиши (pynput.keyboard)
    # --------------------------------------------------------------------------

    def _start_global_hotkeys(self) -> None:
        """Инициализация и запуск слушателя глобальных горячих клавиш F5/F6."""
        self._hotkey_manager.start(
            on_start=lambda: self.after(0, self.on_start_clicker),
            on_stop=lambda: self.after(0, self.on_stop_clicker),
        )

    # --------------------------------------------------------------------------
    # Управление автокликером (Старт / Стоп)
    # --------------------------------------------------------------------------

    def on_start_clicker(self) -> None:
        """Запуск циклического автокликера с валидацией пользовательских параметров."""
        if self._clicker_engine.is_running:
            return

        # Валидация интервала
        raw_interval = self.entry_interval.get().strip().replace(",", ".")
        try:
            interval_val = float(raw_interval)
            if interval_val <= 0:
                raise ValueError("Интервал должен быть больше нуля")
        except ValueError:
            self.status_bar.configure(text="⚠️ Ошибка: введите корректный положительный интервал")
            return

        # Определение типа клика (LMB или RMB)
        combo_val = self.combo_click_type.get()
        button_type = "right" if ("RMB" in combo_val or "Правая" in combo_val) else "left"

        # Определение координат клика
        raw_x = self.entry_x.get().strip()
        raw_y = self.entry_y.get().strip()
        coords: Optional[Tuple[int, int]] = None

        if raw_x or raw_y:
            try:
                x_val = int(raw_x)
                y_val = int(raw_y)
                coords = (x_val, y_val)
            except ValueError:
                self.status_bar.configure(
                    text="⚠️ Ошибка: поля X и Y должны содержать целые числа, либо быть пустыми"
                )
                return

        # Если был активен захват координат, выключаем его
        if self._coord_picker.is_active:
            self._coord_picker.stop()
            self._reset_pick_button()

        # Запуск фонового движка кликов
        started = self._clicker_engine.start(
            interval=interval_val,
            button=button_type,
            coords=coords,
            on_error=self._on_clicker_error,
            on_stopped=self._on_clicker_stopped,
        )

        if started:
            btn_title = "ПКМ" if button_type == "right" else "ЛКМ"
            target_str = f"точке ({coords[0]}, {coords[1]})" if coords else "позиции курсора"
            status_msg = f"Кликер запущен: {btn_title}, каждые {interval_val}с в {target_str}"
            self.update_status(status_msg, is_active=True)

    def on_stop_clicker(self) -> None:
        """Остановка циклического автокликера."""
        if not self._clicker_engine.is_running:
            return

        self._clicker_engine.stop()
        self.update_status("Кликер остановлен", is_active=False)

    def _on_clicker_error(self, message: str) -> None:
        """Потокобезопасная обработка системных ошибок кликера."""
        self.after(0, lambda: self._handle_clicker_error(message))

    def _handle_clicker_error(self, message: str) -> None:
        """Отображение ошибки в главном потоке GUI."""
        self.update_status(f"⚠️ {message}", is_active=False)

    def _on_clicker_stopped(self) -> None:
        """Потокобезопасное обновление статуса при завершении цикла."""
        self.after(0, lambda: self.update_status("Кликер остановлен", is_active=False))

    def update_status(self, text: str, is_active: bool = False) -> None:
        """
        Обновляет текстовый статус и индикатор работы в GUI.

        :param text: Текст состояния для статус-бара.
        :param is_active: True, если кликер работает, иначе False.
        """
        if is_active:
            self.status_badge.configure(text="● Работает...", text_color="#3FB950")
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
        else:
            self.status_badge.configure(text="● Остановлен", text_color="#F85149")
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="normal")

        self.status_bar.configure(text=text)

    def on_closing(self) -> None:
        """
        Безопасное завершение работы приложения при закрытии окна.
        Гарантирует остановку всех фоновых потоков и слушателей.
        """
        self._hotkey_manager.stop()
        self._coord_picker.stop()
        self._clicker_engine.stop()
        self.destroy()
