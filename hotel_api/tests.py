import requests
import time
from datetime import datetime, timedelta

# --- Konfigurace ---
BASE_URL = "http://127.0.0.1:8000"
timestamp = int(time.time())
ADMIN_EMAIL = f"admin.{timestamp}@hotel.com"
HOUSEKEEPER_EMAIL = f"uklizecka.{timestamp}@hotel.com"
STOREKEEPER_EMAIL = f"skladnik.{timestamp}@hotel.com"
ADMIN_PASSWORD = "admin_password_123"
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

    # --- ZDE JE OPRAVA č. 1: Unikátní číslo pokoje ---
    unique_room_number = f"101-{timestamp}"
    room_payload = {"number": unique_room_number, "type": "Apartmá", "capacity": 4, "price_per_night": 2500.0}
    room_data = print_result(requests.post(f"{BASE_URL}/rooms/", json=room_payload, headers=get_headers()), 201)
    room_101_id = room_data["id"]
    room_101_location_id = room_data["location_id"]
    print(f"  -> Pokoj {unique_room_number} (ID: {room_101_id}) vytvořen s minibarem (Lokace ID: {room_101_location_id}).")

    # --- ZDE JE OPRAVA č. 2: Unikátní název položky ---
    unique_item_name = f"Coca-Cola 0.33l-{timestamp}"
    item_payload = {"name": unique_item_name, "price": 50.0}
    item_data = print_result(requests.post(f"{BASE_URL}/inventory/items/", json=item_payload, headers=get_headers()), 201)
    coke_id = item_data["id"]
    print(f"  -> Skladová položka '{unique_item_name}' (ID: {coke_id}) vytvořena.")

    # 3. ZÁKLADNÍ SKLADOVÉ OPERACE
    print_step("3. Skladové operace - Příjemka a Přesun")
    storekeeper_login_payload = {"username": STOREKEEPER_EMAIL, "password": USER_PASSWORD}
    storekeeper_token = print_result(requests.post(f"{BASE_URL}/auth/token", data=storekeeper_login_payload), 200)["access_token"]
    
    receipt_payload = {"supplier": f"Dodavatel Limonad {timestamp}", "items": [{"item_id": coke_id, "quantity": 24}]}
    print_result(requests.post(f"{BASE_URL}/inventory/receipts/", json=receipt_payload, headers=get_headers("storekeeper")), 201)
    print("  -> Vytvořena příjemka na 24ks Coca-Coly.")

    transfer_payload = {"item_id": coke_id, "quantity": 10, "source_location_id": central_storage_id, "destination_location_id": room_101_location_id}
    print_result(requests.post(f"{BASE_URL}/inventory/stock/transfer", json=transfer_payload, headers=get_headers("storekeeper")), 200)
    print("  -> Přesunuto 10ks Coca-Coly do minibaru pokoje 101.")

    # 4. SPRÁVA REZERVACÍ A ÚČTOVÁNÍ
    print_step("4. Správa rezervací a účtování")
    check_in_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    check_out_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
    reservation_payload = {
        "room_id": room_101_id,
        "guest_name": "Jan Novák",
        "guest_email": f"jan.novak.{timestamp}@test.cz",
        "check_in_date": check_in_date,
        "check_out_date": check_out_date
    }
    reservation_data = print_result(requests.post(f"{BASE_URL}/reservations/", json=reservation_payload, headers=get_headers()), 201)
    reservation_id = reservation_data["id"]
    print(f"  -> Vytvořena rezervace (ID: {reservation_id}) pro Jana Nováka.")

    print_result(requests.post(f"{BASE_URL}/reservations/{reservation_id}/checkin", headers=get_headers()), 200)
    print("  -> Host Jan Novák byl ubytován (check-in). Pokoj je nyní 'Obsazeno'.")

    charge_payload = {"item_id": coke_id, "quantity": 1}
    print_result(requests.post(f"{BASE_URL}/rooms/{room_101_id}/charges", json=charge_payload, headers=get_headers()), 201)
    print("  -> Na účet pokoje byla přidána 1x Coca-Cola z minibaru.")
    
    stock_response = print_result(requests.get(f"{BASE_URL}/inventory/locations/{room_101_location_id}/stock", headers=get_headers()), 200)
    assert stock_response[0]["quantity"] == 9, "V minibaru by mělo být již jen 9ks Coly."
    print("  -> Stav zásob v minibaru byl správně snížen na 9ks.")

    bill_data = print_result(requests.get(f"{BASE_URL}/reservations/{reservation_id}/bill", headers=get_headers()), 200)
    expected_total = 2 * 2500.0 + 50.0 # 2 noci + 1 cola
    assert bill_data["total_due"] == expected_total, f"Celková cena na účtu nesouhlasí. Očekáváno: {expected_total}, zjištěno: {bill_data['total_due']}"
    print(f"  -> Účet pro rezervaci byl správně spočítán na {expected_total} Kč.")

    print_result(requests.post(f"{BASE_URL}/reservations/{reservation_id}/checkout", headers=get_headers()), 200)
    print("  -> Host Jan Novák byl odubytován (check-out). Pokoj je nyní 'Volno - Čeká na úklid'.")
    
    # 5. SPRÁVA ÚKOLŮ
    print_step("5. Správa úkolů")
    due_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
    task_payload = {
        "title": "Úklid po odjezdu hosta",
        "assignee_id": housekeeper_user_id,
        "due_date": due_date,
        "room_id": room_101_id
    }
    task_data = print_result(requests.post(f"{BASE_URL}/tasks/", json=task_payload, headers=get_headers()), 201)
    task_id = task_data["id"]
    print(f"  -> Vytvořen úkol úklidu (ID: {task_id}) pro uklízečku a pokoj 101.")

    housekeeper_login_payload = {"username": HOUSEKEEPER_EMAIL, "password": USER_PASSWORD}
    housekeeper_token = print_result(requests.post(f"{BASE_URL}/auth/token", data=housekeeper_login_payload), 200)["access_token"]
    
    print("  -> Uklízečka mění stav pokoje a úkolu (začátek úklidu)...")
    print_result(requests.patch(f"{BASE_URL}/rooms/{room_101_id}/status", json={"status": "Probíhá úklid"}, headers=get_headers("housekeeper")), 200)
    print_result(requests.patch(f"{BASE_URL}/tasks/{task_id}/status", json={"status": "probíhá"}, headers=get_headers("housekeeper")), 200)
    
    # 6. KONTROLA DASHBOARDU
    print_step("6. Kontrola dashboard endpointů")
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
    
    print("  -> Testování dashboardu aktivních úkolů...")
    active_tasks = print_result(requests.get(f"{BASE_URL}/dashboard/active-tasks", headers=get_headers()), 200)
    assert any(task['task_id'] == task_id for task in active_tasks), "Aktivní úkol úklidu nebyl nalezen na dashboardu."
    print("  -> OK: Probíhající úklid se správně zobrazil na dashboardu aktivních úkolů.")

    print("  -> Testování timeline pokojů...")
    timeline_data = print_result(requests.get(f"{BASE_URL}/dashboard/timeline?start_date={start_date}&end_date={end_date}", headers=get_headers()), 200)
    room_101_timeline = next((r for r in timeline_data if r['room_id'] == room_101_id), None)
    assert room_101_timeline is not None, "Timeline pro pokoj 101 nebyla nalezena."
    assert any(e['type'] == 'reservation' and e['reservation_id'] == reservation_id for e in room_101_timeline['events']), "Rezervace chybí v timeline pokoje."
    assert any(e['type'] == 'task' and e['task_id'] == task_id for e in room_101_timeline['events']), "Úkol úklidu chybí v timeline pokoje."
    print("  -> OK: Timeline pokoje 101 obsahuje rezervaci i plánovaný úkol.")
    
    print("  -> Testování plánu zaměstnanců...")
    schedule_data = print_result(requests.get(f"{BASE_URL}/dashboard/employees-schedule?start_date={start_date}&end_date={end_date}", headers=get_headers()), 200)
    housekeeper_schedule = next((s for s in schedule_data if s['employee']['id'] == housekeeper_user_id), None)
    assert housekeeper_schedule is not None, "Plán pro uklízečku nebyl nalezen."
    assert any(t['id'] == task_id for t in housekeeper_schedule['tasks']), "Úkol úklidu chybí v plánu uklízečky."
    print("  -> OK: Plán uklízečky správně obsahuje přidělený úkol.")

    print("  -> Uklízečka dokončuje úklid...")
    print_result(requests.patch(f"{BASE_URL}/rooms/{room_101_id}/status", json={"status": "Volno - Uklizeno"}, headers=get_headers("housekeeper")), 200)
    print_result(requests.patch(f"{BASE_URL}/tasks/{task_id}/status", json={"status": "dokončeno"}, headers=get_headers("housekeeper")), 200)
    print("  -> Stav pokoje a úkolu úspěšně změněn na dokončeno.")

    # FINÁLNÍ ZPRÁVA
    print("\n" + "="*60)
    print("\033[92m VŠECHNY TESTY ÚSPĚŠNĚ DOKONČENY! \033[0m")
    print("="*60)


if __name__ == "__main__":
    try:
        time.sleep(3)
        run_hotel_tests()
    except requests.exceptions.ConnectionError:
        print("\n\033[91mFATÁLNÍ CHYBA: Nelze se připojit k API serveru.\033[0m")
        print(f"Ujistěte se, že API běží na adrese {BASE_URL}")
    except AssertionError as e:
        print(f"\n\033[91m--- TEST SELHAL: {e} ---\033[0m")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n\033[91mDošlo k neočekávané chybě: {e}\033[0m")