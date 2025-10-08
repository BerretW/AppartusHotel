@ECHO OFF
TITLE Hotel API - Jednoduchy Spoustec

ECHO [INFO] Pripravuji prostredi...

:: Vytvoření virtuálního prostředí, pokud neexistuje
IF NOT EXIST venv (
    ECHO [INFO] Vytvarim nove virtualni prostredi 'venv'...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        ECHO [CHYBA] Nepodarilo se vytvorit venv.
        PAUSE
        EXIT /B %ERRORLEVEL%
    )
)

:: Aktivace prostředí
CALL venv\Scripts\activate.bat

:: Instalace/aktualizace knihoven
ECHO [INFO] Instaluji pozadavky z requirements.txt...
pip install -r requirements.txt > NUL
IF %ERRORLEVEL% NEQ 0 (
    ECHO [CHYBA] Instalace knihoven selhala.
    PAUSE
    EXIT /B %ERRORLEVEL%
)

ECHO [INFO] Nastavuji konfiguracni promenne...
:: Nastavení systémových proměnných pro tuto session
SET "DATABASE_URL=mysql+asyncmy://root:1234@localhost:3306/hotel_db"
SET "SECRET_KEY=b2a3e6f8c1d4a0b9e8d7f6a5c4b3d2e1a0b9c8d7f6e5a4b3c2d1e0f9a8b7c6d5"
SET "ALGORITHM=HS256"
SET "ACCESS_TOKEN_EXPIRE_MINUTES=30"

ECHO.
ECHO ###############################################################
ECHO #                                                           #
ECHO #   SPUSTIM APLIKACI NA http://localhost:8000                 #
ECHO #   Tabulky v databazi se vytvori automaticky.              #
ECHO #                                                           #
ECHO ###############################################################
ECHO.

:: Spuštění Uvicorn serveru
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

PAUSE