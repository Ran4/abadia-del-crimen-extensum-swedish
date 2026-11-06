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
- **Fönstertiteln** är också ”La Abadía del Crimen Extensum”, av samma skäl (DECISIONS D6). Titeln
  står i raden `E.h[4]` i `translation/strings_sv.tsv`. Den som vill ändra den måste först lägga
  till ett ord ur den nya titeln i `TITLE_RE` i `tools/run_headless.sh`, `tools/headless_lib.sh`
  och `tools/lint_strings.py`. Annars hittar testriggen inte fönstret, och lintern fortsätter att
  varna.
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

```sh
uv run tools/manual/build_manual.py
```

skriver `.docx`-filen, gör PDF:en med `soffice --headless --convert-to pdf` (inget fönster öppnas)
och lägger sedan till PDF:ens länkar, som LibreOffice tappar vid exporten. Skriptet kontrollerar att
varje sida har sin länk och att rubrikerna går att söka på. `--no-pdf` skriver bara `.docx`-filen.
Det behövs LibreOffice, typsnittet Junicode och `pdfimages`/`pdftotext` (poppler-utils). Bilderna är
svenska spelbilder ur `screenshots/runtime_sv/`; motivet till avsnittet Menyn tas fram med
`tools/drivers/manual_menu.sh`.

PDF:en är referensen för hur manualen ska se ut. `.docx`-filen bäddar in Junicode, så att den ser
likadan ut i Word även på en dator som saknar typsnittet. Nästa `uv run tools/build.py` kopierar
PDF:en till `game/` som `User's manual (Swedish).pdf`. Båda filerna innehåller bilder ur spelet och
hålls utanför git (DECISIONS D14, D15).

## Bygga om spelet

När du har ändrat något i `translation/` (eller i `assets_sv/` eller `tools/images/`) bygger du om
`game/` med:

```sh
uv run tools/build.py
```

**Det här behövs:**

- `uv`. All Pythonkod körs med uv, och skripten anger själva sina beroenden.
- JDK 11 (`java`, `javac` och `javap` i PATH) och JDK 8 i `/usr/lib/jvm/java-8-openjdk-amd64`.
  JDK 8 används för verifieringen, och bygget misslyckas utan den.
- ASM-jarfilerna i `tools/` (`asm-9.7.1.jar`, `asm-tree-9.7.1.jar`, `asm-analysis-9.7.1.jar`,
  `asm-util-9.7.1.jar`) från Maven Central. Adresser och kontrollsummor finns i
  `tools/README_tools.md`.
- `original/` med den orörda nedladdningen av originalspelet (jarfilen, startskripten och
  PDF-filerna). Bygget läser därifrån men skriver aldrig dit.

**Bygget kontrollerar bland annat:**

- att originalets jarfil har rätt SHA-256-summa (annars får du en varning);
- att strängarna klarar lintern, innan något byggs (bygget avbryts vid fel);
- att den genererade textklassen `abadia/k.class` har exakt samma fält, flaggor och klassversion
  som originalet;
- att patcharna i `j.class` (Å), `w.class` (”DAG”, ”TOM”) och `E.class` (fönstertiteln) inte
  ändrar något annat;
- att varje pergamentrad ryms på bredden;
- att de sju svenska bilderna har rätt storlek och format (de görs om vid varje körning, från
  originalet och `assets_sv/`, utom med `--no-image-rebuild`);
- att de patchade klasserna går att ladda och länka med `-Xverify:all` på både JDK 11 och JDK 8;
- att strängarna i den färdiga jarfilen stämmer med TSV-filen.

Resultatet är `game/` och `work/build/manifest.json`. Samma indata ger byte för byte samma
utdata. Om en kontroll misslyckas lämnas `game/` orörd. Vid ett lyckat bygge raderas mappen och
skapas på nytt, men `savedata.bin` behålls. Bygget vägrar att köras om `game/` innehåller något
annat än byggets egna filer och `savedata.bin`, så lägg inga egna filer där. Alla flaggor till
`build.py` beskrivs i `tools/README_tools.md`.

### Källfilerna

| Fil | Innehåll |
|---|---|
| `translation/strings_sv.tsv` | Alla strängar i spelet; den svenska texten står i kolumnen `sv` |
| `translation/pergamino1_sv.txt`, `translation/pergamino2_sv.txt` | Inlednings- och slutpergamentet (UTF-8, en textrad per pergamentrad) |
| `assets_sv/glyphs/` | De nya tecknen: `fuente_add.json` (spelets typsnitt) och `letras_add.json` (pergamentens handskrift) |
| `assets_sv/image_src/` | Handritade bokstäver till bilderna, som textfiler |
| `tools/images/` | Byggskripten för de sju svenska bilderna (körs av `build.py`) |
| `translation/glossary.tsv` | Ordlistan i maskinläsbar form, för `check_glossary.py` (läses inte av bygget) |

`assets_sv/res/` skrivs över vid varje vanligt bygge och ska därför inte redigeras för hand.

**Att tänka på** (detaljerna finns i `docs/GLOSSARY.md` och i `docs/FORMAT.md`: §1.4 och §1.13 för
strängarna, §4.5 och §4.7 för pergamenten):

