import serial
import time
import sys

# definicje znakow (zapisane w hex)
SOH = b"\x01"       # poczatek blok
EOT = b"\x04"       # koniec transmisji
ACK = b"\x06"       # pozytywne potwierdzenie odbioru (acknowledged)
NAK = b"\x15"       # negatywne potwierdzenie (not acknowledged)
CAN = b"\x18"       # anuluj transmisje (cancel)
CHAR_C = b"C"       # do trybu CRC
ROZMIAR_BLOKU = 128    # rozmiar bloku danych
DEBUG_FLAG = 0

def debug(*args, **kwargs):
    # prosta funkcja, ktora wyswietli print tylko gdy globalna flaga DEBUG jest ustawiona
    if DEBUG_FLAG == 1:
        print(*args, **kwargs)

def czyCRC():
    trybCRC = input("Użyć trybu CRC? [tak/nie]: ")
    trybCRC = trybCRC.strip().lower()
    if trybCRC == "t" or trybCRC == "tak":
        print("Wybrano tryb CRC")
        uzywajCRC = True
    else:
        print("Wybrano tryb sumy kontrolnej")
        uzywajCRC = False
    return uzywajCRC

def obliczChecksume(blok):
    # jednobajtowa suma kontrolna (mod 256) dla przekazanego bloku
    sumaKontrolna = sum(blok) % 256
    return sumaKontrolna


def obliczCRC(dane):
    # oblicza CRC (16bit) dla podanego bloku danych
    crc = 0
    # wprowadzamy bajt z danych do wartosci crc
    for bajt in dane:
        # przesuniecie bajtu o jeden bajt (8bitow) w lewo i wykonanie xor
        crc ^= (bajt << 8)
        for i in range(8):
            # sprawdzenie czy najbardziej znaczacy bit jest ustawiony (w 16 bitach)
            if crc & 0x8000:
                # jesli tak to przesuwamy crc w lewo o 1, wykonujemy xor z 0x1021 - naszym stalym wielomianem
                # a potem ograniczamy wynik do 16 bitow przez maske 0xFFFF
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                # jesli nie, to przesuwamy crc o 1 w lewo i ograniczamy wynik do 16 bitow dzieki masce 0xFFFF
                crc = (crc << 1) & 0xFFFF
    return crc

def dopelnijDane(dane):
    # dopelnij blok danych do 128 bajtow znakiem CTRL-Z (bajtowo: 0x1A)
    dopelnienie = b"\x1A"
    dlugosc = len(dane)
    if dlugosc < ROZMIAR_BLOKU:
        dane += dopelnienie * (ROZMIAR_BLOKU - dlugosc)
    return dane

def podzielNaBloki(wiadomosc):
    # dzieli wiadomosc na bloki o zdefiniowanym rozmiarze (ustawiono: 128)
    bloki = []
    # iteruj co kazdy rozmiar bloku, w dlugosci calej wiadomosic
    for i in range(0, len(wiadomosc), ROZMIAR_BLOKU):
        # wydziel blok i wypelnij go (w funkcji) jesli nie jest dlugosci 128
        blok = wiadomosc[i:i+ROZMIAR_BLOKU]
        blok = dopelnijDane(blok)
        bloki.append(blok)
    debug(bloki)
    return bloki

