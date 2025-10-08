# Dokumentace Hotel Management API (v2.0.0)

## 1. Přehled

 **Hotel Management API je robustní backendový systém napsaný v Pythonu s využitím frameworku** **FastAPI**. Poskytuje kompletní sadu endpointů pro správu klíčových operací v hotelu, včetně správy uživatelů a jejich rolí, evidence pokojů a jejich stavů, zadávání a sledování úkolů pro personál a základní skladové hospodářství.

 **Klíčové technologie:**

* **FastAPI:** **Pro rychlý a moderní webový server.**
* **SQLAlchemy (Async):** **Pro asynchronní komunikaci s databází.**
* **Alembic:** **Pro správu databázových migrací.**
* **Pydantic:** **Pro validaci a serializaci dat.**
* **MySQL:** **Relační databáze pro ukládání dat.**
* **Docker & Docker Compose:** **Pro snadné spuštění a nasazení aplikace.**
* **JWT:** **Pro bezpečnou autentizaci uživatelů.**

## 2. Spuštění a instalace

**Existují dva hlavní způsoby, jak aplikaci spustit: lokálně pomocí** **start.bat** **nebo pomocí Dockeru.**

### A) Lokální spuštění (pro vývoj)

**Tato metoda je ideální pro vývoj na Windows. Vyžaduje lokálně nainstalovaný Python a MySQL server.**

**Požadavky:**

* **Python 3.10+**
* **Git**
* **Nainstalovaný a spuštěný MySQL server**

**Kroky:**

* **Naklonujte si repozitář a přejděte do složky** **hotel_api**.
* **Vytvořte soubor** **.env** **zkopírováním souboru** **.env.example**.
* **V souboru** **.env** **upravte proměnnou** **DATABASE_URL** **tak, aby odpovídala přístupovým údajům k vaší lokální MySQL databázi.**

  **code**Code

  ```
  # Příklad pro lokální databázi bez hesla
  DATABASE_URL="mysql+asyncmy://root@localhost:3306/hotel_db"
  ```
* **Spusťte skript** **start.bat**.

  **code**Bash

  ```
  .\start.bat
  ```

  **Skript automaticky vytvoří virtuální prostředí, nainstaluje závislosti, provede databázové migrace a spustí server na** **http://127.0.0.1:8000**.

### B) Spuštění pomocí Dockeru

**Tato metoda je doporučená pro spolehlivé spuštění v jakémkoliv prostředí. Spustí API server i databázi v izolovaných kontejnerech.**

**Požadavky:**

* **Docker**
* **Docker Compose**

**Kroky:**

* **Naklonujte si repozitář a přejděte do složky** **hotel_api**.
* **Vytvořte soubor** **.env** **zkopírováním souboru** **.env.example**. **Není potřeba nic měnit**, výchozí **DATABASE_URL** **je již nastavena pro komunikaci mezi kontejnery.**
* **Spusťte Docker Compose.**

  **code**Bash

  ```
  docker-compose up --build
  ```

  **Tento příkaz postaví a spustí oba kontejnery (API a databázi). API bude dostupné na** **http://localhost:8000**.

## 3. Autentizace

 **API používá** **OAuth2 Password Flow s Bearer tokeny (JWT)**. Každý chráněný endpoint vyžaduje v hlavičce **Authorization** **platný token.**

 **Postup získání tokenu:**

* **Odešlete** **POST** **požadavek na endpoint** **/auth/token**.
* **Tělo požadavku musí být typu** **x-www-form-urlencoded** **a obsahovat** **username** **(což je e-mail uživatele) a** **password**.
* **Pokud jsou přihlašovací údaje správné, API vrátí** **access_token**.

**Použití tokenu:**
Tento token musíte vložit do HTTP hlavičky každého dalšího požadavku na chráněné endpointy:
Authorization: Bearer <váš_access_token>

## 4. API Endpoints

### Autentizace

#### Získání přístupového tokenu

* **Endpoint:** **POST /auth/token**
* **Popis:** **Autentizuje uživatele a vrací JWT token.**
* **Oprávnění:** **Veřejný.**
* **Tělo požadavku (**x-www-form-urlencoded**):**

  * **username** **(string, povinné): E-mail uživatele.**
  * **password** **(string, povinné): Heslo uživatele.**
