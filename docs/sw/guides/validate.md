# Thibitisha

Uthibitishaji daima ni wazi: upakiaji na uhifadhi kamwe hauthibitishi kwa njia fiche.

```python
import sil_lift

# Kamilifu: mtiririko wa uvivu wa Matatizo (schema + tabaka za semantiki).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # hitilafu [dangling-ref] dictionary.lift:88 (entry apu): ref 'nope' inalingana ...

# Fail-fast: simama mara tu unapopata tatizo la kiwango cha kosa.
if any(p.level == "error" for p in sil_lift.iter_problems("dictionary.lift")):
    raise SystemExit(1)

# Hali ndani ya kumbukumbu (inayosafirishwa kwanza, gharama iliyoorodheshwa kwa kamusi kubwa):
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Kila `Problem` huambatana na `level` (`"error"`/`"warning"`), `code` thabiti, na `message`, pamoja na anwani kadri upataji ulivyo nayo:

- `file`: `None` wakati kamusi haina njia.
- `entry_id`: weka wakati upataji unahusu kipengee kimoja.
- `guid`: weka wakati kitu kinachohusika kina moja (kipengee, au kipengele cha wigo).
- `line`: weka wakati upatikanaji unapoendana na mstari katika hati.

Matokeo kuhusu safu huelekezwa kwa kiongozi mwenza `.lift-ranges` unaoifafanua, na haina kipengee. Sehemu zisizowekwa ni `None` (`null` katika `--format json`, ambapo kila ufunguo daima upo).

## Tabaka

1. **LIFT schema** (`lift-0.13.rng`, sarufi ya LIFT 0.13 RELAX NG, iliyotolewa na vendored ikiwa sawa kabisa kwa baiti kutoka lift-standard) juu ya `.lift`.
2. **Rangi za schema** (`lift-ranges-0.13.rng`, pia imewekwa kama vendor kutoka lift-standard) juu ya kila `.lift-ranges` companion inayofuatiliwa, ikielekezwa kwa companion badala ya `.lift`.
3. **Ukaguzi wa semanti** ambao schemas haziwezi kueleza: kumi na tatu kati yao, kila moja ikiwa na msimbo mmoja.

## Misimbo ya matatizo

Kila ugunduzi huambatana na mojawapo ya hizi, kulingana na safu iliyouzalisha: `schema` na `uri-not-rfc` hutoka kwenye safu za schema, zingine ni ukaguzi wa semantiki. Kila kodi huchunguzwa kwa chaguo-msingi isipokuwa `missing-id`, ambayo ni ya hiari: tumia `require_ids=True` (au `--require-ids`) ili kuiwasha. Misimbo ni thabiti, hivyo skiripti zinaweza kuendana nayo. `--strict` huibadilisha kila onyo kuwa kosa. `sil-lift validate --allow CODE` huacha msimbo nje ya uamuzi wa kupita/kushindwa.

| msimbo                             | kiwango  | kinachoashiria                                                                                         |
| ---------------------------------- | -------- | ------------------------------------------------------------------------------------------------------ |
| faili la masafa yenye utata        | Onyo     | faili kadhaa zinazojibiwa kwa jina moja la mwandani chini ya case folding na NFC                       |
| viwigo-vinavyoelea-href            | Onyo     | Kichwa `range/@href` kinachotatua hadi faili rafiki isiyopo                                            |
| rejea-isiyo na mwisho              | Hitilafu | `relation/@ref` au `variant/@ref` inayolingana na kiingilio au maana yoyote                            |
| fomu-maradufu-lugha                | Onyo     | fomu mbili katika maandishi mengi yanayoshiriki lugha moja                                             |
| nakala-ya-guid                     | Hitilafu | mwongozo unaotumika tena miongoni mwa maingizo, au miongoni mwa wigo/vipengele-vya-wigo vya hati moja  |
| Fomu inakosa lugha                 | Hitilafu | <form>` au `<gloss>` bila `lang` inayohitajika na schema                                               |
| kutofautiana kwa kiungo cha media  | Onyo     | href ya media inayofikia faili yake tu chini ya urekebishaji wa herufi au NFC                          |
| kitambulisho-kinachokosekana       | Hitilafu | [opt-in] ingizo lisilo na guid, hisia lisilo na id |
| Vyombo vya habari vinakosekana     | Onyo     | Faili ya sauti au picha iliyorejelewa haipo kwenye diski                                               |
| kutopatana kwa urekebishaji        | Onyo     | Jina linalofikia kitambulisho kinachorejelewa tu kupitia NFC                                           |
| eneo-mzazi                         | Hitilafu | Hakuna id ya ndugu inayotambuliwa na `range-element/@parent`.                          |
| `shemia`                           | Hitilafu | ukiukaji wa sarufi ya RELAX NG, katika `.lift` au katika faili rafiki                                  |
| Thamani-ya-wigo-isiyoainishwa      | Onyo     | Thamani ya sifa ya taarifa ya kisarufi au yenye funguo za wigo ambayo wigo haitaorodhesha              |
| faili la masafa yasiyoweza kusomwa | Onyo     | mgombea mwenza uliopo lakini si hati ya masafa inayoweza kusomeka                                      |
| URL si RFC                         | Onyo     | href ambayo si URI halali (kama vile `file://C:/...` ya FLEx)                       |

