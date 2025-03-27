# Ćwiczenie 2 - protokół XModem
Zadaniem jest zaimplementować protokół zgodny ze specyfikacją XModem. Należy przetestować go z innymi programami posiadającymy też ten protokół. W celu komunikacji można wykorzystać emulację portów szerogowych. Emulator portów szeregowych można znaleść przykładowo pod adresem:
https://freevirtualserialports.com/
https://www.aggsoft.com/com-port-emulator.htm

Poniżej linki do opisu protokołu XMODEM
http://web.mit.edu/6.115/www/amulet/xmodem.htm

# Instrukcja
1. Pobierz com0com w wersji 2.2.2.0 (fre-signed) z sourceforge.net: https://sourceforge.net/projects/com0com/files/com0com/2.2.2.0/
Q: Po co nam to? 
A: Na komputerze domyślnie nie mamy portów połączeniowych "COMx" oprócz COM1. Potrzebujemy dwóch takich portów. Program com0com tworzy wirtualne porty COM i łączy je między sobą.
2. Rozpakuj paczkę i zainstaluj wybraną przez siebie wersję (x64 lub x86).
Uwaga: przy instalacji sterownika zaznacz "Ufaj firmie". Bez tego Windows nie uzna tych portów za bezpieczne.
3. Wejdź do "C:\Program Files (x86)\com0com" i uruchom "setupc.exe". 
4. Wprowadź komendę: install PortName=COM10 PortName=COM11
Utworzy ona dwa wirtualne porty COM10 i COM11 oraz je powiąże między sobą.
5. Wejdź w menadżer urządzeń (device manager) w windowsie i sprawdź czy w zakładce "com0com" nie wyświetlają się znaki ostrzeżenia przy com0com.
6. Otwórz główny folder z programem (main.py). Powinny się w nim znaleźć także pliki: testNadaj.txt, testOdbior.txt, trybNadajnika.bat oraz trybOdbiornika.bat. Pliki .bat wykonują komendę, która otwiera skrypt w pythonie z odpowiednimi argumentami.
7. Otwórz dwa okna CMD (lub PowerShell). W pierwszym uruchom trybNadajnika.bat, w drugim trybOdbiornika.bat. Zaczekaj chwilę, a komunikacja powinna przejść.