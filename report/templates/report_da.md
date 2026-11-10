<!-- page -->
FOLKESUNDHED · ANALYSE PÅ KOMMUNENIVEAU

# Sundhed og middellevetid i Danmark

### Geografiske forskelle i sundhed, socioøkonomiske forhold og middellevetid på tværs af danske kommuner

**Frederik Jensen**  
Professional Bachelor of Physiotherapy  
Master of Science (MSc) in Health in Critical Health Studies (cand.san.)

Selvstændigt folkesundhedsanalytisk portfolio-projekt

10. november 2026 · Version 1.1 · Dansk udgave

Rapporten samler officielle danske kommunedata for at beskrive mønstre i befolkningens sundhed, undersøge statistiske sammenhænge og pege på spørgsmål til videre analyse.

**Dataperioder**  
Socioøkonomiske forhold: 2024  
Den Nationale Sundhedsprofil: 2025  
Periodemiddellevetid for 0-årige: 2021–2025

**Omfang**  
98 kommuner i atlasset · 94 komplette observationer i modeller for middellevetid · Ingen imputation

<!-- page -->
## Resumé

Sundhedsplanlægning kræver viden om forskelle mellem lokalområder og deres sammenhæng med sociale forhold. Analysen kombinerer officielle data fra Danmarks Statistik med offentlige kommuneestimater fra Den Nationale Sundhedsprofil. Den beskriver 98 kommuner; analyser af middellevetid omfatter 94, da fire kommuners estimater ikke offentliggøres.

Kort uddannelse og daglig rygning har de stærkeste negative simple sammenhænge med middellevetid: Pearsons r = henholdsvis {{r_education}} og {{r_smoking}}. Disponibel indkomst er positivt forbundet med middellevetid (r = {{r_income}}). Mønstrene gælder kommuner og kan ikke uden videre overføres til den enkelte borger.

> **Hovedresultater**
>
> - Uddannelse og rygning viser særligt stærke simple sammenhænge med kommunernes middellevetid.
> - Sundhedsadfærd tilfører statistisk information ud over indkomst og uddannelse: ΔR² = {{delta_r2}}, samlet HC3-test p = {{block_p}}.
> - Den kombinerede model beskriver ca. 75% af den observerede variation mellem kommuner (R² = {{M3_r2}}). Det er et mål for modeltilpasning, ikke en kausal andel.
> - Overlap mellem prædiktorer komplicerer de justerede koefficienter. Den positive betingede koefficient for svær overvægt er ikke dokumentation for en beskyttende virkning.
> - PCA og klyngeanalyse beskriver sammensatte profiler, herunder en kontrast for alkohol; de udgør ikke en samlet sundhedsrangering.

Model 3 har R² = {{loo_r2}} ved leave-one-out-validering, hvilket er lavere end ved tilpasning til hele datasættet. Residualer kan give anledning til nærmere undersøgelse af udeladte forhold, men måler ikke kommunal præstation. Forskellige dataperioder, selvrapportering, kollinearitet, manglende estimater for økommuner og ubehandlet rumlig afhængighed begrænser fortolkningen. Projektet er beskrivende og hypotesegenererende, ikke en effektevaluering.

### Læsevejledning

**Ramme og design:** 1 Baggrund · 2 Formål · 3 Data · 4 Metoder  
**Resultater:** 5 Variation · 6 Korrelationer · 7 Modeller · 8 Justering · 9 Residualer · 10 Profiler · 11 Kønsspecifikke analyser · 12 Følsomhed  
**Fortolkning:** 13 Diskussion · 14 Begrænsninger · 15 Konklusion  
**Dokumentation:** Reproducerbarhed · Kilder

Begge sprogversioner anvender decimalpunktum i de numeriske tabeller for at gøre resultaterne direkte sammenlignelige. Figurerne er identiske i de to versioner og har engelske aksetekster.

<!-- page -->
## 1. Baggrund

Nationale gennemsnit kan skjule væsentlige forskelle mellem lokalbefolkninger. Kommuneniveauet er velegnet til at beskrive den geografiske fordeling af sundhed, sociale forhold og mulige forebyggelsesbehov. Offentlige danske data gør det muligt at undersøge disse mønstre med gennemsigtige definitioner og identificerbare kilder.

Uddannelse og indkomst belyser forskellige sider af de socioøkonomiske forhold. Rygning, fysisk aktivitet, alkoholforbrug og svær overvægt beskriver aspekter af sundhedsadfærd eller beslægtede helbredsforhold. De hænger sammen frem for at være konkurrerende, adskilte forklaringer. En kommunes mønster kan afspejle befolkningssammensætning, levevilkår og ophobede eksponeringer såvel som aktuel adfærd.

Middellevetid for 0-årige er et bredt mål for befolkningens sundhed. Her er der tale om et **periodemål** baseret på dødeligheden i 2021–2025, ikke en prognose for, hvor længe børn født i 2025 faktisk vil leve. Målet kan ikke i sig selv vise, hvilke sygdomme, tilbud eller indsatser der ligger bag en forskel.

Den Nationale Sundhedsprofil skal understøtte sundhedsplanlægning [5–6]. Når profilens aggregerede estimater sammenholdes med socioøkonomiske data, kan det kvalificere spørgsmål til lokal undersøgelse. Det kan ikke fastslå, om en ændring i én indikator vil føre til en bestemt ændring i middellevetiden.

