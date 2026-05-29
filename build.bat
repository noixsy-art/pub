@echo off
call .venv\Scripts\python build_secure.py
echo.
echo [업로드] GitHub에 최신 코드 업로드 중...
call .venv\Scripts\python upload.py
pause