def nadajWiadomosc(port, komunikat, uzywajCRC=True, timeout=10):
    # funkcja ktora wysyla wiadomosc przez protokol Xmodem
    # kazdy blok ma po 128 bajtow
    # format: [SOH][blok_num][~blok_num][128 bajtów danych][error_check]

    wiadomosc = komunikat.encode("utf-8")
    bloki = podzielNaBloki(wiadomosc)

    print("Oczekiwanie na inicjację od strony odbiornika (znak 'C' lub 'NAK')...")
    # bierzemy czas rozpoczecia (sekunda '0')
    start = time.time()
    znakStartu = None

    # petla wykonuje sie dopoki nie przekroczy 60 sekund (timeout)
    while time.time() - start < 60:
        # jesli ilosc bajtow w budorze jest >0
        if port.in_waiting > 0:
            # odczytaj znak czekajacy w buforze (tylko 1)
            ch = port.read(1)
            # jesli ten znak to NAK lub C, to idziemy do nastepnego kroku
            if ch in [NAK, CHAR_C]:
                znakStartu = ch
                break
        # jesli nie ma bajtow w buforze, to zaczekaj sekunde przed ponownym sprawdzeniem
        time.sleep(1)

    if znakStartu is None:
        print("Timeout! Nie otrzymano odpowiedzi od odbiornika przez ostatenie 60 sekund.")
        return False
    print("Odebrano sygnał inicjujący od odbiornika:", znakStartu)

    # do zmiany to nizej
    numerBloku = 1
    for blok in bloki:
        powtorzenie = 0
        # ustaw 'timeout' na maksymalnie 10 powtorzen
        while powtorzenie < 10:
            # naglowek = SOH, numer bloku (zapisany bajtowo), dopełnienie (255 - numer bloku)
            numerBlokuBajt = bytes([numerBloku & 0xFF])
            dopelnienie = bytes([(255 - numerBloku) & 0xFF])

            naglowek = SOH + numerBlokuBajt + dopelnienie

            # jesli uzytkownik zdecydowal sie na uzycie CRC
            if uzywajCRC == True:
                wartoscCRC = obliczCRC(blok)
                crcBajty = wartoscCRC.to_bytes(2, byteorder="big")
            else:
                # jesli nie crc, to checksuma
                wartoscCRC = obliczChecksume(blok)
                crcBajty = bytes([wartoscCRC])

            packet = naglowek + blok + crcBajty
            print(f"Nadawanie bloku: {numerBloku}, próba: {powtorzenie+1}...")
            port.write(packet)
            # czekanie na odpowiedz od odbiorcy
            start = time.time()
            odpowiedz = None

            while time.time() - start < timeout:
                # jesli w buforze (in_waiting) znajdzie sie jakis znak, to go odczytaj i zakoncz petle
                if port.in_waiting > 0:
                    odpowiedz = port.read(1)
                    break
                time.sleep(0.1)
            # jesli odpowiedz to ACK (zmienna globalna)
            if odpowiedz == ACK:
                print(f"Blok {numerBloku} wysłany poprawnie")
                numerBloku += 1
                break
            # NAK (not acknowleged), odebrany blednie
            elif odpowiedz == NAK:
                print(f"Blok {numerBloku} odebrany błędnie, próba retransmisji: {powtorzenie+1}...")
                powtorzenie += 1
            # jesli odebrany znak to nie jest to czego sie spodziewamy
            else:
                print(f"Blok {numerBloku}: brak odpowiedzi albo niewłaściwy znak, próba retransmisji: {powtorzenie+1}).")
                powtorzenie += 1
        else:
            print(f"Nie udało się wysłać bloku {numerBloku} (limit retransmisji: {powtorzenie})")
            return False

    # EOT - koniec transmisji
    powtorzenie = 0
    while powtorzenie < 10:
        # wyslij komunikat o zakonczeniu transmisji
        port.write(EOT)
        start = time.time()
        odpowiedz = None
        while time.time() - start < timeout:
            # jesli w buforze znajdzie sie jakis znak
            if port.in_waiting > 0:
                odpowiedz = port.read(1)
                if odpowiedz == ACK:
                    print("Odbiornik potwierdził zakończenie komunikacji, operacja przebiegła pomyślnie.")
                    return
            time.sleep(0.1)
        powtorzenie += 1
    print("Odbiornik nie potwierdził zakończenie komunikacji, wystąpił błąd.")


