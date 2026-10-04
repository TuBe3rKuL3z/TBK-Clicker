@echo off
chcp 65001 > nul
echo ========================================================
echo        Сборка TBK-Clicker в исполняемый файл .exe
echo ========================================================
echo.

echo [1/3] Проверка и установка зависимостей...
python -m pip install -r requirements.txt

echo.
echo [2/3] Запуск сборки через PyInstaller...
python -m PyInstaller --noconsole --onefile --clean --collect-all customtkinter --name "TBK-Clicker" main.py

echo.
echo [3/3] Сборка завершена!
echo Исполняемый файл находится в папке: dist\TBK-Clicker.exe
echo.
pause
