# EuroOil / RoBiN OIL pro Home Assistant

Vlastní integrace pro veřejná data aplikace EuroOil Srdcovka. Vytvoří jedno zařízení pro každou zvolenou čerpací stanici a v nastaveném intervalu načte ceny i parametry kvality paliv.

## Instalace

1. V HACS otevřete **Integrace → Vlastní repozitáře** a přidejte URL tohoto repozitáře jako typ **Integrace**.
2. Nainstalujte **EuroOil / RoBiN OIL** a restartujte Home Assistant.
3. V **Nastavení → Zařízení a služby → Přidat integraci** vyhledejte **EuroOil / RoBiN OIL**.
4. Vyberte stanici. Další stanici přidáte stejným způsobem znovu.
5. V možnostech integrace nastavte interval aktualizace v hodinách; výchozí je 12 hodin.

## Aktualizace dat

Po prvním načtení při spuštění integrace se data obnovují opakovaně po nastaveném počtu hodin. Interval lze změnit v **Nastavení → Zařízení a služby → EuroOil / RoBiN OIL → Konfigurovat**. Hodnota `0` vypne automatické obnovování; data pak zůstanou jen na ruční aktualizaci.

Pro ruční aktualizaci lze v automatizaci nebo skriptu použít akci `homeassistant.update_entity` a vybrat entitu **Poslední aktualizace dat** vybrané stanice. Tím se společně načtou ceny, kvalita paliv i údaje o posledním závozu.

## Entity

Entity se vytvářejí podle paliv, která vybraná stanice skutečně prodává. U běžné stanice to jsou například **Diesel**, **Diesel Plus**, **Natural 95**, **BA 98 Super+**, **LPG PB** a **AdBlue**.

U naftových paliv jsou podle dat Srdcovky dostupné cena, obsah biosložky, hustota a bod vzplanutí. U benzínů cena, konec destilace, obsah biolihu a hustota. Pokud Srdcovka poskytne datum posledního závozu, zobrazí se i samostatná entita. Diagnostická entita ukazuje čas poslední úspěšné aktualizace všech dat integrace.

Data poskytuje veřejné API Srdcovky společnosti ČEPRO. Při každé aktualizaci integrace používá jeden dotaz pro ceny celé sítě a jeden dotaz pro kvalitu vybrané stanice.