* **Úspěšná odpověď (200 OK):**

  **code**JSON

  ```
  {
    "access_token": "eyJhbGciOiJIUz...",
    "token_type": "bearer"
  }
  ```
* **Chybová odpověď (401 Unauthorized):** **Pokud jsou údaje nesprávné.**

---

### Uživatelé

#### Vytvoření prvního uživatele (majitele)

* **Endpoint:** **POST /users/**
* **Popis:** **Vytvoří nového uživatele. Pokud v databázi neexistuje žádný uživatel, tento první automaticky získá roli** **majitel**.
* **Oprávnění:** **Veřejný (pouze pro prvního uživatele).**
* **Tělo požadavku:**

  **code**JSON

  ```
  {
    "email": "prvni.majitel@hotel.com",
    "password": "silneheslo123",
    "role": "majitel" 
  }
  ```
* **Úspěšná odpověď (201 Created):**

  **code**JSON

  ```
  {
    "id": 1,
    "email": "prvni.majitel@hotel.com",
    "role": "majitel",
    "is_active": true
  }
  ```
* **Chybová odpověď (400 Bad Request):** **Pokud e-mail již existuje.**

#### Vytvoření dalšího uživatele (administrátorem)

* **Endpoint:** **POST /users/admin_create_user/**
* **Popis:** **Vytvoří nového uživatele (např. zaměstnance).**
* **Oprávnění:** **majitel**, **spravce**.
* **Tělo požadavku:**

  **code**JSON

  ```
  {
    "email": "uklizecka@hotel.com",
    "password": "heslouklizecky",
    "role": "uklizecka" 
  }
  ```
* **Úspěšná odpověď (201 Created):** **Vrací data o nově vytvořeném uživateli.**

#### Získání informací o sobě

* **Endpoint:** **GET /users/me**
* **Popis:** **Vrací data o aktuálně přihlášeném uživateli.**
* **Oprávnění:** **Jakýkoliv přihlášený uživatel.**
* **Úspěšná odpověď (200 OK):**

  **code**JSON

  ```
  {
    "id": 2,
    "email": "uklizecka@hotel.com",
    "role": "uklizecka",
    "is_active": true
  }
  ```

---

### Pokoje

#### Vytvoření nového pokoje

* **Endpoint:** **POST /rooms/**
* **Popis:** **Vytvoří nový pokoj a automaticky pro něj založí lokaci "Minibar Pokoje X".**
* **Oprávnění:** **majitel**, **spravce**.
* **Tělo požadavku:**

  **code**JSON

  ```
  {
    "number": "205",
    "type": "Dvoulůžkový",
    "capacity": 2
  }
  ```
* **Úspěšná odpověď (201 Created):** **Vrací data o novém pokoji.**

#### Získání seznamu pokojů

* **Endpoint:** **GET /rooms/**
* **Popis:** **Vrací seznam všech pokojů. Lze filtrovat podle stavu.**
* **Oprávnění:** **Veřejný (pro přihlášené uživatele).**
* **Query parametry:**

  * **status** **(string, volitelné): Filtruje pokoje podle stavu. Možné hodnoty:** **"Volno - Uklizeno"**, **"Volno - Čeká na úklid"**, **"Obsazeno"**, **"Probíhá úklid"**, **"V údržbě"**.
* **Úspěšná odpověď (200 OK):** **Pole objektů pokojů.**

#### Aktualizace stavu pokoje

* **Endpoint:** **PATCH /rooms/{room_id}/status**
* **Popis:** **Změní stav konkrétního pokoje.**
* **Oprávnění:** **uklizecka**, **recepcni**, **spravce**, **majitel**.
* **Tělo požadavku:**

  **code**JSON

  ```
  {
    "status": "Probíhá úklid"
  }
  ```
* **Úspěšná odpověď (200 OK):** **Vrací aktualizovaná data o pokoji.**

---

### Úkoly

#### Vytvoření nového úkolu

* **Endpoint:** **POST /tasks/**
* **Popis:** **Přiřadí nový úkol konkrétnímu zaměstnanci.**
* **Oprávnění:** **majitel**, **spravce**.
* **Tělo požadavku:**

  **code**JSON

  ```
  {
    "title": "Vyměnit žárovku v pokoji 101",
    "notes": "Nefunguje světlo v koupelně.",
    "assignee_id": 2,
    "due_date": "2025-10-28"
  }
  ```
* **Úspěšná odpověď (201 Created):** **Vrací data o novém úkolu.**

#### Získání mých úkolů

* **Endpoint:** **GET /tasks/my/**
* **Popis:** **Vrací seznam úkolů přiřazených přihlášenému uživateli v zadaném časovém rozmezí.**
* **Oprávnění:** **Jakýkoliv přihlášený uživatel.**
* **Query parametry:**

  * **start_date** **(string, povinné): Počáteční datum ve formátu** **YYYY-MM-DD**.
  * **end_date** **(string, povinné): Koncové datum ve formátu** **YYYY-MM-DD**.
* **Úspěšná odpověď (200 OK):** **Pole objektů úkolů.**

#### Aktualizace stavu úkolu

* **Endpoint:** **PATCH /tasks/{task_id}/status**
* **Popis:** **Umožňuje uživateli změnit stav úkolu, který mu byl přidělen.**
* **Oprávnění:** **Uživatel, kterému je úkol přiřazen, nebo** **majitel**/**spravce**.
* **Tělo požadavku:**

  **code**JSON

  ```
  {
    "status": "dokončeno",
    "notes": "Vše hotovo."
  }
  ```
