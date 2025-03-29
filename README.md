# Ćwiczenie 2 - protokół XModem
Zadaniem jest zaimplementować protokół zgodny ze specyfikacją XModem.<br />Należy przetestować go z innymi programami posiadającymy też ten protokół. W celu komunikacji można wykorzystać emulację portów szerogowych.<br />Emulator portów szeregowych można znaleść przykładowo pod adresem:<br />
https://freevirtualserialports.com/
https://www.aggsoft.com/com-port-emulator.htm

Poniżej linki do opisu protokołu XMODEM
http://web.mit.edu/6.115/www/amulet/xmodem.htm

# Instrukcja
1. Pobierz com0com w wersji 2.2.2.0 (fre-signed) z sourceforge.net:<br />https://sourceforge.net/projects/com0com/files/com0com/2.2.2.0/<br />
Q: Po co nam to?<br />
A: Na komputerze domyślnie nie mamy portów połączeniowych "COMx" oprócz COM1. Potrzebujemy dwóch takich portów. Program com0com tworzy wirtualne porty COM i łączy je między sobą.
2. Rozpakuj paczkę i zainstaluj wybraną przez siebie wersję (x64 lub x86).
Uwaga: przy instalacji sterownika zaznacz "Ufaj firmie". Bez tego Windows nie uzna tych portów za bezpieczne.
3. Wejdź do "C:\Program Files (x86)\com0com" i uruchom "setupc.exe". 
4. Wprowadź komendę: install PortName=COM10 PortName=COM11
Utworzy ona dwa wirtualne porty COM10 i COM11 oraz je powiąże między sobą.
5. Wejdź w menadżer urządzeń (device manager) w windowsie i sprawdź czy w zakładce "com0com" nie wyświetlają się znaki ostrzeżenia przy com0com.
6. Pobierz Tera Term (jebać HyperTerminal):<br />https://github.com/TeraTermProject/teraterm/releases/tag/v5.4.0<br />
Zatwierdź wszystkie domyślne opcje podczas instalacji.

# Sprawdzanie poprawności działania
1. Otwórz Tera Term i ustaw New Connection. Zaznacz opcję "Serial" i wybierz port, który chcesz zająć przez Tera Term (np. COM11).
2. Uruchom main.py. Wprowadź port, który chcesz zająć przez skrypt (np. COM10).<br />
Prędkość transmisji ustaw na 9600 (możesz kliknąć enter)
## Nadaj wiadomość z main.py do Tera Term
1. Wybierz w programie opcję 1. i wybierz czy chcesz używać trybu CRC. Wprowadź wiadomość do wysłania. Program powinien czekać na inicjację transmisji ze strony odbiorcy.
2. W aplikacji Tera Term wybierz File -> Transfer -> XModem -> Receive, a następnie wybierz gdzie chcesz zapisać plik. Zwróć uwagę na wybór Checksuma/CRC na dole okna zapisu.
3. W terminalu pythona powinno pokazać się potwierdzenie nadania wiadomości. Sprawdź odebraną wiadomość w zapisanym pliku.< /br>Uwaga: Tekst odebrany przez Tera Term będzie zawierać dodatkowe znaki po zapisanym komunikacie. Jest to normalne i dotyczy dopełnienia wysłanego bloku do rozmiaru 255. Jeśli Tera Term tego nie usuwa, to w takiej postaci otrzymuje się komunikat.
## Odbierz wiadomość w main.py od Tera Term
1. W aplikacji Tera Term wybierz File -> Transfer -> XModem -> Send, a następnie wybierz plik, który chcesz nadać. 
2. W programie main.py wybierz opcję 2. i wybierz czy chcesz używać trybu CRC. Program niemal natychmiastowo powinien odebrać znak SOH (nagłówka wiadomości) a następnie odebrać wiadomość.
</ br>
ToDo: Można dodać funkcjonalność "odczytaj z pliku / zapisz do pliku" ale jeśli to będzie wymagane.