## 2. Formål og undersøgelsesspørgsmål

**Hovedspørgsmål:** Hvilke kommunale karakteristika vedrørende sundhedsadfærd og socioøkonomiske forhold er forbundet med geografiske forskelle i middellevetid mellem danske kommuner?

De supplerende spørgsmål er:

1. Hvilke indikatorer viser de stærkeste simple sammenhænge med middellevetid?
2. Tilfører sundhedsadfærd forklarende information ud over socioøkonomiske forhold?
3. Kan kommunerne beskrives ved forskellige multivariate sundhedsprofiler?
4. Hvilke kommuner har højere eller lavere observeret middellevetid end beregnet ud fra de inkluderede indikatorer?
5. Er mønstrene forskellige for mænds og kvinders middellevetid?

De fire primære modelspecifikationer blev fastlagt i projektets kode før estimering. Dette selvstændige portfolio-projekt er ikke eksternt præregistreret. Korrelationer, profiler, residualrangeringer, udelukkelse af indflydelsesrige observationer og kønsspecifikke modeller er eksplorative eller sekundære analyser.

<!-- page -->
## 3. Datakilder og opbygning af datasæt

Tabel 1 angiver datakilder og referenceperioder. Offentlige svar fra Statistikbankens API og formaterede Excel-eksporter fra sundhedsprofilens officielle gæsteadgang er bevaret. Kommunekoder og standardiserede navne forbinder kilderne; masterdatasættet har én række pr. kommune.

**Tabel 1. Officielle kilder og analyseindikatorer**

| Datakilde | Indikator | Referenceperiode | Geografi | Bemærkninger |
| --- | --- | --- | --- | --- |
| Danmarks Statistik, INDKP106 [1] | Gennemsnitlig disponibel personindkomst | 2024 | Kommune | Kroner; personer over 14 år; begge køn |
| Danmarks Statistik, HFUDD11 [2] | Grundskole og uoplyst uddannelse | 30. sep. 2024 | Kommune | Andele blandt 25–64-årige; uoplyst indgår i nævneren |
| Danmarks Statistik, FOLK1A [3] | Befolkning og aldersandele | 1. jan. 2024 | Kommune | Aldersgrupper 0–17, 18–64 og 65+ |
| Den Nationale Sundhedsprofil [5–6] | Rygning; BMI ≥30; utilstrækkelig aktivitet; alkohol >10 genstande/uge | 2025 | Kommune | Offentliggjort prævalens; gyldige besvarelser afhænger af indikator |
| Den Nationale Sundhedsprofil [5–6] | Selvvurderet helbred og mental sundhed, SF-12 | 2025 | Kommune | Se definitioner nedenfor |
| Danmarks Statistik, HISBK [4] | Middellevetid i alt, mænd, kvinder og kønsforskel | 2021–2025 | Kommune | Periodemål; fire kommuners estimater offentliggøres ikke |

*Kilde: bevarede indsamlingsmetadata, kildeoversigt og analytisk variabelfortegnelse. Tabel 1 beskriver kilderne og er ikke et nyt dataudtræk.*

**Dækning.** Atlasset indeholder {{municipalities}} kommuner. Middellevetid offentliggøres ikke for Ærø, Fanø, Samsø og Læsø, fordi Danmarks Statistik vurderer estimaterne som for usikre. De resterende {{N}} kommuner indgår i alle primære og kønsspecifikke modeller. Alle 98 indgår i PCA og klyngeanalyse af sundhedsprofiler. Manglende eller tilbageholdte værdier imputeres ikke, og kommuner uden offentliggjort middellevetid får ingen modelprædiktion.

**Definitionerne er afgørende.** Kort uddannelse betyder grundskole som højeste fuldførte uddannelse blandt 25–64-årige. Svær overvægt er BMI ≥30 baseret på selvrapporteret højde og vægt. Utilstrækkelig fysisk aktivitet følger portalens gemte ugentlige WHO-definition og afgrænsning, herunder advarslen om spørgeskemasammenlignelighed. Alkohol angiver over 10 genstande i en typisk uge, ikke rusdrikning eller afhængighed.

Mindre godt/dårligt selvvurderet helbred omfatter begge svarkategorier og er beregnet som den verificerede komplementære andel til fremragende, vældig godt eller godt helbred. Dårlig mental sundhed er portalens lave mentale SF-12-score (≤35.76), ikke komplementet til højt mentalt velbefindende.

**Sammenkobling og kvalitet.** Dubletter, kommunenavne, dækning, manglende værdier og numeriske intervaller er kontrolleret. Råfilernes kontrolsummer og variablernes proveniens er gemt. Dataperioderne overlapper, men er forskellige: 2025-undersøgelsen er ikke en eksponeringsmåling, der ligger før hele dødelighedsperioden. Det begrænser tidslig og kausal fortolkning.

<!-- page -->
## 4. Analytiske metoder

### Beskrivelse og sammenligning af kommuner

De gemte deskriptive opgørelser omfatter antal observerede og manglende værdier, gennemsnit, stikprøvestandardafvigelser, medianer, kvartiler og variationsbredder. Kommunerne vægtes ens. Gennemsnittet er derfor ikke et befolkningsvægtet landstal.

Pearsons r går fra −1 til +1 og beskriver en lineær sammenhæng: tæt på −1 betyder, at højere værdier på den ene indikator typisk optræder sammen med lavere værdier på den anden. Spearmans ρ sammenligner rangordninger og supplerer Pearson, når rækkefølgen er mere oplysende end en retlinjet sammenhæng.

