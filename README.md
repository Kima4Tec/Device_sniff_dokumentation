# Device_sniff_dokumentation
Dokumentation til projekter omkring sniffing af devices

## Projektopgave, Positionsbestemmelse af enheder uden GPS dækning

### Projekt 1: ESP32 → MQTT → Broker → trilateration
https://github.com/Kima4Tec/WifiSniff  

### Projekt 2: ESP-NOW + Master ESP32 + MQTT  
Master ESP32: https://github.com/Kima4Tec/Sniff_master  

Slave ESP32: https://github.com/Kima4Tec/Sniff_slave  

Heatmap ved brug af MQTT: https://github.com/Kima4Tec/Device_sniff_dokumentation/blob/main/heatmap_mqtt.py  
Vi sendte først til mqtt, hvorfra vi lavede heatmap, men vi misforstod, da vi blev bedt om ikke at sende til MQTT, at det kun var mellemregninger fra de tre esp32, vi ikke skulle sende, og derfor fandt vi på en anden løsning med UDP og slettede helt vores løsning med at sende til MQTT.   

Heatmap ved brug af UDP og laptop: https://github.com/Kima4Tec/Device_sniff_dokumentation/blob/main/heatmap.py     
```
Slave A ──UDP──┐
               ├──► Master ESP32 ──UDP──► Laptop :5005 ──► heatmap.py
Slave B ──UDP──┘   (port 5006)

```

## Introduktion
Der findes flere metoder til at estimere position uden brug af GPS. I dette projekt undersøges især teknologier baseret på Wi-Fi og ESP32-enheder. Undersøgelse har strukket sig over fire dage, blandet med et andet smiley-projekt, hvor en bruger skulle tilkendegive tilfredshed ved et tryk på en knap. 

