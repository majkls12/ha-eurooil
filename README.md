# EuroOil / RoBiN OIL pro Home Assistant

Vlastní integrace pro veřejná data aplikace EuroOil Srdcovka. Vytvoří jedno zařízení pro každou zvolenou čerpací stanici a každý den v nastavený čas načte ceny, biosložku benzínu a datum posledního závozu.

## Instalace

1. V HACS otevřete **Integrace → Vlastní repozitáře** a přidejte URL tohoto repozitáře jako typ **Integrace**.
2. Nainstalujte **EuroOil / RoBiN OIL** a restartujte Home Assistant.
3. V **Nastavení → Zařízení a služby → Přidat integraci** vyhledejte **EuroOil / RoBiN OIL**.
4. Vyberte stanici. Další stanici přidáte stejným způsobem znovu.
5. V možnostech integrace nastavte denní čas aktualizace, výchozí je 06:00.

## Entity

Podle nabídky zvolené stanice jsou k dispozici ceny Natural 95, Super 98, nafty, nafty Plus a LPG. U benzínů jsou navíc senzory obsahu bioetanolu a u benzínu i naft datum posledního závozu.

Data poskytuje veřejné API Srdcovky společnosti ČEPRO. Integrace používá jeden dotaz pro ceny celé sítě a jeden dotaz pro kvalitu vybrané stanice při každé plánované aktualizaci.
