# Glossary and style guide: Swedish *La Abadía del Crimen Extensum*

Phase B output. Every translator and editor in Phase C, and every checker in Phase E, follows this
file. The machine-readable twin is `translation/glossary.tsv` (same decisions, one row per fixed
term; columns `es en sv kind note`; §11 lists the kinds and the check each gets). If the two ever
disagree, fix both; neither silently wins. Review rounds 1, 2 and 3 are applied; the critic
suggestions taken only in part or not at all are listed with a reason in §12.

Sources used: `work/phaseA/strings_all.json` (all 164 `g` strings read in full, es with en/fr/it
for meaning), `work/phaseA/text.md` §0, §3.5-3.6, §4, §7-§10, `font.md` §3, §5, `parchment.md`
§4, §5, §7, the Spanish parchments `work/jar/res/es/pergamino1|2`, `images.md` §2, §3.8, and
`deslot.md` §1.3. No published Swedish translation of the novel or of the film was consulted.

Notation: `gNN` = message index NN of the `g` table. Speaker ids as in `text.md` §3.6
(0 Guillermo, 1 Adso, 2 Severino, 3 Abad, 4 Malaquías, 5 Berengario, 6 Bernardo Gui, 7 Jorge,
8 Remigio, 10 Salvatore, 11 villager, 12 Ubertino, 13 Nicola). In the tables and in the TSV,
` / ` separates alternative forms for different contexts (e.g. `SKYNDA DIG / SKYNDA ER`); it is
never part of a game string. Swedish examples are written in UPPERCASE exactly as they go into
the game; parchment and image text is mixed case.

## 0. The decisions at a glance

