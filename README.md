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

Pro každé palivo, které vybraná stanice aktuálně uvádí v ceníku, vzniká právě jedna entita s cenou. Podporovány jsou **Diesel**, **Diesel Plus**, **Natural 95**, **BA 98 Super+**, **BA 91 Special**, **Optimal BA95**, **LPG PB**, **AdBlue**, **CNG** a **HVO (XTL)**. Služby stanice (myčka, Wi-Fi, výdejní místa) a kapalina do ostřikovačů se nezobrazují.

Podrobnosti jsou atributy cenové entity: `obsah_bioslozky`, `obsah_biolihu`, `hustota`, `bod_vzplanuti`, `konec_destilace`, `posledni_zavoz`, `platnost_od`, `platnost_do` a `aktualizovano`. Diagnostická entita ukazuje čas poslední úspěšné aktualizace všech dat integrace.

Data poskytuje veřejné API Srdcovky společnosti ČEPRO. Při každé aktualizaci integrace používá jeden dotaz pro ceny celé sítě a jeden dotaz pro kvalitu vybrané stanice. Katalog názvů produktů se načte jednou při spuštění integrace.
