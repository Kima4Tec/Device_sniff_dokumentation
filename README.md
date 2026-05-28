# Device_sniff_dokumentation
Dokumentation til projekter omkring sniffing af devices

## Teknisk: Hvordan finder man position uden GPS?

## Introduktion
Der findes flere metoder til at estimere position uden brug af GPS. I dette projekt undersøges især teknologier baseret på Wi-Fi og ESP32-enheder. Undersøgelse har strukket sig over tre dage, blandet med et andet smiley-projekt, hvor en bruger skulle tilkendegive tilfredshed ved et tryk på en knap. 

## Logbog
### Dag 1
Vi fandt ud at sniffe os til flere forskellige enheder i nærheden. Havde tanker på sikkerhed med hashing. Vi opsatte en mqtt server på pc. Herefter satte vi programmet til at søge på specifikke mobiler med kendte mac-adresser. Dette kræver tilladelse af den enkelte, der ejer mobilerne, der bliver sniffet, pga GDPR-regler (Se mere om GDPR regler her: 
[GDPR](#GDPR)
). Med MQTT-server på vores egen pc, er vi både dataansvarlige og databehandlere. Se længere nede i noterne omkring deres ansvar.


### Dag 2
Vi er gået videre med vores sniffer-program, der bruger mqtt-serveren som modtager af de tre esp32s data med en broker (program skrevet i python), som samler data fra de tre esp32 og udregner afstand til en kendt mobil vha trilateration. Vi finder desuden, hvor mange andre devices, der er i nærheden.  
Vi krypterer alle fundne mac-adresser med hashing, og da vi fandt ud af, at det ikke er sikkert nok, har vi også saltet disse data.
Ved at salte forhindres rainbow table-angreb – Uden salt kan en angriber bruge forudberegnede hash-tabeller til at reverse-engineer MAC-adresser. Saltet gør dette upraktisk. (se yderligere om hashing her: 
[Hashing](#Hashing)
)
Vi har finder kun afstand fra en kendt mobil og registrerer desuden antal af fundne devices uden at bruge deres mac-adresser.
Vi opstartede desuden nyt projekt, hvor vi undersøger mulighederne med esp-now. 
Du finder programmet her: 

https://github.com/Kima4Tec/WifiSniff


### Dag 3
Vi lavede 
---


# Hashing

**Fordele**

- **Forhindrer rainbow table-angreb** – Uden salt kan en angriber bruge forudberegnede hash-tabeller til at reverse-engineer MAC-adresser. Saltet gør dette upraktisk.
- **Unikhed på tværs af systemer** – To ESP32-noder med samme salt producerer samme anonyme ID for samme enhed, så du kan korrelere på tværs af noder. Eller omvendt: skifter du salt, får du helt andre IDs.
- **Simpel implementering** – Din nuværende løsning er let at forstå og hurtig at køre på en microcontroller.

**Ulemper**

- **Hardkodet salt i `secrets.h`** – Hvis nogen får adgang til din firmware, kender de saltet og kan bruge det til at reverse-engineer specifikke MAC-adresser, de kender i forvejen.
- **Statisk salt** – Du bruger ét fast salt for alle enheder og altid. Et *per-enhed* eller *tidsbaseret* salt ville give stærkere anonymisering.
- **SHA-256 alene er hurtig** — Det er godt for performance på ESP32, men en angriber kan også hashe hurtigt. Til stærkere beskyttelse ville HMAC-SHA256 være mere korrekt (salt som nøgle, ikke blot præfiks/suffiks).
- **Salt-længde ikke valideret** – `strlen(SALT)` antager at SALT er null-termineret og ikke for langt. Hvis `input`-bufferen (kun `6 + 20` bytes) overskrides, får du et buffer overflow.