Analysen undersøger alle 136 unikke par af 17 kontinuerte variabler. Benjamini–Hochberg-korrektion (BH) for false discovery rate (FDR) anvendes særskilt for Pearson og Spearman. Under metodens forudsætninger begrænses den forventede andel af falske fund blandt de forkastede hypoteser; det gør ikke det enkelte fund sikkert. Svage og ikke-signifikante sammenhænge er bevaret i de fulde resultater.

### Justerede sammenhænge og usikkerhed

Regressionsmodeller estimeret med mindste kvadraters metode (OLS) beskriver betingede sammenhænge, når de øvrige inkluderede indikatorer holdes statistisk konstante. Alle modeller har et konstantled. Indkomst skaleres pr. 10.000 kr.; uddannelse og sundhedsindikatorer pr. procentpoint. HC3-robuste standardfejl gør inferensen mindre følsom over for uens residualvarians, med t-baserede 95%-konfidensintervaller [7]. De håndterer ikke rumlig afhængighed eller målefejl.

Et konfidensinterval angiver koefficientværdier, der er rimeligt forenelige med data og modellens forudsætninger. Standardiseret beta omregner hældningen med SD(X)/SD(Y), så størrelser i forskellige enheder lettere kan sammenlignes. Variansinflationsfaktorer (VIF) beskriver statistisk overlap mellem prædiktorer; stort overlap kan gøre koefficienter ustabile. Ingen prædiktor fjernes på baggrund af p-værdi, fortegn eller VIF.

R² angiver den andel af den observerede udfaldsvariation, som modellens variabler statistisk beskriver i denne stikprøve. **Det er ikke en kausal andel af middellevetiden.** Justeret R² tager højde for antallet af prædiktorer. BH-korrektion omfatter 20 test af hældningskoefficienter på tværs af M1–M4; en særskilt familie omfatter 18 kønsspecifikke test. Den ene på forhånd fastlagte HC3-bloktest af sundhedsadfærd rapporteres uden yderligere korrektion [8].

### Profiler, residualer og robusthed

PCA sammenfatter de seks standardiserede sundhedsindikatorer i kombinationer, der varierer sammen. K-means undersøger k=2–6 i alle seks dimensioner; løsningen vælges efter højest gennemsnitlig silhouette med mindst fem kommuner pr. gruppe [9]. Grupperne er beskrivende profiler, ikke naturlige eller kausale kategorier.

Residualer i M3 er observeret minus modelberegnet middellevetid. Leave-one-out-validering udelader hver kommune fra estimeringen, før dens værdi forudsiges, som en intern kontrol af optimisme. Cook’s distance anvendes som screening ved D>4/N. Særskilte følsomhedsmodeller udelader de observationer, som den enkelte model udpeger; primærmodellerne beholder alle komplette observationer. Kontrollen belyser observationsafhængighed og er ikke en automatisk datarensningsregel.

<!-- page -->
## 5. Geografisk variation i sundhed

Den offentliggjorte kommunale middellevetid varierer fra **{{min_le}} til {{max_le}} år**. Figur 1 viser fordelingen og udvalgte kommuner i hver ende af den numeriske rækkefølge. Det er en beskrivelse af offentliggjorte estimater, ikke kvalitetsvurderinger eller test af parvise forskelle.

![Figur 1. Kommunal variation i middellevetid](figures/variation.png)

**Figur 1. Offentliggjort kommunal middellevetid, 2021–2025.** Fordeling og fem kommuner i hver ende af den observerede rækkefølge; 94 offentliggjorte estimater. Landstallet er hentet direkte fra HISBK og er ikke et kommunegennemsnit. Kilde: HISBK og det validerede masterdatasæt.

Tabel 2 sammenholder variationen med udvalgte sociale forhold og sundhedsindikatorer. Rygning og svær overvægt varierer mærkbart mellem kommunerne, ligesom indkomst og uddannelse. Variationsbredderne viser forskelle, der er relevante for sundhedsplanlægning, men surveyestimaterne har stikprøve- og bortfaldsusikkerhed, som ikke fremgår her.

**Tabel 2. Udvalgte deskriptive statistikker på tværs af kommuner**

{{descriptive_table}}

*Kilde: gemte deskriptive statistikker. Gennemsnit og medianer vægter kommunerne ens. N=98 bortset fra middellevetid (N=94, fire tilbageholdte estimater). Beløb afrundes til hele kroner, øvrige mål til én decimal; procentindikatorer er andele, ikke antal.*

<!-- page -->
## 6. Simple sammenhænge med middellevetid

Kort uddannelse (r = {{r_education}}) og rygning (r = {{r_smoking}}) har de stærkeste negative simple sammenhænge: højere andele optræder typisk med lavere middellevetid. Indkomst er positivt forbundet med middellevetid (r = {{r_income}}). Figur 2 viser alle karakteristika uanset signifikans.

![Figur 2. Rangering af korrelationer](figures/correlations.png)

**Figur 2. Pearson-korrelationer med samlet middellevetid.** De algebraisk beslægtede mål for middellevetid er udeladt af denne visning af karakteristika. Positive og negative retninger fremgår eksplicit. Kilde: gemte korrelationsresultater, N=94 for hvert vist par.

