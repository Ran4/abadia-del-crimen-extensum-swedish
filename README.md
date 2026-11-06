# La Abadía del Crimen Extensum på svenska

*La Abadía del Crimen Extensum* är en gratis nyversion från 2016 av Manuel Pazos och Daniel
Celemín. Förlagan är klassikern *La Abadía del Crimen* från 1987 av Paco Menéndez och Juan Delcán.
Det spelet bygger i sin tur på Umberto Ecos roman *Rosens namn*. Det här är en svensk översättning
av nyversionen.

Svenskan tar över spelets oanvända språkplats ”de”, som inget av originalets startskript väljer.

## Starta spelet

```sh
"game/TheAbbeyOfCrimeExtensum(Swedish).sh"
```

Citattecknen behövs eftersom skalet annars tolkar parenteserna som specialtecken.

- Spelet kräver Java. Det är kompilerat för Java 7 och testat med OpenJDK 11.
- Startskriptet byter till mappen där det ligger och kör
  `java -Xms256M -Xmx256M -jar TheAbbeyOfCrimeExtensum.jar de`. Argumentet `de` väljer
  språkplatsen som svenskan använder. För Windows finns `TheAbbeyOfCrimeExtensum(Swedish).bat`.
- Originalets startskript för spanska, engelska, franska, italienska och polska ligger kvar
  oförändrade i `game/`. De fungerar som förut, och på de språken ser spelet ut precis som
  originalet.
- Med Java 11 visar spelet två ofarliga felmeddelanden (stack traces) i terminalen när det startar.
  Det gör originalet också. Med Java 8 visas inga.
- Sparade spel hamnar i `game/savedata.bin`.

## Styrning

Här är styrningen i korthet, enligt den engelska manualen. Tipsen längst ner kommer från projektets
egna testkörningar.

**Allmänt**

| Tangent | Funktion |
|---|---|
| F1 | Växla mellan helskärm och fönster |
| Esc | Paus och meny |
| Enter | Visa kartan (när den finns) |
| Mellanslag | Visa nästa replik direkt (bara i mellansekvenser; annars går samtalet vidare av sig självt) |

**Klassiskt läge** (”KLASSISK STYRNING”, förvalt)

| Tangent | Funktion |
|---|---|
| Vänster-/högerpil | Vänd dig åt vänster/höger |
| Uppåtpil | Gå framåt |
| Nedåtpil | Styr Adso |

**Riktningsläge** (”RIKTNINGSSTYRNING”)

| Tangent/mus | Funktion |
|---|---|
| Piltangenterna eller W | Gå åt det håll du väljer |
| Högerklick | Vänd dig mot muspekaren |
| Vänsterklick | Gå mot muspekaren |
| Mellanslag | Styr Adso |

Styrläget byter du i pausmenyn (Esc).

**Adso.** Du spelar Vilhelm, men du kan också styra hans novis Adso, fast bara när Adso är i samma
bild som Vilhelm. Så länge du håller ned nedåtpilen (mellanslag i riktningsläget) går Adso åt det
håll som Vilhelm är vänd åt, om inget står i vägen.

**Föremål.** Du plockar upp ett föremål genom att ställa dig framför det. Vissa föremål måste
Vilhelm ta, andra Adso.

**Tips.** Mellanslag eller Enter hoppar över introbilderna. Med mellanslag kan du också hoppa över
inledningspergamentet medan texten skrivs fram. När ett pergament är färdigskrivet väntar spelet
tills du trycker på mellanslag. Slutpergamentet går inte att hoppa över.

## Vad som är översatt

- **Dialog, menyer och statusfält:** alla repliker, pausmenyn, timmarna (NATT, PRIM, TERS, SEXT,
  NON, VESPER, NATTBÖN) och ordet ”Dag” i statusfältet, sparplatsernas etiketter (”DAG 3
  NATTBÖN”, ”TOM”) och slutskärmen (”DU HAR LÖST … PROCENT AV GÅTAN”, ”TRYCK PÅ MELLANSLAG”).
- **Båda pergamenten:** inlednings- och slutpergamentet. Pergamentens handskrift har fått nya
  bokstäver: å, ä och ö (och Å, Ä och Ö).
- **Introbilderna:** raden ”LADDAR: var god vänta...” på laddningsskärmen, de fyra bilderna med
  förtexter och ”Tryck för att starta”. Förtexterna lyder tillsammans: *Manuel Pazos och Daniel
  Celemín · efter spelet av Paco Menéndez och Juan Delcán · efter romanen ”Rosens namn” av Umberto
  Eco · och Jean-Jacques Annauds film med samma namn.*
- **Nya tecken i spelets typsnitt:** ett Å i meddelandetypsnittet och ett Ö för NATTBÖN i
  statusfältet. Spelets teckenrutin har fått en liten patch, så att den ritar Å som ett A med en
  ring över (DECISIONS D5). Ö ligger i en tidigare tom ruta i typsnittet (DECISIONS D8). Inga
  befintliga tecken har ändrats, och de andra språken ritas pixel för pixel som förut.

## Vad som inte är översatt, och varför

- **Logotypen och titelbilden på laddningsskärmen** behåller det spanska namnet ”La Abadía del
  Crimen Extensum”. Det är spelets egentliga namn, så ingen titelgrafik behövde ritas om.
  Språkplatsen ”de” hade från början en engelsk titelbild. Hade den fått stå kvar bredvid den
  spanska logotypen, skulle spelet ha visat två olika titlar (DECISIONS D3a).
