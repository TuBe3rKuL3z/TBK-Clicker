"""
Модуль главного окна графического интерфейса автокликера.
Построен на библиотеке CustomTkinter в современном темном стиле.
"""

from typing import Optional
import customtkinter as ctk


class AutoClickerApp(ctk.CTk):
    """
    Главный класс графического интерфейса приложения TBK-Clicker.
    Наследуется от ctk.CTk и инкапсулирует в себе все элементы управления,
    разметку секций и первичную обработку пользовательских событий.
    """

    def __init__(self) -> None:
        """Инициализация главного окна и построение интерфейса."""
        super().__init__()

        # Настройка глобальной темы CustomTkinter
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Конфигурация параметров окна
        self.title("TBK-Clicker — Автокликер")
        self.geometry("450x600")
        self.resizable(False, False)

        # Флаг блокировки взаимного обновления полей (для Шага 2)
        self.is_updating_rate: bool = False

        # Построение графических компонентов
        self._setup_ui()

        # Привязка протокола корректного закрытия окна
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_ui(self) -> None:
        """Инициализация и размещение всех секций пользовательского интерфейса."""
        # Главный контейнер со скроллом или отступами
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
    # Методы обновления состояния интерфейса
    # --------------------------------------------------------------------------

    def update_status(self, text: str, is_active: bool = False) -> None:
        """
        Обновляет текстовый статус и индикатор работы.

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

    # --------------------------------------------------------------------------
    # Обработчики событий (заглушки для Шагов 2 и 3)
    # --------------------------------------------------------------------------

    def on_pick_coordinates(self) -> None:
        """Обработчик нажатия на кнопку выбора координат с экрана (Шаг 2)."""
        self.status_bar.configure(text="Режим захвата координат будет реализован на Шаге 2...")

    def on_clear_coordinates(self) -> None:
        """Очистка полей ввода координат X и Y."""
        self.entry_x.delete(0, "end")
        self.entry_y.delete(0, "end")
        self.status_bar.configure(text="Координаты сброшены. Клики будут в позиции курсора.")

    def on_start_clicker(self) -> None:
        """Обработчик нажатия на кнопку старта автокликера (Шаг 3)."""
        self.status_bar.configure(text="Запуск кликера будет реализован на Шаге 3...")

    def on_stop_clicker(self) -> None:
        """Обработчик нажатия на кнопку остановки автокликера (Шаг 3)."""
        self.status_bar.configure(text="Остановка кликера будет реализована на Шаге 3...")

    def on_closing(self) -> None:
        """
        Безопасное завершение работы приложения при закрытии окна.
        Гарантирует остановку фоновых потоков и слушателей.
        """
        self.destroy()