* **Úspěšná odpověď (200 OK):** **Vrací aktualizovaná data o úkolu.**

---

### Sklad

#### Vytvoření skladové položky

* **Endpoint:** **POST /inventory/items/**
* **Popis:** **Vytvoří novou "master" položku ve skladu (např. typ nápoje).**
* **Oprávnění:** **majitel**, **spravce**.
* **Tělo požadavku:**

  **code**JSON

  ```
  {
    "name": "Mattoni 0.5l",
    "description": "Perlivá minerální voda",
    "price": 45.0
  }
  ```
* **Úspěšná odpověď (201 Created):** **Vrací data o nové položce.**

#### Vytvoření příjemky

* **Endpoint:** **POST /inventory/receipts/**
* **Popis:** **Vytvoří příjemku a automaticky naskladní položky z ní do "Centrálního skladu".**
* **Oprávnění:** **skladnik**, **spravce**, **majitel**.
* **Tělo požadavku:**

  **code**JSON

  ```
  {
    "supplier": "Coca-Cola HBC",
    "items": [
      { "item_id": 1, "quantity": 24 },
      { "item_id": 2, "quantity": 12 }
    ]
  }
  ```
* **Úspěšná odpověď (201 Created):** **Vrací data o vytvořené příjemce.**

#### Přesun zásob mezi lokacemi

* **Endpoint:** **POST /inventory/stock/transfer**
* **Popis:** **Přesune zadané množství položky mezi dvěma lokacemi (např. z centrálního skladu do minibaru).**
* **Oprávnění:** **skladnik**, **spravce**, **majitel**.
* **Tělo požadavku:**

  **code**JSON

  ```
  {
    "item_id": 1,
    "quantity": 10,
    "source_location_id": 1,
    "destination_location_id": 2
  }
  ```
* **Úspěšná odpověď (200 OK):**

  **code**JSON

  ```
  {
    "message": "Přesun zásob byl úspěšně proveden."
  }
  ```

#### Získání stavu zásob v lokaci

* **Endpoint:** **GET /inventory/locations/{location_id}/stock**
* **Popis:** **Zobrazí seznam všech položek a jejich množství v konkrétní lokaci.**
* **Oprávnění:** **Jakýkoliv přihlášený uživatel.**
* **Úspěšná odpověď (200 OK):**

  **code**JSON

  ```
  [
    {
      "item_id": 1,
      "quantity": 10,
      "id": 5,
      "location_id": 2,
      "item": {
        "name": "Coca-Cola 0.33l",
        "description": null,
        "price": 50.0,
        "id": 1
      }
    }
  ]
  ```

#### Získání všech lokací

* **Endpoint:** **GET /inventory/locations/**
* **Popis:** **Vrací seznam všech existujících lokací (skladů, minibarů).**
* **Oprávnění:** **Jakýkoliv přihlášený uživatel.**
* **Úspěšná odpověď (200 OK):** **Pole objektů lokací.**
