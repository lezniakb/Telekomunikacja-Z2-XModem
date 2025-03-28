import serial
import time
import sys

# definicje znakow (zapisane w hex)
SOH = b'\x01'       # poczatek blok
EOT = b'\x04'       # koniec transmisji
ACK = b'\x06'       # pozytywne potwierdzenie odbioru (acknowledged)
NAK = b'\x15'       # negatywne potwierdzenie (not acknowledged)
CAN = b'\x18'       # anuluj transmisje (cancel)
CHAR_C = b'C'       # do trybu CRC
ROZMIAR_BLOKU = 128    # rozmiar bloku danych
DEBUG_FLAG = 1

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
        print("Wybrano tryb sumy kontrolnej")
    else:
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

def nadajWiadomosc(port, message, uzywajCRC=True, timeout=15):
    # funkcja ktora wysyla wiadomosc przez protokol Xmodem
    # kazdy blok ma po 128 bajtow
    # format: [SOH][blok_num][~blok_num][128 bajtów danych][error_check]

    wiadomosc = message.encode("utf-8")
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
        debug("Brak odpowiedzi..")
        time.sleep(1)

    if znakStartu is None:
        print("Timeout! Nie otrzymano odpowiedzi od odbiornika przez ostatenie 60 sekund.")
        return False
    odebranyZnakASCII = ord(znakStartu)
    print("Odebrano sygnał inicjujący od odbiornika:", odebranyZnakASCII)

    # do zmiany to nizej
    blok_number = 1
    for blok in bloki:
        retry_count = 0
        while retry_count < 10:
            # Budowa nagłówka: SOH, numer bloku, dopełnienie (255 - numer bloku)
            header = SOH + bytes([blok_number & 0xFF]) + bytes([(255 - blok_number) & 0xFF])
            if uzywajCRC:
                error_val = obliczCRC(blok)
                error_bytes = error_val.to_bytes(2, byteorder="big")
            else:
                error_val = obliczChecksume(blok)
                error_bytes = bytes([error_val])
            packet = header + blok + error_bytes
            print(f"Wysyłanie bloku {blok_number} (próba {retry_count+1})...")
            port.write(packet)
            # Oczekiwanie na odpowiedź (ACK lub NAK)
            trial_start = time.time()
            response = None
            while time.time() - trial_start < timeout:
                if port.in_waiting > 0:
                    response = port.read(1)
                    break
                time.sleep(0.1)
            if response == ACK:
                print(f"Blok {blok_number} wysłany poprawnie.")
                blok_number += 1
                break
            elif response == NAK:
                print(f"Blok {blok_number} odebrany błędnie, retransmisja (próba {retry_count+1}).")
                retry_count += 1
            else:
                print(f"Blok {blok_number}: brak odpowiedzi lub nieznany znak, retransmisja (próba {retry_count+1}).")
                retry_count += 1
        else:
            print("Przekroczono limit retransmisji dla bloku", blok_number)
            return

    # Wysyłanie EOT
    retry_count = 0
    while retry_count < 10:
        port.write(EOT)
        trial_start = time.time()
        response = None
        while time.time() - trial_start < timeout:
            if port.in_waiting > 0:
                response = port.read(1)
                if response == ACK:
                    print("Transmisja zakończona pomyślnie.")
                    return
            time.sleep(0.1)
        retry_count += 1
    print("Nie udało się zakończyć transmisji.")

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
    ser = serial.Serial(port, baudrate, timeout=15)
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
        message = input("Podaj wiadomość do wysłania: ")
        debug("uzywajCRC: {uzywajCRC}\n"
              f"message: {message}\n")
        print("nadajWiadomosc(ser, message, uzywajCRC=uzywajCRC)")
        #nadajWiadomosc(ser, message, uzywajCRC=uzywajCRC)

    elif wybor == "2":
        uzywajCRC = czyCRC()
        debug(f"uzywajCRC: {uzywajCRC}\n")
        print("xmodem_receive_message(ser, uzywajCRC=uzywajCRC)")
        #xmodem_receive_message(ser, uzywajCRC=uzywajCRC)

    elif wybor == "3":
        break

    else:
        print("Wybrano niepoprawną opcję!")

ser.close()
input("Wciśnij enter, aby zakończyć.")