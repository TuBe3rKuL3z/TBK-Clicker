"""
Точка входа в приложение TBK-Clicker.
Инициализирует и запускает графический интерфейс CustomTkinter.
"""

import sys
from src.gui.app import AutoClickerApp


def main() -> None:
    """Главная функция запуска приложения."""
    try:
        app = AutoClickerApp()
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as exc:
        print(f"Критическая ошибка при работе приложения: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
