# FILE: hotel_api/tests.py
import requests
import time
from datetime import datetime, timedelta

# --- Konfigurace ---
BASE_URL = "http://127.0.0.1:8000"
timestamp = int(time.time())

# --- Unikátní data pro každý test run ---
ADMIN_EMAIL = f"admin.{timestamp}@hotel.com"
RECEPTIONIST_EMAIL = f"recepcni.{timestamp}@hotel.com"
HOUSEKEEPER_EMAIL = f"uklizecka.{timestamp}@hotel.com"
GUEST_EMAIL = f"karel.novy.{timestamp}@test.com"
ADMIN_PASSWORD = "admin_password_123"
USER_PASSWORD = "password123"
ROOM_TYPE_PREMIUM = "Apartmá Premium"

# --- Globální proměnné, které budeme postupně naplňovat ---
admin_token = None
receptionist_token = None
housekeeper_token = None
housekeeper_user_id = None

# --- Pomocné funkce ---

def print_step(title):
    """Vytiskne hezky naformátovaný nadpis kroku."""
    print("\n" + "="*70)
    print(f" STEP: {title.upper()}")
    print("="*70)

def print_result(response, expected_status_code=None):
    """Zpracuje odpověď z API, vytiskne výsledek a v případě chyby ukončí test."""
    status_code = response.status_code
    is_success = (expected_status_code is not None and status_code == expected_status_code) or \
                 (expected_status_code is None and 200 <= status_code < 300)
    
    try:
        data = response.json() if response.text and response.status_code not in [204] else None
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
        "receptionist": receptionist_token,
        "housekeeper": housekeeper_token
    }
    token = token_map.get(token_type)
    if not token:
        if token_type is None: # Pro veřejné endpointy
            return {"Content-Type": "application/json"}
        raise ValueError(f"Token pro '{token_type}' není k dispozici.")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# --- Hlavní testovací scénář ---

