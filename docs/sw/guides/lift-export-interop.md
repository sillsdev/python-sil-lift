# Kutengeneza LIFT inayokidhi viwango

Mwongozo huu ni kwa yeyote anayeandika _exporter_ ya LIFT: msimbo katika lugha yoyote unaobadilisha muundo wa data wa programu nyingine kuwa LIFT 0.13. `sil-lift` inatekeleza majukumu mawili kwa kazi hiyo:

- lango la utiifu linalokagua pato dhidi ya schema na semantiki ambazo schema haiwezi kueleza;
- Rejea ya sheria za maumbo na maandishi ambazo matokeo lazima yafuate.

Kuandika LIFT ni rahisi zaidi kuliko kuchanganua: kiendeshaji cha kusafirisha hutoa tu sehemu ndogo ya miundo ambayo mfano wake wenyewe huzalisha, na kamwe hakikabiliwi na chaguzi zote za kiwango kamili. Sehemu ngumu ni maelezo (msaidizi wa `.lift-ranges`, maandishi kulingana na mfumo wa uandishi, vitambulisho thabiti, na utokomezaji wa XML), na hayo ndiyo hasa yanayodhibitiwa na ukaguzi hapa chini.

## Vifurushi vilivyosimbwa

LIFT kawaida huhamishwa kama faili moja la `.zip`; FieldWorks na The Combine zote huingiza na kusafirisha kwa njia hiyo. `sil-lift` husoma na kuandika vifurushi vilivyobanwa moja kwa moja, katika mpangilio wowote unaotumiwa na mfumo wa ikolojia: faili kwenye mzizi wa hifadhi, au zilizopangwa ndani ya folda moja kuu.

### Kusoma kifurushi

`sil_lift.load("package.zip")` hutoa maudhui kwenye saraka ya muda, hutafuta faili moja la `.lift`, na kulipakia (viendani na vyombo vya habari hutatuliwa kama kawaida).

- Amri za CLI `validate`, `stats`, `check-media`, na `export` pia zinakubali njia ya `.zip`, hivyo lango hapa chini linafanya kazi dhidi ya kifurushi kama kilivyo.
- Mtiririko wa `stats` na `export`, na uchague tu `.lift` badala ya kifurushi kizima. Zinabaki nafuu kwenye ile yenye media nyingi, na kikomo cha uchimbaji kinatumika kwa `.lift` pekee badala ya kila kitu kilicho kando yake.
- Uchimbaji umepunguzwa hadi 10 GiB na wanachama 100,000. Kifurushi kinachozidi mojawapo ya mipaka kinakataliwa kwa `LiftParseError`, vivyo hivyo na kile ambacho njia za wanachama wake zinatoka nje ya saraka ya uchimbaji.

### Kuandika kifurushi

`Lexicon.save_zip("out.zip", wrap_folder="MyDict")` hufunga `.lift`, `.lift-ranges` zake, na kila faili nyingine katika saraka ya chanzo (media, `WritingSystems/`, `consent/`, ...) katika zipu

