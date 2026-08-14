# Kutengeneza LIFT inayokidhi viwango

Mwongozo huu ni kwa yeyote anayeandika _exporter_ ya LIFT — msimbo katika lugha yoyote unaobadilisha muundo wa data wa programu nyingine kuwa LIFT 0.13. `sil-lift` ina majukumu mawili katika kazi hiyo: lango la utimilifu linalokagua pato dhidi ya skema na semantiki ambazo skema haiwezi kueleza, na rejea ya maumbo na kanuni za maandishi ambazo pato linapaswa kufuata.

Kuandika LIFT ni rahisi zaidi kuliko kuchanganua: kiendeshaji cha kusafirisha hutoa tu sehemu ndogo ya miundo ambayo mfano wake wenyewe huzalisha, na kamwe hakikabiliwi na chaguzi zote za kiwango kamili. Sehemu ngumu ni maelezo — `.lift-ranges` companion, maandishi kulingana na mfumo wa uandishi, vitambulisho thabiti, na kuepuka XML — na hayo ndiyo hasa yanayokamatwa na ukaguzi hapa chini.

## Vifurushi vilivyosimbwa

LIFT kawaida huhamishwa kama faili moja ya `.zip` — FieldWorks na The Combine zote huingiza na kusafirisha kwa njia hiyo — hivyo `sil-lift` husoma na kuandika vifurushi vilivyofungwa kwa `zip` moja kwa moja, katika mpangilio wowote ambao mfumo unatumia: faili ziko mizizi ya hifadhi, au zimepangwa ndani ya folda moja kuu.

- Soma: `sil_lift.load("package.zip")` hutoa maudhui kwenye saraka ya muda, hupata faili moja la `.lift`, na kulipakia (viendani na vyombo vya habari hutatuliwa kama kawaida).
  - Amri za CLI `validate`, `stats`, `check-media`, na `export` pia zinakubali njia ya `.zip`, hivyo lango hapa chini linafanya kazi dhidi ya kifurushi kama kilivyo.
  - mtiririko wa `stats` na `export`, na uchimbe tu `.lift` badala ya kifurushi kizima — ili viwe nafuu kwenye mfumo wenye media nyingi, na kikomo cha uchimbaji kitumike kwa `.lift` pekee badala ya kila kitu kingine.
  - Utoaji umepunguzwa hadi 10 GiB na wanachama 100,000; kifurushi kinachovuka mojawapo ya mipaka hiyo kinakataliwa kwa `LiftParseError`, vivyo hivyo kifurushi ambacho njia za wanachama zake zinatoka nje ya saraka ya uondoaji.
- **Andika:** `Lexicon.save_zip("out.zip", wrap_folder="MyDict")` hufunga `.lift`, `.lift-ranges` zake, na kila faili nyingine katika folda ya chanzo (media, `WritingSystems/`, `consent/`, ...) katika zipu
  - `wrap_folder` kwa chaguo-msingi huunda folda ya ngazi ya juu inayopewa jina la faili la zip (utaratibu wa kuingiza wa FieldWorks/Combine); toa `False` ili kupata hifadhi tambarare.

`.lift` na `.lift-ranges` huhifadhi uaminifu wa baiti ndani ya kifurushi; chombo cha zip chenyewe hakiruhusu kurejesha baiti kikamilifu.

## Thibitisha pato kama lango la utii

Lenga `sil-lift validate` kwenye faili ya `.lift` iliyotengenezwa. Inatekeleza RELAX NG (kupitia `.lift` na mwenza wake `.lift-ranges`) pamoja na ukaguzi wa kisemantiki ambao sarufi haiwezi kueleza: marejeleo ya `relation`/`variant` yasiyo na kiungo, GUID zilizorudiwa, uadilifu wa wazazi wa vipengele vya safu, thamani za sifa na taarifa za kisarufi ambazo hazijaelezwa katika safu zao, na marejeleo ya `range/@href` katika kichwa yanayotatua hadi kwa mwandani asiye na muunganisho.

Kwa CI, shindwa katika chochote na kutoa matokeo yanayosomeka na mashine:

```
sil-lift validate export.lift --strict --no-check-media --format json
```

- `--strict` hufanya maonyo (sio tu makosa) kusababisha utekelezaji kushindikana.
- `--no-check-media` hupuuza ukaguzi wa uwepo wa media kwenye mfumo wa faili, ambao matokeo yake ya `missing-media` ni kelele tu wakati faili za sauti/picha haziko kwenye folda moja na `.lift` katika CI.
- `--format json` huchapisha kitu kimoja cha JSON (`{"problems": [...], "summary": {...}}`) badala ya maandishi ya kawaida; misimbo yake ya kutoka na schema ni kiolesura kinachotumika kinachofunikwa na SemVer (tazama [mwongozo wa mstari wa amri](cli.md)).
- `--require-ids` pia hutoa hitilafu kwa maingizo yanayokosa `guid` au `id` — ni muhimu wakati uingizaji upya wa baadaye unapaswa kusasisha badala ya kurudia.

