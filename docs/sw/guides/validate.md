# Thibitisha

Uthibitishaji daima ni wazi — kupakia na kuhifadhi kamwe havithibitishi kwa njia fiche.

```python
import sil_lift

# Exhaustive: mtiririko wa vigezo (schema + tabaka za semantiki).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # kosa [dangling-ref] dictionary.lift:88 (entry apu): ref 'nope' inalingana ...

# Fail-fast: inasababisha LiftValidationError kwenye tatizo la kwanza la kiwango cha kosa.
sil_lift.validate_file("dictionary.lift")

# Hali ya kumbukumbu (inayosafirishwa kwanza — gharama iliyoorodheshwa kwa kamusi kubwa):
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Kila `Problem` hubeba `level` (`"error"`/`"warning"`), `code` thabiti, `message`, na anwani yoyote ile ambayo ugunduzi unao: `file` (`None` wakati kamusi haina njia), `entry_id` linapohusu kipengee kimoja, `guid` linapohusu kitu kinachohusika kikiwa nacho (kipengee, au kipengele cha safu), na `line` linapohusiana na mstari katika hati. Matokeo kuhusu safu huelekezwa kwa kiongozi mwenza `.lift-ranges` unaoifafanua, na haina kipengee. Sehemu zisizowekwa ni `None` — `null` katika `--format json`, ambapo kila ufunguo daima upo.

## Tabaka

1. **RELAX NG** dhidi ya sarufi ya LIFT 0.13 (iliyotolewa kutoka lift-standard — nakala inayofanana byte kwa byte iliyowekwa katika kifurushi hiki).
2. **Rangi za schema** — `lift-ranges-0.13.rng` ya mradi huu — juu ya kila mwenzi wa `.lift-ranges` unaofuatiliwa, ikielekezwa kwa mwenzi badala ya `.lift`.
3. **Ukaguzi wa semanti** ambao sarufi haiwezi kuonyesha — tisa kati yao, kila moja ikiwa na msimbo wake.

## Misimbo ya matatizo

Kila ugunduzi huambatana na mojawapo ya hizi, kulingana na safu iliyouzalisha — `schema` na `uri-not-rfc` hutoka kwenye safu za schema, na tisa zilizobaki ni ukaguzi wa semantiki. Vifungo ni kiolesura kinachotumika; `--strict` huibadilisha kila onyo kuwa kosa.

| msimbo                         | kiwango  | kinachoashiria                                                                                         |
| ------------------------------ | -------- | ------------------------------------------------------------------------------------------------------ |
| viwigo-vinavyoelea-href        | Onyo     | Kichwa `range/@href` kinachotatua hadi faili rafiki isiyopo                                            |
| rejea-isiyo na mwisho          | Hitilafu | `relation/@ref` au `variant/@ref` inayolingana na kiingilio au maana yoyote                            |
| fomu-maradufu-lugha            | Onyo     | fomu mbili katika maandishi mengi yanayoshiriki lugha moja                                             |
| nakala-ya-guid                 | Hitilafu | mwongozo unaotumika tena miongoni mwa maingizo, au miongoni mwa wigo/vipengele-vya-wigo vya hati moja  |
| kitambulisho-kinachokosekana   | Hitilafu | kuingia kwa hiari kupitia `require_ids`: kipengee kisicho na guid, hisia kisicho na id |
| Vyombo vya habari vinakosekana | Onyo     | Faili ya sauti au picha iliyorejelewa haipo kwenye diski                                               |
| kutopatana kwa urekebishaji    | Onyo     | Jina linalofikia kitambulisho kinachorejelewa tu kupitia NFC                                           |
| eneo-mzazi                     | Hitilafu | Hakuna id ya ndugu inayotambuliwa na `range-element/@parent`.                          |
| `shemia`                       | Hitilafu | ukiukaji wa sarufi ya RELAX NG, katika `.lift` au katika faili rafiki                                  |
| Thamani-ya-wigo-isiyoainishwa  | Onyo     | Thamani ya sifa ya taarifa ya kisarufi au yenye funguo za wigo ambayo wigo haitaorodhesha              |
| URL si RFC                     | Onyo     | href ambayo si URI halali — `file://C:/...` ya FLEx                                                    |

## Matokeo halisi ya FieldWorks (FLEx)

FieldWorks kwa utaratibu huandika baadhi ya maudhui ambayo zana kali hupinga. Hapa kuna sera ya sil-lift, ili kamusi halisi ziwe na manufaa:

- Viungo vya `file://C:/...` (URI zisizofaa) huripotiwa kama **maonyo** (`uri-not-rfc`), si makosa ya skema — mhakiki wa C# haujawahi kuzikataa.
- Watoto waliopangwa kisheria (kwa mfano `field, note, field, note`) hawapati alama, hivyo kuepuka matokeo ya uongo chanya katika libxml2.
- Nyongeza za `trait`/`field` za FLEx ndani ya `range-element` zinaripotiwa (makosa ya schema dhidi ya schema ya rangi): ni upotovu halisi wa vipimo.
- Majina yanatafsiriwa kulingana na safu na vitambulisho vya vipengele vya safu chini ya usawazishaji wa Unicode (NFC) — viungo vya `parent`, thamani za safu, na jina la `trait` au kitambulisho cha kichwa cha safu kinachoongoza safu. FLEx inalinganisha na NFC wakati wa kusafirisha nje, lakini baadhi ya uandishi ulikuwa ukiepuka hatua hiyo, hivyo `id` ya kipengele cha safu inaweza kuwa NFD wakati lebo zake, `parent` yake mwenyewe, na thamani za `.lift` zinazoiita ni NFC.
  - Ikilinganishwa kwa usahihi, usafirishaji wa sauti unaonekana umevunjika — na safu yenye `id` iliyotamkwa kinyume haikaguliwi kabisa, kwa kuwa jina la sifa lisilofikia safu lolote linakubaliwa kimya kimya.
  - Jina lililolingana tu baada ya urekebishaji linaripotiwa kama onyo la `normalization-mismatch`, mara moja kwa kila kitambulisho hata kama marejeleo mengi yanatofautiana, likielekezwa kwenye faili inayofafanua kitambulisho hicho. Data ni sahihi, lakini mtumiaji anayelinganisha nyuzi ghafi hawezi kutatua marejeleo hayo.
  - Vitambulisho havibadilishwi kamwe: faili linaendelea kuwa na tahajia iliyokuja nalo.
