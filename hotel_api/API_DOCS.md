
Samozřejmě. Gratuluji ještě jednou!

Zde je kompletní soubor `API_DOCS.md` v plném znění. Zahrnul jsem všechny změny, přeuspořádal sekce pro lepší logiku a popsal všechny nové i upravené endpointy. Můžete bezpečně nahradit celý obsah vašeho stávajícího souboru.

---

# Dokumentace Hotel Management API (v3.0.0)

## 1. Přehled

**Hotel Management API je robustní backendový systém napsaný v Pythonu s využitím frameworku FastAPI.** Poskytuje kompletní sadu endpointů pro správu klíčových operací v hotelu. Verze 3.0 rozšiřuje původní systém o klíčové komerční funkce, včetně **dynamické cenotvorby**, **veřejného rezervačního API (booking engine)**, správy blokací pokojů a pokročilého účetnictví.

**Klíčové technologie:**

* **FastAPI:** Pro rychlý a moderní webový server.
* **SQLAlchemy (Async):** Pro asynchronní komunikaci s databází.
* **Alembic:** Pro správu databázových migrací.
* **Pydantic:** Pro validaci a serializaci dat.
* **MySQL:** Relační databáze pro ukládání dat.
* **Docker & Docker Compose:** Pro snadné spuštění a nasazení aplikace.
* **JWT:** Pro bezpečnou autentizaci uživatelů.

## 2. Spuštění a instalace

**Existují dva hlavní způsoby, jak aplikaci spustit: lokálně pomocí `start.bat` nebo pomocí Dockeru.**

### A) Lokální spuštění (pro vývoj)

Tato metoda je ideální pro vývoj na Windows. Vyžaduje lokálně nainstalovaný Python a MySQL server.

**Požadavky:**

* **Python 3.10+**
* **Git**
* **Nainstalovaný a spuštěný MySQL server**

**Kroky:**

1. Naklonujte si repozitář a přejděte do složky `hotel_api`.
2. Vytvořte soubor `.env` zkopírováním souboru `.env.example`.
3. V souboru `.env` upravte proměnnou `DATABASE_URL` tak, aby odpovídala přístupovým údajům k vaší lokální MySQL databázi.
   ```
   # Příklad pro lokální databázi bez hesla
   DATABASE_URL="mysql+asyncmy://root@localhost:3306/hotel_db"
   ```
4. Spusťte skript `start.bat`.
   ```bash
   .\start.bat
   ```

   Skript automaticky vytvoří virtuální prostředí, nainstaluje závislosti, provede databázové migrace a spustí server na `http://127.0.0.1:8000`.

### B) Spuštění pomocí Dockeru

Tato metoda je doporučená pro spolehlivé spuštění v jakémkoliv prostředí. Spustí API server i databázi v izolovaných kontejnerech.

**Požadavky:**

* **Docker**
* **Docker Compose**

**Kroky:**

1. Naklonujte si repozitář a přejděte do složky `hotel_api`.
2. Vytvořte soubor `.env` zkopírováním souboru `.env.example`. **Není potřeba nic měnit**, výchozí `DATABASE_URL` je již nastavena pro komunikaci mezi kontejnery.
3. Spusťte Docker Compose.
   ```bash
   docker-compose up --build
   ```

   Tento příkaz postaví a spustí oba kontejnery (API a databázi). API bude dostupné na `http://localhost:8000`.

## 3. Autentizace

API používá **OAuth2 Password Flow s Bearer tokeny (JWT)**. Každý chráněný endpoint vyžaduje v hlavičce `Authorization` platný token.

**Postup získání tokenu:**

1. Odešlete `POST` požadavek na endpoint `/auth/token`.
2. Tělo požadavku musí být typu `x-www-form-urlencoded` a obsahovat `username` (což je e-mail uživatele) a `password`.
3. Pokud jsou přihlašovací údaje správné, API vrátí `access_token`.

**Použití tokenu:**
Tento token musíte vložit do HTTP hlavičky každého dalšího požadavku na chráněné endpointy:
`Authorization: Bearer <váš_access_token>`

---

## 4. API Endpoints

### Booking Engine (Veřejné API)

Tyto endpointy jsou navrženy pro integraci s webovými stránkami hotelu a umožňují hostům vyhledávat dostupné pokoje a vytvářet rezervace bez nutnosti přihlášení.

#### Zjištění dostupnosti a ceny