Jikinga dhidi ya upotevu wa data kimya (mtindo wa kushindwa unaofanya usafirishaji wa CSV wa kawaida upoteze data) kwa kuthibitisha idadi kwa kutumia `stats --format json` dhidi ya mfano wako wa chanzo:

```
sil-lift takwimu toa.lift --format json
```

Inaripoti idadi ya `entries`, `senses`, `examples`, `media_refs`, `languages`, na `traits` kwa kila jina.

### Kuendesha lango bila mnyororo wa zana za Python

CI ya mradi wa TypeScript au C# inaweza kufanya ukaguzi uleule bila kusakinisha Python, kupitia GitHub Action iliyojumuishwa:

```yaml
- matumizi: sillsdev/python-sil-lift@v0.1.0
  na:
    njia: export.lift
    strict: "kweli"
    no-check-media: "kweli"
    format: json
```

au picha ya kontena, iliyojengwa kutoka kwa `Dockerfile` ya repo:

```
docker build -t sil-lift .
docker run --rm -v "$PWD:/work" -w /work sil-lift validate export.lift --strict
```

## Mwandani wa `.lift-ranges`

Vibainishi vilivyodhibitiwa — aina za maneno, nyanja za maana, na seti nyingine yoyote ya thamani zilizo na ufunguo wa sifa — huishi katika faili ndugu ya `.lift-ranges`, inayorejelewa kutoka kwenye `<header>`:

```xml
<header>
  <ranges>
    <range id="grammatical-info" href="mydict.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="mydict.lift-ranges"/>
  </ranges>
</header>
```

Kiambatisho kinabeba ufafanuzi kamili wa kila safu. Thamani ni `<range-element>`; `parent` huunda ngazi; `label` / `abbrev` / `description` ni maandishi mengi:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
  <range id="grammatical-info">
    <range-element id="Noun">
      <label><form lang="en"><text>Nomino</text></form></label>
      <abbrev><form lang="en"><text>n</text></form></abbrev>
    </range-element>
  </range>
  <range id="semantic-domain-ddp4">
    <range-element id="1.6.1.2">
      <label><form lang="en"><text>Ndege</text></form></label>
    </range-element>
  </range>
</lift-ranges>
```

Kisha, kila kipengee kinarejelea thamani kwa kutumia ID: sehemu ya hotuba ya hisia ni `<grammatical-info value="Noun"/>`, na uwanja wa semantiki ni `<trait name="semantic-domain-ddp4" value="1.6.1.2"/>`. `sil-lift validate` inatoa onyo (`undefined-range-value`) wakati thamani haijafafanuliwa katika upeo wake na makosa (`range-parent`) wakati `parent` si id ya ndugu — kwa hivyo toa upeo ambao data yako inatumia kweli. Tazama pia [Vipimo na vyombo vya habari](folder-media.md).

Ukijenga toleo la kusafirisha kwa kutumia Python, `Lexicon.add_ranges_file()`, `RangesFile.add_range()`, na `Range.add_element()` huunda kiambatisho na kuongeza marejeleo ya kichwa kwa niaba yako; `open_writer(..., ranges=...)` hufanya vivyo hivyo kwenye njia ya utiririshaji.

## Maandishi na maandishi mengi

Kila mfululizo wa lugha ya kibinadamu katika LIFT ni _multitext_: `<form>` moja kwa kila mfumo wa uandishi, kila moja ikizunguka `<text>`:

```xml
<lexical-unit>
  <form lang="seh"><text>kanga</text></form>
  <form lang="pt"><text>kuku</text></form>
</lexical-unit>
```

Mfano unaopanga nyuzi kwa msimbo wa lugha (MultiString, Record<code, string>, dict[str, str]) unaakisi uwiano wa moja kwa moja: kila kipengee kwa kila ufunguo kinakuwa<form lang="… "> moja. Kila lugha inaweza kuwa na fomu moja tu katika maandishi mengi — vinginevyo `sil-lift` itatoa onyo la `duplicate-form-lang`.

Utoaji wa XML ni sehemu pekee inayohitaji usahihi hasa. Katika maandishi ya elementi, `&`, `<`, and `>` lazima ziwekwe kwa alama za kutoroka (`&amp;`, `&lt;`, `&gt;`); katika thamani za sifa, pia alama ya nukuu. Mwandishi wa `sil-lift` hutumia kanuni hizi hasa na kamwe haibadilishi nafasi tupu ndani ya `<text>` — haiongezi nafasi ya kuanzishia hapo, kwa sababu hilo lingeharibu data ya kisemaji. Ikiwa unalenga kuendana na matokeo yake, tumia tena mbinu halisi ya serializer ya XML ya kuepuka alama (sio uingizaji uliofanywa kwa mkono unaosahau `&`) na acha maudhui ya `<text>` byte kwa byte kama chanzo chako kilivyo.