Selvvurderet helbred, aktivitet og svær overvægt viser også stærke negative sammenhænge. Alle seks hovedfund består global BH-korrektion. Tabel 3 viser begge metoder, også ikke-signifikante fund for befolkningsstørrelse og 18–64-årige. Alkohols positive kommunesammenhæng dokumenterer ingen sundhedsgevinst; befolkningssammensætning og sociale mønstre kan spille ind.

**Tabel 3. Alle korrelationer mellem karakteristika og middellevetid**

{{correlation_table}}

*Kilde: gemte korrelationer. BH-q omfatter alle 136 par særskilt for hver metode; tabellen viser Pearson-q. Spearman-q og uafrundede p-værdier er bevaret i de fulde output. Alle viste par har N=94. Sammenhængene er fortsat økologiske.*

<!-- page -->
## 6. Simple sammenhænge med middellevetid — fortsat

![Figur 3. Punktdiagrammer for uddannelse og rygning](figures/associations.png)

**Figur 3. Kommunemønstre bag to stærke simple sammenhænge.** Hvert punkt er en kommune med offentliggjort middellevetid. Linjerne er beskrivende hjælpelinjer genskabt fra de gemte Pearson-korrelationer samt den viste stikprøves gennemsnit og standardafvigelser; der estimeres ingen ny inferentiel model. Kilde: valideret masterdatasæt og gemte korrelationer, N=94.

Figur 3 tydeliggør den praktiske betydning: højere andele med grundskole som højeste uddannelse og højere forekomst af daglig rygning optræder typisk sammen med lavere middellevetid. Punkterne ligger ikke alle på en linje. En stærk sammenhæng er forenelig med betydelig lokal variation og identificerer ikke årsagen til den enkelte kommunes placering.

Spearman-korrelationerne i tabel 3 er også negative for disse indikatorer. For uddannelse er rangkorrelationen svagere end den lineære korrelation, hvilket viser, at de to mål ikke behøver have samme størrelse. Ingen af dem fastslår en effekt på individniveau.

**Fra simpel til justeret sammenhæng.** En simpel korrelation undersøger én indikator ad gangen. Uddannelse, indkomst, rygning og andre sundhedsmål overlapper. En multivariabel koefficient beskriver derimod en kontrast mellem kommuner, som statistisk ligner hinanden på de øvrige inkluderede prædiktorer. Det er forskellige spørgsmål; en stærk simpel sammenhæng behøver ikke bevare samme styrke efter justering.

## 7. Multivariable modeller

De fire faste specifikationer er:

- **M1 — socioøkonomi:** indkomst og grundskoleandel.
- **M2 — sundhedsadfærd:** rygning, svær overvægt, utilstrækkelig aktivitet og alkohol.
- **M3 — kombineret:** M1 samt de fire M2-indikatorer.
- **M4 — udvidet helbred:** M3 samt selvvurderet helbred og mental sundhed.

Alle modeller anvender de samme 94 komplette observationer. M1 og M2 er alternative specifikationer; M1→M3 og M3→M4 tilføjer prædiktorblokke. Tabel 4 og figur 4 sammenligner modeltilpasningen på næste side.

<!-- page -->
## 7. Multivariable modeller — fortsat

**Tabel 4. Tilpasning af de fire primære modeller for middellevetid**

{{model_table}}

*Kilde: gemt OLS-modeltabel. Kommuner vægtes ens; alle modeller har konstantled, som ikke tælles med blandt prædiktorerne. HC3 anvendes til inferens om koefficienter og omdefinerer ikke R².*

![Figur 4. Sammenligning af modeltilpasning](figures/models.png)

**Figur 4. R² og justeret R² for de faste primærmodeller.** Tekstetiketter skelner mellem de to mål; fremhævelsen af de kombinerede specifikationer udpeger ikke en universelt foretrukken model. Kilde: gemte modelresultater.

Når sundhedsadfærd tilføjes til M1, stiger R² med **{{delta_r2}}**. Den samlede HC3-bloktest har **p = {{block_p}}**. Den kombinerede model indeholder dermed yderligere statistisk information ud over indkomst og uddannelse i dette datasæt. Testen vedrører blokken samlet og dokumenterer ikke en selvstændig effekt af hver adfærd.

M3 beskriver ca. 75% af den observerede variation mellem kommuner (R² = {{M3_r2}}; justeret R² = {{M3_adj}}). M4 har R² = {{M4_r2}} og justeret R² = {{M4_adj}}. Bedre tilpasning med flere helbredsindikatorer fastslår hverken deres kausale bidrag eller fremtidig prædiktionsnøjagtighed. Målene beskriver dette datasæt og disse specifikationer.

De tilføjede indikatorer for selvvurderet helbred og mental sundhed beskriver delvist samtidig helbredsstatus. Det ændrer spørgsmålet: M4 er en udvidet model for betingede sammenhænge, mens den gemte residual- og prædiktionsanalyse bevidst anvender M3. Denne skelnen forhindrer, at den mere omfattende justering fremstår som den eneste mulige fortolkning af data.

<!-- page -->
## 8. Fuldt justerede resultater og kollinearitet

Tabel 5 viser alle M4-hældningskoefficienter, også de ikke-signifikante. Indkomst, uddannelse, svær overvægt og mental sundhed består den fastlagte korrektion af de 20 primære koefficienttest. Rygning ligger tæt på den nominelle grænse og består ikke korrektionen (p=0.0494; q=0.0760).

**Tabel 5. Betingede sammenhænge med middellevetid i Model 4**