# Indholdsfortegnelse
1. [Logbog](#Logbog)
2. [GDPR](#GDPR)
3. [Hashing](#Hashing)  
4. [Trilaterering](#Trilaterering)
5. [Teknologier](#Teknologier)
6. [RSSI](#RSSI)  





# Logbog
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

### Dag 4
Dokumentation og opgaveaflevering.   

---

[Home](#Indholdsfortegnelse)

---

# GDPR
## Hvilke GDPR-problemer rejser opgaven?

## Gruppens undersøgelse og vurderinger omkring GDPR

En ESP32 i "promiscuous mode" kan opfange **MAC-adresser** fra enheder i nærheden. MAC-adresser betragtes under GDPR som **personoplysninger**, fordi de kan identificere en person indirekte via deres enhed.

**Lovligt grundlag** – Artikel 6
- Vi opsamler MAC-adresser om personer, der *ikke* har givet samtykke
- For et skoleprojekt er det typisk legitim interesse (artikel 6(1)(f))
- Vi logger position + tid, hvilket er lokaliseringsdata
- Vi transmitterer og gemmer data på en MQTT-broker. 

**Dataminimering** – Artikel 5
- Vi anonymiserer MAC-adresser med det samme. MAC-adresser bliver hashet og saltet, og devices får tildelt nyt id.
- Vi gemmer ikke rå MAC-adresser på MQTT-brokeren.
- Vi må kun indsamle, det vi faktisk har brug for. OPgaven lød på: Hvordan laver man positionsbestemmelse af f.eks. mobile enheder. Vi har indsamlet data fra alle devices i området, der kan måles med RSSI. Alle devices i klasselokalet var mobile, men vi kunne godt have udvidet projektet med kun at finde data på mobile enheder, der havde randomisering slået til. 

**Formålsbegrænsning**
- Hvad bruges dataene præcist til? Det skal være klart defineret.
- Data bruges i et skoleforsøg, der går ud på at afstandsbedømme og vurdere, hvor mange devices, der er indenfor et område vha triangulering ved brug af tre esp32. Opgaven går bl.a. ud på at vurdere sikkerhedsregler ift. GDPR.

**Sikkerhed**
- Er vores MQTT-broker sikret (TLS, autentificering)?
- Hvem har adgang til dataene?
- Vi bruger TLS og autentificering i forbindelsen med MQTT-serveren, men alle på netværket kan læse data, der sendes op til MQTT-serveren http://wilsons.local uden brug af ssl, og det gør sikkerheden lille og viser, at vi ikke kan stole på databehandleren.

**Opbevaringsbegrænsning**
- MQTT er en protokol, ikke en database — den opbevarer som udgangspunkt **ingen data**. Men der er en undtagelse: Brokeren (wilsons.local) kan have en persistens-konfiguration der logger beskeder til disk — det er væsentligt at spørge ejeren om dette. Det er der tilsyneladende i dette tilfælde. Vi skal have aftale om, hvor længe disse data bliver gemt.

**Hvor længe behandler vi data i vores projekt?**

| Sted | Data | Levetid |
|---|---|---|
| Slave ESP32 | Rå MAC i ISR-queue | Millisekunder — overskrives løbende |
| Master ESP32 | `macHash` + RSSI per enhed | Maks 30 sekunder — ryddes hvis enheden forsvinder |
| Master ESP32 | Anonymt `devId` + position | Maks 30 sekunder |
| Master ESP32 | Dagligt salt | Nulstilles ved midnat |
| `heatmap.py` | Positioner i RAM | Kun mens programmet kører — intet gemmes til disk |
| `heatmap.py` | Heatmap-grid | Kun i RAM, falmer løbende |

**Det korte svar: vi gemmer intet permanent.** Alt lever kun i RAM og forsvinder når enhederne genstarter eller programmet lukkes.

---

**Opsummering**
- Data behandles kun i realtid til et afgrænset formål (positionsestimering)
- Ingen personfølsomme oplysninger forlader systemet (rå MAC hashes aldrig ud)
- Der er ingen logfiler, ingen database, ingen langtidsopbevaring
- Dagligt salt betyder at data ikke kan kobles på tværs af dage

Det eneste usikre punkt er hvad brokerens ejer logger på `wilsons.local`.


Vi har fundet information her: 
https://pentests.dk/docs/gdpr-developers-guide/
og ved brug af AI Claude har vi fundet forpligtelser for databehandler og dataansvarlig:

## Generelt om dataansvarlig og databehandler
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

[Home](#Indholdsfortegnelse)

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


---

[Home](#Indholdsfortegnelse)

---

# Trilaterering
<img width="322" height="272" alt="image" src="https://github.com/user-attachments/assets/57b6ff41-5805-4041-ae72-40aa85811ec6" />

Hver sensor definerer en cirkel: centrum = sensorposition, radius = estimeret afstand
Positionen er der hvor de tre cirkler skærer hinanden

Trilaterering virker ved at hver sensor definerer en cirkel hvor radius = estimeret afstand. Den sande position er der hvor de tre cirkler skærer hinanden.
Her er den matematiske løsning. Med tre sensorer på position (x₁,y₁), (x₂,y₂), (x₃,y₃) og afstande d₁, d₂, d₃ opstiller vi to ligninger ved at trække cirkelligningerne fra hinanden (det eliminerer de kvadratiske led):

```
2(x₂-x₁)·x + 2(y₂-y₁)·y = d₁²-d₂² - x₁²+x₂² - y₁²+y₂²
2(x₃-x₁)·x + 2(y₃-y₁)·y = d₁²-d₃² - x₁²+x₃² - y₁²+y₃²
```

---

[Home](#Indholdsfortegnelse)

---

# RSSI (Wi-Fi signalstyrke)

RSSI (*Received Signal Strength Indicator*) bruges til at estimere afstanden mellem to enheder ud fra signalstyrken.

## Hvordan virker det?
En ESP32 måler styrken på et modtaget Wi-Fi-signal i dBm:

- **-30 dBm** → meget tæt på
- **-90 dBm** → langt væk

Signalstyrken kan derefter omregnes til en estimeret afstand ved hjælp af matematiske modeller som:

- *Log-Distance Path Loss Model*

## Fordele
- Indbygget i ESP32
- Simpel at implementere
- Lavt strømforbrug

## Ulemper
RSSI er upræcist, fordi signalstyrken påvirkes af:

- vægge og beton
- mennesker
- refleksioner
- antennens retning
- møbler og metal

## Præcision
Indendørs præcision ligger typisk på:

- **2–8 meters usikkerhed**

RSSI fungerer derfor bedst til:
- zonedetektion
- rum-positionering
- grove afstandsvurderinger


---

[Home](#Indholdsfortegnelse)

---


# Teknologier
**Sammenligning af teknologier til indendørs positioning med ESP32**

| Teknologi | Hvordan virker det? | Fordele | Ulemper | Egnet til projektet? |
|---|---|---|---|---|
| ESP32 → MQTT → Broker → trilateration | Alle ESP32-enheder sniffer WiFi-signaler og sender RSSI-data direkte til MQTT-server. Broker/backend udregner position via trilateration. | Simpel arkitektur, let debugging, central databehandling, nem visualisering, god skalerbarhed, let at integrere med dashboards/databaser | Kræver WiFi-netværk og broker, flere MQTT-forbindelser, mere netværkstrafik, backend skal samle alle målinger | Ja – meget god og stabil løsning |
| ESP-NOW + Master ESP32 + MQTT | Slave-ESP32’er sender RSSI-data til en master via ESP-NOW. Master samler data og sender til MQTT. | Lav latency, mindre netværkstrafik, kun én MQTT-forbindelse, fungerer uden router mellem ESP32’er, mere professionel edge/gateway-arkitektur | Mere kompleks kode, ESP-NOW kræver samme WiFi-kanal, begrænset rækkevidde, sværere debugging | Ja – meget stærk løsning til projektet |
| ESP-MESH | ESP32’er danner selvorganiserende mesh-netværk og videresender data mellem noder til root-node | Stor rækkevidde, selvhelende netværk, god til store områder, robust mod node-fejl | Kompleks opsætning, højere latency, mere RAM/CPU-forbrug, svær debugging | Muligt, men ofte overkill til mindre projekter |
| RTT (Round Trip Time) | Måler tiden et signal bruger på at rejse mellem enheder og tilbage igen | Potentielt mere præcis afstandsbestemmelse end RSSI | ESP32 understøtter ikke præcis hardware-timing til RTT/Fine Timing Measurement (FTM), meget vanskelig implementering, kræver synkronisering | Ikke realistisk til dette projekt |
| RSSI-trilateration | Afstand estimeres ud fra signalstyrke (RSSI), hvorefter position beregnes geometrisk | Simpel implementering, virker med standard ESP32 hardware, ingen aktiv forbindelse nødvendig | Lav præcision, påvirkes af vægge, mennesker og støj, signalstyrke varierer meget | Ja – mest realistiske metode med ESP32 |





Kort sagt: fordi vi kun tracker kendte telefoner med ejernes samtykke, er vi i en relativt god position — men vi bør kunne dokumentere det samtykke og have en plan for datasletning.
