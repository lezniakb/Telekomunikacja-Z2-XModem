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