{{coefficient_table}}

*Kilde: gemte regressionskoefficienter. b angiver år pr. 10.000 kr. for indkomst og pr. procentpoint for øvrige indikatorer. β er standardiseret beta. Intervaller anvender HC3-kovarians og t-reference med residualfrihedsgrader; q omfatter alle 20 primære hældningstest. Alle estimater har N=94.*

![Figur 5. Fuldt justerede standardiserede koefficienter](../outputs/figures/model4_coefficients.png)

**Figur 5. Standardiserede koefficienter og 95% HC3-intervaller i M4.** Gengivet uændret fra den validerede analysefigur. Retningen er betinget af øvrige prædiktorer; intervallet viser usikkerhed, ikke kausal sikkerhed. Kilde: gemt output fra Model 4.

**Hvorfor fortegnet for svær overvægt kræver forsigtighed.** Svær overvægt har en negativ simpel sammenhæng, men en positiv justeret koefficient. Når prædiktorer med meget fælles variation holdes konstante, kan den resterende kontrast skifte fortegn: et suppressions- eller kollinearitetsmønster. Højeste M4-VIF er {{vif}}. Det er **ikke dokumentation for, at svær overvægt beskytter**, og koefficienten bør ikke omsættes til en indsatsanbefaling. Aktivitet, alkohol og selvvurderet helbred har også usikre betingede estimater; manglende signifikans dokumenterer ikke fravær af en folkesundhedsmæssig sammenhæng.

<!-- page -->
## 9. Modelberegnet og observeret middellevetid

**Residual = observeret middellevetid − modelberegnet middellevetid.** Positive værdier betyder højere middellevetid end beregnet ud fra de inkluderede kommuneindikatorer; negative værdier betyder lavere. Figur 6 sammenligner observationer med M3’s tilpassede værdier; figur 7 viser de største positive og negative gemte residualer.

![Figur 6. Observeret og modelberegnet middellevetid](../outputs/figures/observed_vs_predicted.png)

**Figur 6. Observeret og M3-beregnet middellevetid.** Identitetslinjen svarer til præcist sammenfald. Prædiktionerne er tilpassede værdier for de 94 kommuner i estimeringsgrundlaget; fire kommuner uden offentliggjort udfald får ingen prædiktion. Kilde: uændret valideret prædiktionsfigur.

![Figur 7. Kommunale residualer](../outputs/figures/prediction_residual_ranking.png)

**Figur 7. Udvalgte positive og negative M3-residualer.** Værdierne er observeret minus tilpasset middellevetid i år. Det er en eksplorativ rækkefølge efter residualer, ikke en rangering af kommunal præstation eller dokumentation for statistisk usædvanlige udfald. Kilde: uændret valideret residualfigur.

<!-- page -->
## 9. Modelberegnet og observeret middellevetid — fortsat

Tabel 6 angiver de samme eksempler som figur 7, afrundet til to decimaler. En numerisk placering på listen fastslår ikke, at residualet afviger signifikant fra nul, eller at kommunerne adskiller sig signifikant fra hinanden.

**Tabel 6. De fem største positive og fem største negative gemte residualer**

{{residual_table}}

*Kilde: gemte M3-prædiktioner og residualer, ikke en ny rangeringsmodel. Observeret middellevetid offentliggøres med én decimal; prædiktioner og residualer beregnes ved gemt præcision før afrunding. Alle forskelle angives i år.*

Odder og København illustrerer henholdsvis højere og lavere middellevetid end beregnet ud fra de inkluderede kommuneindikatorer. Ingen af eksemplerne identificerer årsagen til forskellen. Udeladte forhold, kildeusikkerhed, aggregering, målefejl og tilfældig variation kan bidrage.

**Intern validering.** R² i estimeringsgrundlaget er {{M3_r2}}; ved leave-one-out-validering er R² **{{loo_r2}}**. Her forudsiges hver kommunes udfald med koefficienter estimeret uden den pågældende kommune. Det lavere mål er foreneligt med en vis optimisme i træningstilpasningen. Det er en intern kontrol, ikke ekstern validering i en ny bølge eller befolkning. Nabokommuner kan dele kontekst, så udelukkelse af én kommune fjerner ikke al beslægtet information.

**Anvendelse i praksis.** Residualmønstre kan pege på spørgsmål til en nærmere lokal gennemgang: mangler modellen relevante helbredsforhold, befolkningsbevægelser eller sociale forhold? De måler ikke kommunens effektivitet, indsatsers virkning eller forebyggelig dødelighed. Rapporten tilskriver ingen kommune en bestemt lokal forklaring.

<!-- page -->
## 10. PCA og kommunale sundhedsprofiler

PCA sammenfatter fælles mønstre i seks standardiserede sundhedsindikatorer for alle 98 kommuner. PC1 beskriver **{{pc1}}%** og PC2 **{{pc2}}%** af variationen i indikatorerne. Figur 8 viser komponenternes bidrag; figur 9 viser indholdet i de to første komponenter.

![Figur 8. Scree-plot for PCA](../outputs/figures/pca_scree.png)

**Figur 8. Variation beskrevet af de seks hovedkomponenter.** Gengivet uændret fra gemt PCA-output; procentandelene vedrører sundhedsindikatorerne, ikke variation i middellevetid. Kilde: valideret PCA, N=98.

![Figur 9. PCA-loadings](figures/loadings.png)