| topic | decision |
|---|---|
| polite address | **NI / ER** (vos and vosotros). Familiar **DU / DIG / DIN** (tú). One fixed choice per ordered speaker pair (§2), plus two documented switches (g75, g128). No archaic **I / EDER**. |
| key titles | FRAY GUILLERMO → **BRODER VILHELM**; HERMANO → **BRODER**; HERMANOS → **BRÖDER**; MAESTRO → **MÄSTARE**; VENERABLE → **ÄREVÖRDIGE** (NI pairs only); INSENSATO → **DIN DÅRE**; EL ABAD → **ABBOTEN** |
| names | **VILHELM, ADSO, SEVERINUS, BERENGAR, MALACHIAS, VENANTIUS, ADELMO, JORGE (AV BURGOS), BERNARDO GUI, REMIGIO, SALVATORE, UBERTINO, NICOLA** |
| places | ABADÍA → **KLOSTRET** (a host's *esta abadía* → **VÅRT KLOSTER**); EDIFICIO → **BYGGNADEN**; SCRIPTORIUM → **SCRIPTORIET**; CLAUSTRO → **KORSGÅNGEN**; FINIS AFRICAE stays |
| HUD hours (7 cells) | `' NATT  '` `' PRIM  '` `' TERS  '` `' SEXT  '` `'  NON  '` `'VESPER '` `'NATTBÖN'` (Ö = one new precomposed HUD glyph) |
| day | HUD image **Dag**; save prefix **`DAG `**; empty slot **TOM** |
| menu | FORTSÄTT · SPARA SPEL · LADDA SPEL · `LJUD: ` · `MUSIK: ` · *(empty)* · `HELSKÄRM: ` · `VISA INDIKATORER: ` · STARTA OM · AVSLUTA; on/off **PÅ/AV**; control values **KLASSISK STYRNING / RIKTNINGSSTYRNING** |
| end screen | **DU HAR LÖST / 42 PROCENT / AV GÅTAN**, **TRYCK PÅ MELLANSLAG** |
| window title | **La Abadía del Crimen Extensum** (matches the reused Spanish logo) |
| novel title | **Rosens namn** |
| Latin | stays Latin; three spellings normalised to Eco/Vulgate: PENITENZIAGITE, MAGNIFICENTISSIMO, SUPER THRONOS |
| QUATUOR (g127) | kept; Swedish says **DEN FÖRSTA OCH SJUNDE BOKSTAVEN I QUATUOR** (= Q and R) |

---

## 1. Register and style

### 1.1 The voice

Natural, idiomatic modern Swedish grammar, with a slightly raised vocabulary and a handful of
deliberate old-fashioned forms (list in §1.3). The model is a good Swedish translation of a
historical novel: it reads easily, never sounds like a modern office or a costume drama, and
never sounds translated. When in doubt, choose the plainer word, then check that it does not
sound modern (no SNÄLLA, OKEJ, KILLE, FIXA).

Each speaker keeps a recognisable voice:

| speaker | voice in Swedish |
|---|---|
| Guillermo (0) | dry, precise, ironic, kind to Adso; short declaratives, occasional wit (g62, g163) |
| Adso (1) | young, earnest, respectful (NI to his master), simple sentences |
| Abad (3) | formal, politic, a little pompous; MÅ only in his two fixed permissions (NI MÅ ÄTA, NI MÅ GÅ TILL ERA CELLER), a plain yes with FÅ (`DET FÅR NI.`, g1); commands with imperatives |
| Jorge (7) | solemn, biblical cadence, short absolute statements; TY allowed |
| Ubertino (12) | ecstatic, prophetic, repetitions kept (DÖDA, ALLTFÖR MÅNGA DÖDA...) |
| Bernardo Gui (6) | cold, legal, clipped; DU to the accused, NI to Guillermo |
| Severino (2) | calm, learned, helpful |
| Berengario (5) | nervous, evasive, then pleading |
| Remigio (8) | courteous host on day 1, servile and frightened at the trial |
| Nicola (13) | friendly craftsman, plain speech |
| Malaquías (4) | curt guardian |
| Salvatore (10) | pidgin, see §1.10 |

### 1.2 Word order and sentence building

- Swedish main clauses are verb-second; Spanish adverb-first sentences must not keep the Spanish
  order. Bad `NU JAG MÅSTE GÅ.` Good `NU MÅSTE JAG GÅ.` (g5 AHORA DEBO IRME)
- Negation and sentence adverbs go before the finite verb in subordinate clauses. Bad
  `OM HAN HADE INTE TAGIT SITT LIV` Good `OM HAN INTE HADE TAGIT SITT LIV`.
- Spanish drops subjects; Swedish never does. `LLEGÓ HACE UNOS DÍAS` → `HAN KOM FÖR NÅGRA DAGAR SEDAN.`
- Do not copy Spanish gerunds. Bad `HAN TILLBRINGAR SIN TID BEDJANDE OCH MEDITERANDE.`
  Good `HAN TILLBRINGAR DET MESTA AV SIN TID I BÖN OCH BETRAKTELSE.` (g1)
- Spanish impersonal *se* becomes an s-passive or MAN, whichever sounds natural.
  `AQUÍ SE PREPARA LA COMIDA` → `HÄR LAGAS MATEN ÅT ALLA MUNKARNA.` (g58)
- Spanish `ES ... QUE` clefts and `LO QUE` relatives: rebuild, do not calque.
  Bad `DET ÄR I KYRKAN SOM NI KOMMER ATT HITTA HONOM.` Good `NI HITTAR HONOM I KYRKAN.`
- Demonstratives: prefer **DENNA / DETTA / DESSA** over DEN HÄR / DET HÄR in all speech
  (`DETTA ÄR REFEKTORIET.`, `DENNA SPEGEL`). After DENNA / DETTA / DESSA the noun stays
  **indefinite**: `DENNA ELDSTAD`, never `DENNA ELDSTADEN`; `DESSA ÅNGOR`. For a male person
  use **DENNE** (the weak masculine of §1.3): g68 ESTE NO → `MEN INTE DENNE`, g120 ¿QUIÉN HA
  MATADO A ESTE? → `VEM HAR DÖDAT DENNE?`. Introducing someone stays neuter: `DETTA ÄR VILHELM.` (g59)
- Use Swedish modal particles where Spanish uses tags or intonation: VÄL, JU, NOG, ÄNDÅ.
  `YA CONOZCO ESTA PARAFERNALIA. TAMBIÉN VOS LA CONOCÉIS, ¿VERDAD, FRAY GUILLERMO?` →
  `JAG KÄNNER IGEN DENNA ATTIRALJ. NI KÄNNER VÄL OCKSÅ IGEN DEN, BRODER VILHELM?` (g110). The
  pair is fixed together: DEN agrees with ATTIRALJ (common gender). Never `PARAFERNALIA` (rare and
  jocular in Swedish); `DESSA TING` or `DETTA` would break the agreement with DEN (§7.1).

### 1.3 Old-fashioned touches: the closed list

Allowed (and only these):

| form | where | example |
|---|---|---|
| weak masculine -E on adjectives for a male referent or in address | everyone | `KÄRE ADSO`, `DEN UNGE OCH VACKRE ADELMO`, `VACKRE MÄSTARE`, `DEN HELIGE GREGORIUS`, `ÄREVÖRDIGE BRODER`, `DEN ÄREVÖRDIGE JORGE`, `DEN BLINDE` |
| MÅ for permission and wishes | only the abbot's two fixed permission formulas and fixed wishes | `NI MÅ ÄTA, BRÖDER.` `NI MÅ GÅ TILL ERA CELLER.` `GUD FÖRBJUDE`. Not for a short yes: g1 PODRÉIS → `DET FÅR NI.` (never `DET MÅ NI`, which is not Swedish) |
| LÅTOM OSS | only the liturgical OREMOS (g21) | `LÅTOM OSS BEDJA.` (every other *vamos/veamos* is `LÅT OSS ...`) |
| VORE | conditional of VARA, elevated speakers | `DET VORE EN SYND ATT ...` |
| TY ("for") | Jorge, Ubertino, the abbot, and the parchments; at most once per message | `TY FÖRSYNEN VILL INTE ATT ...` (g62); everyone else: FÖR / EFTERSOM |
| MÅHÄNDA | Jorge and Ubertino only; everybody else KANSKE | |
| GOD AFTON | greeting at night | `GOD AFTON, ÄREVÖRDIGE JORGE.` (g128) |

Not allowed anywhere: plural verb forms (`VI ÄRO`, `VORO`, `HAVA`, `I HAVEN`, `DE GINGO`), the
pronouns `I` and `EDER`, `EJ`, `ICKE`, `ALLENAST`, `EMEDAN`, `EHURU`, `OCK`, `VARDA`, old
spellings (`HVAD`, `HAFVA`), and `SKALL`. Use **SKA**. (VORE, the conditional, is allowed; VORO,
the old plural past, is not.)

### 1.4 Modal verbs

| Spanish | Swedish | example |
|---|---|---|
| DEBER (obligation), TENER QUE, HABER DE | MÅSTE | `NI MÅSTE LÄMNA BYGGNADEN, BRODER.` (g7) |
| DEBERÍA / DEBERÍAMOS | BORDE | `ADSO, VI BORDE VILA.` (g65) |
| PODER = be allowed | FÅ | `NI FÅR INTE GÅ UPP TILL BIBLIOTEKET.` (g43) |
| PODER = be able | KUNNA | `KAN NI VISA MIG ...` (g64) |
| PODÉIS in the abbot's two fixed permissions | MÅ | `NI MÅ ÄTA, BRÖDER.` (g20, g23; `NI MÅ ÄTA.` g59, g96), `NI MÅ GÅ TILL ERA CELLER.` (g11); nowhere else |
| PODRÉIS (a short granting reply) | FÅ | g1 `FÅR JAG STÄLLA FRÅGOR TILL DE ANDRA MUNKARNA?@3 DET FÅR NI.` |
| future of intent or command | SKA | `I MORGON SKA NI LÄMNA KLOSTRET.` (g28) |
| future as prediction | KOMMER ATT | `NÄSTA LIK KOMMER ATT HITTAS I VATTEN.` (g85) |

### 1.5 Address in one line

Polite *vos* and plural *vosotros* → NI (object ER, possessive ER/ERT/ERA). Familiar *tú* → DU.
With singular polite NI the predicative adjective stays **singular**: `NI ÄR VÄLKOMMEN, BRODER.`,
`VAR VÄLKOMMEN, ÄREVÖRDIGE BRODER` (g42). With plural NI (Guillermo and Adso together, the monks)
it is plural: `NI ÄR VÄLKOMNA`. The full matrix is §2.
The old courtesy capital (`Ni`) is irrelevant: all game text is uppercase.

### 1.6 Exclamations and oaths (fixed)

"Avoid" = not chosen here. Only the forms marked † are errors in every context; those are also
TSV `forbidden` rows (§10).

| Spanish | Swedish | avoid |
|---|---|---|
| ¡DIOS SANTO! | HERRE GUD! | HERREGUD † (colloquial), HELIGA GUD † |
| DIOS NO LO QUIERA | GUD FÖRBJUDE | |
| ¡JESÚS! (Adso, g126) | HERRE JESUS! | bare JESUS! (reads as a mild modern curse) |
| OH CIELOS (g163) | MILDA MAKTER | HIMMEL! as an exclamation (the noun HIMMEL is of course fine) |
| ¡LO JURO! (g113) | DET SVÄR JAG! | a bare JAG SVÄR! (modern ring, close to English "I swear!", and SVÄRA also means "to curse"); in an oath Swedish puts the object first |
| OS JURO QUE + clause (g118) | JAG SVÄR ATT + clause | JAG SVÄR ER † (hispanicism: SVÄRA takes no 'to you') |
| ¡NO JURES! (g118) | SVÄR INTE! | (biblical, Matt 5:34) |
| ¡BASTA! (Jorge, g61, g62) | NOG NU! | a bare NOG! (literary, close to German *Genug!*); DET RÄCKER! (fine Swedish, but one form) |
| ¡SILENCIO! | TYSTNAD! | |
| ¡CUIDADO! | g78 (flame too close to the parchment): FÖRSIKTIGT! · g133 (sudden danger): SE UPP, ADSO! | AKTA DIG! (idiomatic and old-fashioned, but not chosen) |
| CALLA, INSENSATO (g110) | TIG, DIN DÅRE... | a bare `DÅRE` as vocative; HÅLL KÄFTEN † |
| ¿... INSENSATO? (g118, Remigio → Salvatore) | `VAD HAR DU SAGT TILL DEM, DIN DÅRE?` | a bare `DÅRE` as vocative |
| AVE MARÍA PURÍSIMA | AVE MARIA PURISSIMA (Latin) | |
| JAJAJAJA / JIJIJI / JEJEJE | HAHAHAHA / HIHIHI / HEHEHE (same number of syllables: g126's five-syllable JAJAJAJAJA → HAHAHAHAHA) | |
| ¡AAARGH! · GRRR... · HMMM... · AH... | AAARGH! · GRRR... · HMMM... · AH... (unchanged) | |
| ¡POR DIOS! (does not occur) | VID GUD! | |

A direct-address insult always takes **DIN** (or the biblical DU): `DIN DÅRE`, as in `DU DÅRE`
(Luke 12:20). A bare noun as vocative (`TIG, DÅRE`) reads translated.

### 1.7 Page breaks and other markers

The engine rules are in `text.md` §0 and §3.5. Translation rules on top of them:

1. Keep every `@N` speaker marker, in the same order, with a space after it. The string starts
   with `@N `. A mid-string marker may stay glued to the previous punctuation as in Spanish
   (`...SÅ.@0 JAG FÖRSTÅR`).
2. `_` (end of page) is a layout choice; the count may differ from Spanish. Put each `_` at a
   **sentence or clause boundary** in the Swedish. If Swedish reorders a sentence across a
   Spanish `_`, move the `_`; never leave half a Swedish clause on one page because the Spanish
   page ended there. Exception: dramatic breaks the Spanish uses on purpose (g78 `NECESITO MÁS
   LUZ. ACERCA LA LÁMPARA... _ ¡CUIDADO!`, g163 `_ QUÉ SEGURA. _ QUÉ TRANQUILA. _ Y QUÉ INSULSA.`):
   keep them one-for-one.
3. A page is 2 lines × 35 glyphs. If a Swedish segment between two `_` runs a few words over
   two lines, prefer adding a `_` at the nearest sentence boundary to letting the automatic
   page cut fall mid-sentence.
4. Both `X._ Y` (glued) and `X. _ Y` are fine; follow the Spanish spacing of that message.
5. `*` (forced line break) only where Spanish has one (g53, g62, g118; and unused g48) and only
   if the Swedish line still makes sense broken there; otherwise drop it or replace it with `_`.
   In g48 it stays (`@1 J : JA * N : NEJ`).
6. The 8-space pauses in g126 (`@1 EN DJÄVUL!        @0 ...`) and g138
   (`@0 AVE MARIA PURISSIMA...        _ ...`) are timing: keep exactly 8 spaces.
7. No trailing space at the end of a string. No token longer than 35 characters.
8. g92 `@1 ...` stays `@1 ...`.
9. **Unused messages** (0, 2, 3, 13, 16, 25-30, 32, 38, 40-42, 44-48; `text.md` §2) are
   translated too, last and with the same rules, so the table is complete and nothing Spanish
   is left in the Swedish slot; they have no effect in game and no length cap. Keep their marker
   layout exactly as in Spanish: g2, g3, g45 and g46 have **no leading `@`** and must not get
   one; g48 keeps its `*`. Phase E checks their markers, their charset and the glossary rows
   (phrase and forbidden, like any other message, so §7 lists unused indices where a phrase
   occurs); it does not check their length.

### 1.8 Punctuation in UPPERCASE text

- No `¿` and no `¡`, ever. `?` and `!` only at the end of the sentence. `?!` is allowed where
  Spanish has `¡¿...?!` (g99 `NU?!`, g118). No space before `?`, `!`, `:` or `;`.
- **Colon** introduces direct speech, quoted words and explanations, because quotation marks
  cannot be drawn: `HAN SADE: JAG ÄR FÖRDÖMD, VACKRE MÄSTARE.` (g75). Titles of works stand
  bare: `DET ÄR COENA CYPRIANI.`
- **Semicolon**: allowed sparingly where Spanish has one.
- **Dash**: none as punctuation. The en/em dash cannot be drawn and a spaced hyphen looks wrong in
  this font; use a comma, colon, full stop or `...` instead. The hyphen `-` only inside a
  word or name (`JEAN-JACQUES`, none currently needed in `g`).
- **Ellipsis**: three full stops `...`, no space before; keep Spanish ellipses (they time the
  speech too).
- **Apostrophe**: do not use (no genitive apostrophe, no elision).
- Not drawable, never use: `" ( ) / + & # [ ] * % _` as characters, lowercase letters.
- Comma after the vocative and around it: `TACK, BRODER.` `KOM HIT, BRODER VILHELM.` Swedish
  comma rules otherwise (no comma before ATT-clauses; comma between two main clauses).
- Numbers are written as words (`SEX DAGAR`, `TUSEN SKORPIONERS KRAFT`), as in Spanish.
- Drawable accented letters for Swedish: Å Ä Ö (Å after the font patch) and É (`IDÉ`,
  `AVILÉS`). Spanish names keep their accent only where it is drawable and the name is a real
  person's or an in-joke (`AVILÉS`). Do not add accents that Swedish does not write
  (`ARISTOTELES`, not `ARISTÓTELES`).

### 1.9 Length

- Aim at **≤ +12 %** characters over Spanish, averaged over all messages (French ships at +12 %).
  Single messages may run longer when Swedish needs it; there is no hard cap except below.
- **Remigio's day-1 walk, g157, g158, g159, g51** (`text.md` §0.14, §5.3). g157 starts when the
  walk to waypoint 8 begins; g158, g159 and g51 start, interrupting the message before, when
  Remigio *arrives* at waypoints 8, 9 and 10 (g51 = the cell). So g157, g158 and g159 are cut
  off by the next arrival, and g51 is itself cut off when the abbot sees Guillermo inside the
  cell (`j.b(1)`, which depends on the player). All four must stay at or under the longest
  shipped version.
- Measure with `uv run work/phaseA/scripts/text_sim.py` (frames = ticks × 3; its `simulate()`
  function takes one string, which is how the trial values below were measured). The caps below are
  **text_sim values**, the numbers that tool prints for the longest shipped language:

  | msg | cap (text_sim ticks × 3) | longest shipped | real-harness value (`text.md` §5.3) | es (text_sim) |
  |---|---|---|---|---|
  | g157 | **≤ 696** | it | 695 | 663 |
  | g158 | **≤ 288** | it | 287 | 279 |
  | g159 | **≤ 633** | fr | 631 | 576 |
  | g51 | **≤ 231** | it | (not measured) | 204 |

  text_sim reads 1-2 frames higher than the harness, so its cap is the right one for the tool.
- Use the shortest natural wording there (`SÅ ÄR DET.`, `SNART ÄR VI FRAMME.`, `DETTA ÄR ...`).
  **g158 is tight:** `DETTA ÄR KORSGÅNGEN. _ EN STILLA PLATS FÖR VANDRING OCH BETRAKTELSE.`
  measures 264, while `EN STILLA PLATS, SOM GJORD FÖR PROMENADER OCH BETRAKTELSE.` measures
  303 and is over. Trial measurements that fit: g51 `@8 DETTA ÄR ER CELL. ABBOTEN VÄNTAR PÅ ER
  DÄRINNE.` 201; g159 `@8 SENARE FÅR NI TRÄFFA DE ÖVRIGA MUNKARNA I KLOSTRET. _ NU ÄR DE UPPTAGNA
  MED SINA SYSSLOR.@0 JAG FÖRSTÅR.@8 SNART ÄR VI FRAMME.` 531; g157 with `... SÅ VÄCKER SOLEN I
  GRYNINGEN MUNKARNA I CELLERNA.` 672.

### 1.10 Salvatore's pidgin (g54, g100, g101, g118)

The rule, token by token:

- **Keep**, spelled exactly as in §4: every Latin word and formula; his fixed Romance slogans
  (`LA MORTZ EST SUPER NOS`, `LO PAPA SANTO`, `A LIBERAR NOS A MALO`, `DE TUTTE ... PECCATA`,
  `DI VITRIO`); his own pronoun **IO**; his sentence-final copula **EST**; the tag **NO?**.
- **Replace** with broken Swedish every Spanish word, and every Romance word that carries the
  meaning of the sentence (the verbs VINGA, INTENDO, ISPERO; MUY MAGNIFICO; SUYA). A Swedish
  player must be able to follow him as well as a Spanish player can.
- Broken Swedish means: verbs uninflected, in the infinitive (`IO INTE VETA`, `HAN VETA`,
  `SALVATORE HÄMTA`); articles dropped (`FLASKA`, `I FÖRRÅD`); possessive after the noun
  (`INDULGENTIA HANS`); himself in the third person; `EST` as a final copula.
- Never make him sound like a modern immigrant parody; the model is a medieval vagabond who
  mixes every language he has heard.

Fixed lines. Phase C uses them as written; Phase E checks the kept tokens (TSV kind `latin`) and
the Swedish lines (TSV kind `phrase`, note "Salvatore").

| msg | Spanish | keep | replace → Swedish | Swedish line |
|---|---|---|---|---|
| g54 (1) | PENITENCIAGITE! LA MORTZ EST SUPER NOS! RUEGA QUE VINGA LO PAPA SANTO A LIBERAR NOS A MALO DE TUTTE LAS PECCATA! | PENITENZIAGITE (★ §4), LA MORTZ EST SUPER NOS, LO PAPA SANTO, A LIBERAR NOS A MALO, DE, TUTTE, PECCATA | RUEGA QUE → BEDJA ATT (the full infinitive, so the verb is unmistakable and the automatic page cut falls before A LIBERAR, as in es); VINGA → KOMMA, placed after the subject; LAS → dropped | `PENITENZIAGITE! LA MORTZ EST SUPER NOS! BEDJA ATT LO PAPA SANTO KOMMA A LIBERAR NOS A MALO DE TUTTE PECCATA!` |
| g54 (2) | DOMINE FRATE MAGNIFICENTISIMO. JESUS VENTURUS EST ET LOS HOMINES DEBENT FACERE PENITENTIA, NO? | everything (MAGNIFICENTISSIMO ★), NO? | nothing | `DOMINE FRATE MAGNIFICENTISSIMO. JESUS VENTURUS EST ET LOS HOMINES DEBENT FACERE PENITENTIA, NO?` |
| g54 (3) | NO INTENDO. | nothing | NO INTENDO → IO INTE FÖRSTÅ | `IO INTE FÖRSTÅ.` |
| g54 (4) | SALVATORE ESTÚPIDO. IO NO SABE. ESTÚPIDO... | IO | ESTÚPIDO → DUM; NO SABE → INTE VETA | `SALVATORE DUM. IO INTE VETA. DUM...` |
| g100 | ¡SÍ, SÍ! BOTELLA DI VITRIO EN ALMACEN EST. _ SALVATORE TRAE, SALVATORE TRAE. | DI VITRIO, EST | SÍ → JA; BOTELLA → FLASKA; EN → I; ALMACEN → FÖRRÅD; TRAE → HÄMTA | `JA, JA! FLASKA DI VITRIO I FÖRRÅD EST. _ SALVATORE HÄMTA, SALVATORE HÄMTA.` |
| g101 | BOTELLA TUYA EST. | EST | BOTELLA → FLASKA; TUYA → DIN | `FLASKA DIN EST.` |
| g118 | NO SOY HOMO LITERATUS, PECCAVI SINE MALITIA E EL SEÑOR BERNARDO MUY MAGNIFICO EL SABE, ET ISPERO EN LA INDULGENTIA SUYA IN NOMINE PATRE ET FILIO ET SPIRITIS SANCTIS... | HOMO LITERATUS, PECCAVI SINE MALITIA, ET, INDULGENTIA, IN NOMINE PATRE ET FILIO ET SPIRITIS SANCTIS | NO SOY → IO INTE VARA; E → OCH; EL SEÑOR → HERR; MUY MAGNIFICO → MYCKET MAGNIFIK; EL SABE → HAN VETA; ISPERO → IO HOPPAS; EN LA → PÅ; SUYA → HANS, after the noun | `IO INTE VARA HOMO LITERATUS, PECCAVI SINE MALITIA, OCH HERR BERNARDO MYCKET MAGNIFIK HAN VETA, ET IO HOPPAS PÅ INDULGENTIA HANS IN NOMINE PATRE ET FILIO ET SPIRITIS SANCTIS...` |

Why: VINGA (his Italianate *venga*, "may come") is the verb of the sentence and opaque to a
Swedish reader, so it becomes KOMMA; the kept `A LIBERAR NOS A MALO` is the Pater Noster's *libera
nos a malo*, as in Eco. `NO?` stays because the tag is international (en keeps it too). `MAGNIFIK`
is an old Swedish loan ("splendid") and echoes his Latin flattery in g54. `HOPPAS` is the
infinitive; never `HOPPA` (= jump). Lengths stay close to the Spanish (g54 (1) 108 vs 112 glyphs,
g100 74 vs 76, the g118 segment 175 vs 167).

### 1.11 Messages that carry player information

Some lines are the game's only hint for an action. A free rendering must not blur the fact. Keep
each fact below exact, and use the fixed wording where one is given (TSV kind `phrase`, so Phase E
checks it).

| msg | fact the player needs | fixed Swedish wording |
|---|---|---|
| g65 | to sleep, Guillermo must stand next to the bed in the cell | `NÄR JAG VILL SOVA STÄLLER JAG MIG VID SÄNGEN.` (key: `STÄLLER JAG MIG VID SÄNGEN`) |
| g73 | the way into the locked building at night: through the ossuary (BENHUSET); in the chapel (KAPELLET) is an altar carved with a thousand skeletons; press in the eyes of the **fourth** skull **from the left** to open it; a lamp comes from Remigio in the kitchen | `TRYCKA IN ÖGONEN PÅ DEN FJÄRDE DÖSKALLEN FRÅN VÄNSTER` (e.g. `MAN MÅSTE TRYCKA IN ÖGONEN PÅ DEN FJÄRDE DÖSKALLEN FRÅN VÄNSTER FÖR ATT ÖPPNA DET.`) |
| g74 | Remigio leaves a full oil lamp in the same place (the kitchen) every day | no fixed wording; keep `VARJE DAG` and `PÅ SAMMA STÄLLE` |
| g88 | with this parchment and this charcoal Adso can draw a map of the abbey | `RITA EN KARTA ÖVER KLOSTRET` (e.g. `MED DETTA PERGAMENT OCH DETTA RITKOL SKULLE DU KUNNA RITA EN KARTA ÖVER KLOSTRET.`) |
| g99 | Severinus needs hot water for the infusion; the bottle comes from Salvatore | no fixed wording; keep `HETT VATTEN`, `FLASKA` and `SALVATORE` |
| g107 | the cloth soaked in the infusion protects against the library lamps: breathe through it | no fixed wording; keep the cloth (`DENNA DUK`, `DUKEN`) and the instruction to breathe through it |
| g127 | the mirror opens with the 1st and 7th letters of QUATUOR (keys Q and R) | §4: `DEN FÖRSTA OCH SJUNDE BOKSTAVEN I QUATUOR!` |

---

## 2. Address

### 2.1 The rule

- **NI** (object and reflexive ER, possessive ER/ERT/ERA) renders Spanish *vos* (singular
  polite, with plural verb) and *vosotros* (plural). **DU** (DIG, DIN/DITT/DINA) renders *tú*.
- **No archaic I / EDER.** In uppercase text the pronoun `I` is identical to the preposition `I`
  (`I HAR KOMMIT I RÄTT TID`), and it sounds like the 1917 Bible, not like people speaking. NI
  is the established polite pronoun of Swedish historical fiction and keeps the hierarchy of the
  Spanish visible.
- One choice per **ordered pair** of speakers, used in every message. Where the Spanish wavers
  inside a pair, the majority wins and the stray forms are not copied (noted in the table).
  Coldness or intimacy that the Spanish signals by switching is carried by wording instead,
  with **two documented exceptions**, where the Spanish switch is plainly deliberate and Swedish
  DU/NI carries exactly the same nuance:
  1. g75, Guillermo → Berengar: DU throughout, then NI for the cold refusal in his last turn
     (`BE MIG INTE ATT FÖRSEGLA MINA LÄPPAR MED BIKTENS SIGILL. _ GÅ OCH BEKÄNN ERA SYNDER FÖR HERREN.`).
  2. g128, Jorge → Guillermo: `ÄR DET DU, VILHELM? JAG HAR VÄNTAT PÅ DIG.` (intimate, contemptuous),
     then back to NI: `HÄR HAR NI ER BELÖNING.`
  No other switch is copied (e.g. Guillermo's ROBASTE to Jorge in g131 stays NI).
- Imperatives have no pronoun and work for both: `KOM!`, `FÖLJ MIG.`
- **Generic or impersonal** *tú* / *vos* ("you" = anyone) is not address and becomes **MAN**,
  whatever the pair: g42 LLEGA CUANDO MENOS LO ESPERAS → `HAN KOMMER NÄR MAN MINST ANAR DET.`
- The honorific **ÄREVÖRDIGE** goes only with NI. In a DU pair the vocative is BRODER or
  BRODER + name (g87, Guillermo → Nicola: VENERABLE HERMANO → `BRODER NICOLA`), because
  `ÄREVÖRDIGE BRODER ... SKULLE DU ...` sounds like a slip.

### 2.2 The matrix (every pair that occurs)

Evidence = message indices. "Vocative" = how the addressee is called.

| speaker → addressee | Swedish | Spanish evidence | vocative(s) |
|---|---|---|---|
| Abad → Guillermo | **NI** | vos 1, 4, 6, 12, 14, 15, 18, 20, 25, 28, 31, 35, 39, 40, 67, 68, 84, 112, 121, 122 | BRODER (g1), BRODER VILHELM |
| Guillermo → Abad | **NI** | vos 1, 122 | none in Spanish; do not add one |
| Abad → monks (plural) | **NI** | vosotros 11, 20, 23, 59, 96; 22 and 24 have only the vocative HERMANOS | BRÖDER |
| Guillermo → Adso | **DU** | tú throughout (52 ... 163) | ADSO, KÄRE ADSO (g126), DIN DÅRE (g110 `TIG, DIN DÅRE...`) |
| Adso → Guillermo | **NI** | vos 89, 163 (¿HABÉIS...?, ¿VOS QUÉ PENSÁIS?) | MÄSTARE |
| Severino → Guillermo | **NI** | vos 13 (unused, ESCUCHAD), 38 (unused, ESPERAD), 47, 55, 57, 71, 99, 106, 107 | ÄREVÖRDIGE BRODER (g47, g55), BRODER (g13, g38), BRODER VILHELM (g111, no pronoun there), VILHELM (g57) |
| Guillermo → Severino | **DU** | tú 56, 95, 99, 106, 111 (REGRESA, CIERRA, NO ABRAS); vos 70, 71 not copied | SEVERINUS, BRODER |
| Severino → Adso | **DU** | tú 57 | GOSSE |
| Severino → monks (plural) | **NI** | 93 | BRÖDER! |
| Malaquías → Guillermo | **NI** | vos 7, 43, 44 (unused, SI LO DESEÁIS ... OS MOSTRARÁ) | BRODER, ÄREVÖRDIGE BRODER |
| Berengario → Guillermo | **NI** | vos 60, 61, 62 (ESTÁIS VIENDO), 75 | ÄREVÖRDIGE BRODER |
| Guillermo → Berengario | **DU**; **NI** in his last turn of g75 | tú 75; the closing switch to vos (NO ME PIDÁIS ... VUESTROS PECADOS) **is** copied: documented exception (§2.1). Not a switch: TENÍAIS in `SI TENÍAIS LA MISMA EDAD` (g75) is plural, "you two" (Berengar and Adelmo), so plural NI: `OM NI VAR JÄMNGAMLA` | (none) |
| Jorge → Guillermo | **NI**; **DU** in the opening of g128 | vos 42, 62, 128 (TENÉIS VUESTRO), 129, 130; tú twice in g128 (ERES TÚ, TE ESTABA ESPERANDO) **is** copied: documented exception (§2.1); the generic tú of g42 (LO ESPERAS) → MAN (§2.1) | BRODER VILHELM, VILHELM (g128), ÄREVÖRDIGE BRODER (g42, unused) |
| Guillermo → Jorge | **NI** | vos 62, 128; tú once in g131 (ROBASTE) not copied | ÄREVÖRDIGE JORGE |
| Jorge → Adso | **DU** | tú 130 | GOSSE |
| Adso → Jorge | **NI** | vos 131 | ÄREVÖRDIGE JORGE |
| Remigio → Guillermo | **NI** | vos 49, 50, 51, 74, 159 | BRODER, BRODER VILHELM |
| Guillermo → Remigio | **NI** | vos 74 (¿SABÉIS?, ¿HABÉIS VISTO?) | REMIGIO, BRODER |
| Salvatore → Guillermo | **DU** (pidgin) | TUYA 101 | DOMINE FRATE MAGNIFICENTISSIMO (Latin, kept) |
| Guillermo → Salvatore | **DU** | tú 54, 100 | BRODER |
| Ubertino → Guillermo | **DU** | tú 53 (g115 has no pronoun) | VILHELM, KÄRASTE BRODER, BRODER (g115) |
| Guillermo → Ubertino | **DU** | tú 53 (g97 has no pronoun) | UBERTINO |
| Nicola → Guillermo | **NI** | vos 63, 64, 73, 114, 123, 155 (g87 has no pronoun) | BRODER, BRODER VILHELM (g87, g114) |
| Guillermo → Nicola | **DU** | tú 64, 98, 114, 123, 155; vos 64 (AQUÍ TENÉIS), 87, 114 (OS VOY) not copied | NICOLA, BRODER NICOLA (g87, where Spanish has VENERABLE HERMANO; g123), BRODER. No ÄREVÖRDIGE in this DU pair (§2.1) |
| Bernardo → Guillermo | **NI** | vos 109, 110, 113, 116, 117, 120 | BRODER VILHELM |
| Guillermo → Bernardo | **NI** | vos 110, 120 | BERNARDO (bare) |
| Bernardo → Remigio | **DU** | tú 113, 118 | REMIGIO |
| Remigio → Bernardo | **NI** | vos 118 | (none) |
| Remigio → Salvatore | **DU** | tú 118 | DIN DÅRE (`VAD HAR DU SAGT TILL DEM, DIN DÅRE?`) |
| Salvatore → Bernardo | 3rd person | 118 EL SEÑOR BERNARDO ... EL SABE | HERR BERNARDO ... HAN VETA |
| Bernardo → all present | **NI** (plural) | 110 MIRAD, 118 ¿VÉIS? | |
| villager → Guillermo and Adso | **NI** (plural; only an imperative occurs) | 66 ¡VENID! | `KOM!` |
| Severino, Nicola, Bernardo, Berengario, Abad → Guillermo **and** Adso together | **NI**, plural agreement where both are meant | clearly plural: Severino 57 (DEBÉIS VENIR), 99 (TRAIGÁIS, PEDIDLE), 107 (TOMAD, TAPAOS); singular or plural: Severino 106, Nicola 73, Bernardo 109, Berengario 62, Abad 40 | as for Guillermo |
| Abad → Jorge (unused g41) | **NI** | vos 41 (ANTE VOS) | ÄREVÖRDIGE JORGE |

How the matrix was built: **each pair follows the Spanish majority** for that pair, nothing
more. No deeper rule is claimed (Remigio and Severinus both hold offices and are both
questioned, yet the Spanish has Guillermo say vos to the first and tú to the second, and the
Swedish copies that). The result, for reference: the abbey's monks say **NI** to the famous
guest; Guillermo says **NI** to the abbot, Jorge, Bernardo and Remigio and **DU** to Adso,
Ubertino, Severinus, Berengar, Nicola and Salvatore; superiors and elders say **DU** to Adso, and
Adso says **NI** to everyone.

### 2.3 Titles and forms of address

| Spanish | Swedish | rules |
|---|---|---|
| FRAY GUILLERMO | BRODER VILHELM | address and third person (g41 `BRODER VILHELM, VÅR GÄST`). Never FRA, FRAY, FRIAR, MUNKEN. Also BRODER FRANCISCO, BRODER JUAN (g149) |
| HERMANO (address) | BRODER | never BROR (family word), never BRODERN in address |
| HERMANOS (address) | BRÖDER | no article |
| HERMANO GUILLERMO / HERMANO NICOLA | BRODER VILHELM / BRODER NICOLA | |
| un hermano (a monk) | EN BRODER | g95 `EN BRODER HADE MED SIG ETT GIFT ...` |
| VENERABLE HERMANO | ÄREVÖRDIGE BRODER | weak form in address, **only in pairs that use NI** (§2.1). ÄREVÖRDIG is the traditional Swedish clerical address and 3 glyphs shorter than VÖRDNADSVÄRDE, which is correct but not used (one word everywhere; VENERABLE occurs in g41-43, 47, 55, 60, 62, 87, 128, 131). Exception: g87 (Guillermo → Nicola, a DU pair) → `BRODER NICOLA` |
| VENERABLE JORGE | ÄREVÖRDIGE JORGE | third person: DEN ÄREVÖRDIGE JORGE |
| MAESTRO (Adso → Guillermo) | MÄSTARE | never LÄRARE, HERRE, MAESTRO |
| BELLO MAESTRO (g75, twice) | VACKRE MÄSTARE | the same BELLO as Adelmo's own (g71, g122 → VACKRE ADELMO); never SKÖNE (modern *skön* about a person = cool, comfy) |
| QUERIDO ADSO | KÄRE ADSO | |
| QUERIDÍSIMO HERMANO | KÄRASTE BRODER | |
| MUCHACHO (address, g57, g130) | GOSSE | g57 `VILHELM, NI SKA SITTA TILL HÖGER OM ABBOTEN. _ DU, GOSSE, SITTER TILL VÄNSTER OM MIG.` (chosen to mirror `TILL HÖGER OM ABBOTEN`; `TILL MIN VÄNSTER` is equally good Swedish, but one form is used); g130 `SEDAN SKA JAG VISA DIG DEN, GOSSE.` |
| MUCHACHO (reference, g53, g122) | YNGLING | `YNGLINGEN SOM DOG`, `VACKRA YNGLINGAR` |
| INSENSATO | DÅRE; as vocative always **DIN DÅRE** | g110 `TIG, DIN DÅRE...` (Guillermo → Adso); g118 `VAD HAR DU SAGT TILL DEM, DIN DÅRE?` (Remigio → Salvatore); §1.6 |
| PADRE (spiritual, g145) | FADER / FÄDER | `EN AV VÅR ORDENS ANDLIGA FÄDER` |
| PADRE HERBOLARIO (g55) | ÖRTLÄKARE | `JAG ÄR SEVERINUS, KLOSTRETS ÖRTLÄKARE.` An established word that names what he does (herbs and the infirmary); not ÖRTKÄNNARE (rare, names expertise rather than an office) |
| SEÑOR (God) | HERREN | `HERRENS VILJA` |
| SEÑOR (Salvatore, of Bernardo) | HERR | `HERR BERNARDO` |
| HIJO (does not occur) | MIN SON | |
| DOMINE FRATE MAGNIFICENTISSIMO | unchanged | Latin |

Offices and roles (also in the TSV, kind `title`):

| Spanish | Swedish | where |
|---|---|---|
| CILLERERO | KÄLLARMÄSTARE (def. KÄLLARMÄSTAREN) | g49 `JAG ÄR REMIGIO, KÄLLARMÄSTAREN.` |
| VIDRIERO | GLASMÄSTARE | g63, g64 |
| AYUDANTE DEL BIBLIOTECARIO | BIBLIOTEKARIENS MEDHJÄLPARE | g56, g60 |
| BIBLIOTECARIO | BIBLIOTEKARIE (def. BIBLIOTEKARIEN) | |
| ILUSTRADOR / MINIATURISTA | MINIATYRMÅLARE | g1, g61; PINTANDO MINIATURAS → MÅLADE MINIATYRER (g56) |
| COPISTAS | AVSKRIVARE (def. AVSKRIVARNA) | g45, g58 |
| TRADUCTOR DE GRIEGO | ÖVERSÄTTARE FRÅN GREKISKA | g71 |
| NOVICIADO | NOVICIAT (reference term) | g56 HICIERON EL NOVICIADO JUNTOS → `DE VAR NOVISER TILLSAMMANS`, which needs neither word |
| MONJE | MUNK (pl. MUNKAR, MUNKARNA) | |
| SOLDADOS | KNEKTAR | g109 |
| BRUJA | HÄXA | g110 |
| HEREJE | KÄTTARE | g118, g145 |
| ASESINO | MÖRDARE | g113, g120 |

**The abbot** is never named in the game and gets no name in Swedish (no Abbone, no Abbo).
Third person: always **ABBOTEN** (genitive ABBOTENS): `ABBOTEN VÄNTAR PÅ ER.` Nobody addresses
him with a title in the strings; if a rewrite ever needs one, it is FADER ABBOT, but do not add
one where the Spanish has none.

---

## 3. Names

### 3.1 Principles

1. Follow the split the remake's own English version makes (it mirrors the established forms of
   the novel): Latin monastic names in Latin form, Italian and Spanish names that are not
   Latinised in common use unchanged.
2. Swedish conventions on top: an English or Spanish exonym of a medieval person becomes the
   Swedish one (**Vilhelm**, as in Vilhelm av Ockham); *de / of / da* before a place becomes
   **AV** (Jorge av Burgos, Vilhelm av Occam); ancient authors take their Swedish Latin form
   (Aristoteles, Ovidius, Vergilius, Gregorius). **Exception:** where the game uses one form in
   every language, that form stays even if Swedish reference works use another (BERNARDO GUI,
   historically Bernard Gui).
3. Genitive: add **-S**; names ending in -S, -X, -Z take **nothing** and no apostrophe
   (Swedish rule, Språkrådet's first choice): `VENANTIUS MANUSKRIPT`, `SEVERINUS ÖRTAGÅRD`,
   `MALACHIAS NYCKEL`.
4. Real people (credits, images, parchment) are never changed.

### 3.2 Characters

| Spanish (speaker id) | en game | Swedish | genitive | why |
|---|---|---|---|---|
| Guillermo (0) | WILLIAM | **VILHELM** | VILHELMS | a deliberate historicising exonym, as Swedish has long done for medieval Williams (Vilhelm Erövraren; Vilhelm av Ockham in older works). Chosen knowing that modern references and most readers of the novel say William: VILHELM suits the elevated register and is easy to say |
| Guillermo de Occam (parchment 1) | William of Occam | **Vilhelm av Occam** | | the 1987 game named him after Ockham; keep the game's spelling Occam |
| (Guillermo de Baskerville) | | Vilhelm av Baskerville | | **not used** by the Spanish game; do not introduce |
| Adso (1) | ADSO | **ADSO** | ADSOS | Latin form already; Adso av Melk |
| Severino (2) | SEVERINUS | **SEVERINUS** | SEVERINUS | Latin monastic name, as en |
| Abad (3) | THE ABBOT | **ABBOTEN** | ABBOTENS | never named |
| Malaquías (4) | MALACHI | **MALACHIAS** | MALACHIAS | Latin form, consistent with Venantius/Severinus |
| Berengario (5) | BERENGAR | **BERENGAR** | BERENGARS | established form (cf. Berengar av Tours), as en/fr |
| Bernardo Gui (6) | BERNARDO GUI | **BERNARDO GUI**, short **BERNARDO** | BERNARDO GUIS / BERNARDOS | the game's form in all languages and Eco's; keep (historical Bernard Gui) |
| Jorge (7), Jorge de Burgos | JORGE, JORGE OF BURGOS | **JORGE**, **JORGE AV BURGOS** | JORGES | Spanish name, not Latinised; *de* → AV |
| Remigio (8) | REMIGIO | **REMIGIO** | REMIGIOS | Italian, not Latinised |
| Venancio | VENANTIUS | **VENANTIUS** | VENANTIUS | Latin monastic name, as en/fr |
| Salvatore (10) | SALVATORE | **SALVATORE** | SALVATORES | Italian |
| villager (11) | VILLAGER | **BYBON** | | speaker label only |
| Ubertino (12) | UBERTINO | **UBERTINO** (av Casale) | UBERTINOS | Italian historical figure, Ubertino av Casale |
| Nicola (13) | NICOLA | **NICOLA** | avoid | `NICOLAS` would read as the name Nicolas: write `HOS NICOLA`, `SOM NICOLA BERÄTTADE` |
| Adelmo | ADELMO | **ADELMO** | ADELMOS | Italian (Adelmo da Otranto), not Latinised |
| la chica | THE GIRL | **FLICKAN** | | the text says UNA MUJER / ELLA |
| soldados (g109) | SOLDIERS | **KNEKTAR** | | |
| fray Francisco de Avilés (g149) | FRIAR FRANCISCO DE AVILÉS | **BRODER FRANCISCO AV AVILÉS** | | in-joke for Paco Menéndez (from Avilés); É is drawable |
| fray Juan (g149) | FRIAR JUAN | **BRODER JUAN** | | in-joke for Juan Delcán |

### 3.3 Other names in the strings

| Spanish | Swedish | note |
|---|---|---|
| DIOS | GUD (GUDS) | |
| EL SEÑOR | HERREN (HERRENS) | God |
| CRISTO | KRISTUS | g62 `KRISTUS SKRATTADE ALDRIG.` |
| JESÚS | JESUS | |
| MARÍA | MARIA | only in AVE MARIA PURISSIMA |
| EL ANTICRISTO | ANTIKRIST (no article) | unused g42 |
| EL APÓSTOL (g85, only in EL LIBRO DEL APÓSTOL) | not rendered as a word: the book is **JOHANNES UPPENBARELSE** (gen. JOHANNES, no -s) | Swedish APOSTELN on its own means Paul, and APOSTELNS BOK is no Swedish name for Revelation. The trumpets of g85/g97 are Revelation 8 (fr: LE LIVRE DE L'APOCALYPSE) |
| SAN GREGORIO | DEN HELIGE GREGORIUS | g150 |
| ARISTÓTELES | ARISTOTELES (gen. ARISTOTELES, rarely needed) | g62: `ARISTOTELES ÄGNADE ANDRA BOKEN AV SIN POETIK ÅT KOMEDIN, SOM ETT REDSKAP FÖR SANNINGEN.` (or `POETIKENS ANDRA BOK`). AL HUMOR here means comedy, as en/fr/it say |
| EL FILÓSOFO | FILOSOFEN | g130 |
| OVIDIO, VIRGILIO | OVIDIUS, VERGILIUS | g163 |
| DULCINISTAS | DOLCINIANERNA | g54 |
| LA SANTA INQUISICIÓN | DEN HELIGA INKVISITIONEN | g54; LA INQUISICIÓN → INKVISITIONEN (g122) |
| NUESTRA ORDEN | VÅR ORDEN | Franciscan order (g145) |

### 3.4 Places

| Spanish | Swedish | note |
|---|---|---|
| la abadía | **KLOSTRET** (gen. KLOSTRETS). ESTA ABADÍA: from a host **VÅRT KLOSTER** (g1, g49 welcome; g1, g122 `VÅRT KLOSTERS GODA NAMN`); as a real demonstrative **DETTA KLOSTER** (g12, g157) | not ABBEDI: correct (an abbey under an abbot or abbess) but rare and bookish, nobody says it in speech; KLOSTER is the everyday word |
| el monasterio | KLOSTER | g53; parchment `monasterio de Melk` → `klostret i Melk` |
| el edificio | **BYGGNADEN** (gen. BYGGNADENS) | Eco's *l'Edificio*; the game uses the plain word in every language; clear for the Vespers warning g7 |
| el torreón (este) | (ÖSTRA) TORNET | g1, g75, g122 |
| el scriptorium | **SCRIPTORIET** (indef. SCRIPTORIUM) | Latin loan with Swedish definite ending, like REFEKTORIET. The **C spelling is deliberate** (the source keeps *scriptorium* in every language, and the parchment uses it too): never "correct" it to the naturalised SKRIPTORIET/SKRIPTORIUM halfway through |
| la biblioteca | BIBLIOTEKET (BIBLIOTEKETS) | |
| el laberinto | LABYRINTEN | |
| Finis Africae | FINIS AFRICAE | Latin (one TSV row, kind `latin`); EL FIN DE ÁFRICA → AFRIKAS ÄNDE |
| el refectorio | REFEKTORIET | |
| la cocina | KÖKET | |
| la iglesia | KYRKAN | |
| el coro, el altar | KORET, ALTARET | |
| la nave central | MITTSKEPPET | |
| el cementerio | KYRKOGÅRDEN | |
| el osario | BENHUSET | |
| la capilla | KAPELLET | |
| la celda / las celdas | CELLEN / CELLERNA | |
| el claustro | **KORSGÅNGEN** | false friend: never KLOSTRET |
| la enfermería, el hospital | **SJUKHUSET** (both words; gen. SJUKHUSETS) | the same place, so the same word. *Klostrets sjukhus* is a common Swedish name for a medieval monastery's infirmary, and it matches es HOSPITAL; not SJUKSTUGAN (a 19th/20th-century rural cottage hospital or a sick bay) |
| los baños / la bañera | BADHUSET / BADKARET | |
| el huerto / los huertos | ÖRTAGÅRDEN / ÖRTAGÅRDARNA | `SEVERINUS ÖRTAGÅRD` |
| el laboratorio | LABORATORIET | Severino's |
| el taller | VERKSTADEN | Nicola's |
| la pocilga | SVINSTIAN | |
| la tinaja (de sangre) | KARET / BLODKARET | neuter ETT KAR |
| el pozo, el horno | BRUNNEN, UGNEN | |
| la despensa | SKAFFERIET | |
| el pasadizo | LÖNNGÅNGEN | |
| la sala de las reliquias | RELIKKAMMAREN | |
| la aldea | BYN | |
| el estercolero | GÖDSELSTACKEN | |
| el barranco | RAVINEN | |
| la planta inferior / superior (g55, g58), el piso superior (g154), el último piso (g64) | NEDRE / ÖVRE VÅNINGEN, ÖVRE VÅNINGEN, ÖVERSTA VÅNINGEN | |
| los dormitorios (g157) | **CELLERNA** (`... VÄCKER MUNKARNA I CELLERNA.`) | the game's monks sleep in cells (CELDA everywhere); SOVSALAR would contradict it, and g157 is length-capped |
| la chimenea (g154) | **ELDSTADEN** (`DENNA ELDSTAD`) | not SPISEN (a cooking stove), not KAMINEN |
| las escaleras (g137) | **TRAPPAN** | singular, as Swedish says it |
| el almacén (g100) | **FÖRRÅDET**; in Salvatore's pidgin `I FÖRRÅD` | |
| Occidente (unused g45) | VÄSTERLANDET | |
| Melk, Burgos, Avilés, Occam, Casale | unchanged | |
| la meseta (parchment 2) | **platån** | es *abandonaron la meseta, que aún humeaba, como un lugar maldito* → `övergav den ännu rykande platån som en förbannad plats` (present participle: the weak past *rykte* collides with the noun *rykte*, rumour; the mild *platån ... plats* echo is accepted, because *ort* reads as a town or locality) |
| Munich (parchment 2) | **Bayern** in Phase C: `När vi kom till Bayern`; `München` only after the Phase D upgrade of §9.4 | ü is outside the parchment charset |

### 3.5 Real people and works (unchanged)

Paco Menéndez, Juan Delcán, Manuel Pazos, Daniel Celemín (with í, as the es image), David
Cañadas, Umberto Eco, Jean-Jacques Annaud (with the hyphen, as the it/en images). Novel title:
**Rosens namn**, in images written `”Rosens namn”` (Swedish quotes: the closing mark ” at both
ends). Game title: **La Abadía del Crimen Extensum**, unchanged.

---

## 4. Latin and fixed foreign words

Everything below stays as written in the Swedish text. Three spellings are normalised to the form
the other localisations and the sources use (marked ★); the Spanish spelling is a Spanish
adaptation that Swedish has no reason to keep.

| where | text | treatment |
|---|---|---|
| HUD image (not `g` text) | OBSEQUIUM | keep (image, untouched; TSV kind `image`) |
| title logo (not `g` text) | EXTENSUM | keep (TSV kind `image`) |
| g54 ×2 | ★ **PENITENZIAGITE** (es PENITENCIAGITE) | Eco's form, as en/it/fr. Guillermo's follow-up question repeats the same spelling |
| g54 | LA MORTZ EST SUPER NOS | keep |
| g54 | LO PAPA SANTO · A LIBERAR NOS A MALO · DE TUTTE ... PECCATA (LAS dropped) | Salvatore's Romance and Latin formulas (A LIBERAR NOS A MALO = the Pater Noster's *libera nos a malo*, as in Eco); keep inside his Swedish pidgin; token list in §1.10 |
| g54 | NO? (tag after PENITENTIA) | keep |
| g54, g118 | IO | Salvatore's Italian "I"; kept, and also supplied where his Swedish needs a subject (§1.10) |
| g54 | ★ **DOMINE FRATE MAGNIFICENTISSIMO** (es MAGNIFICENTISIMO) | correct superlative, as en/it |
| g54 | JESUS VENTURUS EST ET LOS HOMINES DEBENT FACERE PENITENTIA | keep exactly (LOS kept, as en/fr) |
| g64 | OCULI DE VITRO CUM CAPSULA | keep; context glosses it (Guillermo's spectacles) |
| g100, g101 | DI VITRIO, EST | keep: `FLASKA DI VITRIO I FÖRRÅD EST.` `FLASKA DIN EST.` |
| g118 | HOMO LITERATUS, PECCAVI SINE MALITIA, ET (before IO HOPPAS), INDULGENTIA, IN NOMINE PATRE ET FILIO ET SPIRITIS SANCTIS | keep exactly; the bad Latin is deliberate. The Romance E, MUY MAGNIFICO, EL SABE, ISPERO, SUYA are replaced (§1.10) |
| g125 | SECRETUM FINIS AFRICAE MANUS SUPRA IDOLUM AGE PRIMUM ET SEPTIMUM DE QUATUOR | keep byte for byte |
| g127 | ★ **SUPER THRONOS VIGINTI QUATUOR** (es TRONOS) | Vulgate spelling, as it/fr. An optional gloss after it is allowed: `PÅ TJUGOFYRA TRONER.` (Rev. 4:4: *upon* the thrones) |
| g127 ×3 | **QUATUOR** | must stay: its 1st letter Q and 7th letter R are the hard-coded mirror keys |
| g130 | COENA CYPRIANI | keep, no quotes |
| g138 | AVE MARIA PURISSIMA | the Latin formula behind es AVE MARÍA PURÍSIMA; keep the 8-space pause |
| everywhere | SCRIPTORIUM | Latin loan; Swedish definite SCRIPTORIET (one TSV row, kind `place`, §3.4) |

**Message 127, the mirror riddle.** The Swedish must keep the arithmetic joke and still point
unambiguously to Q and R. Fixed wordings:

- Venantius's sentence, translated by Guillermo: `HEMLIGHETEN MED AFRIKAS ÄNDE: HANDEN ÖVER
  BILDEN, TRYCK PÅ DEN FÖRSTA OCH DEN SJUNDE AV FYRA.` (Swedish says HEMLIGHETEN MED X, not
  HEMLIGHETEN OM X; plain BILDEN for *idolum*, the image in the mirror, since AVBILDEN means a
  likeness or copy.) Keep `AV FYRA`: it is what makes Adso
  answer `JAG FÖRSTÅR INTE, MÄSTARE.`
- The solution: `DET SYFTAR PÅ ORDET QUATUOR. DEN FÖRSTA OCH SJUNDE BOKSTAVEN I QUATUOR!`
  (`BOKSTAVEN` is added because the bare Swedish `DEN FÖRSTA OCH SJUNDE AV QUATUOR` is not
  idiomatic; it also makes the player's task explicit.)

No other Latin needs a Swedish gloss: Salvatore's Latin is glossed by Guillermo's questions, the
manuscript by g127, OCULI DE VITRO by the scene.

---

## 5. Canonical hours

### 5.1 HUD names (exactly 7 cells)

The hour strip draws 7 raw bytes per hour, 8 px each, with no accent overlays (`text.md` §7,
`font.md` §5). Shipped centring rule (es/en/pl): left pad = floor((7 − letters) / 2), right pad
= the rest. So 5 letters ` NOCHE `, 4 letters ` NONA  ` / ` SEXT  `, 3 letters `  NOC  `, 6
letters `TERCIA ` / `VESPER `, 7 letters fill the field (`VESPERS`).

| hour | es | en | **Swedish (exact 7 bytes, quotes not part of it)** | bytes |
|---|---|---|---|---|
| 0 NOCHE | `·NOCHE·` | `·NIGHT·` | `' NATT  '` | 32,78,65,84,84,32,32 |
| 1 PRIMA | `·PRIMA·` | `·PRIME·` | `' PRIM  '` | 32,80,82,73,77,32,32 |
| 2 TERCIA | `TERCIA·` | `·TERCE·` | `' TERS  '` | 32,84,69,82,83,32,32 |
| 3 SEXTA | `·SEXTA·` | `·SEXT··` | `' SEXT  '` | 32,83,69,88,84,32,32 |
| 4 NONA | `·NONA··` | `·NONE··` | `'  NON  '` | 32,32,78,79,78,32,32 |
| 5 VÍSPERAS | `VgPERAS` (ligature) | `VESPERS` | `'VESPER '` | 86,69,83,80,69,82,32 |
| 6 COMPLETAS | `COMdefg` (ligatures) | `COMbcNE` (ligatures) | `'NATTBÖN'` | 78,65,84,84,66,**119**,78 (119 = the HUD Ö, provisional) |

**Ö** = one new precomposed, squashed HUD glyph (diaeresis in rows 0-1, O squashed below, as
the shipped precomposed Ó in slot 68 and as demonstrated by the Phase A demo "ÖTTA"). Suggested
code **119** (slot 74); Phase D assigns the final code. The Ö in the text is **not** byte 214
(U+00D6): that is a negative signed byte, which `v.c()` does not draw and the save list shows as
blank. So the TSV gives every `hour_hud` row its exact bytes as the first token of the note
(`bytes=78,65,84,84,66,119,78`), and a generator emits those bytes, never the encoded `sv` cell. Constraints: slot ≤ 82, never code 120,
never 33/39/44/95/37 (the save menu runs the same byte through `j.a(int)`). All other bytes are
plain A-Z and space.

**Why these.** PRIM, TERS, SEXT, NON and VESPER are the Swedish names of the canonical hours
(clipped from the Latin exactly as the Swedish liturgical tradition does) and fit in plain
letters. NATT renders the game's non-liturgical NOCHE (the night period the player sleeps or
prowls in), as every other language does.

For compline, the options were:

| candidate | cells | verdict |
|---|---|---|
| KOMPLETORIUM / COMPLETORIUM | 12 | cannot fit 7 cells legibly (even the Spanish needed 4 ligature glyphs for 9 letters) |
| KOMPLET | 7, free | the German word; in Swedish it reads as a misspelt KOMPLETT ("complete"), which is actively misleading on a clock |
| KOMPL. | 6, free | abbreviation, ugly and opaque |
| **NATTBÖN** | 7, one new glyph | **chosen**. A real, transparent Swedish word for the last prayer of the day ("night prayer"); every player understands it, and it tells the player what the hour is for: the abbot sends everyone to their cells (g11, g14). Swedish also says COMPLETORIUM, KVÄLLSBÖN or AFTONBÖN for compline, and NATTBÖN alone could suggest the night office (vigils); on the clock the order VESPER → NATTBÖN → NATT settles which prayer is meant |

The NATT / NATTBÖN overlap was weighed: the strip shows one name at a time, scrolled in whole;
the two names are different words; and the order on the clock is VESPER → NATTBÖN → NATT, which
is literally true (the night prayer comes before the night). The save list shows
`DAG 3 NATTBÖN` and `DAG 4  NATT  `, which are distinct at a glance. The cost is one glyph,
which Phase D needs the machinery for anyway. **Fallback** only if the HUD glyph proves
impossible: `'KOMPLET'` (75,79,77,80,76,69,84), accepting the weakness above.

### 5.2 Hours inside dialogue and parchment

No hour name occurs in the shipped `g` strings or parchments, but if a rewrite needs one, use
these (no length limit there, so the full natural word):

| hour | dialogue form | usage |
|---|---|---|
| NOCHE | NATTEN | `OM NATTEN` (habitual), `EN NATT` (one past night), `I NATT` (tonight), `UNDER NATTEN`, `DEN NATTEN` |
| PRIMA | PRIM | no article: `VID PRIM`, `TILL PRIM`, `EFTER PRIM` |
| TERCIA | TERS | `VID TERS` |
| SEXTA | SEXT | `VID SEXT` |
| NONA | NON | `VID NON` |
| VÍSPERAS | VESPERN | definite: `TILL VESPERN`, `EFTER VESPERN` |
| COMPLETAS | NATTBÖNEN | `EFTER NATTBÖNEN` (the HUD word, definite); COMPLETORIUM only where a Latin term is wanted |

The HUD form is the dialogue form minus the article, so a player who sees NATTBÖN on the clock
recognises NATTBÖNEN in speech. The services as a whole (LOS OFICIOS, g1) are **TIDEBÖNERNA**:
the liturgical hours, those on the clock being PRIM ... NATTBÖN (NATT is the game's night
period, not an office), one of them EN TIDEBÖN. Never GUDSTJÄNSTERNA for them.

Other time words: AMANECER → `GRYNING`, `SNART GRYR DAGEN` (g33), `I GRYNINGEN` (g157);
MAÑANA / HOY / AYER → `I MORGON / I DAG / I GÅR`; A LA MAÑANA SIGUIENTE → `MORGONEN DÄRPÅ`.

### 5.3 Day

| context | Swedish |
|---|---|
| HUD image `marcador.png` (es `Día`, en `Day`) | **Dag** (mixed case, §8) |
| save-slot prefix `w.t[4]` | **`DAG `** (with trailing space) |
| save-slot label as drawn | `'DAG ' + day + ' ' + 7 hour bytes` = `DAG 1  NATT  `, `DAG 7 NATTBÖN` (13 glyphs; the bar holds 15) |
| empty save slot `w.u[4]` | **TOM** |
| dialogue | `DAG / DAGEN / DAGAR`: AL TERCER DÍA → `PÅ TREDJE DAGEN`; SEIS DÍAS → `SEX DAGAR`; EL OTRO DÍA → `HÄROMDAGEN`; TODOS LOS DÍAS / CADA DÍA → `VARJE DAG`; CIERTO DÍA → `EN DAG` |

---

## 6. UI strings (final)

Glyph counts include spaces. All verified with the same `len()` the game uses for centring.

### 6.1 End screen (`a`, centred, ≤ 40 glyphs; `a[1]` ≤ 37)

| field | es | Swedish | glyphs |
|---|---|---|---|
| a[0] (y=32) | `HAS RESUELTO EL` | `DU HAR LÖST` | 11 |
| a[1] (y=48, after the number) | ` POR CIENTO` | ` PROCENT` (leading space) | 8 (`100 PROCENT` = 11) |
| a[2] (y=64) | `DE LA INVESTIGACION` | `AV GÅTAN` | 8 |
| a[3] (y=128) | `PULSA ESPACIO` | `TRYCK PÅ MELLANSLAG` | 19 |

Reads `DU HAR LÖST / 42 PROCENT / AV GÅTAN`, the idiomatic Swedish for solving a mystery, and
matches g144 `LÖSA GÅTAN`. Longest line 19 ≤ 40.

### 6.2 Values (`c`, `d`, `e`)

| field | es | Swedish | glyphs |
|---|---|---|---|
| c[0] off | `NO` | `AV` | 2 |
| c[1] on | `SÍ` | `PÅ` | 2 |
| d[0] classic | `CLÁSICO` | `KLASSISK STYRNING` | 17 |
| d[1] directional | `DIRECCIONAL` | `RIKTNINGSSTYRNING` | 17 |
| e[0] voices + sfx | `VOCES,SFX` | `RÖSTER, EFFEKTER` | 16 |
| e[1] sfx | `SFX` | `EFFEKTER` | 8 |
| e[2] silence | `SILENCIO` | `AV` | 2 |

### 6.3 Menu labels (`f`) and every row, proven ≤ 23

| row | es | Swedish label (exact, trailing spaces matter) | glyphs | longest row as drawn | glyphs |
|---|---|---|---|---|---|
| 0 | `CONTINUAR` | `FORTSÄTT` | 8 | `FORTSÄTT` | 8 |
| 1 | `GRABAR PARTIDA` | `SPARA SPEL` | 10 | `SPARA SPEL` | 10 |
| 2 | `CARGAR PARTIDA` | `LADDA SPEL` | 10 | `LADDA SPEL` | 10 |
| 3 | `SONIDOS: ` | `LJUD: ` | 6 | `LJUD: RÖSTER, EFFEKTER` | **22** |
| 4 | `MÚSICA: ` | `MUSIK: ` | 7 | `MUSIK: AV` / `MUSIK: PÅ` | 9 |
| 5 | `CONTROL ` | `""` (empty string) | 0 | `KLASSISK STYRNING` / `RIKTNINGSSTYRNING` | 17 |
| 6 | `PANTALLA COMPLETA: ` | `HELSKÄRM: ` | 10 | `HELSKÄRM: AV` | 12 |
| 7 | `MOSTRAR EXTRAS: ` | `VISA INDIKATORER: ` | 18 | `VISA INDIKATORER: PÅ` | 20 |
| 8 | `REINICIAR PARTIDA` | `STARTA OM` | 9 | `STARTA OM` | 9 |
| 9 | `SALIR` | `AVSLUTA` | 7 | `AVSLUTA` | 7 |

Longest row of the whole menu: `LJUD: RÖSTER, EFFEKTER` = 22 ≤ 23.

**Row 5.** Spanish reads as one phrase (`CONTROL CLÁSICO`, no colon). Swedish puts the adjective
first (`KLASSISK STYRNING`), which a label-then-value row cannot do, and `STYRNING: ` + a
Swedish word for "directional" does not fit 23 (`STYRNING: RIKTNINGSSTYRD` = 24). So the label
`f[5]` is the **empty string** and the two values carry the whole row. The code just concatenates
(`w.java`: `v[i].concat(value)`), so `""` is safe. **Phase D:** the generator must emit `""` for
`k.f[5]` and must not treat it as missing. Fallback if that is ever a problem: `f[5]` =
`STYRNING: `, `d` = `KLASSISK` / `RIKTAD` (rows 18 / 16), which is less idiomatic.

Row 7: "extras" are the on-screen displays that this option switches (lamp gauge, Adso
indicator, `h.java`, `E.java:761`). `INDIKATORER` is the usual Swedish game-menu word for such
displays. Not `HJÄLPMEDEL` (round 1 choice: it suggests aids one uses, such as assistive devices,
not something shown on screen) and not `TILLÄGG`, which a Swedish player reads as add-ons or
plug-ins. Plain letters only, no Å Ä Ö.

### 6.4 Strings outside the text class

| field | es | Swedish | note |
|---|---|---|---|
| `w.t[4]` save prefix | `DÍA ` | `DAG ` | trailing space, 4 glyphs |
| `w.u[4]` empty slot | `VACÍO` | `TOM` | 3 glyphs |
| `E.h[4]` window title | `La Abadía del Crimen Extensum` | `La Abadía del Crimen Extensum` | AWT title |

**Window title.** It matches the logo the player sees on the title screen (the Spanish logo is
reused because *La Abadía del Crimen* is the game's real name). A translated window title would
give the game two names in one install, and *Rosens namn* is the novel's title, not the game's.

The Spanish-only `JOptionPane` errors in `w` (`text.md` §8.5) are shared by every language;
leave them untouched so es/en/pl do not change.

---

## 7. Recurring phrases: one rendering each

Use these every time the Spanish phrase (or its obvious variant) occurs. The index list shows
where it occurs; the same list is in `translation/glossary.tsv` (kind `phrase`). Indices listed
plainly are messages where the Swedish form appears **verbatim** in a correct translation;
indices after **"variant:"** are messages where the Spanish appears in another grammatical form
(definite, predicative, embedded) and the Swedish form is inflected or rebuilt there. Phase E
checks the plain indices automatically and the variant ones by hand.

| Spanish | Swedish (use every time) | where (g index) / note |
|---|---|---|
| BIENVENIDO A ESTA ABADÍA, HERMANO | **VÄLKOMMEN TILL VÅRT KLOSTER, BRODER** | 1, 49 (the host speaks) |
| EL NOMBRE DE ESTA ABADÍA | **VÅRT KLOSTERS GODA NAMN** | 1, 122 (the abbot) |
| BIENVENIDO A MI TALLER, HERMANO | **VÄLKOMMEN TILL MIN VERKSTAD, BRODER** | 64 |
| EL ABAD OS ESPERA | **ABBOTEN VÄNTAR PÅ ER** | 49, 50, 51 |
| OS RUEGO QUE | **JAG BER ER ATT** | 1, 49 |
| OS LO SUPLICO | **JAG BÖNFALLER ER** | 68 |
| SEGUIDME | **FÖLJ MIG** | 55, 60, 67, 121 |
| VENID | **KOM** | 25, 50, 66, 116 |
| VENID AQUÍ | **KOM HIT** | 18 |
| OS ORDENO QUE VENGÁIS | **JAG BEFALLER ER ATT KOMMA** | 6 |
| DEBÉIS ACOMPAÑARME | **NI MÅSTE FÖLJA MED MIG** | 109, 117 |
| LLEGÁIS TARDE | **NI KOMMER FÖR SENT** | 4 |
| LLEGÁIS JUSTO A TIEMPO | **NI KOMMER I RÄTT TID** | 113 |
| DEBÉIS ABANDONAR EL EDIFICIO | **NI MÅSTE LÄMNA BYGGNADEN** | 7 |
| DEBÉIS ABANDONAR LA ABADÍA | **NI MÅSTE LÄMNA KLOSTRET** | 31 |
| ABANDONAD PARA SIEMPRE ESTA ABADÍA | **LÄMNA DETTA KLOSTER FÖR ALLTID** | 12 |
| MAÑANA ABANDONARÉIS LA ABADÍA | **I MORGON SKA NI LÄMNA KLOSTRET** | 28, 122 |
| BERNARDO ABANDONARÁ HOY LA ABADÍA | **BERNARDO LÄMNAR KLOSTRET I DAG** | 27, 121 |
| ESTA NOCHE ABANDONARÉ LA ABADÍA | **I NATT LÄMNAR JAG KLOSTRET** | 115 |
| ABANDONAR / DEJAR LA INVESTIGACIÓN | **AVBRYTA UNDERSÖKNINGEN** | 15, 122 |
| PODÉIS COMER, HERMANOS | **NI MÅ ÄTA, BRÖDER** | 20, 23; variant: 59, 96 (without HERMANOS: `NI MÅ ÄTA`) |
| OREMOS | **LÅTOM OSS BEDJA** | 21; only liturgical use of LÅTOM |
| PODÉIS IR A VUESTRAS CELDAS | **NI MÅ GÅ TILL ERA CELLER** | 11 |
| ENTRAD EN VUESTRA CELDA | **GÅ IN I ER CELL** | 14 |
| OCUPAD VUESTRO SITIO | **INTA ER PLATS** | 39 |
| ASISTIR A LOS OFICIOS Y A LA COMIDA | **INFINN ER TILL TIDEBÖNERNA OCH MÅLTIDERNA** (own sentence after `_`, as in Spanish) / **INFINNA ER TILL TIDEBÖNERNA OCH MÅLTIDERNA** (only if joined to the MÅSTE sentence) | 1; the Spanish bare infinitive is a command, which Swedish gives as an imperative: `NI MÅSTE ÅTLYDA MINA BEFALLNINGAR ..._ INFINN ER TILL TIDEBÖNERNA OCH MÅLTIDERNA._ OM NATTEN MÅSTE NI VARA I ER CELL.` A standalone infinitive `INFINNA ER ...` is ungrammatical. INFINNA SIG TILL fits both nouns (BEVISTA does not go with meals) |
| DE NOCHE DEBÉIS ESTAR EN VUESTRA CELDA | **OM NATTEN MÅSTE NI VARA I ER CELL** | 1 |
| NO HABÉIS RESPETADO MIS ÓRDENES | **NI HAR INTE ÅTLYTT MINA BEFALLNINGAR** | 12 |
| DEBÉIS RESPETAR MIS ÓRDENES | **NI MÅSTE ÅTLYDA MINA BEFALLNINGAR** | 1 |
| ADVERTIRÉ AL ABAD | **ABBOTEN SKA FÅ VETA DETTA** | 8; variant: 2 (unused) `LÄMNA VENANTIUS MANUSKRIPT, ANNARS SKA ABBOTEN FÅ VETA DET.` The natural Swedish threat; not UNDERRÄTTA (officialese) |
| AHORA DEBO IRME | **NU MÅSTE JAG GÅ** | 5; variant: 63 (AHORA DEBO MARCHARME A MI TALLER → `NU MÅSTE JAG GÅ TILL MIN VERKSTAD`) |
| TENGO ALGO QUE DECIROS | **JAG HAR NÅGOT ATT SÄGA ER** | 18 |
| DEBEMOS IR A LA IGLESIA, MAESTRO | **VI MÅSTE GÅ TILL KYRKAN, MÄSTARE** | 9 |
| DEBEMOS IR AL REFECTORIO, MAESTRO | **VI MÅSTE GÅ TILL REFEKTORIET, MÄSTARE** | 10 |
| DEBEMOS ENCONTRAR UNA LÁMPARA | **VI MÅSTE HITTA EN LAMPA** | 17 |
| LA LÁMPARA SE AGOTA | **LAMPAN BÖRJAR SLOCKNA** | 34 |
| SE HA AGOTADO LA LÁMPARA | **LAMPAN HAR SLOCKNAT** | 36 |
| PRONTO AMANECERÁ | **SNART GRYR DAGEN** | 33 |
| DIOS SANTO | **HERRE GUD** | 26, 68, 113; two words, never HERREGUD |
| DIOS NO LO QUIERA | **GUD FÖRBJUDE** | 1, 99 |
| OH CIELOS | **MILDA MAKTER** | 163 |
| ¡LO JURO! | **DET SVÄR JAG!** | 113 `JAG HAR INTE DÖDAT HONOM. DET SVÄR JAG!`; not a bare JAG SVÄR! (§1.6) |
| OS JURO QUE | **JAG SVÄR ATT** | 118 `JAG SVÄR ATT JAG INTE DÖDADE HONOM!`; never JAG SVÄR ER |
| CUANDO LLEGUÉ YA ESTABA MUERTO | **HAN VAR REDAN DÖD NÄR JAG KOM** | 113, 118; Remigio's alibi, the same words both times (g113 `... DET SVÄR JAG! _ HAN VAR REDAN DÖD NÄR JAG KOM.`, g118 `... HAN VAR REDAN DÖD NÄR JAG KOM, OCH MALACHIAS VAR DÄR.`). No DIT/HIT: g113 is at the scene, g118 is not |
| ¡NO JURES! | **SVÄR INTE!** | 118 |
| ¡BASTA! | **NOG NU!** | 61, 62 |
| ¡SILENCIO! | **TYSTNAD!** | 61 |
| CALLA, INSENSATO | **TIG, DIN DÅRE** | 110 (`TIG, DIN DÅRE...`) |
| ¿PERO QUÉ LES HAS DICHO, INSENSATO? | **VAD HAR DU SAGT TILL DEM, DIN DÅRE?** | 118 (Remigio → Salvatore) |
| ¡CUIDADO! (g78, the flame near the parchment) | **FÖRSIKTIGT!** | 78 `FÖRSIKTIGT! VILL DU BRÄNNA UPP DET?` |
| ¡CUIDADO, ADSO! (g133, sudden danger) | **SE UPP, ADSO!** | 133 |
| DATE PRISA / DAOS PRISA | **SKYNDA DIG / SKYNDA ER** | 84, 161; SKYNDA ER from the abbot (g84, vos), SKYNDA DIG to Adso (g161 `SKYNDA DIG, ADSO!`) |
| GRACIAS, HERMANO | **TACK, BRODER** | 55, 71, 99, 114 |
| MUCHAS GRACIAS, HERMANO | **HJÄRTLIGT TACK, BRODER** | 74 |
| SÍ, MAESTRO | **JA, MÄSTARE** | 91, 160 |
| NO LO ENTIENDO, MAESTRO | **JAG FÖRSTÅR INTE, MÄSTARE** | 127 |
| LO SIENTO, MAESTRO | **FÖRLÅT MIG, MÄSTARE** | 78 |
| ASÍ ES | **SÅ ÄR DET** | 1, 55, 73, 126, 157 |
| SIN DUDA | **UTAN TVIVEL** | 61, 64, 68, 99 |
| INTERESANTE | **INTRESSANT** | 64, 73 |
| CIERTO, ADSO | **MYCKET RIKTIGT, ADSO / DU HAR RÄTT, ADSO** | 78, 108; MYCKET RIKTIGT in g78 (confirming what Adso saw), DU HAR RÄTT in g108 (agreeing with his complaint) |
| LO COMPRENDO | **JAG FÖRSTÅR** | 159 |
| HMMM... | **HMMM...** | 95, 127 |
| JAJAJAJA / JIJIJI / JEJEJE | **HAHAHAHA / HIHIHI / HEHEHE** | 61; variant: 126 (JAJAJAJAJA, five syllables → `HAHAHAHAHA`) |
| ¿VERDAD? | **INTE SANT? / VÄL** | 110, 132; the tag INTE SANT? in g132 (`DET VAR EN GOD IDÉ, INTE SANT? MEN NU ÄR DET FÖR SENT.`), the particle VÄL in g110 (`NI KÄNNER VÄL OCKSÅ IGEN DEN, BRODER VILHELM?`, DEN = ATTIRALJ, §1.2) |
| BUENAS NOCHES | **GOD AFTON** | 128 |
| ESTE ES / ESTA ES | **DETTA ÄR** | 51, 57, 58, 59, 124, 158 (`DETTA ÄR ER CELL`, `DETTA ÄR REFEKTORIET`, `BRÖDER, DETTA ÄR VILHELM`) |
| UN EXTRAÑO LIBRO | **EN MÄRKLIG BOK** | 13, 72, 111; variant: 77 (EL EXTRAÑO LIBRO → `DEN MÄRKLIGA BOKEN`). EXTRAÑO is MÄRKLIG by default, UNDERLIG where uncanny (§7.1) |
| QUÉ EXTRAÑO | **SÅ MÄRKLIGT** | 19 |
| EL LIBRO EN GRIEGO | **BOKEN PÅ GREKISKA** | 78; variant: 72 (UN EXTRAÑO LIBRO ESCRITO EN GRIEGO → `EN MÄRKLIG BOK SKRIVEN PÅ GREKISKA`) |
| LA MESA DE VENANCIO | **VENANTIUS PULPET** | 73, 77, 81, 122 |
| LA MESA DE TRABAJO DE ADELMO | **ADELMOS PULPET** | 60 |
| EL MANUSCRITO DE VENANCIO | **VENANTIUS MANUSKRIPT** | 2, 125, 127; g2 unused (`LÄMNA VENANTIUS MANUSKRIPT, ...`), twice in g127 |
| LA LLAVE DE MALAQUÍAS | **MALACHIAS NYCKEL** | 83 |
| LAS LÁMPARAS DE LA BIBLIOTECA | **BIBLIOTEKETS LAMPOR** | 99, 107 |
| EVITAR RESPIRAR ESOS HUMOS | **UNDVIKA ATT ANDAS IN DESSA ÅNGOR** | 90 only. g99 has another sentence (EVITAR RESPIRAR LOS HUMOS QUE SALEN DE ESAS LÁMPARAS → `ATT INTE ANDAS IN ÅNGORNA SOM STIGER UPP UR DESSA LAMPOR`), g107 has none; the term is ÅNGOR (§7.1) |
| MANCHAS NEGRAS | **SVARTA FLÄCKAR** | 32, 122; variant: 95 (MANCHADAS DE NEGRO → `SVARTA`, ESAS MANCHAS → `DESSA FLÄCKAR`) |
| LA TINAJA DE SANGRE | **BLODKARET** | 85, 122; LA TINAJA alone -> KARET (68, 69, 142) |
| EL ÚLTIMO QUE VIO CON VIDA A ADELMO | **DEN SISTE SOM SÅG ADELMO VID LIV** | 75; variant: 74 (AL JOVEN ADELMO → `DEN SISTE SOM SÅG DEN UNGE ADELMO VID LIV`) |
| LA MUERTE DE ADELMO | **ADELMOS DÖD** | 59, 122; variant: 74 (LA NOCHE DE LA MUERTE DE ADELMO → a clause, `DEN NATT ADELMO DOG SÅG JAG HONOM GÅ TILL BERENGARS CELL`; never `NATTEN FÖR ADELMOS DÖD`) |
| UN MONJE SE AVENTURÓ POR LA NOCHE EN LA BIBLIOTECA Y TUVO VISIONES EXTRAÑAS | **EN MUNK VÅGADE SIG EN NATT IN I BIBLIOTEKET OCH FICK UNDERLIGA SYNER** | variant: 64 (with EN BUSCA DE UN LIBRO: `... IN I BIBLIOTEKET FÖR ATT SÖKA EN BOK OCH ...`), 99 (SE AVENTURÓ A ENTRAR ... TUVO EXTRAÑAS VISIONES, same Swedish words); one past night, so EN NATT, not OM NATTEN (§5.2) |
| DECIDAN POR SÍ SOLOS | **SJÄLVA AVGÖR** | 47, 64 |
| ID A VERME | **SÖK UPP MIG** | 63, 155 |
| AQUÍ TENÉIS (handing over) | **VARSÅGOD** | 64; one word = "here you are". Three words `VAR SÅ GOD OCH ...` = old-fashioned "please, kindly" (§10) |
| ¡AQUÍ LAS TENÉIS! | **HÄR ÄR DE!** | 123 |
| A LA HORA DE LA COMIDA | **VID MÅLTIDERNA** | 57 |
| DESPUÉS DE LA COMIDA | **EFTER MÅLTIDEN** | 155 |
| DEMASIADO TARDE / YA ES TARDE | **FÖR SENT** | 132, 162 |
| EL LIBRO DEL APÓSTOL | **JOHANNES UPPENBARELSE** | 85 `MEN DET STOD SKRIVET I JOHANNES UPPENBARELSE.`; in g97 EL LIBRO → BOKEN points back to it |
| LA PRIMERA / SEGUNDA / TERCERA / CUARTA TROMPETA | **DEN FÖRSTA BASUNEN / DEN ANDRA BASUNEN / DEN TREDJE BASUNEN / DEN FJÄRDE BASUNEN** | 85, 97 |
| LUJURIA Y SOBERBIA | **VÄLLUST OCH HÖGMOD** | 53; LUJURIA -> VÄLLUST also in 163 |
| ESTOY CONDENADO | **JAG ÄR FÖRDÖMD** | 75 |
| EL CASTIGO ETERNO | **DET EVIGA STRAFFET** | 75 |
| EL SECRETO DE CONFESIÓN (in SELLE MIS LABIOS CON ...) | **BIKTENS SIGILL** | 75 (*sigillum confessionis*: one seals with a seal, not with a secret). The general concept, if ever needed elsewhere, is BIKTHEMLIGHETEN (§7.1) |
| NO ME PIDÁIS QUE SELLE MIS LABIOS CON EL SECRETO DE CONFESIÓN | **BE MIG INTE ATT FÖRSEGLA MINA LÄPPAR MED BIKTENS SIGILL** | 75; start of the documented NI switch (§2.1) |
| DIJO: ESTOY CONDENADO, BELLO MAESTRO | **HAN SADE: JAG ÄR FÖRDÖMD, VACKRE MÄSTARE** | 75; colon instead of quotation marks (§1.8) |
| OS PIDO QUE ME CONFESÉIS | **JAG BER ER ATT HÖRA MIN BIKT** | 75 |
| CONFIESA | **BEKÄNN** | 118 (judicial) |
| EL SECRETO DEL FIN DE ÁFRICA | **HEMLIGHETEN MED AFRIKAS ÄNDE** | 127; never HEMLIGHETEN OM (translationese) |
| LA MANO SOBRE LA IMAGEN | **HANDEN ÖVER BILDEN** | 127; not AVBILDEN (a likeness or copy) |
| PULSA EL PRIMERO Y EL SÉPTIMO DE CUATRO | **TRYCK PÅ DEN FÖRSTA OCH DEN SJUNDE AV FYRA** | 127; keep FYRA so the riddle still points to QUATUOR |
| ¡EL PRIMERO Y SÉPTIMO DE QUATUOR! | **DEN FÖRSTA OCH SJUNDE BOKSTAVEN I QUATUOR!** | 127; = Q and R (hard-coded keys) |
| SE REFIERE A LA PALABRA QUATUOR | **DET SYFTAR PÅ ORDET QUATUOR** | 127 |
| ESTÁIS MUERTO, FRAY GUILLERMO | **NI ÄR EN DÖD MAN, BRODER VILHELM** | 129 (= you are doomed; NI ÄR DÖD would say he already is) |
| HABÉIS CAÍDO EN LA TRAMPA | **NI HAR GÅTT I FÄLLAN** | 129 |
| ¿ERES TÚ, GUILLERMO? TE ESTABA ESPERANDO | **ÄR DET DU, VILHELM? JAG HAR VÄNTAT PÅ DIG** | 128 (DU exception, §2.1); then `HÄR HAR NI ER BELÖNING.` |
| ID A CONTARLE VUESTROS PECADOS AL SEÑOR | **GÅ OCH BEKÄNN ERA SYNDER FÖR HERREN** | 75 (NI exception, §2.1) |
| AQUÍ TENÉIS VUESTRO PREMIO | **HÄR HAR NI ER BELÖNING** | 128; back to NI after the DU opening (§2.1) |
| RESOLVER EL MISTERIO | **LÖSA GÅTAN** | 144; matches end screen AV GÅTAN |
| VEAMOS QUÉ HA OCURRIDO | **LÅT OSS SE VAD SOM HAR HÄNT** | 67 |
| YA ESTAMOS LLEGANDO | **SNART ÄR VI FRAMME** | 159 (length-capped) |
| EN LA MEDIDA DE LO POSIBLE | **SÅ GOTT NI KAN** | 59 |
| EL OTRO DÍA | **HÄROMDAGEN** | 95, 99 |
| POR LA NOCHE (habitual) | **OM NATTEN** | 64, 73, 99 |
| ESTA NOCHE | **I NATT** | 115 |
| AQUELLA NOCHE | **DEN NATTEN** | 75 |
| ¡VENID! (villager) | **KOM!** | 66 |
| ¡HERMANOS! | **BRÖDER!** | 93 |
| ¿SABÉIS DÓNDE PUEDO ENCONTRAR UNA LÁMPARA? | **VET NI VAR JAG KAN FÅ TAG I EN LAMPA?** | 74 (`REMIGIO, VET NI ...`); an embedded question takes subordinate order, subject before verb (§1.2) |
| ¡QUÉ MARAVILLA! | **VILKET UNDERVERK!** | 64 (Nicola, about the spectacles); never VILKEN UNDERBARHET |
| OS LO AGRADEZCO | **TACK SKA DU HA** | 87 (Guillermo → Nicola, DU per §2.2: `TACK SKA DU HA. OM JAG FÅR TAG I EN BÅGE SKA JAG LÅTA DIG VETA.`); not JAG TACKAR DIG (a prayer formula, stiff to a craftsman) |
| HACER PREGUNTAS | **STÄLLA FRÅGOR** | 1 `FÅR JAG STÄLLA FRÅGOR TILL DE ANDRA MUNKARNA?`; never GÖRA FRÅGOR |
| A LA DERECHA DEL ABAD / A MI IZQUIERDA | **TILL HÖGER OM ABBOTEN / TILL VÄNSTER OM MIG** | 57; the two halves mirror each other. TILL MIN VÄNSTER is also idiomatic Swedish, just not the chosen form |
| SABES MÁS DE LO QUE DEMUESTRAS | **DU VET MER ÄN DU LÅTSAS OM** | 75 (`NEJ, DU SÅG HONOM SENARE, OCH DU VET MER ÄN DU LÅTSAS OM.`); the set Swedish phrase. DEMOSTRAR is otherwise VISA, never DEMONSTRERA |
| LOS RECIENTES SUCESOS | **DE SENASTE HÄNDELSERNA** | 84, 112; g112 has TRAS LOS RECIENTES ACONTECIMIENTOS → `EFTER DE SENASTE HÄNDELSERNA`, the same Swedish; never SUCCÉER |
| NO HE SATISFECHO VUESTRAS EXPECTATIVAS | **JAG HAR INTE INFRIAT ERA FÖRVÄNTNINGAR** | 122; never EXPEKTATIONER |
| ES ÉPOCA DE MATANZA | **DET ÄR SLAKTTID** | 142; not EPOK |
| HE COMENZADO LA AUTOPSIA | **JAG HAR BÖRJAT UNDERSÖKA LIKET** | 69 (`..., MEN KROPPEN HAR INGA SÅR ...`); never LIKBESIKTNING |
| SI LO DESEÁIS | **OM NI SÅ ÖNSKAR** | 44, 55, 74; g44 unused. Courteous offer to the guest: `OM NI SÅ ÖNSKAR, VISAR JAG ER KLOSTRET.` (g55) |
| SOY X, EL Y (self-introduction) | **JAG ÄR SEVERINUS, SOM HAR HAND OM SJUKHUSET / JAG ÄR REMIGIO, KÄLLARMÄSTAREN / JAG ÄR SEVERINUS, KLOSTRETS ÖRTLÄKARE / JAG ÄR BERENGAR, BIBLIOTEKARIENS MEDHJÄLPARE / JAG ÄR NICOLA, GLASMÄSTAREN** | 47, 49, 55, 60, 63; in that order, one form per message; g47 unused. The formula is JAG ÄR + name + comma + the office in the definite or genitive form, with no article before a genitive; EL ENCARGADO DE becomes a relative clause with HA HAND OM (§7.1) |
| ERA VERDAD, TENÍA EL PODER DE MIL ESCORPIONES | **DET VAR SANT. DEN HADE TUSEN SKORPIONERS KRAFT.** | 29, 119; Malachias's dying words (g119 `HAN HADE SAGT DET TILL MIG... DET VAR SANT. DEN HADE TUSEN SKORPIONERS KRAFT.`); g29 unused, same Swedish, the Spanish comma becomes a full stop. DEN = the book |
| PODRÉIS (the abbot's short yes) | **DET FÅR NI** | 1 (`FÅR JAG STÄLLA FRÅGOR TILL DE ANDRA MUNKARNA?@3 DET FÅR NI.`); never DET MÅ NI (§1.3) |
| ES MUY TARDE | **DET ÄR MYCKET SENT** | does not occur in shipped strings; reserve |
| ES HORA DE ... | **DET ÄR DAGS ATT** | does not occur; reserve (+ infinitive: `DET ÄR DAGS ATT ÄTA`) |

### 7.1 Fixed vocabulary (objects, concepts)

| Spanish | Swedish | note |
|---|---|---|
| EL LIBRO | **BOKEN** |  |
| EL MANUSCRITO | **MANUSKRIPTET** | neuter: ETT MANUSKRIPT |
| EL PERGAMINO | **PERGAMENTET** |  |
| MIS LENTES / LAS LENTES (spectacles) | **MINA GLASÖGON / GLASÖGONEN** | Guillermo's spectacles as an object (61, 78, 82, 87, 98, 114) |
| LAS LENTES (pieces of glass to grind/cut) | **GLASEN** | 87, 98, 123, 156 |
| LA MONTURA | **BÅGEN** | 87, 98 |
| OJOS DE VIDRIO | **ÖGON AV GLAS** | 63 (Swedish GLASÖGON = 'glass eyes': keep the image) |
| VIDRIO / CRISTAL | **GLAS** |  |
| LAS VIDRIERAS | **GLASMÅLNINGARNA** | 64 |
| LA LLAVE | **NYCKELN** |  |
| LA LÁMPARA | **LAMPAN** | pl. LAMPOR |
| LA MECHA | **VEKEN** | 64 |
| EL ACEITE | **OLJAN** |  |
| EL ESPEJO | **SPEGELN** |  |
| EL PAÑO | **DUKEN** | 99, 107 |
| LA GASA | **GASVÄV** | mass noun, so it is counted with STYCKE: g99 UNA GASA → `ETT STYCKE GASVÄV` (never `EN GASVÄV`); not TUNT LINNE (ett linne = a vest) |
| LA BOTELLA | **FLASKAN** | 99-101 |
| AGUA CALIENTE | **HETT VATTEN** | 99, 105, 106 |
| EL CUBO | **ÄMBARET** | 102; neuter ETT ÄMBAR |
| LA INFUSIÓN | **AVKOKET** | 99, 106, 107 |
| LAS HIERBAS | **ÖRTERNA** |  |
| EL VENENO | **GIFTET** | ENVENENADO -> FÖRGIFTAD |
| ARSÉNICO | **ARSENIK** | 70 |
| PIEDRA DE MAGNETITA / LA PIEDRA QUE ATRAE METALES | **MAGNETSTEN / STENEN SOM DRAR TILL SIG METALL** | 71, 108, 114 |
| ARTILUGIO | **ANORDNING** | 108, 114 |
| INSTRUMENTO | **INSTRUMENT** | 62, 114 |
| AGUJA | **NÅL** | 114 |
| DIAMANTE | **DIAMANT** | 123, 156 |
| ESFERA ARMILAR | **ARMILLARSFÄR** | 113 |
| CARBONCILLO | **RITKOL** | 88 |
| MAPA | **KARTA** | 88, 108 |
| GUANTES | **HANDSKAR** | 131 |
| FOLIOS | **BLADEN** | 131 |
| EL CUERPO | **KROPPEN** | dead body |
| EL CADÁVER | **LIKET** | pl. LIKEN |
| LA TUMBA | **GRAVEN** |  |
| CALAVERA / ESQUELETOS | **DÖSKALLE / SKELETT** | 73 |
| SANGRE DE CERDO / MORCILLAS / MATANZA | **SVINBLOD / BLODKORV / SLAKTTID** | 142 |
| RELIQUIAS | **RELIKER** | 122, 146 |
| HOMILÍA | **HOMILIA** | 150 |
| PROFECÍA | **PROFETIA** | 97 |
| PECADO | **SYND** |  |
| PENITENCIA | **BOT** | only Latin in strings |
| CONFESIÓN (sacrament) | **BIKT** | IR A CONFESARSE CON JORGE -> GÅ TILL BIKT HOS JORGE (74) |
| CONFESIÓN (judicial) | **BEKÄNNELSE** | 110, 118 |
| JUICIO | **RÄTTEGÅNG** | 113, 116 |
| INTERROGATORIO | **FÖRHÖR** | 118 |
| HOGUERA | **BÅL** | 118 |
| BRUJERÍA | **TROLLDOM** | 64 |
| MAGIA | **MAGI** | 64 |
| NIGROMANTES | **SVARTKONSTNÄRER** | 79 |
| DIABLO / DIABÓLICO | **DJÄVUL / DJÄVULSK** | 53, 64, 126 |
| VISIONES | **SYNER** |  |
| HEREJÍA | **KÄTTERI** |  |
| LA INVESTIGACIÓN | **UNDERSÖKNINGEN** | INVESTIGAR -> UNDERSÖKA; never UTREDNING |
| CRIMEN | **BROTT** | pl. BROTTEN |
| ASESINADO / ASESINAR | **MÖRDAD / MÖRDA** |  |
| AUTOPSIA | **UNDERSÖKA LIKET** (verb phrase) | 69 `JAG HAR BÖRJAT UNDERSÖKA LIKET`; never LIKBESIKTNING (modern forensic and legal term) |
| LAS ESCRITURAS | **SKRIFTEN** | 61, 62; SKRIFTERNA (as in the Creed's *enligt skrifterna*, DE HELIGA SKRIFTERNA) is not wrong, only not chosen: one form everywhere |
| LA PROVIDENCIA | **FÖRSYNEN** | 62 |
| LA CRISTIANDAD | **KRISTENHETEN** | 130 |
| POÉTICA | **POETIK / POETIKEN** | 62 `ANDRA BOKEN AV SIN POETIK` |
| TIERRA CONSAGRADA | **VIGD JORD** | 1 |
| EL MISTERIO | **GÅTAN** | 144 |
| ORDEN (religious) | **ORDEN** | 145: VÅR ORDEN |
| ÓRDENES (commands) | **BEFALLNINGAR** | 1, 12; OS ORDENO -> JAG BEFALLER ER |
| LOS OFICIOS | **TIDEBÖNERNA** | 1; the liturgical hours (on the clock PRIM ... NATTBÖN, §5.2) |
| LA COMIDA (meal) | **MÅLTIDEN** | pl. MÅLTIDERNA |
| LA COMIDA (food) | **MATEN** | 58 |
| EXTRAÑO | **MÄRKLIG** (odd, curious): 13, 19, 32, 72, 77, 111, 160 · **UNDERLIG** (uncanny): 47, 64, 79, 89, 99. This is every EXTRAÑ* in `g` | all forms: MÄRKLIGT/-A, UNDERLIGT/-A. `DET ÄR MYCKET MÄRKLIGT, BRODER VILHELM` (32), `AV NÅGON MÄRKLIG ANLEDNING ...` (160), `DEN UNDERLIGA LUKTEN` (89), `UNDERLIGA SYNER` (64, 99), `UNDERLIGA TECKEN` (79), `MYCKET UNDERLIGA TING` (47) |
| BELLO (of a person) | **VACKER** | g71 `DEN UNGE OCH VACKRE ADELMO`, g75 `VACKRE MÄSTARE`, g122 `DEN VACKRE ADELMO`; LOS MUCHACHOS HERMOSOS → VACKRA YNGLINGAR (g122) |
| LA RISA / REÍR | **SKRATTET / SKRATTA** | g62 `SKRATTET VANSTÄLLER ANLETSDRAGEN`, `KRISTUS SKRATTADE ALDRIG` |
| COSAS RISIBLES | **LÖJLIGA TING** | g62 |
| SENTIDO DEL HUMOR | **SINNE FÖR HUMOR** | g61 |
| EL HUMOR (the saints' weapon) | **SKÄMT** | g62 `HELGONEN ANVÄNDE SKÄMT FÖR ATT ...` |
| AL HUMOR (Aristotle's subject) | **KOMEDIN** | g62 |
| EL SABER | **VETANDET** | g53 `VETANDETS BLÄNDVERK`, g130 `KRISTENHETENS VETANDE` |
| EL SABER PROHIBIDO | **DET FÖRBJUDNA VETANDET** | g126 |
| EL CONOCIMIENTO / CONOCIMIENTO PROHIBIDO | **KUNSKAP / FÖRBJUDEN KUNSKAP** | g122 / g71 |
| LA CIENCIA | **VETENSKAPEN** (indef. VETENSKAP) | g64 LA CIENCIA HUMANA → `MÄNSKLIG VETENSKAP`, LOS SECRETOS DE LA CIENCIA → `VETENSKAPENS HEMLIGHETER`. Here VETENSKAP has its old sense, learning (Bacon's *scientia*); kept apart from VETANDET (SABER) and KUNSKAP (CONOCIMIENTO) |
| REMEDIO | **MEDEL** (def. MEDLET), with **MOT** | g70 `ETT GOTT MEDEL MOT SINNESSJUKDOMAR`; g99 ×4 `NÅGOT MEDEL MOT ...`, `DET BÄSTA MEDLET ÄR ATT ...`, `DET MEDLET`. Not BOTEMEDEL (one word everywhere), not MEDEL FÖR |
| DESCIFRAR | **TYDA** | g82, g125 |
| CIFRADO, CIFRADA | **I CHIFFER** | g122 `NYCKELN ... SKRIVEN I CHIFFER PÅ ETT PERGAMENT`, `ANVISNINGARNA I CHIFFER` |
| ARTIFICIOS | **KONSTGREPP** | g64 `MAGISKA KONSTGREPP`, g126 |
| LOS HUMOS (lamp) / EL HUMO (fire) | **ÅNGOR, ÅNGORNA / RÖKEN** | g90 `DESSA ÅNGOR`; g99 `ÅNGORNA SOM STIGER UPP UR DESSA LAMPOR`; g161 (fire) `RÖKEN` |
| LA LENGUA (the organ) | **TUNGAN** | g32 `PÅ TUNGAN OCH FINGRARNA`, g95 `TUNGAN ÄR OCKSÅ SVART!`, g120, g122, g131 `FUKTA FINGRARNA MED TUNGAN`. g53 LAS LENGUAS (people's talk) is not this term |
| NEGRO / ENNEGRECIDO (tongue, fingers) | **SVART / SVARTNAD** | g95 `SVART`, g120 `SVARTA`, g122 ENNEGRECIDOS → `SVARTNADE`; never a fixed `SVART TUNGA` phrase, because none of the three sentences has that shape |
| LAS YEMAS DE LOS DEDOS | **FINGERTOPPARNA** (indef. FINGERTOPPAR) | g120 `FINGERTOPPARNA`; g95 LAS YEMAS DE DOS DEDOS DE SU MANO DERECHA → `TVÅ FINGERTOPPAR PÅ HANS HÖGRA HAND` (not "fingertips of two fingers"; not `PÅ HÖGER HAND`, which is also the fixed adverbial "on the right-hand side") |
| MESA (scriptorium desk) | **PULPET** | common gender: EN PULPET, PULPETEN; 60, 73, 77, 78, 81, 122 |
| MESA (other table) | **BORD** | 71, 133 |
| LA LETRA (handwriting) | **HANDSTILEN** | 78 |
| GALLO Y GATO NEGROS | **EN SVART TUPP OCH EN SVART KATT** | 110 |
| MISA | **MÄSSAN** | does not occur in shipped strings; reserve |
| REGLA | **REGELN / KLOSTERREGELN** | does not occur; reserve |
| APOCALIPSIS / EL LIBRO DEL APÓSTOL | **JOHANNES UPPENBARELSE** | the word APOCALIPSIS does not occur; EL LIBRO DEL APÓSTOL (g85) is the one place Revelation is named. Always this form |
| GAFAS | **GLASÖGON** | does not occur; the game says LENTES |
| SECRETO DE CONFESIÓN (concept) | **BIKTHEMLIGHETEN** | reserve; in g75 the image is kept: `BIKTENS SIGILL` (§7) |
| IMAGEN (g127, the *idolum*) | **BILDEN** | not AVBILDEN |
| REALIZAR | **GÖRA / UTFÖRA**, or the specific verb | g64 REALIZO ALGUNOS TRABAJOS DE ARTESANÍA → `UTFÖR EN DEL HANTVERKSARBETEN`; g108 REALIZAR EL MAPA → `RITA KARTAN`; g149 ILUSTRACIONES REALIZADAS POR → `ILLUSTRATIONER UTFÖRDA AV`. Never REALISERA |
| DEMOSTRAR | **VISA** | the general rendering, for rewrites; never DEMONSTRERA. Its one occurrence, g75 SABES MÁS DE LO QUE DEMUESTRAS, is the set phrase `DU VET MER ÄN DU LÅTSAS OM` (§7) |
| PARAFERNALIA | **ATTIRALJ** (common gender: DENNA ATTIRALJ, DEN) | g110 `JAG KÄNNER IGEN DENNA ATTIRALJ. NI KÄNNER VÄL OCKSÅ IGEN DEN, BRODER VILHELM?` (§1.2); never `PARAFERNALIA` |
| ENCARGARSE DE / EL ENCARGADO DE | **HA HAND OM** (an office) / **TA HAND OM** (a task) | g47 `JAG ÄR SEVERINUS, SOM HAR HAND OM SJUKHUSET`; g55 `JAG HAR HAND OM BADHUSET, SJUKHUSET OCH ÖRTAGÅRDARNA`; g76 `... TAR HAND OM DEN` (the lamp) |
| SUCESOS | **HÄNDELSER** (def. HÄNDELSERNA) | g84; never SUCCÉER |
| EXPECTATIVAS | **FÖRVÄNTNINGAR** | g122; never EXPEKTATIONER |
| SUICIDARSE | **TA SITT LIV / TA LIVET AV SIG** | g1 ×2, g68, g122; never SUICIDERA |
| FACCIONES | **ANLETSDRAG** (def. ANLETSDRAGEN) | g62 `SKRATTET VANSTÄLLER ANLETSDRAGEN`; never FRAKTIONER |
| ASISTIR A | **INFINNA SIG TILL** | g1; never ASSISTERA, not BEVISTA (does not go with meals) |
| ESTE (a man, as pronoun) | **DENNE** | g68 ESTE NO → `MEN INTE DENNE`; g120 → `VEM HAR DÖDAT DENNE?` (§1.2) |

---

## 8. Images

Exact Swedish wording, mixed case as drawn, `/` = line break. Missing letters per font from
`images.md` §3. Where two wordings were equally natural, the one needing fewer hand-drawn
letters was taken.

| image | Spanish | **Swedish** | font | letters to hand-draw |
|---|---|---|---|---|
| `marcador.png` (HUD word) | `Día` | **`Dag`** | hud | **g** (D and a from es/en; model the g on the en a bowl + y descender; keep ink at x ≤ 36) |
| `intro/loading.png`, bottom line | `CARGANDO: Por favor, espere` | **`LADDAR: var god vänta...`** | loadline | **g, ä** (ä = a + two 1-px dots). Lowercase after the colon as fr does; capitals L A D R exist |
| `intro/loading.png`, title art | `La abadia del crimen / extensum` | unchanged (es art) | title art | none |
| `intro/logo.png` | `La abadia / del crimen / extensum` | unchanged (es logo, decision) | title art | none |
| `intro/manuydani.png` | `Manuel Pazos` / `y Daniel Celemín` | **`Manuel Pazos`** / **`och Daniel Celemín`** | fraktur + script conj. | script **o, c, h** (compose from the a bowl, open e, d ascender + n arch); names are es pixels |
| `intro/pacoyjuan.png` | `inspirado en la obra de` / `Paco Menéndez` / `y Juan Delcán` | **`efter spelet av`** / **`Paco Menéndez`** / **`och Juan Delcán`** | fraktur + script | none in Fraktur; script **o, c, h** (reuse the manuydani `och` glyphs: the en `and` is the same 32 × 15 px in all three images) |
| `intro/novela.png` | `en la novela` / `“El Nombre de la Rosa”` / `de Umberto Eco` | **`efter romanen`** / **`”Rosens namn”`** / **`av Umberto Eco`** | fraktur | none (use the existing ” glyph at both ends, Swedish style) |
| `intro/pelicula.png` | `y en la película de` / `Jean Jacques Annaud` / `del mismo nombre` | **`och`** (script, own line as en) / **`Jean-Jacques Annauds`** / **`film med samma namn`** | script + fraktur | none in Fraktur (it/en `Jean-Jacques Annaud` + existing s); script **o, c, h** (reuse the manuydani `och` glyphs: the en `and` is the same 32 × 15 px in all three images) |
| `intro/pulsa.png` | `Pulsa para empezar` | **`Tryck för att starta`** | pulsa | **T, y, k, f, ö** |

The four credit screens read as one Swedish sentence, like the Spanish:
*Manuel Pazos och Daniel Celemín · efter spelet av Paco Menéndez och Juan Delcán · efter
romanen ”Rosens namn” av Umberto Eco · och Jean-Jacques Annauds film med samma namn.*
`efter` is the Swedish credit idiom for "based on" (`efter en roman av`) and, unlike
`baserat på`, needs no å in the Fraktur font, which has no ring model. `Tryck för att starta`
was preferred over `Tryck för att börja` (equally natural, one more missing letter, b).

---

## 9. Parchment style notes (`pergamino1`, `pergamino2`)

### 9.1 Tone

- **Intro** (adapted from Eco's prologue): old Adso in his cell at Melk, near death, humble and
  solemn, long periodic sentences joined by semicolons as in the Spanish. This is the one place
  where the old-fashioned list of §1.3 may be used more freely: TY, VORE, MÅ (`må min hand inte
  darra`), inverted word order (`Kallt är det i scriptoriet`), MIN FADER for *mi padre*. Still
  modern spelling and singular verb forms; no pastiche (`hafver`, `I`).
  Register sample (style only, not the final text): `Nu, vid slutet av mitt syndiga liv, medan
  jag väntar på att förlora mig i den tysta och öde gudomens bottenlösa avgrund ...`
- **Ending** (pergamino2): the fire, the farewell in Bayern (§9.4), the old monk's doubt whether his
  text has any meaning. Elegiac and quiet; keep the closing repetition (`Jag lämnar denna skrift,
  jag vet inte åt vem ...`).
- Terms: `fray Guillermo de Occam, sabio franciscano` → `broder Vilhelm av Occam, en lärd
  franciskan`; `amanuense y discípulo` → `skrivare och lärjunge`; `la abadía` → `klostret`;
  `monasterio de Melk` → `klostret i Melk`; `El Señor` → `Herren`; `la divinidad` →
  `gudomen`; `scriptorium` → `scriptoriet`; `Cuando llegamos a Munich` → `När vi kom till Bayern`
  (§9.4); `la meseta` → `platån`; `mi buen maestro` → `min gode mästare`; `Guillermo` → `Vilhelm`.
  Year `1327` stays in digits (1, 2, 3, 7 are drawable).
- `F I N` → **`S L U T`** (same letter spacing).
- Credits block (same layout and indents as es): `Efter spelet av` / `Paco Menéndez` /
  `Juan Delcán` · `Programmering:` / `Manuel Pazos` · `Grafik:` / `Daniel Celemín` · `Musik:` /
  `David Cañadas` · `Till minne av` / `Paco Menéndez` / `och` / `Umberto Eco`. Keep the
  accented bytes é, í, ñ, á (Menéndez E9, Celemín ED, Cañadas F1, Delcán E1; `parchment.md` §7.4).

### 9.2 Layout and hyphenation

- Hand-wrapped, CR line ends only, 11 lines per page, ink right edge ≤ 244 px (≤ 169 px from
  x = 76); check every line with
  `uv run work/phaseA/scripts/letras_render.py width "<line>" --sv --letras <swedish letras>`.
- Keep the Spanish rhythm: paragraphs start with one space; similar page count (es 8 / 8 pages),
  ± 1 page is fine; blank lines between paragraphs as in es.
- Swedish hyphenation: break first at a compound joint (`kyrko-gården`, `lär-jungar`), otherwise
  between syllables with one consonant carried to the next line (`mäs-ta-re`, `klos-ter`,
  `syn-da-re`); never split ck, ng, x or the sj/tj/stj/skj sounds; never carry or leave a single
  letter; never hyphenate names, Latin words or words of five letters or fewer; at most two
  hyphenated lines in a row. Hyphen frequency like the Spanish (about one line in four).

### 9.3 Charset

Usable: a-z, A-Z, space, `, - . : ;`, digits **1 2 3 7** only, the cp1252 accented letters of
`parchment.md` §7 (é í ñ ... for the credits), and **å ä ö** (plus Å Ä Ö) once the new letras
slots exist. **Not usable:** `? ! " ( ) /`, apostrophes, digits 0 4 5 6 8 9 (write numbers as
words). Rephrase any question or exclamation as a statement (the Spanish has none). The capital
Å Ä Ö glyphs are placeholders until Phase D designs them: avoid sentence openings such as
`Även`, `Ännu`, `Åter`, `Är` until the final glyphs are in.

### 9.4 Munich

Phase C writes **`När vi kom till Bayern`** (es `Cuando llegamos a Munich`). It is inside the
charset, measurable today, and true (Munich lies in Bavaria). `München` needs a lowercase **ü**,
which is outside the parchment charset: cp1252 `FC` hangs the writer (its table entry is out of
range), and UTF-8 `C3 BC` silently draws **ż** (the lead byte is ignored and trail `BC` is the
Polish ż case), so `München` would come out as `Mżnchen` (`parchment.md` §2, §7). Never `Munchen`, never `Munich`.

Optional Phase D upgrade, only when all three steps are done (until then the text says Bayern):

1. A precomposed **ü** (the ä/ö diaeresis over u) goes into the empty table slot **0x3C `<`**.
   Its code is black (`0x3C & 96 = 32`), as a lowercase letter must be; codes 0x40-0x5F draw red.
2. `letras_render.py --sv` is extended to map `ü` → 0x3C, so the line can be measured.
3. The paragraph is re-wrapped and rendered with the new letras.

Then Phase E may swap `Bayern` → `München` (`När vi kom till München`) and update the TSV row.

---

## 10. Do not

Forms marked **†** are also TSV rows of kind `forbidden` (whole-word, case-sensitive search; §11).
Unmarked forms are human checks; the list at the end of this section says why each is not
machine-checked. The † marks in §1.6 mean the same, and every form on the "Not allowed" line of
§1.3 is a TSV row except the pronoun `I` (the plural verbs as the bare forms ÄRO, VORO, HAVA,
HAVEN, GINGO).

- **HERMANO** → never `BROR` †, and never the definite `BRODERN` as address. `BRODER`, `BRÖDER`.
- **FRAY** → never `FRA` †, `FRAY` †, `FRIAR` †, nor `MUNKEN` before a name. `BRODER VILHELM`.
- **MAESTRO** → never `MAESTRO` †, `LÄRARE` †, `MAGISTER` †, nor `HERRE`. `MÄSTARE`.
- **VENERABLE** → never `VENERABEL` †; not `VÖRDNADSVÄRDE` † / `VÖRDNADSVÄRD` † either (correct, but one word everywhere). `ÄREVÖRDIGE`, and only in NI pairs (§2.1).
- **CLAUSTRO** → never `KLOSTER` (false friend). `KORSGÅNGEN`.
- **ABADÍA** → `KLOSTER`; not `ABBEDI` † / `ABBEDIET` † (correct but bookish, never said in speech), not `ABBOTSKLOSTER` †.
- **EDIFICIO** → never `EDIFICIET` †, nor `HUSET`. `BYGGNADEN`.
- **SCRIPTORIUM** → `SCRIPTORIET` / `SCRIPTORIUM` with C, never the naturalised `SKRIPTORIET` † / `SKRIPTORIUM` † (deliberate Latin loan, §3.4).
- **INVESTIGACIÓN** → never `INVESTIGATION` †, `INVESTIGERING` †, `UTREDNING` † / `UTREDNINGEN` †. `UNDERSÖKNING`.
- **LENTES** (Guillermo's) → never `LINSER` †, `BRILLOR` †. `GLASÖGON`; the glass pieces `GLASEN`.
- **CONFESIÓN** → `BIKT` for the sacrament, `BEKÄNNELSE` for the trial; never mix them.
- **ESCRITURAS** → `SKRIFTEN`. `SKRIFTERNA` is not an error (*enligt skrifterna*, DE HELIGA
  SKRIFTERNA), only not chosen: one form everywhere (human check).
- **SUICIDARSE** → `TA SITT LIV` / `TA LIVET AV SIG`, never `SUICIDERA` † / `SUICIDERADE` †.
- **HACER PREGUNTAS** → `STÄLLA FRÅGOR`, never `GÖRA FRÅGOR` †.
- **¿VERDAD?** → `INTE SANT?` or the particle `VÄL`; never `SANNING?`, never the colloquial `ELLER HUR` †.
- **QUÉ MARAVILLA** → `VILKET UNDERVERK!`, never `VILKEN UNDERBARHET` (`UNDERBARHET` †).
- **AUTOPSIA** → `UNDERSÖKA LIKET`, never `LIKBESIKTNING` † (modern forensic term).
- **g127** → never `HEMLIGHETEN OM AFRIKAS ÄNDE` † (→ HEMLIGHETEN MED), never `AVBILDEN` † / `AVBILD` † (→ BILDEN).
- **A MI IZQUIERDA** (g57) → `TILL VÄNSTER OM MIG`, chosen to mirror `TILL HÖGER OM ABBOTEN`.
  `TILL MIN VÄNSTER` is good Swedish too, not an error; it is simply not the chosen form.
- **OS LO AGRADEZCO** (g87, to someone addressed with DU) → `TACK SKA DU HA`, not the prayer-like
  `JAG TACKAR DIG`; never mix NI and DU for one addressee inside a message, except the two
  documented switches (g75, g128; §2.1).
- **PARAFERNALIA** (g110) → `ATTIRALJ`, never `PARAFERNALIA` † (rare and jocular in Swedish, and
  it is the untranslated Spanish word).
- **Vocative insults** → `DIN DÅRE`, never a bare `DÅRE` as address (§1.6).
- **Spanish false friends that occur here**: ASISTIR A (g1) = `INFINNA SIG TILL`, not
  `ASSISTERA` †, not `BEVISTA` † (does not go with meals); REALIZAR (g64, g108, g149) =
  `GÖRA / UTFÖRA` or the specific verb, not `REALISERA` †; DEMOSTRAR = `VISA`, not
  `DEMONSTRERA` † (its one occurrence, g75 `SABES MÁS DE LO QUE DEMUESTRAS`, is the set phrase
  `DU VET MER ÄN DU LÅTSAS OM`); SUCESOS (g84) = `HÄNDELSER`, not `SUCCÉER` †;
  FACCIONES (g62) = `ANLETSDRAG`, not `FRAKTIONER` †; EXPECTATIVAS (g122) = `FÖRVÄNTNINGAR`, not
  `EXPEKTATIONER` †; ÉPOCA DE MATANZA (g142) = `SLAKTTID`, not `EPOK`.
- **False friends that do not occur in `g`** (listed for any rewrite): PRETENDER = `FÖRSÖKA /
  AVSE`, not `PRETENDERA` †; CONSTIPADO = `FÖRKYLD`, not `KONSTIPERAD` †.
- **Anglicisms and modern words**: no `OKEJ` †, `SNÄLLA` † (use `JAG BER ER` / `VAR SÅ GOD OCH
  ...`; one-word `VARSÅGOD` only when handing something over), `SORRY` †, `COOL` †, `FIXA` †,
  `CHECKA` †, `KILLE` †, `GRABB` †, `HEJ` † (use `VAR HÄLSAD` / `VÄLKOMMEN`), `ASSÅ` †,
  `HERREGUD` †, and no prefixes `SUPER-`, `JÄTTE-`, `MEGA-`. **TYP** † is banned in both uses: the
  filler ("typ", "sort of") is slang, and the noun is modern-technical in this register; use
  **SLAG** (`AV SAMMA SLAG`). **LIKSOM** only as a filler ("liksom", "you know") is banned;
  LIKSOM = "like, as" is good literary Swedish and wanted: g62 COMO EL PECADO → `LIKSOM SYNDEN.`
- **Calques caught in review**: not `APOSTELNS BOK` † (→ JOHANNES UPPENBARELSE); not `NI ÄR DÖD` †
  for ESTÁIS MUERTO (→ NI ÄR EN DÖD MAN); not `JAG SVÄR ER` † (→ JAG SVÄR ATT); not a bare
  `JAG SVÄR!` for ¡LO JURO! (→ DET SVÄR JAG!); not `SKÖNE` † about a person (→ VACKRE); not
  `TUNT LINNE` † (→ GASVÄV); not `TILLÄGG` † or `HJÄLPMEDEL` for the menu extras (→ INDIKATORER);
  not `BEVISTA` † or `GUDSTJÄNSTERNA` † for LOS OFICIOS (→ INFINNA SIG TILL TIDEBÖNERNA); not
  `STORT TACK` † (→ HJÄRTLIGT TACK); not a bare `JESUS!` (→ HERRE JESUS!); not `UNDERRÄTTA
  ABBOTEN` (officialese, → ABBOTEN SKA FÅ VETA DETTA); not `FÖRSEGLA ... MED BIKTHEMLIGHETEN`
  (→ BIKTENS SIGILL); not `DENNA` + definite noun (→ DENNA ELDSTAD); not a bare `NOG!` for
  ¡BASTA! (→ NOG NU!); not `DU VET MER ÄN DU VILL VISA` (→ DU VET MER ÄN DU LÅTSAS OM); not
  `NATTEN FÖR ADELMOS DÖD` (→ DEN NATT ADELMO DOG); not `EN GASVÄV` (→ ETT STYCKE GASVÄV); not
  `DET MÅ NI` as a short yes (→ DET FÅR NI); not a standalone infinitive `INFINNA ER ...` (→ the
  imperative INFINN ER ...).
- **Latin**: never translate it, never Swedify its spelling, never drop QUATUOR.
- **Markers**: never add, drop or reorder an `@N`; never end a string with a space; never type
  `¿ ¡ " ( ) /` or a lowercase letter in `g`.
- **Names**: never `GUILLERMO` †, `SEVERINO` †, `MALAQUÍAS` †, `VENANCIO` †, `BERENGARIO` † in
  Swedish text; never an apostrophe genitive (`VENANTIUS' MANUSKRIPT`); never `NICOLAS` †; never
  `VILHELM AV BASKERVILLE` † (the Spanish game does not use it).
- **Archaisms outside §1.3**: no `I`, no `EDER` †, no plural verbs (`ÄRO` †, `VORO` †, `HAVA` †,
  `HAVEN` †, `GINGO` †), no `EJ` †, `ICKE` †, `SKALL` †, `ALLENAST` †, `EMEDAN` †, `EHURU` †,
  `OCK` †, `VARDA` †, `HVAD` †, `HAFVA` †. Note: `EDER` is also the plural of ED (oath); prefer
  the singular (`SVÄR INGEN ED`) or `EDGÅNGAR`, so the oath scene g113/g118 does not trip the
  check. If `EDER` = oaths is ever used, Phase E records it as a reviewed exception. The same
  holds for `HAVEN`, which is also the definite plural of HAV ("the seas"): prefer `HAVET` or
  `VÄRLDENS HAV` in any rewrite, and record a `HAVEN` = seas as a reviewed exception.
- **Exclamations**: no `HÅLL KÄFTEN` †, no `HELIGA GUD` † (§1.6).
- **Parchment**: no `München` † until §9.4 is done; no `?`, `!` or apostrophe.

**Deliberately not machine-checked** (they are legitimate Swedish words in other uses, so a
whole-word search would raise false alarms; Phase C writes them right and Phase E reads for
them): `BRODERN` (fine as third-person definite), `MUNKEN`, `HERRE` (HERRE GUD, HERRE JESUS),
`KLOSTER` (the word for ABADÍA), `HUSET` (GUDS HUS, a house in the village), `EPOK` (ÉPOCA
occurs only in g142, which the phrase row `DET ÄR SLAKTTID` checks), the pronoun `I` (identical
to the preposition), `LIKSOM` (wanted as "like, as"), `SANNING`, `JESUS`, `JAG SVÄR`, `DÅRE`,
`HIMMEL`, `AKTA`, `HJÄLPMEDEL`, `UNDERRÄTTA`, `BIKTHEMLIGHETEN` (the reserve term),
`SKRIFTERNA` and `TILL MIN VÄNSTER` (correct Swedish, only not chosen), `NOG` (a common word;
the bare `NOG!` is a human check), `JAG TACKAR DIG`, `SJUKSTUGAN`, the prefixes
`SUPER-` `JÄTTE-` `MEGA-` (not whole words), the apostrophe genitive, other old plural verb
forms, `DENNA` + definite noun, and word order. Everything marked † is in the TSV (a verb or
noun together with its inflected forms, e.g. REALISERA / REALISERAR / REALISERADE / REALISERAT),
and the TSV has no `forbidden` row that is not marked † here or listed in §1.3.

---

## 11. The TSV: kinds and what a checker does with them

`translation/glossary.tsv`, UTF-8, tab-separated, header `es en sv kind note`. In a cell, ` / `
separates alternatives for different contexts and is never part of a string. Every row's `sv` is
a target form, except kind `forbidden`. Conventions in `note`:

- `g 1, 49` lists the messages where the row applies. For kind `phrase`, one of the `sv` form's
  ` / ` alternatives must appear **verbatim** in each of those messages, so every alternative is
  a complete string (never a fragment such as `ANDRA` for `DEN ANDRA BASUNEN`), and none ends in
  `...` unless the game text does.
- `variant: 77, 95` lists messages where the Spanish appears in another grammatical form; the
  Swedish is inflected or rebuilt there, so Phase E checks them by hand, not by string match.
- **Index syntax in phrase notes** (machine-parsed): first remove every parenthesised group
  `( ... )` (commentary; never nested). Then the note starts with `g ` followed by integers
  separated by commas up to the first `;` or the end; a later `variant: ` is followed by integers
  separated by commas up to the next `;` or the end. Nothing but integers, commas and spaces
  stands in either list, and whitespace around the commas is ignored. Explanatory text comes after a `;`, and an index mentioned there (`g78`, `in
  g127`) is commentary, not part of a list. Every `phrase` note starts with `g `, `variant: ` or
  `reserve`.
- Unused messages (`text.md` §2) appear in the lists like any other message; the phrase and
  forbidden checks run on them too (§1.7 rule 9).
- `reserve` or `not in strings`: a reference form for rewrites; it occurs in no shipped `g`
  message and the checker skips the row.
- `hour_hud` notes start with `bytes=` followed by the exact 7 byte values; a generator emits
  those bytes and never encodes the `sv` cell (whose Ö stands for the HUD glyph, not byte 214).
- Term rows (`term`, `name`, `place`, `title`) are inflected in context (definite, plural,
  genitive), so their index lists say where the term applies, not where the exact string stands.
- **Keys.** The `es` cell alone is not unique: the same Spanish stands under several kinds by
  design (an hour as `hour_hud` and `hour_text`; a target row and its `forbidden` row, e.g.
  MAESTRO). The key is the pair (`es`, `kind`), and it is unique. A term that is both a name or
  place and Latin has one row only, under `latin` (COENA CYPRIANI, FINIS AFRICAE); SCRIPTORIUM
  has one row, under `place` (EL SCRIPTORIUM).

| kind | the `sv` column holds | appears in | charset and check |
|---|---|---|---|
| `name` `place` `title` `term` `phrase` `hour_text` `latin` | the one fixed Swedish (or kept Latin) form | `g` messages | uppercase `sv`: message font (A-Z, digits, space, `. , : ; ? ! ' -`, É, Å Ä Ö). Only `name` may hold a mixed-case `sv` (real people, the novel title, the game title): a reference form for images and parchment, checked where it occurs. Latin that occurs only in images (OBSEQUIUM, EXTENSUM) is kind `image`, and names that occur only in the parchment (Occam) are kind `parchment` |
| `address` | NI or DU (or the 3rd-person form) for one ordered speaker pair | `g` | one pronoun per pair; the note names the documented exceptions (g75, g128) |
| `hour_hud` | exactly 7 characters, padding included; the note's `bytes=` token is authoritative | HUD strip, save list | A-Z, space and the one HUD Ö glyph (code 119, provisional); length exactly 7 |
| `ui` | the exact string, trailing spaces significant | `a c d e f`, `w.t`, `w.u`, `E.h` | message font, uppercase; menu label + value ≤ 23; end screen ≤ 40; `E.h` any Unicode |
| `image` | exact wording, mixed case, ` / ` = line break | intro and HUD images | that image font's inventory (`images.md` §3.8); letters it lacks are hand-drawn (§8) |
| `parchment` | exact wording, mixed case | `pergamino1/2` (letras font) | a-z A-Z, å ä ö Å Ä Ö (new slots), space, `, - . : ;`, digits 1 2 3 7, and é í ñ á only in the credits; never `? ! ' " ( ) /` (§9.3) |
| `forbidden` | a Swedish form that must **not** appear | `g` (and parchment where the note says so) | whole-word, case-sensitive search; the note says what to use instead |

`parchment` and `forbidden` extend the kind list of the Phase B brief. They were added in review
so that image-font checks and parchment checks never run on each other's rows, and so that
banned forms can be found automatically.

---

## 12. Decisions disputed in review

Every must and should from review rounds 1, 2 and 3 is applied, except where a line below says
otherwise. Where a suggestion was taken only in part or not at all, the reason is given here,
one line each.

Round 1:

- **VÖRDNADSVÄRDE kept as an "acceptable variant"** (suggested): not used at all. The brief asks for one rendering per term, and a single word lets the checker flag the other (kind `forbidden`).
- **HUMOR → SKÄMT in g61** (suggested): g61 says SENTIDO DEL HUMOR, and the Swedish idiom is `SINNE FÖR HUMOR` (HUMOR is an old Latin loan, not an anglicism). SKÄMT is used for the saints in g62 and KOMEDIN for Aristotle.
- **EXTRAÑO → UNDERLIG / EGENDOMLIG / BESYNNERLIG** (suggested): only UNDERLIG is admitted beside MÄRKLIG, with a fixed index list (now complete: every EXTRAÑ* in `g`), so the choice stays checkable.
- **Bernardo's g109 counted as plural** (review evidence): it is addressed to FRAY GUILLERMO and may be singular; it is NI either way, so §2.2 lists it as "singular or plural".
- **DORMITORIOS → SOVSALARNA** (offered as an option): CELLERNA instead, because the game's monks sleep in cells (CELDA throughout) and g157 is length-capped.

Round 2:

- **TYP: ban only the filler** (one critic) vs **add TYP to the TSV** (the other): TYP is banned in both senses and is a TSV row. The noun is modern-technical in this register, and SLAG (`AV SAMMA SLAG`) is the period word, so no correct sentence needs TYP. LIKSOM, by contrast, is banned only as a filler and is not in the TSV.
- **EPOK and HUSET as TSV rows** (asked for, or a reason): left out. Both are ordinary words a correct text may use; EPOK's one risky spot, g142, is covered by the phrase row `DET ÄR SLAKTTID`.
- **ADVERTIRÉ AL ABAD → `JAG GÅR TILL ABBOTEN`** (suggested): `ABBOTEN SKA FÅ VETA DETTA` instead. It is the idiomatic Swedish threat ("det här ska ... få veta") and cannot be read as "I am on my way to the abbot".
- **g95 YEMAS → `TOPPARNA PÅ TVÅ FINGRAR`** (suggested): `TVÅ FINGERTOPPAR PÅ HANS HÖGRA HAND` instead (wording as revised in round 3). It fixes the same fault (no "fingertips of two fingers") and keeps the fixed term FINGERTOPP.
- **la meseta → `som ännu rök` / `som ännu pyrde`** (one critic): the other critic's participle was taken, `övergav den ännu rykande platån`, because it also removes the second SOM. (Round 3 replaced the closing `ort` with `plats`.)
- **NATTBÖN placeholder `NATTB{HUD_OE}N` in the sv cell** (offered): the sv cell stays readable (`NATTBÖN`) and every `hour_hud` note starts with a `bytes=` token instead, which a generator can copy as is.
- **REMEDIO → MEDEL / BOTEMEDEL** (two options offered): MEDEL only, one word everywhere.
- **CIENCIA → VETENSKAPEN or KUNSKAPEN** (either offered): VETENSKAPEN, in its old sense of learning; KUNSKAP stays reserved for CONOCIMIENTO so the two Spanish words stay apart.
- **Menu row 7 → `VISA INDIKATORER: ` or `VISA MÄTARE: `** (both offered): INDIKATORER, because one of the two displays (the Adso indicator) is not a gauge.

Round 3:

- **¡CUIDADO! → `FÖRSIKTIGT! / SE UPP`** (one option offered): split into two rows instead, `FÖRSIKTIGT!` (g78) and `SE UPP, ADSO!` (g133), so each check matches the whole exclamation of its own message.
- **CUANDO LLEGUÉ YA ESTABA MUERTO → `NÄR JAG KOM DIT VAR HAN REDAN DÖD`** (one critic): `HAN VAR REDAN DÖD NÄR JAG KOM` (the other critic's wording) instead, because g113 is spoken at the scene (DIT would be wrong there, HIT wrong at the trial in g118), and the shorter form needs neither.
- **TRAS LOS RECIENTES ACONTECIMIENTOS as `variant: 112`** (suggested): listed as a plain index instead. The Swedish `EFTER DE SENASTE HÄNDELSERNA` contains the fixed form verbatim, so the stricter automatic check applies.
- **VENANTIUS MANUSKRIPT with `variant: 2`** (suggested): plain index 2, for the same reason (`LÄMNA VENANTIUS MANUSKRIPT, ...` contains it verbatim); §1.7 rule 9 now states that the glossary checks run on unused messages too.
- **SOY X, EL Y → `JAG ÄR X, Y-EN`** (suggested): taken, as one complete alternative per message so the check stays exact. g47 (EL ENCARGADO DEL HOSPITAL) takes the relative clause `SOM HAR HAND OM SJUKHUSET`, because Swedish has no natural one-word title for that office, and g55 keeps the genitive `KLOSTRETS ÖRTLÄKARE` fixed in round 1.
- **TILL MIN VÄNSTER**: the † and the forbidden row are gone, as suggested; `TILL VÄNSTER OM MIG` stays the chosen form for g57, because it mirrors `TILL HÖGER OM ABBOTEN` in the same message.
- **SJUKSTUGAN** ("acceptable as is", nit): changed anyway to `SJUKHUSET`, which matches es HOSPITAL and avoids the cottage-hospital ring; SJUKSALEN was not taken, because Severinus's domain is more than one ward.
- **TSV duplicates across kinds** (either fix offered): both done. The duplicate rows are removed (COENA CYPRIANI and FINIS AFRICAE are `latin` only, SCRIPTORIUM is `place` only), and §11 states that the key is (`es`, `kind`).
