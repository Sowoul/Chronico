@echo off
setlocal enabledelayedexpansion
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Downloading and installing...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe' -OutFile 'python-installer.exe'}"
    start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python-installer.exe
) else (
    echo Python is already installed.
)
set PATH=%PATH%;C:\Python311;C:\Python311\Scripts
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo Ollama is not installed. Downloading and installing...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile 'OllamaSetup.exe'}"
    start /wait OllamaSetup.exe /silent
    del OllamaSetup.exe
) else (
    echo Ollama is already installed.
)
ollama serve >nul 2>&1
echo Downloading deepseek-r1:1.5b...
ollama pull deepseek-r1:1.5b
if exist requirements.txt (
    echo Installing Python dependencies...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found! Skipping...
)

echo Setup complete!
pause