**Figur 9. Indikatorernes korrelation med PC1 og PC2.** Loadings med fortegn er gemte indikator–komponent-korrelationer, ikke egenvektorvægte. Kilde: gemte PCA-loadings. Samme figur anvendes i begge sprogversioner.

PC1 har positive loadings for selvvurderet helbred (+0.912), svær overvægt (+0.908), utilstrækkelig aktivitet (+0.887), rygning (+0.855) og mental sundhed (+0.443), men en negativ loading for alkohol (−0.501). Komponenten er derfor en **sammensat kontrastdimension, ikke en simpel sundhedsrisikoscore**. Alkohol blev ikke vendt for at tvinge indikatorerne i samme retning; fortegnet dokumenterer ingen beskyttende eksponering. Komponenternes fortegn følger en visningskonvention og er ikke i sig selv et substantielt resultat.

<!-- page -->
## 10. PCA og kommunale sundhedsprofiler — fortsat

Den valgte k-means-løsning har **to profiler** med **34 og 64 kommuner** og gennemsnitlig silhouette **{{silhouette}}**. Den har højest gennemsnitlig silhouette blandt de tilladte løsninger med k=2–6. Målet beskriver adskillelse i forhold til lighed inden for profilerne og fastslår ikke to naturlige kommunetyper.

![Figur 10. Kommuneprojektion og beskrivende profiler](figures/profiles.png)

**Figur 10. Gemte kommuneprofiler i PCA-rummet og på tværs af de seks indikatorer.** Både symboler og farver skelner profilerne. Projektionen viser PC1 og PC2, men klyngeanalysen anvendte alle seks standardiserede indikatorer. Profilgennemsnit er afvigelser fra gennemsnittet for 98 kommuner målt i standardafvigelser. Kilde: gemte scorer, medlemskaber og standardiserede profiler.

Figur 10 viser, hvorfor en samlet kvalitetsbetegnelse ville være misvisende. Den mindre profil har lavere rygning, svær overvægt, utilstrækkelig aktivitet og dårligere-helbredsindikatorer, men højere alkoholeksponering. Den større profil viser det modsatte relative mønster. Det er **eksplorative kommuneprofiler, ikke naturlige eller kausale grupper**; ingen af dem er sundere på alle inkluderede indikatorer.

Profilerne kan strukturere sammenligninger på flere dimensioner uden at reducere kommunen til én score. Før praktisk anvendelse bør de sammenholdes med lokal viden og kildeusikkerhed. Grupperingen afhænger af indikatorvalg, standardisering, algoritme og antal grupper. Kontrol med forskellige startfrø undersøger beregningsmæssig stabilitet, ikke stabilitet i en ny stikprøve eller sundhedsprofilbølge.

<!-- page -->
## 11. Kønsspecifikke sekundære analyser

Tabel 7 sammenfatter samme M3-specifikation med seks prædiktorer for mænds og kvinders middellevetid samt forskellen mellem kvinder og mænd.

**Tabel 7. Tilpasning af sekundære modeller**

{{secondary_table}}

*Kilde: gemte sekundære modelresultater. Hver model har N=94 og HC3-inferens. De kønsspecifikke koefficienttest udgør en særskilt BH-familie på 18 test.*

Efter korrektion består sammenhænge for mænd med indkomst, uddannelse, rygning og betinget svær overvægt; for kvinder består indkomst og rygning. De øvrige sekundære koefficienter består ikke den fastlagte korrektion. Ingen prædiktor for kønsforskellen består. Signifikans hos det ene køn og manglende signifikans hos det andet er ikke i sig selv en testet kønsforskel. Den positive betingede koefficient for svær overvægt kræver samme forsigtighed som i M4.


## 12. Modeldiagnostik og følsomhed

Højeste M4-VIF er **{{vif}}**, hvilket peger på betydeligt overlap for mindst én prædiktor. Syv kommuner overskrider M4’s screeningstærskel for Cook’s distance; seks gør det i M3. Primærmodellerne beholder alle 94 komplette observationer. Screeningen peger på mulig indflydelse, ikke på ugyldige observationer eller automatisk grundlag for at slette en kommune.

Særskilte eksplorative følsomhedsmodeller udelader hver models egne udpegede observationer. Tabel 8 fremhæver skift omkring den nominelle p-værdigrænse; alle følsomhedskoefficienter findes fortsat i de gemte output. Udelukkelserne bygger på udfaldet og definerer ikke en foretrukken renset analyse.

**Tabel 8. Eksempler på følsomhed over for udelukkelse af indflydelsesrige observationer**

{{sensitivity_table}}

*Kilde: gemt følsomhedssammenligning. M3 udelader seks og M4 syv kommuner udpeget af Cook’s distance. Der er tale om nominelle HC3-p-værdier, ikke nye korrigerede fund; primærresultaterne er uændrede.*

Rygning i M4 går fra p=0.049 til p=0.061 ved denne udelukkelse, mens alkohol i M3 går fra p=0.216 til p=0.025. Det viser sårbarheden ved at behandle 0.05 som en skarp grænse. Resultaterne understøtter en forsigtig fortolkning af betingede estimater frem for at vælge den specifikation, der giver det mest tiltalende fund.

Figurer med residualer mod tilpassede værdier, Q–Q-plot og Cook’s distance bevares i analysearkivet. Diagnostik af heteroskedasticitet og normalitet er beskrivende kontroller, ikke garantier for opfyldte forudsætninger. HC3 anvendes uanset de diagnostiske p-værdier og løser ikke rumlig afhængighed, korrelerede kildefejl eller confounding.