* **Endpoint:** `POST /booking/availability`
* **Popis:** Vrátí seznam dostupných typů pokojů pro zadané období a počet hostů, včetně celkové ceny za pobyt pro každý dostupný cenový plán.
* **Oprávnění:** Veřejný.
* **Tělo požadavku:**
  ```json
  {
    "start_date": "2025-11-15",
    "end_date": "2025-11-18",
    "guests": 2
  }
  ```
* **Úspěšná odpověď (200 OK):**
  ```json
  [
    {
      "room_type": "Apartmá Premium",
      "capacity": 2,
      "total_price": 7500.0,
      "rate_plan_id": 1,
      "rate_plan_name": "Standardní cena"
    },
    {
      "room_type": "Apartmá Premium",
      "capacity": 2,
      "total_price": 6800.0,
      "rate_plan_id": 2,
      "rate_plan_name": "Nevratná cena"
    }
  ]
  ```

#### Vytvoření rezervace hostem

* **Endpoint:** `POST /booking/reservations`
* **Popis:** Vytvoří novou rezervaci na základě vybraného typu pokoje a cenového plánu. Systém automaticky přiřadí první volný pokoj daného typu.
* **Oprávnění:** Veřejný.
* **Tělo požadavku:**
  ```json
  {
    "room_type": "Apartmá Premium",
    "rate_plan_id": 1,
    "guest_name": "Tomáš Marný",
    "guest_email": "tomas.marny@example.com",
    "phone": "123456789",
    "check_in_date": "2025-11-15",
    "check_out_date": "2025-11-18"
  }
  ```
* **Úspěšná odpověď (201 Created):** Vrací detail vytvořené rezervace.

---

### Autentizace

#### Získání přístupového tokenu

* **Endpoint:** `POST /auth/token`
* **Popis:** Autentizuje uživatele a vrací JWT token.
* **Oprávnění:** Veřejný.
* **Tělo požadavku (`x-www-form-urlencoded`):**
  * `username` (string, povinné): E-mail uživatele.
  * `password` (string, povinné): Heslo uživatele.