- **Fönstertiteln** är också ”La Abadía del Crimen Extensum”, av samma skäl (DECISIONS D6).
- **Rösterna:** spelet har inget tal. Varje figur har ett eget ordlöst mummel: för varje bokstav
  som skrivs fram spelas ett av tre korta ljud, slumpvis valt (i jarfilen:
  `res/sound/voces/vozguillermo.ogg` och så vidare). Ljuden är desamma på alla språk.
- **Latin** förblir latin, som i originalet, till exempel OBSEQUIUM i statusfältet och de
  latinska citaten i dialogerna.
- **München** har blivit ”Bayern” i slutpergamentet (”När vi kom till Bayern”), eftersom
  pergamentens handskrift saknar ü. München ligger i Bayern, så det stämmer ändå (DECISIONS D10).
- **Två felrutor** visas bara om sparfilen är skadad eller inte går att skriva till (”Los datos
  guardados están corruptos.” och ”Error al grabar el fichero.”, med rubriken ”ERROR GRAVE”).
  Redan i originalet står de på spanska oavsett språk, så de har lämnats orörda.
- **Manualerna** på spanska, engelska, franska, italienska och polska i `game/` är originalets
  PDF-filer. Den svenska manualen är en egen översättning av den engelska och ligger bredvid dem som
  `User's manual (Swedish).pdf` (se *Användarmanualen* nedan).

## Användarmanualen

Den svenska manualen, `manual/Användarmanual.pdf` (och `manual/Användarmanual.docx`), är översatt
från den engelska manualen. Den använder spelets egna ord: menyraderna och timmarna läses direkt ur
`translation/strings_sv.tsv`, och prologsidan är inledningspergamentet. Översättningen är inofficiell
och för privat bruk, och det står i manualen.

Bygget kopierar PDF:en till `game/` som `User's manual (Swedish).pdf`. Själva manualen bygger du om
med `uv run tools/manual/build_manual.py`. Båda filerna innehåller bilder ur spelet och hålls
utanför git (DECISIONS D14, D15).

## Ändra och bygga om

Texten står i `translation/strings_sv.tsv` (alla strängar i spelet, i kolumnen `sv`) och i
`translation/pergamino1_sv.txt` och `translation/pergamino2_sv.txt` (inlednings- och
slutpergamentet). När du har ändrat något bygger du om `game/` med:

```sh
uv run tools/build.py
```

Det behövs uv, JDK 11, JDK 8, ASM-jarfilerna i `tools/` och originalspelet i `original/`. Allt
detta beskrivs i `tools/README_tools.md`. Bygget kontrollerar översättningen och de patchade
klasserna innan det skriver något. Om en kontroll misslyckas lämnas `game/` orörd. Annars skapas
mappen på nytt (`savedata.bin` behålls), så lägg inga egna filer där.

Reglerna för strängar och pergament, kontrollkommandona och testriggen som kör spelet osynligt
beskrivs i `CLAUDE.md`.

## Var finns vad

| Sökväg | Innehåll |
|---|---|
| `game/` | Det färdiga spelet (byggs av `build.py`) |
| `translation/` | Strängarna, pergamenten och ordlistan i maskinläsbar form |
| `assets_sv/` | De nya tecknen och de handritade bokstäverna till bilderna |
| `manual/` | Den svenska användarmanualen, `.pdf` och `.docx` |
| `docs/FORMAT.md` | Spelets dataformat och gränser, som bygget vilar på |
| `docs/GLOSSARY.md` | Ordlista och stilguide: tilltal, namn, timmar, fasta fraser |
| `docs/DECISIONS.md` | Beslut som ändrar eller kompletterar den ursprungliga planen |
| `docs/TRANSLATION_REVIEW.md` | Protokoll över granskningen av varje sträng och båda pergamenten: redaktörsläsning, blind återöversättning och konsekvensläsning, med alla avvisade förslag och skälen |
| `screenshots/strings/de/` | Kontaktkartor med alla svenska strängar, ritade med spelets egen kod (sammanfattning i `report.txt`) |
| `screenshots/runtime_sv/` | Skärmbilder från körningar av det svenska spelet; `INDEX.md` beskriver vad som kontrollerades |
| `screenshots/runtime_regress/` | Spanska, engelska och polska i det patchade spelet, jämförda med originalet (`INDEX.md`) |
| `screenshots/pristine_en/`, `screenshots/pristine_es/` | Referensbilder från originalspelet |
| `tools/` | Bygget, kontrollerna och testriggen; se `tools/README_tools.md` |
| `CLAUDE.md` | Hur man arbetar med projektet: regler, kontroller och testriggen |
| `implementation_prompt.md` | Den ursprungliga beställningen |
| `work/` | Mellanresultat och rådata från testerna, som INDEX-filerna och `docs/FORMAT.md` hänvisar till. Bygget klarar sig utan mappen, men behåll den (DECISIONS D14) |

Dokumenten i `docs/`, `tools/README_tools.md` och `CLAUDE.md` är skrivna på engelska. Bilderna i
`screenshots/` och `assets_sv/res/` bygger på originalets grafik och hålls utanför git (DECISIONS
D14).