<!-- page -->
## 13. Diskussion

Resultaterne er mest oplysende som et sammenhængende mønster. Stærke korrelationer for uddannelse og rygning optræder sammen med en positiv indkomstsammenhæng og fælles variation mellem sundhedsindikatorer. Målene beskriver forskellige, overlappende træk ved kommunernes befolkninger. Adfærdsblokkens ekstra modeltilpasning viser, at indkomst og uddannelse alene ikke udtømmer informationen i de tilgængelige indikatorer.

Det opdeler ikke befolkningens sundhed i adskilte sociale og adfærdsmæssige årsager. Socioøkonomiske forhold kan være forbundet med muligheder, eksponeringer, ressourcer og befolkningssammensætning, mens tværsnitsindikatorerne sammenfatter ophobede mønstre. Analysen kan ikke fastlægge disse mekanismer eller effekten af at ændre én af dem.

### Fortolkning af mønstrene

**Simple sammenhænge og betingede kontraster har forskellige formål.** Kort uddannelse og rygning identificerer stærke geografiske mønstre. De enkelte M4-hældninger er vanskeligere at fortolke, fordi beslægtede prædiktorer holdes konstante samtidig. En svækket koefficient eller et fortegnsskift ophæver ikke den beskrivende sammenhæng. Svær overvægts fortegnsskift er et konkret eksempel: den betingede kontrast er hverken en anbefaling om at øge forekomsten eller dokumentation for, at den negative simple sammenhæng var uden betydning.

**Modeltilpasning forklarer ikke mekanismer.** M3’s R² på ca. 75% i estimeringsgrundlaget viser betydelig statistisk overensstemmelse med observerede forskelle. Det betyder ikke, at indikatorerne forårsager denne andel af middellevetiden, og M4’s højere tilpasning udpeger ikke en bedre indsatsstrategi. Intern validering er mere krævende end træningstilpasning, men er fortsat ikke prædiktion i fremtidige perioder eller geografisk uafhængige befolkninger.

**Profiler fastholder kompleksiteten.** PCA og klyngeanalysen understreger, at indikatorerne ikke alle følger én gunstig–ugunstig dimension. Alkoholkontrasten er væsentlig: den forhindrer, at profilerne opfattes som ét sundhedshierarki. Profiler er nyttige til at spørge, hvor lignende kombinationer af eksponeringer optræder, ikke til at klassificere borgere eller give kommuner en samlet score.

**Residualer rejser spørgsmål uden at besvare dem.** Adgang til sundhedsydelser, erhvervssammensætning, boligforhold, miljøeksponering, sygelighed, flyttemønstre, lokal organisering af sundhedsydelser og urbanisering er mulige kontekstområder til videre undersøgelse. Ingen af dem er påvist som forklaring på en navngiven kommunes residual. Rumlig afhængighed kan også bidrage til fælles mønstre og for optimistiske usikkerhedsmål.

**Politisk og administrativ anvendelse kræver et yderligere skridt.** Atlasset kan støtte behovsvurdering, sammenligning og drøftelse af, hvor mere detaljeret viden er nødvendig. Lokal fortolkning bør inddrage ulighed inden for kommunen, befolkningssammensætning, surveyusikkerhed, kendskab til tilbud og mere specifikke udfald. Effektevaluering af indsatser kræver et andet design med holdbar tidslig og kausal identifikation.

Projektets styrke er den gennemsigtige forbindelse mellem officielle kilder, bevarede definitioner, gemte resultater og forsigtig fortolkning. Bidraget er et reproducerbart overblik over geografiske mønstre og et grundlag for mere kvalificerede spørgsmål i videre folkesundhedsanalyse.

<!-- page -->
## 14. Begrænsninger

**Økologisk design og økologisk fejlslutning.** En sammenhæng mellem kommunegennemsnit kan ikke automatisk overføres til individer. Sammenhænge fastslår ikke årsager, og kommunegennemsnit kan skjule betydelig ulighed inden for kommunen.

**Tid og confounding.** Socioøkonomiske data er primært fra 2024, sundhedsestimater fra 2025 og dødelighed fra 2021–2025. Tidsrækkefølgen er ikke fastlagt. Uobserverede forhold, omvendt årsagsretning og resterende demografisk confounding er mulige; aldersandele og befolkningsstørrelse beskrives, men indgår ikke som yderligere kovariater i de faste primærmodeller.

**Selvrapportering og usikkerhed.** Sundhedsprofilens estimater bygger på selvrapporterede oplysninger, indikatorspecifikke nævnere og afrundede prævalenser. Stikprøve- og bortfaldsusikkerhed, usikkerhed i middellevetidsestimater og målefejl indgår ikke i regressionen. HC3 korrigerer ikke for disse begrænsninger.

**Tilbageholdte estimater og ingen imputation.** Ærø, Fanø, Samsø og Læsø indgår ikke i analyser af middellevetid, fordi deres estimater ikke offentliggøres. Ingen værdier udfyldes. Resultater fra komplette observationer beskriver derfor ikke middellevetiden i disse små økommuner.

**Kollinearitet og indflydelse.** Overlappende prædiktorer komplicerer betingede hældninger, og udelukkelse af indflydelsesrige observationer ændrer nogle nominelle slutninger. Primærmodellerne beholder alle komplette observationer; eksplorative følsomhedsanalyser udpeger ikke en foretrukken erstatningsmodel.