- `wrap_folder` kwa chaguo-msingi huunda folda ya ngazi ya juu inayopewa jina la faili la zip (utaratibu wa kuingiza wa FieldWorks/Combine); toa `False` ili kupata hifadhi tambarare.
- Ningizo ambazo maudhui yao yamebadilika tangu kupakia yanapigwa muhuri na `dateModified` mpya wanapotoka, sawa kabisa na kwenye `save()`.
  - Kifurushi ndicho chombo cha kuingiza kinachotegemea, hivyo tarehe iliyopitwa na wakati hapo itaifanya kamusi iliyosasishwa ionekane haijaguswa.
  - Inatumia chaguzi zile zile za `stamp=` na `when=` kama `save()`; tazama [Jinsi stamp inavyotumika](../fidelity.md#how-the-stamp-is-applied).

`.lift` na `.lift-ranges` huhifadhi uaminifu wa baiti ndani ya kifurushi; chombo cha zip chenyewe hakiruhusu kurejesha baiti kikamilifu.

## Thibitisha pato kama lango la utii

Lenga `sil-lift validate` kwenye faili la `.lift`. Inatumia RELAX NG juu ya `.lift` na faili yake ya `.lift-ranges`, pamoja na ukaguzi wa semantiki ambao sarufi haiwezi kuonyesha:

- marejeleo ya `relation`/`variant` yanayodondoka;
- GUID zinazorudiwa;
- Uadilifu wa mzazi wa kipengele cha safu;
- Thamani za sifa na taarifa za kisarufi hazijaelezwa katika wigo wao;
- Kichwa `range/@href` kinarejelea vigezo ambavyo havina mwenza.

Kwa CI, shindwa katika chochote na kutoa matokeo yanayosomeka na mashine:

```
sil-lift validate export.lift --strict --no-check-media --format json
```

- `--strict` hufanya maonyo (sio tu makosa) kusababisha utekelezaji kushindikana.
- `--no-check-media` hupuuza ukaguzi wa uwepo wa media kwenye mfumo wa faili, ambao matokeo yake ya `missing-media` ni kelele tu wakati faili za sauti/picha haziko kwenye folda moja na `.lift` katika CI.
- `--format json` huchapisha kitu kimoja cha JSON (`{"problems": [...], "summary": {...}}`) badala ya maandishi ya kawaida; misimbo yake ya kutoka na schema ni kiolesura kinachotumika kinachofunikwa na SemVer (tazama [mwongozo wa mstari wa amri](cli.md)).
- `--allow CODE[,CODE...]` (inaweza kurudiwa) huruhusu msimbo unaokubalika, kama vile `uri-not-rfc` ya FLEx, usishindwe wakati wa utekelezaji. Matokeo yake yamechapishwa lakini hayajahesabiwa.
- `--require-ids` pia hutoa makosa kwa maingizo yanayokosa `guid` au `id`, jambo ambalo ni muhimu wakati uingizaji upya wa baadaye unapaswa kusasisha badala ya kurudia.

### Kujikinga dhidi ya upotevu wa data kimya

Upotevu wa data kimya ni aina ya hitilafu inayofanya usafirishaji wa CSV wa kawaida kupoteza data. Jikinga dhidi yake kwa kuthibitisha hesabu kwa kutumia `stats --format json` dhidi ya modeli yako ya chanzo:

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
    strict: "true"
    no-check-media: "true"
    allow: "uri-not-rfc"
    format: json
```

au picha ya kontena, iliyojengwa kutoka kwa `Dockerfile` ya repo:

```
docker build -t sil-lift .
docker run --rm -v "$PWD:/work" -w /work sil-lift validate export.lift --strict
```

## Mwandani wa `.lift-ranges`

Vibainishi vilivyodhibitiwa (sehemu za hotuba, nyanja za semantiki, na seti nyingine yoyote ya thamani zilizo na ufunguo wa sifa) huishi katika faili ndugu ya `.lift-ranges`, inayorejelewa kutoka `<header>`:

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

Kisha, kila kipengee kinarejelea thamani kwa kutumia ID: sehemu ya hotuba ya hisia ni `<grammatical-info value="Noun"/>`, na uwanja wa semantiki ni `<trait name="semantic-domain-ddp4" value="1.6.1.2"/>`. `sil-lift validate` hukagua marejeleo hayo, kwa hivyo toa masafa ambayo data yako inayotumia kweli:

- thamani ambayo haijaelezwa katika wigo wake ni onyo la `undefined-range-value`;
- `parent` ambayo si id ya ndugu ni hitilafu ya `range-parent`.

Milinganisho hiyo imewekwa katika muundo wa kawaida wa NFC, hivyo kitambulisho na thamani yake au `parent` inayorejelea inaweza kutofautiana katika urekebishaji wa Unicode. Tofauti hiyo ni onyo la `normalization-mismatch` badala ya kosa. Hata hivyo, andika unormalishaji mmoja thabiti ikiwa unaweza: watumiaji wanaolinganisha nyuzi ghafi hawatafafanua marejeleo hayo. Tazama pia [Vipimo na vyombo vya habari](folder-media.md).

Ukijenga toleo la kusafirisha kwa kutumia Python, `Lexicon.add_ranges_file()`, `RangesFile.add_range()`, na `Range.add_element()` huunda kiambatisho na kuongeza marejeleo ya kichwa kwa niaba yako; `open_writer(..., ranges=...)` hufanya vivyo hivyo kwenye njia ya utiririshaji.

## Maandishi na maandishi mengi

Kila mfululizo wa lugha ya kibinadamu katika LIFT ni _multitext_: `<form>` moja kwa kila mfumo wa uandishi, kila moja ikizunguka `<text>`:

```xml
<lexical-unit>
  <form lang="seh"><text>kanga</text></form>
  <form lang="pt"><text>kuku</text></form>
</lexical-unit>
```

Mfano unaopanga nyuzi kwa msimbo wa lugha (MultiString, Record<code, string>, dict[str, str]) unaakisi uwiano wa moja kwa moja: kila kipengee kwa kila ufunguo kinakuwa<form lang="… "> moja. Kila lugha inaruhusiwa fomu moja tu katika maandishi mengi; vinginevyo `sil-lift` inatoa onyo la `duplicate-form-lang`.

Kutoroka kwa XML ndiyo sehemu pekee inayohitaji usahihi kwa kweli:

- katika maandishi ya elementi, `&`, `<`, and `>` lazima zipitishwe (`&amp;`, `&lt;`, `&gt;`);
- katika thamani za sifa, alama ya nukuu lazima pia ipelekwe.

Mwandishi wa `sil-lift` hutumia kanuni hizi hasa na kamwe haibadilishi nafasi tupu ndani ya `<text>`: haiongezi nafasi ya kuanzisha hapo, kwa sababu hilo lingeharibu data ya kisemantiki. Ili kuendana na kile kinachotolewa, tumia maktaba ya XML kufanya ukombozi na acha maudhui ya `<text>` byte kwa byte kama chanzo chako kilivyo.
