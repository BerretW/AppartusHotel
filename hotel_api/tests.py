import requests
import time
from datetime import datetime, timedelta

# --- Konfigurace ---
BASE_URL = "http://127.0.0.1:8000"
timestamp = int(time.time())
ADMIN_EMAIL = f"admin.{timestamp}@hotel.com"
HOUSEKEEPER_EMAIL = f"uklizecka.{timestamp}@hotel.com"
STOREKEEPER_EMAIL = f"skladnik.{timestamp}@hotel.com"
ADMIN_PASSWORD = "admin_password"
USER_PASSWORD = "password123"

# Globální proměnné, které budeme postupně naplňovat
admin_token = None
housekeeper_token = None
storekeeper_token = None
housekeeper_user_id = None
central_storage_id = None

# --- Pomocné funkce ---

def print_step(title):
    """Vytiskne hezky naformátovaný nadpis kroku."""
    print("\n" + "="*60)
    print(f" STEP: {title.upper()}")
    print("="*60)

def print_result(response, expected_status_code=None):
    """Zpracuje odpověď z API, vytiskne výsledek a v případě chyby ukončí test."""
    status_code = response.status_code
    is_success = (expected_status_code is not None and status_code == expected_status_code) or \
                 (expected_status_code is None and 200 <= status_code < 300)
    
    try:
        data = response.json() if response.text and response.status_code != 204 else None
    except requests.exceptions.JSONDecodeError:
        data = response.text

    if is_success:
        print(f"  \033[92mSUCCESS (Status: {status_code})\033[0m")
        return data
    else:
        print(f"  \033[91mFAILURE (Status: {status_code}, Očekáváno: {expected_status_code})\033[0m")
        print(f"  CHYBA: {data}")
        raise AssertionError(f"Test selhal v kroku '{response.request.method} {response.request.url}' se statusem {status_code}")

def get_headers(token_type="admin"):
    """Vrátí autorizační hlavičku pro daný typ uživatele."""
    token_map = {
        "admin": admin_token,
        "housekeeper": housekeeper_token,
        "storekeeper": storekeeper_token
    }
    token = token_map.get(token_type)
    if not token: 
        raise ValueError(f"Token pro '{token_type}' není k dispozici.")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# --- Hlavní testovací scénář ---