- Strängarna skrivs med VERSALER (utom fönstertiteln `E.h[4]`).
- Talarkoderna `@N` ska stå exakt som i den spanska texten.
- I en replik ger `_` ny sida och `*` ny rad. Mellanslag räknas in i längden.
- Håll dig inom gränsen i kolumnen `max_len`. För några repliker gäller i stället en tidsgräns i tick,
  som lintern kontrollerar (DECISIONS D12).
- Rad 2 på varje sida i en replik får ha högst 34 synliga tecken, eftersom den blinkande
  ▶▶-markören täcker det 35:e (DECISIONS D13). Lintern kontrollerar inte detta. Kör
  `render_strings.py` och se till att `screenshots/strings/de/report.txt` inte har någon varning
  om ”continue-marker”.
- Pergamenten klarar bara a–z och A–Z, å ä ö Å Ä Ö, några accentbokstäver (bland annat é, í och ñ,
  som eftertexterna behöver), mellanslag, `, - . : ;` och siffrorna 1, 2, 3 och 7. Skriv tal med
  bokstäver.
- Pergamentraderna bryts för hand, eftersom spelet inte radbryter själv, och en sida rymmer 11
  rader. Bläcket får nå högst till x = 244; mät raderna med `letras.py check` (se nedan).

### Kontrollkommandon

```sh
uv run tools/lint_strings.py      # strängreglerna, utan att bygga
uv run tools/check_glossary.py    # strängar och pergament mot translation/glossary.tsv
uv run tools/render_strings.py    # ritar alla svenska strängar ur game/ med spelets egen kod
                                  # till screenshots/strings/de/; misslyckas om ett tecken saknas
uv run tools/regress.py           # spanska, engelska, franska, italienska och polska: originalet
                                  # och det patchade spelet ska vara pixelidentiska
```

`render_strings.py` och `regress.py` läser det byggda spelet, så kör dem efter `build.py`.
`render_strings.py` säger också till om strängfilen eller pergamentfilerna har ändrats efter
bygget. Ändrade tecken eller bilder märker den inte, så bygg alltid om först.

Två hjälpmedel:

```sh
uv run tools/translate_tool.py pages "@0 TEXT"     # hur spelet delar upp en replik på sidor,
                                                   # och hur många tick den tar
uv run tools/letras.py check translation/pergamino1_sv.txt --text \
    --letras game/TheAbbeyOfCrimeExtensum.jar      # mäter pergamentraderna
```

## Var finns vad

| Sökväg | Innehåll |
|---|---|
| `game/` | Det färdiga spelet (byggs av `build.py`) |
| `manual/` | Den svenska användarmanualen, `.pdf` och `.docx` (byggs av `tools/manual/build_manual.py`) |
| `docs/FORMAT.md` | Spelets dataformat och gränser, som bygget vilar på |
| `docs/GLOSSARY.md` | Ordlista och stilguide: tilltal, namn, timmar, fasta fraser |
| `docs/DECISIONS.md` | Beslut som ändrar eller kompletterar den ursprungliga planen |
| `docs/TRANSLATION_REVIEW.md` | Protokoll över granskningen: redaktörsläsning, blind återöversättning och konsekvensläsning för varje sträng och båda pergamenten, med alla avvisade förslag och skälen (genereras av `tools/review_record.py`) |
| `screenshots/strings/de/` | Kontaktkartor med alla svenska strängar, ritade med spelets egen kod (sammanfattning i `report.txt`) |
| `screenshots/runtime_sv/` | Skärmbilder från körningar av det svenska spelet; `INDEX.md` beskriver vad som kontrollerades |
| `screenshots/runtime_regress/` | Spanska, engelska och polska i det patchade spelet, jämförda med originalet (`INDEX.md`) |
| `screenshots/pristine_en/`, `screenshots/pristine_es/` | Referensbilder från originalspelet |
| `tools/` | Bygget, kontrollerna och testriggen; se `tools/README_tools.md` |
| `implementation_prompt.md` | Den ursprungliga beställningen |
| `work/` | Mellanresultat, data som `translate_tool.py` läser och rådata från testerna (körloggar, skärmbilder) som INDEX-filerna och `docs/FORMAT.md` hänvisar till. Bygget klarar sig utan mappen, men behåll den (DECISIONS D14) |

Dokumenten i `docs/` och `tools/README_tools.md` är skrivna på engelska. Bilderna i `screenshots/`
och `assets_sv/res/` bygger på originalets grafik och hålls utanför git (DECISIONS D14).

## Testriggen

`tools/run_headless.sh` kör spelet osynligt och tyst: på en egen Xvfb-skärm (aldrig på din) och
med ljudet skickat till en stum ljudutgång. Styrskripten i `tools/drivers/` trycker på tangenter
och tar skärmbilder. Ett exempel är en rundtur från introt via början av inledningspergamentet,
statusfältet och pausmenyn fram till slutskärmen (tar ungefär elva minuter):

```sh
SHOT_DIR=work/runs/min-tur tools/run_headless.sh game de tools/drivers/pristine_tour.sh
```

Riggen behöver `bwrap`, `xdotool`, `xwd`, `xwininfo`, ImageMagick (`convert` och `identify`),
`pactl`, `parec` och Xvfb uppackad i `tools/xvfb-root/`. Xvfb packar du upp en gång, utan sudo:

```sh
(cd tools && apt-get download xvfb && dpkg-deb -x xvfb_*.deb xvfb-root)
```