def odbierzWiadomosc(port, uzywajCRC=True, timeout=10):
    # funkcja ktora odbiera wiadomosc przez protokol XModem
    # format: [SOH][blok_num][~blok_num][128 bajtów danych][error_check]
    if uzywajCRC == True:
        pierwszyZnak = CHAR_C
    else:
        pierwszyZnak = NAK

    print("Rozpoczynanie transferu. Wysyłam znak inicjujący: ", pierwszyZnak)
    start = time.time()

    # dopoki czas (liczony od rozpoczecia 'start') nie przekroczy timeoutu 60 s, to wykonuj
    while time.time() - start < 60:
        # wyslij na port pierwszy znak inicjujacy komunikacje
        port.write(pierwszyZnak)
        # zaczekaj 10 sekund na odpowiedz
        time.sleep(10)
        # jesli w buforze (zwrotnie) znajdzie sie znak (odpowiedzi) to zakoncz petle
        if port.in_waiting > 0:
            break
        # jesli nie ma odpowiedzi, to znowu wyslij znak inicjalizacji

    # oczekuj na naglowek
    start = time.time()
    naglowek = None
    while time.time() - start < timeout:
        # jesli w buforze znajdzie sie znak odpowiedzi
        if port.in_waiting > 0:
            # odczytaj go
            znakOdp = port.read(1)
            # jesli znak odpowiedzi to SOH (poczatek bloku) to zapisz w naglowku i opusc petle
            if znakOdp == SOH:
                debug("Odebrano znak SOH od nadawcy!")
                naglowek = znakOdp
                break
        time.sleep(0.1)
    if naglowek is None:
        print("Nie udało się odebrać pakietu.")
        return False

    # odczytujemy numer bloku i jego dopelnienie
    numerBloku = port.read(1)[0]
    numerBlokuDop = port.read(1)[0]
    # 0xFF = 255
    # uzywamy maski 0xFF zeby zapewnic ograniczenie zakresu 255 (jeden blok)
    if (numerBloku + numerBlokuDop) & 0xFF != 0xFF:
        debug(f"numerBloku={numerBloku}\n"
              f"numerBlokuDop={numerBlokuDop}")
        print("Błędny numer bloku.")
        port.write(NAK)
        return False

    # odczytaj 128 bajtow danych
    dane = port.read(ROZMIAR_BLOKU)
    if len(dane) != ROZMIAR_BLOKU:
        print("Wystapił błąd przy odbieraniu danych: Niepoprawny rozmiar bloku!")
        port.write(NAK)
        return False

    if uzywajCRC:
        bajtSprawdzenia = port.read(2)
        otrzymaneSprawdzenie = int.from_bytes(bajtSprawdzenia, byteorder="big")
        obliczoneSprawdzenie = obliczCRC(dane)
    else:
        bajtSprawdzenia = port.read(1)
        otrzymaneSprawdzenie = bajtSprawdzenia[0]
        obliczoneSprawdzenie = obliczChecksume(dane)

    # jesli checksuma/CRC sie nie zgadza z tymi wyslanymi przez nadawce
    if obliczoneSprawdzenie != otrzymaneSprawdzenie:
        print(f"Sprawdzenie błędu nie udało się:\n"
              f"Oczekiwano {obliczoneSprawdzenie}\n"
              f"Odebrano {otrzymaneSprawdzenie}")
        port.write(NAK)
        return False
    # jesli checksuma/CRC sie zgadza:
    else:
        # potwierdz odebranie
        port.write(ACK)
        # usun dopelnienie w wiadomosci i uzyj utf-8
        komunikat = dane.rstrip(b"\x1A")
        try:
            komunikat.decode("utf-8")
        except UnicodeDecodeError:
            # jesli wystapil UnicodeDecodeError to uzyj opcji errors=replace
            komunikat.decode("utf-8", errors="replace")
        print(f"Pomyślnie odebrano wiadomość: '{komunikat}'")
        return True

# main
port = ""
while port.startswith("COM") != True:
    port = input("Podaj wybrany port szeregowy (np. COM10): ")
    port = port.strip().upper()

try:
    baudrate = int(input("Podaj prędkość transmisji (domyślnie 9600): ").strip())
except ValueError:
    baudrate = 9600
    print(f"Podano niepoprawną wartość. Ustawiono baudrate={baudrate}")

try:
    ser = serial.Serial(port, baudrate, timeout=10)
except Exception as e:
    print("Wystąpił błąd przy otwieraniu porta:", e)
    sys.exit(1)

while True:
    print("--------------\nMenu Główne:\n"
    "1. Nadaj wiadomość\n"
    "2. Odbierz wiadomość\n"
    "3. Opuść program")
    wybor = input("Wybierz opcję: ").strip()
    if wybor == "1":
        uzywajCRC = czyCRC()
        komunikat = input("Podaj wiadomość do wysłania: ")
        debug(f"uzywajCRC: {uzywajCRC}\n"
              f"komunikat: '{komunikat}'")
        nadajWiadomosc(ser, komunikat, uzywajCRC=uzywajCRC)

    elif wybor == "2":
        uzywajCRC = czyCRC()
        debug(f"uzywajCRC: {uzywajCRC}")
        print("odbierzWiadomosc(ser, uzywajCRC=uzywajCRC)")
        odbierzWiadomosc(ser, uzywajCRC=uzywajCRC)

    elif wybor == "3":
        break

    else:
        print("Wybrano niepoprawną opcję!")

ser.close()
input("Wciśnij enter, aby zakończyć.")