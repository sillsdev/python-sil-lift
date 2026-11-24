# Tofauti na maktaba za C\#

sil-lift ina mfanano wa jumla na zana za C# LIFT za SIL, hasa sehemu mbili za [libpalaso](https://github.com/sillsdev/libpalaso):

- `SIL.Lift`: mchanganuzi, mhakiki, mhamishaji, `LiftSorter`.
- `SIL.DictionaryServices`: mfano wa `LexEntry`/`LexSense`, wenye msomaji/mwandishi wake wa LIFT, ambao The Combine na WeSay hutumia.

sil-lift ni utekelezaji mpya, sio toleo la mfumo mwingine. Ukurasa huu unafupisha mahali tabia inatofautiana kwa makusudi.

## Wigo

| Uwezo               | Maktaba za C#                                                                            | sil-lift                                                                                      |
| ------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Toleo za LIFT       | 0.10–0.13 (uhamiaji umejengewa ndani) | **0.13 tu**; matoleo ya zamani yanakataliwa kwa kosa dhahiri                  |
| Uhamishaji wa toleo | `Migrator` (mnyororo wa XSLT)                                         | Hakuna; tumia XSLTs katika lift-standard kwa ajili ya masasisho ya mara moja. |
| Uthibitishaji       | RELAX NG tu (`Validator`)                                             | RELAX NG + masanduku ya schema + ukaguzi wa semantiki                                         |
| Utiririshaji        | Uchanganuzi wa ndani wa kiwango cha kuingia                                              | API ya umma `open_reader` / `open_writer`                                                     |

## Umbo la API

Parser ya `SIL.Lift` inaendeshwa na callback (`ILexiconMerger`): inasukuma matukio ya uchanganuzi kwa mtumiaji. sil-lift badala yake hurudisha grafu ya vitu vya kawaida (dataclasses zilizopangwa aina kwa kila kipengele cha LIFT) kwa sababu watunga skripti wa Python wanataka vitu, si callbacks.

`SIL.DictionaryServices` huweka juu ya `SIL.Lift` mfano wa vitu wa `LexEntry`/`LexSense`, lakini ni mfano wa programu: unawakilisha tu miundo ambayo programu hizo hutumia. Kwa hivyo, kuifanyia serialization tena haiwezi kuhifadhi maudhui yaliyo nje ya mfano kama vile sil-lift inavyoshughulikia mabaki ya LIFT na uaminifu wa baiti (tazama hapa chini).

API ya utiririshaji hutoa aina ile ile ya `Entry`, kwa hivyo hakuna modeli ya pili iliyopunguzwa ya kujifunza.

## Uaminifu wa safari ya kwenda na kurudi

Tofauti iliyokusudiwa yenye nguvu zaidi. Kuhifadhi kwa kutumia `SIL.Lift` kunaserialisha tena hati nzima. sil-lift inahakikisha:

- Hati isiyobadilika huhifadhi **byte-identically**, na
- Ningizo zisizoguswa huhifadhi baiti zao halisi za chanzo hata wakati ningizo nyingine zinapobadilika: ugawaji wa baiti kwa kila nyingizo, unaotumika kiotomatiki.

Tazama [Dhamana za Fidelity](fidelity.md).

## Uthibitishaji

Validator ya C# hufanya upitaji mmoja wa RELAX NG na kuripoti makosa ya kwanza kama nyuzi. sil-lift inaripoti mtiririko wa `Problem` uliopangiliwa, kila mmoja ukiwa na faili, kipengee, na mstari unaohusika. Tabaka lake la schema linatofautiana kwa makusudi katika sehemu tatu:

- **URI zisizo halali ni maonyo, si makosa.** Injini ya C# RELAX NG haijawahi kulazimisha aina ya data `anyURI`, hivyo FieldWorks (FLEx) imekuwa ikiandika hrefs za `file://C:/...` katika kamusi halisi kwa miaka mingi. Kukataa faili hizo kungeweka alama karibu kila toleo la FLEx.
- **Kanuni za Schematron zinatekelezwa** (kama ukaguzi wa kisemantiki): lugha za fomu zinazorudiwa na vikwazo vinavyofanana katika sarufi ya LIFT vilipuuzwa kimya kimya na uthibitishaji wa C#.
- Ulinganisho wa vitambulisho vya masafa umeorodheshwa kwa Unicode (NFC), kwa sababu usafirishaji wa FLEx unachanganya vitambulisho vya NFC na NFD. Rejea ambazo zinatatuliwa tu baada ya urekebishaji wa data hurejelewa kama maonyo ya `normalization-mismatch`, ukaguzi ambao haina sawa yake katika C#. Tazama [matokeo ya Real-world FieldWorks (FLEx)](guides/validate.md#real-world-fieldworks-flex-output).

Wakati sil-lift inapothibitisha `.lift`, pia inathibitisha nyaraka zinaambatana na `.lift-ranges` dhidi ya mpangilio wa hati za masafa huru, uliotolewa na `lift-standard`. Validator ya C# haikagui faili za .lift-ranges.

## Upangaji rasmi

`Lexicon.sort()` inaakisi kanuni za msingi za `LiftSorter` (vipengele kwa `guid` isiyozingatia herufi kubwa/ndogo; viwango na vipengele vya kiwango kwa `id`; ufafanuzi wa nyanja za kichwa kwa `tag`; maana zinahifadhiwa kulingana na mpangilio wa faili; nafasi tupu ndani ya `<text>` haibadilishwi kamwe), na tofauti tatu:

- Ingizo bila guid huorodheshwa kwa utaratibu wa uhakika kulingana na id (`LiftSorter` huchukulia kuwa guid ipo);
- Uagizaji hautegemei eneo (alama za kawaida zilizopinduliwa kwa herufi, si upangaji wa .NET wa utamaduni usiobadilika);
- Orodha za aina moja kama vile noti, uhusiano, na fomu huhifadhi mpangilio wao wa hati badala ya kupangwa upya kwa kutumia ufunguo; upangaji makundi tayari ni wa uhakika, na kuzipanga upya tu huongeza kelele za diff.

`canonicalizeLift.xsl` ya repo ya spec haitumiki kabisa: inafuta nafasi tupu ndani ya maandishi ya kileksiki (huharibu) na vitambulisho vyake vinavyotengenezwa hutofautiana kila inapotekelezwa.

## Haijahamishwa

- Vifaa maalum vya WeSay (udhibiti wa dashibodi/usanidi kuhusu faili za LIFT).
- `SynchronicMerger` (kuunganisha faili za sasisho za LIFT): wazo la kugawanya kwa baiti linaendelea kuishi katika safu ya uaminifu, lakini muunganiko wenyewe haupo.
- Uchanganuzi wa mfumo wa uandishi wa LDML: faili zilizo katika `WritingSystems/` zinachukuliwa kama yaliyomo yasiyoonekana ya folda.
