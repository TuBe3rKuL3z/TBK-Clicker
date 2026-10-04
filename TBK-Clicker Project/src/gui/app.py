"""
Модуль главного окна графического интерфейса автокликера.
Построен на библиотеке CustomTkinter с поддержкой плавающих визуальных меток.
"""

from typing import Optional, Any
import customtkinter as ctk

from src.gui.marker_window import ClickMarker


class AutoClickerApp(ctk.CTk):
    """
    Главный класс графического интерфейса приложения TBK-Clicker.
    Управляет настройками скорости, типом клика, назначением горячих клавиш
    и плавающим визуальным маркером-прицелом на экране.
    """

    def __init__(self) -> None:
        """Инициализация главного окна и построение интерфейса."""
        super().__init__()

        # Глобальная тема оформления
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Геометрия и заголовок
        self.title("TBK-Clicker v2.0 — Автокликер с визуальным триггером")
        self.geometry("460x670")
        self.resizable(False, False)

        # Флаг блокировки рекурсивного пересчета скорости (Интервал <-> CPS)
        self._sync_lock: bool = False

        # Плавающий визуальный маркер на экране
        self._marker: Optional[ClickMarker] = None

        # Текущая назначенная клавиша переключателя (Start/Stop Toggle)
        self._current_hotkey_name: str = "F6"
        self._is_listening_for_key: bool = False

        # Построение графических компонентов
        self._setup_ui()

        # Привязка слушателей ввода
        self._setup_bindings()

        # Корректное закрытие приложения
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_ui(self) -> None:
        """Создание всех визуальных секций интерфейса."""
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=18, pady=14)

        # Построение блоков интерфейса
        self._create_header_section()
        self._create_marker_section()
        self._create_timing_section()
        self._create_keybind_section()
        self._create_click_type_section()
        self._create_controls_section()
        self._create_status_bar()

    def _create_header_section(self) -> None:
        """Шапка: логотип, версия и статус работы кликера."""
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        # Заголовок
        title_label = ctk.CTkLabel(
            header_frame,
            text="TBK-Clicker ⚡",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
        )
        title_label.pack(side="left")

        # Индикатор активности
        self.status_badge = ctk.CTkLabel(
            header_frame,
            text="● Остановлен",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#F85149",
        )
        self.status_badge.pack(side="right")

    def _create_marker_section(self) -> None:
        """Карточка управления плавающим маркером (круглым триггером) на экране."""
        card = ctk.CTkFrame(self.main_container, corner_radius=10)
        card.pack(fill="x", pady=(0, 10))

        card_title = ctk.CTkLabel(
            card,
            text="🎯 Плавающий маркер точки клика",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        card_title.pack(anchor="w", padx=14, pady=(10, 4))

        # Кнопка создания / скрытия круглого маркера
        self.btn_toggle_marker = ctk.CTkButton(
            card,
            text="🎯 Добавить маркер на экран",
            fg_color="#1F6AA5",
            hover_color="#144870",
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.toggle_marker,
        )
        self.btn_toggle_marker.pack(fill="x", padx=14, pady=(4, 6))

        # Отображение текущих координат центра маркера в реальном времени
        self.lbl_marker_coords = ctk.CTkLabel(
            card,
            text="⚪ Маркер не активен (клик в текущей позиции курсора)",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8B949E",
            anchor="w",
        )
        self.lbl_marker_coords.pack(fill="x", padx=14, pady=(2, 4))

        # Подсказка для пользователя
        lbl_hint = ctk.CTkLabel(
            card,
            text="💡 Перетащите появившийся кружок мышью в любую точку экрана.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#6E7681",
            justify="left",
            anchor="w",
        )
        lbl_hint.pack(fill="x", padx=14, pady=(0, 10))

    def _create_timing_section(self) -> None:
        """Карточка настройки скорости кликов: Интервал и CPS."""
        card = ctk.CTkFrame(self.main_container, corner_radius=10)
        card.pack(fill="x", pady=(0, 10))

        card_title = ctk.CTkLabel(
            card,
            text="⚡ Скорость кликов",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        card_title.pack(anchor="w", padx=14, pady=(10, 6))

        grid_frame = ctk.CTkFrame(card, fg_color="transparent")
        grid_frame.pack(fill="x", padx=14, pady=(0, 12))
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        # Интервал (сек)
        lbl_interval = ctk.CTkLabel(
            grid_frame,
            text="Интервал (сек):",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        lbl_interval.grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 3))

        self.entry_interval = ctk.CTkEntry(
            grid_frame,
            placeholder_text="0.1",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.entry_interval.insert(0, "0.1")
        self.entry_interval.grid(row=1, column=0, sticky="ew", padx=(0, 6))

        # Кликов/сек (CPS)
        lbl_cps = ctk.CTkLabel(
            grid_frame,
            text="Кликов/сек (CPS):",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        lbl_cps.grid(row=0, column=1, sticky="w", padx=(6, 0), pady=(0, 3))

        self.entry_cps = ctk.CTkEntry(
            grid_frame,
            placeholder_text="10.0",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.entry_cps.insert(0, "10.0")
        self.entry_cps.grid(row=1, column=1, sticky="ew", padx=(6, 0))

    def _create_keybind_section(self) -> None:
        """Карточка настройки клавиши запуска/остановки (Keybind)."""
        card = ctk.CTkFrame(self.main_container, corner_radius=10)
        card.pack(fill="x", pady=(0, 10))

        card_title = ctk.CTkLabel(
            card,
            text="⌨️ Клавиша активации (Start / Stop Toggle)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        card_title.pack(anchor="w", padx=14, pady=(10, 6))

        # Кнопка назначения новой клавиши
        self.btn_keybind = ctk.CTkButton(
            card,
            text=f"⌨️ Назначить клавишу (Текущая: {self._current_hotkey_name})",
            fg_color="#3A3D40",
            hover_color="#4E5256",
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.on_start_keybind_listening,
        )
        self.btn_keybind.pack(fill="x", padx=14, pady=(2, 4))

        lbl_keybind_hint = ctk.CTkLabel(
            card,
            text="Нажатие клавиши переключает Старт/Стоп. Работает в играх и свернутых окнах.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#6E7681",
            justify="left",
            anchor="w",
        )
        lbl_keybind_hint.pack(fill="x", padx=14, pady=(0, 10))

    def _create_click_type_section(self) -> None:
        """Карточка выбора кнопки мыши (LMB / RMB)."""
        card = ctk.CTkFrame(self.main_container, corner_radius=10)
        card.pack(fill="x", pady=(0, 10))

        label = ctk.CTkLabel(
            card,
            text="🖱 Тип клика:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        label.pack(side="left", padx=(14, 10), pady=10)

        self.combo_click_type = ctk.CTkComboBox(
            card,
            values=["Левая кнопка (LMB)", "Правая кнопка (RMB)"],
            state="readonly",
            width=220,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.combo_click_type.set("Левая кнопка (LMB)")
        self.combo_click_type.pack(side="right", padx=(0, 14), pady=10)

    def _create_controls_section(self) -> None:
        """Секция кнопок запуска и остановки."""
        controls_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(4, 6))
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)

        # Кнопка Старт
        self.btn_start = ctk.CTkButton(
            controls_frame,
            text="▶ Старт",
            height=40,
            fg_color="#2EA043",
            hover_color="#238636",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.on_start_clicker,
        )
        self.btn_start.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        # Кнопка Стоп
        self.btn_stop = ctk.CTkButton(
            controls_frame,
            text="⏹ Стоп",
            height=40,
            fg_color="#DA3633",
            hover_color="#B62324",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.on_stop_clicker,
        )
        self.btn_stop.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # Подсказка о хоткее
        self.lbl_hotkey_info = ctk.CTkLabel(
            self.main_container,
            text=f"Глобальная клавиша: [{self._current_hotkey_name}] — Старт / Стоп",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8B949E",
        )
        self.lbl_hotkey_info.pack(pady=(4, 4))

    def _create_status_bar(self) -> None:
        """Нижняя панель (Status bar)."""
        self.status_bar = ctk.CTkLabel(
            self.main_container,
            text="Готов к работе",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#6E7681",
            anchor="w",
        )
        self.status_bar.pack(fill="x", side="bottom", pady=(4, 0))

    # --------------------------------------------------------------------------
    # Логика плавающего маркера точки клика
    # --------------------------------------------------------------------------

    def toggle_marker(self) -> None:
        """Создает или удаляет плавающий круглый маркер на экране."""
        if self._marker is None:
            # Создаем окно маркера в удобной начальной позиции экрана
            self._marker = ClickMarker(
                master=self,
                initial_x=650,
                initial_y=420,
                on_move_callback=self._on_marker_moved,
            )
            self.btn_toggle_marker.configure(
                text="❌ Удалить маркер точки",
                fg_color="#852221",
                hover_color="#631716",
            )
            cx, cy = self._marker.get_center_coords()
            self._on_marker_moved(cx, cy)
            self.status_bar.configure(
                text="Маркер активен. Зажмите его левой кнопкой мыши и переместите в цель."
            )
        else:
            # Удаляем маркер
            try:
                self._marker.destroy()
            except Exception:
                pass
            self._marker = None
            self.btn_toggle_marker.configure(
                text="🎯 Добавить маркер на экран",
                fg_color="#1F6AA5",
                hover_color="#144870",
            )
            self.lbl_marker_coords.configure(
                text="⚪ Маркер не активен (клик в текущей позиции курсора)",
                text_color="#8B949E",
            )
            self.status_bar.configure(
                text="Маркер удален. Кликер будет работать в текущей позиции курсора."
            )

    def _on_marker_moved(self, center_x: int, center_y: int) -> None:
        """
        Обновляет координаты цели в GUI при перетаскивании маркера пользователем.
        """
        self.lbl_marker_coords.configure(
            text=f"🎯 Координаты цели:  X = {center_x} px,  Y = {center_y} px",
            text_color="#00D2FF",
        )

    def get_target_coordinates(self) -> Optional[tuple[int, int]]:
        """
        Возвращает координаты цели: центр маркера или None (если маркер скрыт).
        """
        if self._marker is not None:
            return self._marker.get_center_coords()
        return None

    # --------------------------------------------------------------------------
    # Двусторонняя синхронизация скорости (Интервал <-> CPS)
    # --------------------------------------------------------------------------

    def _setup_bindings(self) -> None:
        """Привязка событий изменения скорости."""
        self.entry_interval.bind("<KeyRelease>", self._on_interval_changed)
        self.entry_interval.bind("<FocusOut>", self._on_interval_changed)

        self.entry_cps.bind("<KeyRelease>", self._on_cps_changed)
        self.entry_cps.bind("<FocusOut>", self._on_cps_changed)

    def _on_interval_changed(self, event: Optional[Any] = None) -> None:
        """Пересчитывает CPS при вводе интервала: CPS = 1 / Interval."""
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
        """Пересчитывает интервал при вводе CPS: Interval = 1 / CPS."""
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
    # Назначение клавиши (Keybind) — заглушка для Шага 2
    # --------------------------------------------------------------------------

    def on_start_keybind_listening(self) -> None:
        """Переход в режим назначения новой клавиши (реализация в Шаге 2)."""
        self.status_bar.configure(text="Перехват клавиши будет подключен на Шаге 2...")

    # --------------------------------------------------------------------------
    # Управление кликером — заглушки для Шага 2
    # --------------------------------------------------------------------------

    def on_start_clicker(self) -> None:
        """Запуск кликера (реализация в Шаге 2)."""
        self.status_bar.configure(text="Поток кликера будет реализован на Шаге 2...")

    def on_stop_clicker(self) -> None:
        """Остановка кликера (реализация в Шаге 2)."""
        self.status_bar.configure(text="Остановка кликера будет реализована на Шаге 2...")

    def update_status(self, text: str, is_active: bool = False) -> None:
        """Обновляет индикатор работы и текст в статус-баре."""
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
        """Безопасное завершение работы приложения при закрытии окна."""
        if self._marker is not None:
            try:
                self._marker.destroy()
            except Exception:
                pass
            self._marker = None
        self.destroy()
