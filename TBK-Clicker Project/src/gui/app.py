"""
Модуль главного окна графического интерфейса автокликера.
Построен на библиотеке CustomTkinter с поддержкой двух режимов:
1) Кликер мыши (со сквозным плавающим маркером, LMB/RMB, Single/Double click).
2) Кликер клавиатуры (циклический спамер любой выбранной клавиши, например ENTER, SPACE и др.).
"""

from typing import Optional, Any, Tuple
import customtkinter as ctk
from pynput import keyboard

from src.gui.marker_window import ClickMarker
from src.core.clicker_engine import ClickerEngine
from src.core.keybind_manager import KeybindManager


class AutoClickerApp(ctk.CTk):
    """
    Главный класс графического интерфейса приложения TBK-Clicker.
    Управляет режимами работы (Мышь / Клавиатура), скоростью, маркером
    и динамическим биндом хоткеев и целевых клавиш.
    """

    def __init__(self) -> None:
        """Инициализация главного окна, сервисов и построение интерфейса."""
        super().__init__()

        # Глобальная тема оформления
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Геометрия и заголовок
        self.title("TBK-Clicker v2.2 — Автокликер мыши и клавиатуры")
        self.geometry("460x730")
        self.resizable(False, False)

        # Текущий рабочий режим: "mouse" или "keyboard"
        self._current_mode: str = "mouse"

        # Флаг блокировки рекурсивного пересчета скорости (Интервал <-> CPS)
        self._sync_lock: bool = False

        # Плавающий визуальный маркер на экране
        self._marker: Optional[ClickMarker] = None

        # Ядро логики: движок кликов и менеджер хоткеев
        self._clicker_engine: ClickerEngine = ClickerEngine()
        self._keybind_manager: KeybindManager = KeybindManager()

        # Текущая назначенная клавиша переключателя (Start/Stop Toggle)
        self._current_hotkey_name: str = self._keybind_manager.get_current_key_name()

        # Целевая клавиша для клавиатурного спама (режим "keyboard")
        self._target_key_name: str = "ENTER"
        self._target_key_vk: int = 13  # VK_RETURN

        # Построение графических компонентов
        self._setup_ui()

        # Привязка слушателей ввода скорости
        self._setup_bindings()

        # Активация глобального отслеживания хоткея
        self._start_hotkey_listener()

        # Корректное закрытие приложения
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_ui(self) -> None:
        """Создание всех визуальных секций интерфейса."""
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=18, pady=14)

        # 1. Шапка приложения
        self._create_header_section()

        # 2. Переключатель режима: Мышь / Клавиатура
        self._create_mode_selector_section()

        # 3. Секция скорости (общая для всех режимов)
        self._create_timing_section()

        # 4. Секции для Режима Мыши
        self._create_marker_section()
        self._create_mouse_settings_section()

        # 5. Секция для Режима Клавиатуры (по умолчанию скрыта)
        self._create_keyboard_settings_section()

        # 6. Секция хоткея активации (Start/Stop Toggle)
        self._create_keybind_section()

        # 7. Кнопки управления (Старт / Стоп)
        self._create_controls_section()

        # 8. Нижний статус-бар
        self._create_status_bar()

    def _create_header_section(self) -> None:
        """Шапка: логотип, версия и статус работы кликера."""
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 8))

        title_label = ctk.CTkLabel(
            header_frame,
            text="TBK-Clicker ⚡",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
        )
        title_label.pack(side="left")

        self.status_badge = ctk.CTkLabel(
            header_frame,
            text="● Остановлен",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#F85149",
        )
        self.status_badge.pack(side="right")

    def _create_mode_selector_section(self) -> None:
        """Переключатель режима работы: Кликер Мыши или Кликер Клавиатуры."""
        self.mode_selector = ctk.CTkSegmentedButton(
            self.main_container,
            values=["🖱 Режим Мыши", "⌨️ Режим Клавиатуры"],
            command=self.on_mode_changed,
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        self.mode_selector.set("🖱 Режим Мыши")
        self.mode_selector.pack(fill="x", pady=(0, 8))

    def _create_timing_section(self) -> None:
        """Карточка настройки скорости: Интервал и CPS."""
        card = ctk.CTkFrame(self.main_container, corner_radius=10)
        card.pack(fill="x", pady=(0, 8))

        card_title = ctk.CTkLabel(
            card,
            text="⚡ Скорость (Интервал / CPS)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        card_title.pack(anchor="w", padx=14, pady=(8, 4))

        grid_frame = ctk.CTkFrame(card, fg_color="transparent")
        grid_frame.pack(fill="x", padx=14, pady=(0, 10))
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        # Интервал (сек)
        lbl_interval = ctk.CTkLabel(
            grid_frame,
            text="Интервал (сек):",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        lbl_interval.grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 2))

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
            text="Действий/сек (CPS):",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        lbl_cps.grid(row=0, column=1, sticky="w", padx=(6, 0), pady=(0, 2))

        self.entry_cps = ctk.CTkEntry(
            grid_frame,
            placeholder_text="10.0",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.entry_cps.insert(0, "10.0")
        self.entry_cps.grid(row=1, column=1, sticky="ew", padx=(6, 0))

    def _create_marker_section(self) -> None:
        """Карточка управления плавающим маркером точки клика."""
        self.card_marker = ctk.CTkFrame(self.main_container, corner_radius=10)
        self.card_marker.pack(fill="x", pady=(0, 8))

        card_title = ctk.CTkLabel(
            self.card_marker,
            text="🎯 Плавающий маркер точки клика",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        card_title.pack(anchor="w", padx=14, pady=(8, 2))

        btn_box = ctk.CTkFrame(self.card_marker, fg_color="transparent")
        btn_box.pack(fill="x", padx=14, pady=(2, 4))
        btn_box.columnconfigure(0, weight=2)
        btn_box.columnconfigure(1, weight=1)

        self.btn_toggle_marker = ctk.CTkButton(
            btn_box,
            text="🎯 Добавить маркер на экран",
            fg_color="#1F6AA5",
            hover_color="#144870",
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.toggle_marker,
        )
        self.btn_toggle_marker.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_lock_marker = ctk.CTkButton(
            btn_box,
            text="🔓 Перетаскивание",
            fg_color="#3A3D40",
            hover_color="#4E5256",
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self.toggle_marker_lock,
            state="disabled",
        )
        self.btn_lock_marker.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.lbl_marker_coords = ctk.CTkLabel(
            self.card_marker,
            text="⚪ Маркер не активен (клик в текущей позиции курсора)",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8B949E",
            anchor="w",
        )
        self.lbl_marker_coords.pack(fill="x", padx=14, pady=(2, 6))

    def _create_mouse_settings_section(self) -> None:
        """Карточка параметров мыши (LMB/RMB, Single/Double click)."""
        self.card_mouse = ctk.CTkFrame(self.main_container, corner_radius=10)
        self.card_mouse.pack(fill="x", pady=(0, 8))

        grid = ctk.CTkFrame(self.card_mouse, fg_color="transparent")
        grid.pack(fill="x", padx=14, pady=8)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        lbl_btn = ctk.CTkLabel(grid, text="Кнопка мыши:", font=ctk.CTkFont(family="Segoe UI", size=12))
        lbl_btn.grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 2))

        self.combo_click_type = ctk.CTkComboBox(
            grid,
            values=["Левая кнопка (LMB)", "Правая кнопка (RMB)"],
            state="readonly",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.combo_click_type.set("Левая кнопка (LMB)")
        self.combo_click_type.grid(row=1, column=0, sticky="ew", padx=(0, 6))

        lbl_mode = ctk.CTkLabel(grid, text="Тип нажатия:", font=ctk.CTkFont(family="Segoe UI", size=12))
        lbl_mode.grid(row=0, column=1, sticky="w", padx=(6, 0), pady=(0, 2))

        self.combo_click_mode = ctk.CTkComboBox(
            grid,
            values=["Одиночный (Single)", "Двойной (Double)"],
            state="readonly",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.combo_click_mode.set("Одиночный (Single)")
        self.combo_click_mode.grid(row=1, column=1, sticky="ew", padx=(6, 0))

    def _create_keyboard_settings_section(self) -> None:
        """Карточка выбора целевой клавиши спама (режим 'keyboard')."""
        self.card_keyboard = ctk.CTkFrame(self.main_container, corner_radius=10)
        # По умолчанию скрыта, отображается при переключении режима
        card_title = ctk.CTkLabel(
            self.card_keyboard,
            text="⌨️ Целевая клавиша для спама",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        card_title.pack(anchor="w", padx=14, pady=(8, 4))

        self.btn_target_key = ctk.CTkButton(
            self.card_keyboard,
            text=f"🎯 Назначить целевую клавишу (Текущая: {self._target_key_name})",
            fg_color="#1F6AA5",
            hover_color="#144870",
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.on_start_target_key_capture,
        )
        self.btn_target_key.pack(fill="x", padx=14, pady=(2, 4))

        lbl_hint = ctk.CTkLabel(
            self.card_keyboard,
            text="💡 Кликер циклически нажимает эту клавишу. Экранный маркер отключен.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#6E7681",
            justify="left",
            anchor="w",
        )
        lbl_hint.pack(fill="x", padx=14, pady=(0, 8))

    def _create_keybind_section(self) -> None:
        """Карточка настройки глобальной клавиши запуска/остановки (Toggle)."""
        card = ctk.CTkFrame(self.main_container, corner_radius=10)
        card.pack(fill="x", pady=(0, 8))

        card_title = ctk.CTkLabel(
            card,
            text="⚙️ Глобальный хоткей активации (Start / Stop)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        card_title.pack(anchor="w", padx=14, pady=(8, 4))

        self.btn_keybind = ctk.CTkButton(
            card,
            text=f"⌨️ Изменить хоткей активации (Текущий: {self._current_hotkey_name})",
            fg_color="#3A3D40",
            hover_color="#4E5256",
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.on_start_keybind_listening,
        )
        self.btn_keybind.pack(fill="x", padx=14, pady=(2, 6))

    def _create_controls_section(self) -> None:
        """Секция кнопок запуска и остановки."""
        controls_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(2, 4))
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)

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

        self.lbl_hotkey_info = ctk.CTkLabel(
            self.main_container,
            text=f"Хоткей: [{self._current_hotkey_name}] — Старт / Стоп (Toggle)",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8B949E",
        )
        self.lbl_hotkey_info.pack(pady=(2, 2))

    def _create_status_bar(self) -> None:
        """Нижняя панель (Status bar)."""
        self.status_bar = ctk.CTkLabel(
            self.main_container,
            text="Готов к работе",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#6E7681",
            anchor="w",
        )
        self.status_bar.pack(fill="x", side="bottom", pady=(2, 0))

    # --------------------------------------------------------------------------
    # Переключение режима работы (Мышь ⇄ Клавиатура)
    # --------------------------------------------------------------------------

    def on_mode_changed(self, mode_text: str) -> None:
        """Переключение между кликером мыши и спамером клавиатуры."""
        # Если кликер работал, останавливаем его
        if self._clicker_engine.is_running:
            self.on_stop_clicker()

        if "Клавиатур" in mode_text:
            self._current_mode = "keyboard"
            # Скрываем маркер, если он был включен
            if self._marker is not None:
                self.toggle_marker()

            # Скрываем карточки мыши и отображаем карточку клавиатуры
            self.card_marker.pack_forget()
            self.card_mouse.pack_forget()
            self.card_keyboard.pack(fill="x", pady=(0, 8), before=self.main_container.winfo_children()[-3])
            self.status_bar.configure(text=f"Выбран режим спама клавиши [{self._target_key_name}]. Маркер отключен.")
        else:
            self._current_mode = "mouse"
            # Скрываем карточку клавиатуры и возвращаем карточки мыши
            self.card_keyboard.pack_forget()
            self.card_marker.pack(fill="x", pady=(0, 8), before=self.main_container.winfo_children()[-3])
            self.card_mouse.pack(fill="x", pady=(0, 8), before=self.main_container.winfo_children()[-3])
            self.status_bar.configure(text="Выбран режим кликера мыши.")

    # --------------------------------------------------------------------------
    # Захват целевой клавиши для спама (режим "keyboard")
    # --------------------------------------------------------------------------

    def on_start_target_key_capture(self) -> None:
        """Запуск захвата клавиши для циклического спама."""
        if self._keybind_manager.is_capturing:
            self._keybind_manager.cancel_capture()
            self._reset_target_key_button()
            self.status_bar.configure(text="Выбор целевой клавиши отменен.")
            return

        self.btn_target_key.configure(
            text="⏳ Нажмите любую клавишу для спама...",
            fg_color="#D97706",
            hover_color="#B45309",
        )
        self.status_bar.configure(
            text="Ожидание нажатия: нажмите клавишу, которую хотите циклически нажимать (Enter, Space, E, 1 и др.)..."
        )
        self._keybind_manager.start_capture(callback=self._on_target_key_captured)

    def _on_target_key_captured(self, key_obj: Any, key_name: str, vk_code: int) -> None:
        """Потокобезопасный коллбек после перехвата целевой клавиши."""
        self.after(0, lambda: self._apply_target_key_captured(key_name, vk_code))

    def _apply_target_key_captured(self, key_name: str, vk_code: int) -> None:
        """Сохранение и отображение целевой клавиши спама в GUI."""
        self._target_key_name = key_name
        self._target_key_vk = vk_code or 13
        self._reset_target_key_button()
        self.status_bar.configure(text=f"Целевая клавиша [{key_name}] успешно установлена для спама!")

    def _reset_target_key_button(self) -> None:
        """Сброс кнопки целевой клавиши в стандартный вид."""
        self.btn_target_key.configure(
            text=f"🎯 Назначить целевую клавишу (Текущая: {self._target_key_name})",
            fg_color="#1F6AA5",
            hover_color="#144870",
        )

    # --------------------------------------------------------------------------
    # Логика плавающего маркера точки клика
    # --------------------------------------------------------------------------

    def toggle_marker(self) -> None:
        """Создает или удаляет плавающий круглый маркер на экране."""
        if self._marker is None:
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
            self.btn_lock_marker.configure(
                state="normal",
                text="🔓 Перетаскивание",
                fg_color="#3A3D40",
            )
            cx, cy = self._marker.get_center_coords()
            self._on_marker_moved(cx, cy)
            self.status_bar.configure(
                text="Маркер активен. Перетащите его в цель. При старте он станет сквозным."
            )
        else:
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
            self.btn_lock_marker.configure(
                state="disabled",
                text="🔓 Перетаскивание",
                fg_color="#3A3D40",
            )
            self.lbl_marker_coords.configure(
                text="⚪ Маркер не активен (клик в текущей позиции курсора)",
                text_color="#8B949E",
            )
            self.status_bar.configure(
                text="Маркер удален. Кликер будет работать в текущей позиции курсора."
            )

    def toggle_marker_lock(self) -> None:
        """Ручное переключение между режимом перетаскивания и сквозным режимом."""
        if self._marker is None:
            return

        new_state = not self._marker.is_click_through
        self._marker.set_click_through(new_state)

        if new_state:
            self.btn_lock_marker.configure(
                text="🔒 Сквозной (клик)",
                fg_color="#2E7D32",
                hover_color="#1B5E20",
            )
            self.status_bar.configure(text="Маркер зафиксирован и пропускает все клики мыши сквозь себя.")
        else:
            self.btn_lock_marker.configure(
                text="🔓 Перетаскивание",
                fg_color="#3A3D40",
                hover_color="#4E5256",
            )
            self.status_bar.configure(text="Маркер разблокирован. Зажмите его левой кнопкой для перемещения.")

    def _on_marker_moved(self, center_x: int, center_y: int) -> None:
        """Обновляет координаты цели в GUI при перетаскивании маркера пользователем."""
        self.lbl_marker_coords.configure(
            text=f"🎯 Координаты цели:  X = {center_x} px,  Y = {center_y} px",
            text_color="#00D2FF",
        )

    def get_target_coordinates(self) -> Optional[Tuple[int, int]]:
        """Возвращает актуальный центр маркера или None."""
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
    # Глобальные горячие клавиши активации (Start / Stop Toggle)
    # --------------------------------------------------------------------------

    def _start_hotkey_listener(self) -> None:
        """Запуск фонового глобального слушателя переключателя."""
        self._keybind_manager.start(on_toggle=lambda: self.after(0, self.toggle_clicker))

    def on_start_keybind_listening(self) -> None:
        """Переводит приложение в режим ожидания нажатия клавиши хоткея."""
        if self._keybind_manager.is_capturing:
            self._keybind_manager.cancel_capture()
            self._reset_keybind_button()
            self.status_bar.configure(text="Назначение хоткея отменено.")
            return

        self.btn_keybind.configure(
            text="⏳ Нажмите любую клавишу для хоткея...",
            fg_color="#D97706",
            hover_color="#B45309",
        )
        self.status_bar.configure(
            text="Ожидание нажатия: нажмите любую клавишу для установки в качестве Start/Stop хоткея..."
        )
        self._keybind_manager.start_capture(callback=self._on_hotkey_captured)

    def _on_hotkey_captured(self, key_obj: Any, key_name: str, vk_code: int) -> None:
        """Потокобезопасный коллбек после перехвата клавиши хоткея."""
        self.after(0, lambda: self._apply_hotkey_captured(key_obj, key_name))

    def _apply_hotkey_captured(self, key_obj: Any, key_name: str) -> None:
        """Применяет назначенный хоткей активации."""
        self._keybind_manager.set_hotkey(key_obj)
        self._current_hotkey_name = key_name
        self._reset_keybind_button()
        self.lbl_hotkey_info.configure(
            text=f"Хоткей: [{key_name}] — Старт / Стоп (Toggle)"
        )
        self.status_bar.configure(text=f"Хоткей активации [{key_name}] успешно назначен!")

    def _reset_keybind_button(self) -> None:
        """Возвращает кнопку бинда хоткея в стандартный вид."""
        self.btn_keybind.configure(
            text=f"⌨️ Изменить хоткей активации (Текущий: {self._current_hotkey_name})",
            fg_color="#3A3D40",
            hover_color="#4E5256",
        )

    # --------------------------------------------------------------------------
    # Управление кликером (Старт / Стоп / Toggle)
    # --------------------------------------------------------------------------

    def toggle_clicker(self) -> None:
        """Переключатель (Toggle): если работает — останавливает, иначе запускает."""
        if self._clicker_engine.is_running:
            self.on_stop_clicker()
        else:
            self.on_start_clicker()

    def on_start_clicker(self) -> None:
        """Запуск кликера (в режиме мыши или клавиатуры) с валидацией параметров."""
        if self._clicker_engine.is_running:
            return

        # Валидация интервала
        raw_interval = self.entry_interval.get().strip().replace(",", ".")
        try:
            interval_val = float(raw_interval)
            if interval_val <= 0:
                raise ValueError("Интервал должен быть больше нуля")
        except ValueError:
            self.status_bar.configure(text="⚠️ Ошибка: укажите корректный интервал (> 0)")
            return

        if self._current_mode == "keyboard":
            # --- ЗАПУСК РЕЖИМА КЛАВИАТУРЫ ---
            started = self._clicker_engine.start(
                interval=interval_val,
                mode="keyboard",
                target_vk=self._target_key_vk,
                on_error=self._on_clicker_error,
                on_stopped=self._on_clicker_stopped,
            )
            if started:
                msg = f"Спам клавиши запущен: [{self._target_key_name}], каждые {interval_val}с"
                self.update_status(msg, is_active=True)

        else:
            # --- ЗАПУСК РЕЖИМА МЫШИ ---
            combo_val = self.combo_click_type.get()
            button_type = "right" if ("RMB" in combo_val or "Правая" in combo_val) else "left"

            mode_val = self.combo_click_mode.get()
            click_type = "double" if "Double" in mode_val or "Двойной" in mode_val else "single"

            # Включаем сквозной режим маркера, чтобы клики проходили насквозь
            if self._marker is not None:
                self._marker.set_click_through(True)
                self.btn_lock_marker.configure(
                    text="🔒 Сквозной (клик)",
                    fg_color="#2E7D32",
                    hover_color="#1B5E20",
                )

            started = self._clicker_engine.start(
                interval=interval_val,
                mode="mouse",
                button=button_type,
                click_type=click_type,
                coords_provider=self.get_target_coordinates,
                on_error=self._on_clicker_error,
                on_stopped=self._on_clicker_stopped,
            )

            if started:
                coords = self.get_target_coordinates()
                target_str = f"центр маркера ({coords[0]}, {coords[1]})" if coords else "позиция курсора"
                btn_title = "ПКМ" if button_type == "right" else "ЛКМ"
                mode_title = "2x Double" if click_type == "double" else "1x Single"
                msg = f"Кликер мыши запущен: {btn_title} [{mode_title}], интервал {interval_val}с ({target_str})"
                self.update_status(msg, is_active=True)

    def on_stop_clicker(self) -> None:
        """Остановка циклического кликера."""
        if not self._clicker_engine.is_running:
            return

        self._clicker_engine.stop()

        # Возвращаем маркер в режим перетаскивания
        if self._marker is not None:
            self._marker.set_click_through(False)
            self.btn_lock_marker.configure(
                text="🔓 Перетаскивание",
                fg_color="#3A3D40",
                hover_color="#4E5256",
            )

        self.update_status("Кликер остановлен", is_active=False)

    def _on_clicker_error(self, message: str) -> None:
        """Потокобезопасный вызов при системной ошибке кликера."""
        self.after(0, lambda: self._handle_clicker_error(message))

    def _handle_clicker_error(self, message: str) -> None:
        """Обработка ошибки кликера в GUI."""
        if self._marker is not None:
            self._marker.set_click_through(False)
        self.update_status(f"⚠️ {message}", is_active=False)

    def _on_clicker_stopped(self) -> None:
        """Потокобезопасный вызов при завершении потока кликов."""
        self.after(0, lambda: self._handle_clicker_stopped())

    def _handle_clicker_stopped(self) -> None:
        """Обновление состояния GUI при остановке потока кликера."""
        if self._marker is not None:
            self._marker.set_click_through(False)
            self.btn_lock_marker.configure(
                text="🔓 Перетаскивание",
                fg_color="#3A3D40",
                hover_color="#4E5256",
            )
        self.update_status("Кликер остановлен", is_active=False)

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
        self._keybind_manager.stop()
        self._clicker_engine.stop()
        if self._marker is not None:
            try:
                self._marker.destroy()
            except Exception:
                pass
            self._marker = None
        self.destroy()
