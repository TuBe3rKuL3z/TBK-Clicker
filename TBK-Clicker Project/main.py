"""
Точка входа в приложение TBK-Clicker.
Инициализирует и запускает графический интерфейс CustomTkinter.
"""

import sys
import os
from src.gui.app import AutoClickerApp


def main() -> None:
    """Главная функция запуска приложения с мгновенным завершением процессов."""
    try:
        app = AutoClickerApp()
        app.mainloop()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"Критическая ошибка при работе приложения: {exc}", file=sys.stderr)
    finally:
        # Гарантированное мгновенное закрытие всех фоновых хуков и потоков ОС
        os._exit(0)


if __name__ == "__main__":
    main()
