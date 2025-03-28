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
BLOCK_SIZE = 128    # rozmiar bloku danych


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
    if dlugosc < BLOCK_SIZE:
        dane += dopelnienie * (BLOCK_SIZE - dlugosc)
    return dane


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
        trybCRC = input("Użyć trybu CRC? [tak/nie]: ")
        trybCRC = trybCRC.strip().lower()
        if trybCRC == "t" or trybCRC == "tak":
            print("Wybrano tryb CRC")
            uzywajCRC = True
            print("Wybrano tryb sumy kontrolnej")
        else:
            uzywajCRC = False
        message = input("Podaj wiadomość do wysłania: ")
        print("xmodem_send_message(ser, message, use_crc=use_crc)")
        #xmodem_send_message(ser, message, use_crc=use_crc)

    elif wybor == "2":
        trybCRC = input("Użyć trybu CRC? [tak/nie]: ")
        trybCRC = trybCRC.strip().lower()
        if trybCRC == "t" or trybCRC == "tak":
            print("Wybrano tryb CRC")
            uzywajCRC = True
        else:
            print("Wybrano tryb sumy kontrolnej")
            uzywajCRC = False
        print("xmodem_receive_message(ser, use_crc=use_crc)")
        #xmodem_receive_message(ser, use_crc=use_crc)

    elif wybor == "3":
        break

    else:
        print("Wybrano niepoprawną opcję!")

ser.close()
input("Wciśnij enter, aby zakończyć.")