def run_hotel_tests():
    global admin_token, receptionist_token, housekeeper_token, housekeeper_user_id

    # 1. NASTAVENÍ UŽIVATELŮ A PŘIHLÁŠENÍ
    print_step("1. Vytvoření uživatelů a přihlášení")
    # Vytvoření majitele
    admin_payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "role": "majitel"}
    print_result(requests.post(f"{BASE_URL}/users/", json=admin_payload), 201)
    admin_token = print_result(requests.post(f"{BASE_URL}/auth/token", data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}), 200)["access_token"]
    print("  -> Admin (majitel) úspěšně vytvořen a přihlášen.")

    # Vytvoření recepční
    receptionist_payload = {"email": RECEPTIONIST_EMAIL, "password": USER_PASSWORD, "role": "recepcni"}
    print_result(requests.post(f"{BASE_URL}/users/admin_create_user/", json=receptionist_payload, headers=get_headers("admin")), 201)
    receptionist_token = print_result(requests.post(f"{BASE_URL}/auth/token", data={"username": RECEPTIONIST_EMAIL, "password": USER_PASSWORD}), 200)["access_token"]
    print("  -> Recepční úspěšně vytvořena a přihlášena.")
    
    # Vytvoření uklízečky
    housekeeper_payload = {"email": HOUSEKEEPER_EMAIL, "password": USER_PASSWORD, "role": "uklizecka"}
    housekeeper_data = print_result(requests.post(f"{BASE_URL}/users/admin_create_user/", json=housekeeper_payload, headers=get_headers("admin")), 201)
    housekeeper_user_id = housekeeper_data["id"]
    housekeeper_token = print_result(requests.post(f"{BASE_URL}/auth/token", data={"username": HOUSEKEEPER_EMAIL, "password": USER_PASSWORD}), 200)["access_token"]
    print("  -> Uklízečka úspěšně vytvořena a přihlášena.")

    # 2. NASTAVENÍ HOTELU - POKOJE A CENOTVORBA
    print_step("2. Nastavení hotelu - pokoje a cenotvorba")
    room_101_data = print_result(requests.post(f"{BASE_URL}/rooms/", json={"number": f"101-{timestamp}", "type": ROOM_TYPE_PREMIUM, "capacity": 2}, headers=get_headers("admin")), 201)
    room_101_id = room_101_data["id"]
    room_102_data = print_result(requests.post(f"{BASE_URL}/rooms/", json={"number": f"102-{timestamp}", "type": ROOM_TYPE_PREMIUM, "capacity": 2}, headers=get_headers("admin")), 201)
    room_102_id = room_102_data["id"]
    print(f"  -> Vytvořeny pokoje 101 a 102 typu '{ROOM_TYPE_PREMIUM}'.")

    # Zajištění unikátního názvu cenového plánu pomocí timestamp
    unique_plan_name = f"Standardní cena {timestamp}"
    plan_data = print_result(requests.post(f"{BASE_URL}/pricing/rate-plans/", json={"name": unique_plan_name, "description": "Základní cena s možností storna."}, headers=get_headers("admin")), 201)
    rate_plan_id = plan_data["id"]
    print(f"  -> Vytvořen cenový plán '{unique_plan_name}' (ID: {rate_plan_id}).")
    
    rates_payload = []
    for i in range(10):
        day = datetime.now().date() + timedelta(days=i)
        rates_payload.append({
            "date": day.isoformat(),
            "price": 2500.0,
            "room_type": ROOM_TYPE_PREMIUM,
            "rate_plan_id": rate_plan_id
        })
    print_result(requests.post(f"{BASE_URL}/pricing/rates/batch", json=rates_payload, headers=get_headers("admin")), 201)
    print(f"  -> Nhrány denní ceny pro typ '{ROOM_TYPE_PREMIUM}' na dalších 10 dní.")
    
    # 3. VEŘEJNÝ BOOKING ENGINE - HOST SI REZERVUJE POBYT
    print_step("3. Veřejný booking engine - host si rezervuje pobyt")
    check_in_date = (datetime.now() + timedelta(days=2)).date()
    check_out_date = (datetime.now() + timedelta(days=4)).date()
    
    availability_payload = {"start_date": check_in_date.isoformat(), "end_date": check_out_date.isoformat(), "guests": 2}
    available_rooms = print_result(requests.post(f"{BASE_URL}/booking/availability", json=availability_payload, headers=get_headers(None)), 200)
    assert any(r["room_type"] == ROOM_TYPE_PREMIUM for r in available_rooms), "Dostupnost pro Apartmá Premium nebyla nalezena!"
    assert available_rooms[0]["total_price"] == 5000.0, "Celková cena za 2 noci nesouhlasí!"
    print(f"  -> Dostupnost pro '{ROOM_TYPE_PREMIUM}' úspěšně ověřena, cena 5000.0 Kč.")

    reservation_payload = {
        "room_type": ROOM_TYPE_PREMIUM,
        "rate_plan_id": rate_plan_id,
        "guest_name": "Karel Nový",
        "guest_email": GUEST_EMAIL,
        "check_in_date": check_in_date.isoformat(),
        "check_out_date": check_out_date.isoformat()
    }
    reservation_data = print_result(requests.post(f"{BASE_URL}/booking/reservations", json=reservation_payload, headers=get_headers(None)), 201)
    reservation_id = reservation_data["id"]
    reserved_room_id = reservation_data["room"]["id"]
    print(f"  -> Host Karel Nový úspěšně vytvořil rezervaci (ID: {reservation_id}) na pokoj ID: {reserved_room_id}.")

    # 4. INTERNÍ SPRÁVA - RECEPČNÍ PRACUJE S REZERVACÍ
    print_step("4. Interní správa - recepční pracuje s rezervací")
    print_result(requests.post(f"{BASE_URL}/reservations/{reservation_id}/checkin", headers=get_headers("receptionist")), 200)
    print("  -> Recepční provedla check-in hosta.")

    charge_payload = {"description": "Parkování", "quantity": 2, "price_per_item": 250.0}
    print_result(requests.post(f"{BASE_URL}/reservations/{reservation_id}/charges", json=charge_payload, headers=get_headers("receptionist")), 201)
    print("  -> Na účet rezervace naúčtováno parkování za 500.0 Kč.")
    
    payment_payload = {"amount": 3000.0, "method": "Karta"}
    print_result(requests.post(f"{BASE_URL}/reservations/{reservation_id}/payments", json=payment_payload, headers=get_headers("receptionist")), 201)
    print("  -> K rezervaci zaznamenána platba 3000.0 Kč.")

    bill_data = print_result(requests.get(f"{BASE_URL}/reservations/{reservation_id}/bill", headers=get_headers("receptionist")), 200)
    assert bill_data["grand_total"] == 5500.0, "Celková částka na účtu nesouhlasí."
    assert bill_data["total_paid"] == 3000.0, "Zaplacená částka nesouhlasí."
    assert bill_data["balance"] == 2500.0, "Zůstatek k úhradě nesouhlasí."
    print("  -> Finální účet (folio) byl správně spočítán. Zbývá doplatit 2500.0 Kč.")
    
    print_result(requests.post(f"{BASE_URL}/reservations/{reservation_id}/checkout", headers=get_headers("receptionist")), 200)
    checked_out_room = print_result(requests.get(f"{BASE_URL}/rooms/", headers=get_headers("admin")), 200)
    room_status = next(r["status"] for r in checked_out_room if r["id"] == reserved_room_id)
    assert room_status == "Volno - Čeká na úklid"
    print("  -> Recepční provedla check-out. Pokoj je nyní ve stavu 'Volno - Čeká na úklid'.")
    
    # 5. HOUSEKEEPING - ÚKLID POKOJE
    print_step("5. Housekeeping - úklid pokoje")
    task_payload = {
        "title": f"Úklid pokoje {room_101_data['number']}",
        "assignee_id": housekeeper_user_id,
        "due_date": datetime.now().date().isoformat(),
        "room_id": reserved_room_id
    }
    task_data = print_result(requests.post(f"{BASE_URL}/tasks/", json=task_payload, headers=get_headers("admin")), 201)
    task_id = task_data["id"]
    print(f"  -> Admin vytvořil úkol úklidu (ID: {task_id}) pro uklízečku.")

    print_result(requests.patch(f"{BASE_URL}/tasks/{task_id}/status", json={"status": "probíhá"}, headers=get_headers("housekeeper")), 200)
    print("  -> Uklízečka zahájila úklid.")
    
    print_result(requests.patch(f"{BASE_URL}/rooms/{reserved_room_id}/status", json={"status": "Volno - Uklizeno"}, headers=get_headers("housekeeper")), 200)
    print_result(requests.patch(f"{BASE_URL}/tasks/{task_id}/status", json={"status": "dokončeno"}, headers=get_headers("housekeeper")), 200)
    print("  -> Uklízečka dokončila úklid. Pokoj je opět čistý a připravený.")

    # 6. BLOKACE A KONTROLA DASHBOARDU
    print_step("6. Blokace a kontrola dashboardu")
    block_start_date = (datetime.now() + timedelta(days=5)).date()
    block_end_date = (datetime.now() + timedelta(days=7)).date()
    block_payload = {
        "reason": "Malování",
        "start_date": block_start_date.isoformat(),
        "end_date": block_end_date.isoformat(),
        "room_id": room_102_id
    }
    block_data = print_result(requests.post(f"{BASE_URL}/rooms/blocks/", json=block_payload, headers=get_headers("admin")), 201)
    block_id = block_data["id"]
    print(f"  -> Admin zablokoval pokoj 102 z důvodu 'Malování'.")
    
    timeline_start = datetime.now().date()
    timeline_end = (datetime.now() + timedelta(days=10)).date()
    timeline_data = print_result(requests.get(f"{BASE_URL}/dashboard/timeline?start_date={timeline_start.isoformat()}&end_date={timeline_end.isoformat()}", headers=get_headers("admin")), 200)
    
    # Ověření rezervace a úkolu v timeline pokoje 101
    room_101_timeline = next((r for r in timeline_data if r['room_id'] == reserved_room_id), None)
    assert room_101_timeline is not None, "Timeline pro rezervovaný pokoj nebyla nalezena."
    assert any(e['type'] == 'reservation' and e['reservation_id'] == reservation_id for e in room_101_timeline['events']), "Rezervace Karla Nového chybí v timeline."
    assert any(e['type'] == 'task' and e['task_id'] == task_id for e in room_101_timeline['events']), "Úkol úklidu chybí v timeline."
    print("  -> OK: Timeline rezervovaného pokoje správně obsahuje rezervaci i úkol.")
    
    # Ověření blokace v timeline pokoje 102
    room_102_timeline = next((r for r in timeline_data if r['room_id'] == room_102_id), None)
    assert room_102_timeline is not None, "Timeline pro blokovaný pokoj nebyla nalezena."
    assert any(e['type'] == 'block' and e['block_id'] == block_id for e in room_102_timeline['events']), "Blokace 'Malování' chybí v timeline."
    print("  -> OK: Timeline blokovaného pokoje správně obsahuje blokaci.")
    
    print_result(requests.delete(f"{BASE_URL}/rooms/blocks/{block_id}", headers=get_headers("admin")), 204)
    print("  -> Blokace byla úspěšně odstraněna.")
    
    # FINÁLNÍ ZPRÁVA
    print("\n" + "="*70)
    print("\033[92m VŠECHNY TESTY ÚSPĚŠNĚ DOKONČENY! \033[0m")
    print("="*70)


if __name__ == "__main__":
    try:
        time.sleep(3) # Dáme API čas na start
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