### Kinachoonekana katika uthibitishaji

Tabaka zote tatu hufanya kazi kwa hati iliyoseriwaliswa kama ilivyo, hivyo ile ambayo haiwezi kuseriwaliswa kabisa huripotiwa kama kosa moja la `lone-surrogate`. Tazama [Dhamana za Fidelity](../fidelity.md#content-xml-cannot-represent).

Uthibitishaji ni wa kusoma tu: unaripoti hati kama ilivyo, kabla ya uhifadhi kuweka alama ya tarehe ya mabadiliko. Stampu hazisababishi hitilafu, hivyo hati inayopita uthibitishaji bado inapita hata baada ya kuhifadhiwa.

### Misimbo ya folda-mwenza

Jina la kiashiria linalolingana na faili kadhaa halipaki yoyote kati yao: vipimo wanavyovibainisha havionekani hadi faili zote isipokuwa moja ziitwe tena au ziondolewe.

Misimbo mitatu ya folda-wenza (`ambiguous-ranges-file`, `dangling-ranges-href`, na `unreadable-ranges-file`) huripotiwa tu wakati ugunduzi wa folda-wenza ulipofanyika:

- Upakiaji kwa kutumia `resolve_ranges=False` huwafanya wenzake kuwa nje ya wigo, hivyo hakuna hata mmoja wao anayeripotiwa.
- Kuambatanisha moja baadaye kwa kutumia `add_ranges_file()` hakurejeshi ripoti hizo, kwa sababu haisomi kamwe folda ambayo misimbo hii inaripoti.

`resolve_ranges=False` haibadilishi `missing-media` au `media-href-mismatch`: media haisombwi kamwe kwenye modeli, kwa hivyo hakuna kitu cha kujiondoa.

### Misimbo ya vyombo vya habari

sil-lift hutafuta kila faili ya media katika href yake kama ilivyotolewa, pamoja na chini ya `audio/` (media ya matamshi) au `pictures/` (michoro). Folda hiyo ni dhana binafsi ya sil-lift, si kitu kilichoandikwa kwenye hati, kwa hivyo inalingana na uandishi wowote wa herufi kubwa na tahajia yake haijawahi kuripotiwa.

`missing-media` na `media-href-mismatch` hugawanya ukaguzi wa media kati yao: ya kwanza ina maana hakuna faili lililojibu href kwa tahajia yoyote, ya pili ina maana faili lilijibu href lakini href haitaji jina lake kwa usahihi. Ya pili ni ugunduzi wa uhamaji: faili iko hapa, na seva inayohudumia folda hii na kutambua herufi kubwa na ndogo haitaipata.

Folda iliyotajwa vibaya ni moja tu; hata kama inatajwa tena mara nyingi, inaripotiwa mara moja na haina kiingilio. Jina la faili lililoandikwa vibaya linaripotiwa kwa kila rejeleo, likielekezwa kwenye kipengee kilichoandika.

## Matokeo halisi ya FieldWorks (FLEx)

FieldWorks kwa utaratibu huandika baadhi ya maudhui ambayo zana kali hupinga. Hapa kuna sera ya sil-lift, ili kamusi halisi ziwe na manufaa:

- Viungo vya `file://C:/...` (URI zisizofaa) huripotiwa kama **maonyo** (`uri-not-rfc`), si makosa ya schema; mhakiki wa C# haujawahi kuzikataa.
- Watoto walioambatanishwa kisheria (kwa mfano `field, note, field, note`) hawapati alama; hii hupuuza utambuzi potofu katika libxml2.
- Nyongeza za `trait`/`field` za FLEx ndani ya `range-element` zinaripotiwa (makosa ya schema dhidi ya schema ya rangi): ni upotovu halisi wa vipimo.
- Majina yanatatuliwa dhidi ya safu na vitambulisho vya vipengele vya safu chini ya usawazishaji wa Unicode (NFC): viungo vya `parent`, thamani za safu, na jina la `trait` au kitambulisho cha kichwa cha safu kinachoongoza safu.
  - FLEx inalinganisha na NFC wakati wa kusafirisha nje, lakini baadhi ya uandishi ulikuwa ukiepuka hatua hiyo, hivyo `id` ya kipengele cha safu inaweza kuwa NFD wakati lebo zake, `parent` yake mwenyewe, na thamani za `.lift` zinazoiita ni NFC.
  - Ulinganisho sahihi ungekosea hili kwa njia mbili. Rejea za kitambulisho cha NFD zitaripotiwa kuwa zimevunjika, ingawa usafirishaji ni sahihi. Na safu yenye `id` yake iliyobadilishwa kuwa NFD haitachunguzwa: hakuna jina la sifa litakaloendana nayo, na sifa ambayo jina lake haliendani na safu yoyote inakubaliwa kama ilivyo.
  - Jina lililolingana tu baada ya kusawazisha linaripotiwa kama onyo la `normalization-mismatch`, mara moja kwa kila kitambulisho badala ya mara moja kwa kila rejeleo, likielekezwa kwenye faili inayofafanua kitambulisho hicho. Data ni sahihi, lakini mtumiaji anayelinganisha nyuzi ghafi hawezi kutatua marejeleo hayo.
  - Vitambulisho havibadilishwi kamwe: faili linaendelea kuwa na tahajia iliyokuja nalo.