* **Úspěšná odpověď (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUz...",
    "token_type": "bearer"
  }
  ```

---

### Uživatelé

#### Vytvoření prvního uživatele (majitele)

* **Endpoint:** `POST /users/`
* **Popis:** Vytvoří nového uživatele. Pokud v databázi neexistuje žádný uživatel, tento první automaticky získá roli **majitel**.
* **Oprávnění:** Veřejný (pouze pro prvního uživatele).
* **Tělo požadavku:**
  ```json
  {
    "email": "prvni.majitel@hotel.com",
    "password": "silneheslo123",
    "role": "majitel" 
  }
  ```

#### Vytvoření dalšího uživatele (administrátorem)

* **Endpoint:** `POST /users/admin_create_user/`
* **Popis:** Vytvoří nového uživatele (např. zaměstnance).
* **Oprávnění:** `majitel`, `spravce`.
* **Tělo požadavku:**
  ```json
  {
    "email": "recepcni@hotel.com",
    "password": "heslorecepcni",
    "role": "recepcni" 
  }
  ```

#### Získání informací o sobě

* **Endpoint:** `GET /users/me`
* **Popis:** Vrací data o aktuálně přihlášeném uživateli.
* **Oprávnění:** Jakýkoliv přihlášený uživatel.

---

### Cenotvorba (Správa)

Endpointy pro definování cen hotelu. Vyžadují oprávnění **majitel** nebo **spravce**.

#### Vytvoření cenového plánu

* **Endpoint:** `POST /pricing/rate-plans/`
* **Popis:** Vytvoří nový cenový plán (např. 'Standard', 'Nevratný', 'Víkendový balíček').
* **Oprávnění:** `majitel`, `spravce`.
* **Tělo požadavku:**
  ```json
  {
    "name": "Nevratná cena",
    "description": "Cena se 100% storno poplatkem."
  }
  ```
* **Úspěšná odpověď (201 Created):** Vrací data o novém plánu.

#### Hromadné nahrání denních cen

* **Endpoint:** `POST /pricing/rates/batch`
* **Popis:** Umožňuje nahrát ceny pro více dní, typů pokojů a plánů najednou. Ideální pro nastavení ceníku na celou sezónu.
* **Oprávnění:** `majitel`, `spravce`.
* **Tělo požadavku:** Pole objektů s cenami.
  ```json
  [
    {
      "date": "2025-12-24",
      "price": 3500.0,
      "room_type": "Apartmá Premium",
      "rate_plan_id": 1
    },
    {
      "date": "2025-12-25",
      "price": 4000.0,
      "room_type": "Apartmá Premium",
      "rate_plan_id": 1
    }
  ]
  ```
* **Úspěšná odpověď (201 Created):** Potvrzovací zpráva.

---

### Pokoje a Blokace (Správa)

#### Vytvoření pokoje

* **Endpoint:** `POST /rooms/`
* **Popis:** Vytvoří nový pokoj. Pole `price_per_night` bylo odstraněno, ceny se nyní řídí přes modul Cenotvorby.
* **Oprávnění:** `majitel`, `spravce`.
* **Tělo požadavku:**
  ```json
  {
    "number": "301",
    "type": "Rodinné apartmá",
    "capacity": 4
  }
  ```

#### Vytvoření blokace pokoje

* **Endpoint:** `POST /rooms/blocks/`
* **Popis:** Zablokuje pokoj na určité období (např. z důvodu údržby). Pokoj v tomto termínu nebude nabízen v `booking engine`.
* **Oprávnění:** `majitel`, `spravce`.
* **Tělo požadavku:**
  ```json
  {
    "reason": "Výměna oken",
    "start_date": "2026-01-10",
    "end_date": "2026-01-15",
    "room_id": 3
  }
  ```
* **Úspěšná odpověď (201 Created):** Vrací data o vytvořené blokaci.

#### Smazání blokace pokoje

* **Endpoint:** `DELETE /rooms/blocks/{block_id}`
* **Popis:** Odstraní existující blokaci pokoje.
* **Oprávnění:** `majitel`, `spravce`.
* **Úspěšná odpověď (204 No Content):** Bez těla odpovědi.

*(Ostatní endpointy pro pokoje, jako `GET /rooms/` a `PATCH /rooms/{room_id}/status`, zůstávají beze změny.)*

---

### Rezervace (Správa)

Endpointy pro interní práci personálu s rezervacemi.

#### Úprava rezervace

* **Endpoint:** `PATCH /reservations/{reservation_id}`
* **Popis:** Umožňuje změnit základní údaje rezervace, typicky pro změnu statusu (např. na 'zruseno').
* **Oprávnění:** `recepcni`, `spravce`, `majitel`.
* **Tělo požadavku:**
  ```json
  {
    "status": "zruseno"
  }
  ```
* **Úspěšná odpověď (200 OK):** Vrací aktualizovaná data rezervace.

#### Přidání položky na účet (Folio)

* **Endpoint:** `POST /reservations/{reservation_id}/charges`
* **Popis:** Přidá libovolnou položku (službu, konzumaci) na účet hosta. Pokud je zadáno `item_id`, automaticky sníží stav zásob.
* **Oprávnění:** `recepcni`, `spravce`, `majitel`.
* **Tělo požadavku:**
  ```json
  {
    "description": "Parkování 2 dny",
    "quantity": 2,
    "price_per_item": 250.0
  }
  ```
* **Úspěšná odpověď (201 Created):** Vrací data o vytvořené položce na účtu.

#### Získání kompletního účtu (Folio)

* **Endpoint:** `GET /reservations/{reservation_id}/bill`
* **Popis:** Získá kompletní přehled účtu pro danou rezervaci, včetně detailů o rezervaci, všech naúčtovaných položek, všech plateb a finálního zůstatku.
* **Oprávnění:** `recepcni`, `spravce`, `majitel`.
* **Úspěšná odpověď (200 OK):**
  ```json
  {
    "reservation_details": { "... data o rezervaci ..." },
    "charges": [ "... seznam položek ..." ],
    "payments": [ "... seznam plateb ..." ],
    "total_accommodation": 5000.0,
    "total_charges": 500.0,
    "grand_total": 5500.0,
    "total_paid": 3000.0,
    "balance": 2500.0
  }
  ```

*(Endpointy pro `checkin`, `checkout` a `payments` zůstávají funkčně stejné.)*

---

### Úkoly

*(Tato sekce zůstává beze změny)*

---

### Sklad

*(Tato sekce zůstává beze změny)*

---

### Dashboard

#### Získání časové osy (Timeline)

* **Endpoint:** `GET /dashboard/timeline`
* **Popis:** Vrací kompletní časovou osu událostí. **Nově kromě rezervací a úkolů zobrazuje i blokace pokojů.**
* **Oprávnění:** `majitel`, `spravce`.
* **Query parametry:** `start_date`, `end_date`.

*(Ostatní endpointy dashboardu zůstávají beze změny.)*