**Rumlig afhængighed og eksplorativt design.** Nabokommuner kan dele eksponeringer og fejl. Der er ikke estimeret formelle rumlige modeller; HC3 og BH fjerner ikke denne problemstilling. Profiler, residualrækkefølge og sekundære analyser er fortsat hypotesegenererende.

## 15. Konklusion

Socioøkonomiske forhold og sundhedsadfærd viser tydelige geografiske sammenhænge med kommunal middellevetid. Uddannelse og rygning har særligt stærke simple sammenhænge, og sundhedsadfærd tilfører statistisk information ud over indkomst og uddannelse. Overlap mellem indikatorer komplicerer de enkelte justerede koefficienter. Atlasset bør forstås som et beskrivende og hypotesegenererende overblik over ulighed i sundhed på kommuneniveau frem for kausal dokumentation eller vurdering af kommunal præstation.

### Reproducerbarhed

Råfiler er bevaret; reproducerbar databehandling, proveniens, programmatisk genererede statistiske output og valideringstest indgår i projektet. Rapportfelter er knyttet til kontrolsumverificerede output, og eksisterende analysefigurer gengives uændret. Supplerende publikationsfigurer viser kun gemte værdier eller validerede observationer. Ingen tilbageholdte værdier for middellevetid imputeres. Byggevejledningen dokumenterer den nødvendige software; fortsat adgang til eksterne tjenester kan ikke garanteres.

<!-- page -->
## Kilder og kildebemærkninger

Kilderegistreringer er indsamlet eller kontrolleret **6. november 2026**. Tabelnavnene nedenfor bevarer deres officielle ordlyd, så den præcise kilde kan identificeres. Analysen anvender det bevarede datasnapshot og ikke eventuelle senere revisioner af tabellerne.

1. **Danmarks Statistik. INDKP106 — Disponibel indkomst efter område, enhed, køn, alder, indkomstinterval og tid.** 2024, gennemsnitlig disponibel indkomst i kroner, begge køn. [Officiel tabel](https://www.statbank.dk/INDKP106).
2. **Danmarks Statistik. HFUDD11 — Befolkningens højeste fuldførte uddannelse (15–69 år) efter bopælsområde, herkomst, højeste fuldførte uddannelse, alder, køn og tid.** Udvalgte aldre 25–64 år, 2024. [Officiel tabel](https://www.statbank.dk/HFUDD11).
3. **Danmarks Statistik. FOLK1A — Befolkningen den 1. i kvartalet efter område, køn, alder, civilstand og tid.** 2024K1. [Officiel tabel](https://www.statbank.dk/FOLK1A).
4. **Danmarks Statistik. HISBK — Middellevetid for 0-årige efter område, køn og tid.** Kommuner og Danmark, perioden 2021:2025; i alt, mænd og kvinder. [Officiel tabel](https://www.statbank.dk/HISBK).
5. **Sundhedsstyrelsen; Statens Institut for Folkesundhed, SDU; de fem regioner. Danskernes Sundhed / Den Nationale Sundhedsprofil, 2025.** Offentlige kommuneeksporter: *Andel der ryger dagligt; Svær overvægt; Opfylder ikke WHOs anbefalinger for fysisk aktivitet; Drikker mere end 10 genstande om ugen; Andel med godt selvvurderet helbred; Dårligt mentalt helbred.* [Officiel portal](https://www.danskernessundhed.dk/). Præcise rapport-URL’er til gæsteadgang, valg, definitioner, regneark og kontrolsummer findes i projektets kildeoversigt og indsamlingsmanifest.
6. **Sundhedsstyrelsen. Danskernes sundhed — Den Nationale Sundhedsprofil.** Officiel kildeoversigt og henvisning til 2025-rapporten. [Kildeoversigt](https://www.sst.dk/sundhedsprofilen). Anvendt til kildekontekst, ikke som erstatning for kommuneeksporterne.
7. **statsmodels. OLSResults.get_robustcov_results.** Officiel dokumentation for robust kovarians, herunder HC3. [Dokumentation](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html).
8. **statsmodels. stats.multitest.multipletests.** Officiel dokumentation for korrektion af multiple test, herunder Benjamini–Hochberg FDR. [Dokumentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html).
9. **scikit-learn. Clustering; PCA.** Officiel dokumentation for k-means, fortolkning af silhouette og hovedkomponentanalyse. [Klyngeanalyse](https://scikit-learn.org/stable/modules/clustering.html) · [PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html).

### Publikationsoplysninger

Forfatter: Frederik Jensen. Professional Bachelor of Physiotherapy; Master of Science (MSc) in Health in Critical Health Studies (cand.san.). Selvstændig portfolio-analyse; ingen institutionel tilknytning eller arbejdsgivertilknytning angives. Analyseværdier stammer fra projektets validerede snapshot. Rapportversion 1.1; dansk og engelsk udgave har tilsvarende analytisk indhold, afsnitsrækkefølge, tabeller og figurer.

De fulde uafrundede koefficient-, korrelations-, diagnostik- og følsomhedstabeller bevares i projektet. Rapportens udvalg af deskriptive mål er ikke filtreret efter signifikans; alle M4-hældninger og karakteristikkorrelationer vises, og de gemte output omfatter samtlige primære og sekundære estimater.