def run_hotel_tests():
    global admin_token, housekeeper_token, storekeeper_token, housekeeper_user_id, central_storage_id

    # 1. VYTVOŘENÍ ZÁKLADNÍCH UŽIVATELŮ A PŘIHLÁŠENÍ
    print_step("1. Vytvoření uživatelů a přihlášení")
    admin_payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "role": "majitel"}
    print_result(requests.post(f"{BASE_URL}/users/", json=admin_payload), 201)

    login_payload = {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    admin_token = print_result(requests.post(f"{BASE_URL}/auth/token", data=login_payload), 200)["access_token"]
    print("  -> Admin (majitel) úspěšně vytvořen a přihlášen.")

    housekeeper_payload = {"email": HOUSEKEEPER_EMAIL, "password": USER_PASSWORD, "role": "uklizecka"}
    housekeeper_data = print_result(requests.post(f"{BASE_URL}/users/admin_create_user/", json=housekeeper_payload, headers=get_headers()), 201)
    housekeeper_user_id = housekeeper_data["id"]
    print("  -> Uklízečka úspěšně vytvořena adminem.")

    storekeeper_payload = {"email": STOREKEEPER_EMAIL, "password": USER_PASSWORD, "role": "skladnik"}
    print_result(requests.post(f"{BASE_URL}/users/admin_create_user/", json=storekeeper_payload, headers=get_headers()), 201)
    print("  -> Skladník úspěšně vytvořen adminem.")

    # 2. PŘÍPRAVA PROSTŘEDÍ (POKOJE A SKLAD)
    print_step("2. Příprava pokojů a skladu")
    locations = print_result(requests.get(f"{BASE_URL}/inventory/locations/", headers=get_headers()), 200)
    central_storage = next((loc for loc in locations if loc["name"] == "Centrální sklad"), None)
    assert central_storage is not None, "Centrální sklad nebyl nalezen!"
    central_storage_id = central_storage["id"]
    print(f"  -> Centrální sklad nalezen (ID: {central_storage_id}).")

    room_payload = {"number": "101", "type": "Apartmá", "capacity": 4}
    room_data = print_result(requests.post(f"{BASE_URL}/rooms/", json=room_payload, headers=get_headers()), 201)
    room_101_id = room_data["id"]
    room_101_location_id = room_data["location_id"]
    print(f"  -> Pokoj 101 (ID: {room_101_id}) vytvořen s minibarem (Lokace ID: {room_101_location_id}).")

    item_payload = {"name": "Coca-Cola 0.33l", "price": 50.0}
    item_data = print_result(requests.post(f"{BASE_URL}/inventory/items/", json=item_payload, headers=get_headers()), 201)
    coke_id = item_data["id"]
    print(f"  -> Skladová položka 'Coca-Cola' (ID: {coke_id}) vytvořena.")

    # 3. ZÁKLADNÍ SKLADOVÉ OPERACE
    print_step("3. Skladové operace - Příjemka a Přesun")
    storekeeper_login_payload = {"username": STOREKEEPER_EMAIL, "password": USER_PASSWORD}
    storekeeper_token = print_result(requests.post(f"{BASE_URL}/auth/token", data=storekeeper_login_payload), 200)["access_token"]
    
    print("  -> Vytvoření příjemky na 24ks Coca-Coly do centrálního skladu...")
    receipt_payload = {
        "supplier": f"Dodavatel Limonad {timestamp}",
        "items": [{"item_id": coke_id, "quantity": 24}]
    }
    print_result(requests.post(f"{BASE_URL}/inventory/receipts/", json=receipt_payload, headers=get_headers("storekeeper")), 201)

    print("  -> Přesun 10ks Coca-Coly z centrálního skladu do minibaru pokoje 101...")
    transfer_payload = {
        "item_id": coke_id,
        "quantity": 10,
        "source_location_id": central_storage_id,
        "destination_location_id": room_101_location_id
    }
    print_result(requests.post(f"{BASE_URL}/inventory/stock/transfer", json=transfer_payload, headers=get_headers("storekeeper")), 200)

    print("  -> Kontrola stavu zásob na pokoji 101...")
    stock_response = print_result(requests.get(f"{BASE_URL}/inventory/locations/{room_101_location_id}/stock", headers=get_headers()), 200)
    assert len(stock_response) > 0, "Minibar pokoje 101 by neměl být prázdný"
    assert stock_response[0]["item"]["id"] == coke_id, "V minibaru je špatná položka"
    assert stock_response[0]["quantity"] == 10, "V minibaru je špatné množství"
    print("  -> Stav zásob v minibaru je správný.")
    
    # 4. PRÁCE S ÚKOLY A STAVY POKOJŮ
    print_step("4. Správa úkolů a pokojů")
    due_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    task_payload = {
        "title": "Důkladný úklid pokoje 101",
        "assignee_id": housekeeper_user_id,
        "due_date": due_date
    }
    task_data = print_result(requests.post(f"{BASE_URL}/tasks/", json=task_payload, headers=get_headers()), 201)
    task_id = task_data["id"]
    print(f"  -> Vytvořen úkol (ID: {task_id}) pro uklízečku.")

    print("  -> Uklízečka si načítá své úkoly...")
    housekeeper_login_payload = {"username": HOUSEKEEPER_EMAIL, "password": USER_PASSWORD}
    housekeeper_token = print_result(requests.post(f"{BASE_URL}/auth/token", data=housekeeper_login_payload), 200)["access_token"]
    
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
    my_tasks = print_result(requests.get(f"{BASE_URL}/tasks/my/?start_date={start_date}&end_date={end_date}", headers=get_headers("housekeeper")), 200)
    assert len(my_tasks) > 0, "Uklízečka by měla mít přiřazený úkol"
    assert my_tasks[0]["id"] == task_id, "Uklízečka má přiřazený špatný úkol"
    print("  -> Úkoly úspěšně načteny.")

    print("  -> Uklízečka mění stav pokoje a úkolu...")
    
    # Uklízečka začíná úklid - ZDE JE OPRAVA
    status_payload = {"status": "Probíhá úklid"}
    print_result(requests.patch(f"{BASE_URL}/rooms/{room_101_id}/status", json=status_payload, headers=get_headers("housekeeper")), 200)
    
    # Uklízečka dokončila úklid - ZDE JE OPRAVA
    status_payload = {"status": "Volno - Uklizeno"}
    print_result(requests.patch(f"{BASE_URL}/rooms/{room_101_id}/status", json=status_payload, headers=get_headers("housekeeper")), 200)

    # Uklízečka označí úkol jako dokončený
    task_status_payload = {"status": "dokončeno"}
    print_result(requests.patch(f"{BASE_URL}/tasks/{task_id}/status", json=task_status_payload, headers=get_headers("housekeeper")), 200)
    print("  -> Stav pokoje a úkolu úspěšně změněn.")


    # FINÁLNÍ ZPRÁVA
    print("\n" + "="*60)
    print("\033[92m VŠECHNY TESTY ÚSPĚŠNĚ DOKONČENY! \033[0m")
    print("="*60)


if __name__ == "__main__":
    try:
        time.sleep(2)
        run_hotel_tests()
    except requests.exceptions.ConnectionError:
        print("\n\033[91mFATÁLNÍ CHYBA: Nelze se připojit k API serveru.\033[0m")
        print(f"Ujistěte se, že API běží na adrese {BASE_URL}")
    except AssertionError as e:
        print(f"\n\033[91m--- TEST SELHAL: {e} ---\033[0m")
    except Exception as e:
        print(f"\n\033[91mDošlo k neočekávané chybě: {e}\033[0m")