# EuroOil / RoBiN OIL pro Home Assistant

Vlastní integrace pro veřejná data aplikace EuroOil Srdcovka. Vytvoří jedno zařízení pro každou zvolenou čerpací stanici a v nastaveném intervalu načte ceny, biosložku benzínu a datum posledního závozu.

## Instalace

1. V HACS otevřete **Integrace → Vlastní repozitáře** a přidejte URL tohoto repozitáře jako typ **Integrace**.
2. Nainstalujte **EuroOil / RoBiN OIL** a restartujte Home Assistant.
3. V **Nastavení → Zařízení a služby → Přidat integraci** vyhledejte **EuroOil / RoBiN OIL**.
4. Vyberte stanici. Další stanici přidáte stejným způsobem znovu.
5. V možnostech integrace nastavte interval aktualizace v hodinách; výchozí je 12 hodin.

## Aktualizace dat

Po prvním načtení při spuštění integrace se data obnovují opakovaně po nastaveném počtu hodin. Interval lze změnit v **Nastavení → Zařízení a služby → EuroOil / RoBiN OIL → Konfigurovat**.

Pro ruční aktualizaci lze v automatizaci nebo skriptu použít akci `homeassistant.update_entity` a vybrat entitu **Poslední aktualizace dat** vybrané stanice. Tím se společně načtou ceny, kvalita paliv i údaje o posledním závozu.

## Entity

Podle nabídky zvolené stanice jsou k dispozici ceny Natural 95, Super 98, nafty, nafty Plus a LPG. U benzínů jsou navíc senzory obsahu bioetanolu a u benzínu i naft datum posledního závozu. Diagnostická entita ukazuje čas poslední úspěšné aktualizace všech dat integrace.

Data poskytuje veřejné API Srdcovky společnosti ČEPRO. Integrace používá jeden dotaz pro ceny celé sítě a jeden dotaz pro kvalitu vybrané stanice při každé plánované aktualizaci.
