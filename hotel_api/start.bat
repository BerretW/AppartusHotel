@ECHO OFF
CHCP 1250 > NUL
TITLE Hotel API - Lokalni Spoustec

ECHO [INFO] Pripravuji prostredi...

:: Vytvoreni virtualniho prostredi, pokud neexistuje
IF NOT EXIST venv (
    ECHO [INFO] Vytvarim nove virtualni prostredi 'venv'...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        ECHO [CHYBA] Nepodarilo se vytvorit venv.
        PAUSE
        EXIT /B %ERRORLEVEL%
    )
)

:: Aktivace prostredi
CALL venv\Scripts\activate.bat

:: Instalace/aktualizace knihoven
ECHO [INFO] Instaluji pozadavky z requirements.txt...
pip install -r requirements.txt > NUL
IF %ERRORLEVEL% NEQ 0 (
    ECHO [CHYBA] Instalace knihoven selhala.
    PAUSE
    EXIT /B %ERRORLEVEL%
)

:: Vytvoreni .env souboru, pokud neexistuje
IF NOT EXIST .env (
    ECHO [INFO] Soubor .env nenalezen, vytvarim z .env.example...
    copy .env.example .env > NUL
    ECHO [UPOZORNENI] Byl vytvoren novy .env soubor.
    ECHO [UPOZORNENI] Pro lokalni beh ^(mimo Docker^) upravte DATABASE_URL v nem!
)

ECHO [INFO] Spoustim databazove migrace...
alembic upgrade head
IF %ERRORLEVEL% NEQ 0 (
    ECHO [CHYBA] Databazova migrace selhala. Zkontrolujte pripojeni k databazi.
    PAUSE
    EXIT /B %ERRORLEVEL%
)


ECHO.
ECHO ###############################################################
ECHO #                                                             #
ECHO #   SPUSTIM APLIKACI NA http://localhost:8000                   #
ECHO #   Databaze byla uspesne migrovana.                          #
ECHO #                                                             #
ECHO ###############################################################
ECHO.

:: Spusteni Uvicorn serveru
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

PAUSE