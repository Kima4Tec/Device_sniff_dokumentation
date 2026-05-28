# Device_sniff_dokumentation
Dokumentation til projekter omkring sniffing af devices

## Projektopgave, Positionsbestemmelse af enheder uden GPS dækning

### Projekt 1: ESP32 → MQTT → Broker → trilateration
https://github.com/Kima4Tec/WifiSniff

### Projekt 2: ESP-NOW + Master ESP32 + MQTT
Master ESP32: https://github.com/Kima4Tec/Sniff_master  
Slave ESP32: https://github.com/Kima4Tec/Sniff_slave  
Heatmap ved brug af MQTT:   
Heatmap ved brug af UDP og laptop: 
```
Slave A ──UDP──┐
               ├──► Master ESP32 ──UDP──► Laptop :5005 ──► heatmap.py
Slave B ──UDP──┘   (port 5006)

```

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
Vi opstartede desuden nyt projekt, hvor vi undersøger mulighederne med esp-now, hvor esp32-devices kommunikerer med hinanden. 
Du finder programmet her: 

https://github.com/Kima4Tec/WifiSniff


### Dag 3
Vi arbejder videre med ESP-NOW.

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


# GDPR
Vi har fundet information her: 
https://pentests.dk/docs/gdpr-developers-guide/
og ved brug af AI Claude har vi fundet forpligtelser for databehandler og dataansvarlig:
## Databehandler og Dataansvarlig (ikke "dataudgiver") under GDPR

---

### Dataansvarlig (Data Controller)

Den fysiske eller juridiske person, myndighed, institution eller andet organ, der **alene eller sammen med andre afgør**, til hvilke formål og med hvilke hjælpemidler der må foretages behandling af personoplysninger.

**Ansvar:**
- Fastlægger formålet med behandlingen
- Skal have et lovligt grundlag (f.eks. samtykke, kontrakt, legitim interesse)
- Skal overholde de registreredes rettigheder (indsigt, sletning osv.)
- Skal udarbejde fortegnelse over behandlingsaktiviteter
- Bærer det primære juridiske ansvar over for de registrerede og tilsynsmyndigheder

---

### Databehandler (Data Processor)

En fysisk eller juridisk person, myndighed, institution eller andet organ, der **behandler personoplysninger på den dataansvarliges vegne**.

**Kendetegn:**
- Handler kun efter instruks fra den dataansvarlige
- Må ikke bruge data til egne formål
- Typiske eksempler: IT-leverandører, cloud-udbydere, lønadministration, markedsføringsbureauer

**Forpligtelser:**
- Skal indgå en **databehandleraftale** med den dataansvarlige (artikel 28)
- Skal implementere passende tekniske og organisatoriske sikkerhedsforanstaltninger
- Må kun anvende underdatabehandlere med den dataansvarliges godkendelse
- Skal slette eller tilbagelevere data efter opgavens afslutning

---

### Databehandleraftalen (artikel 28)

Et centralt krav er, at forholdet **altid skal reguleres skriftligt**. Aftalen skal bl.a. indeholde:

- Behandlingens varighed, art og formål
- Typen af personoplysninger og kategorier af registrerede
- Den dataansvarliges forpligtelser og rettigheder
- Krav om fortrolighed og sikkerhed

---

### Hvornår er man hvad?

| Situation | Rolle |
|---|---|
| Virksomhed der behandler egne kundedata | Dataansvarlig |
| IT-leverandør der drifter et system med kundedata | Databehandler |
| To virksomheder der fælles bestemmer formålet | Fælles dataansvarlige |
| Databehandler der hyrer en underleverandør | Underdatabehandler |

---



Vi opsamler MAC-adresser fra personer der ikke har givet samtykke
Vi logger position + tid, hvilket er lokaliseringsdata
Vi transmitterer og gemmer data på en MQTT-broker
Det er muligt at rekonstruere en persons bevægelser over tid

De vigtigste GDPR-krav
Retsgrundlag — I skal have et gyldigt grundlag for behandlingen. For et skoleprojekt er det typisk legitim interesse (artikel 6(1)(f)), men det kræver at I kan argumentere for at interessen ikke overstiger de registreredes rettigheder.
Dataminimering — I må kun indsamle det I faktisk har brug for. Overvej:

Behøver vi gemme den fulde MAC, eller er et anonymt hash nok?
Behøver vi gemme præcise tidsstempler?

Opbevaringsbegrænsning — Data må ikke gemmes længere end nødvendigt. Definer en konkret slettefrist.
Information til de registrerede — Personer hvis telefoner I scanner, skal i princippet informeres. I et kontrolleret forsøg (f.eks. kun kendte telefoner tilhørende jer selv) er det håndterbart.
Hvad der gør jeres projekt mere acceptabelt

Vi scanner kun kendte, specifikke MAC-adresser — ikke alle i nærheden
Telefonerne tilhører sandsynligvis jer selv eller folk der har givet samtykke
Det er et afgrænset eksperiment, ikke kontinuerlig overvågning

Praktiske anbefalinger

Hash MAC-adresserne inden I gemmer dem — SHA256(MAC) er ikke reversibelt og reducerer risikoen markant
Indhent eksplicit samtykke fra ejerne af de telefoner I tracker
Begræns adgang til MQTT-brokeren og den data der gemmes
Slet data efter projektet er afsluttet
Dokumentér hvad vi indsamler, hvorfor, og hvem der har adgang — selv en enkel side er nok til et skoleprojekt

Kort sagt: fordi vi kun tracker kendte telefoner med ejernes samtykke, er vi i en relativt god position — men vi bør kunne dokumentere det samtykke og have en plan for datasletning.
