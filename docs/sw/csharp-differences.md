# Tofauti na maktaba za C\#

sil-lift ni mfano hafifu wa zana za LIFT za C# za SIL — hasa `SIL.Lift` katika [libpalaso](https://github.com/sillsdev/libpalaso) (mshinikizo, mhakiki, mhamishaji, `LiftSorter`), `SIL.DictionaryServices` katika repo hiyo hiyo (mfano wa `LexEntry`/`LexSense`, ukiwa na msomaji/mwandishi wake wa LIFT, ambao The Combine na WeSay hutumia), na vishughulikiaji vya LIFT katika [Chorus](https://github.com/sillsdev/chorus). Ni utekelezaji mpya, sio toleo lililohamishwa. Ukurasa huu unafupisha mahali tabia inatofautiana kwa makusudi.

## Wigo

| Uwezo                               | Maktaba za C#                                                                            | sil-lift                                                                      |
| ----------------------------------- | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Toleo za LIFT                       | 0.10–0.13 (uhamiaji umejengewa ndani) | **0.13 tu**; matoleo ya zamani yanakataliwa kwa kosa dhahiri  |
| Uhamishaji wa toleo                 | `Migrator` (mnyororo wa XSLT)                                         | Hakuna — tumia XSLTs katika lifti-kawaida kwa ajili ya masasisho ya mara moja |
| Muunganiko/Ulinganisho wa njia tatu | Kwaya                                                                                    | Nje ya wigo                                                                   |
| Uthibitishaji                       | RELAX NG tu (`Validator`)                                             | RELAX NG + masanduku ya schema + ukaguzi wa semantiki                         |
| Utiririshaji                        | Uchanganuzi wa ndani wa kiwango cha kuingia                                              | API ya umma `open_reader` / `open_writer`                                     |

## Umbo la API

Parser ya `SIL.Lift` inaendeshwa na callback (`ILexiconMerger`): inasukuma matukio ya uchanganuzi kwa mtumiaji. sil-lift badala yake hurudisha grafu ya vitu ya kawaida — dataclasses zilizotengwa aina kwa kila kipengele cha LIFT — kwa sababu watunzi wa skripti za Python wanataka vitu, si callbacks. `SIL.DictionaryServices` huweka juu ya `SIL.` mfano wa kitu wa `LexEntry`/`LexSense`Lift`, lakini kama mfano wa programu unawakilisha tu miundo ambayo programu hizo hutumia — hivyo kuirudisha tena katika muundo kupitia kwake haiwezi kuhifadhi maudhui yaliyo nje ya mfano kama vile sil-lift inavyofanya kwa kunasa mabaki na uaminifu wa baiti (tazama hapa chini). API ya utiririshaji hutoa aina ile ile ya `Entry\`, kwa hivyo hakuna mfano wa pacha uliopunguzwa uwezo.

## Uaminifu wa safari ya kwenda na kurudi

Tofauti iliyokusudiwa yenye nguvu zaidi. Kuhifadhi kwa kutumia `SIL.Lift` kunaserialisha tena hati nzima. sil-lift inahakikisha:

- Hati isiyobadilika huhifadhi **byte-identically**, na
- Ningizo zisizoguswa huhifadhi baiti zao halisi za chanzo hata wakati nyingo zingine zinabadilika (Ugawaji wa baiti wa kiwango cha Chorus, unaotumika kiotomatiki).

Tazama [Dhamana za Fidelity](fidelity.md).

## Uthibitishaji

Validator ya C# hufanya upitaji mmoja wa RELAX NG na kuripoti makosa ya kwanza kama nyuzi. sil-lift inaripoti mtiririko wa `Problem` uliopangiliwa, wa kuingia/anwani-ya-mstari, na safu yake ya schema inakwenda njia tofauti kwa makusudi katika sehemu tatu:

- **URI zisizo halali ni maonyo, si makosa.** Injini ya C# RELAX NG haijawahi kulazimisha aina ya data `anyURI`, hivyo FieldWorks (FLEx) imekuwa ikiandika hrefs za `file://C:/...` katika kamusi halisi kwa miaka mingi. Kukataa faili hizo kungeweka alama karibu kila toleo la FLEx.
- **Kanuni za Schematron zinatekelezwa** (kama ukaguzi wa kisemantiki): lugha za fomu zilizorudiwa na vikwazo vinavyofanana katika sarufi ya LIFT vilipuuzwa kimya kimya na C# na uthibitishaji wa lxml ghafi.
- Ulinganisho wa faili-msalaba ume-normalishwa kwa Unicode, kwa sababu FLEx huandika `.lift` katika NFC na faili mwenza `.lift-ranges` katika NFD.

sil-lift pia huthibitisha faili za `.lift-ranges` zinazohusiana na kamusi iliyopakiwa dhidi ya skema ya nyaraka huru za masafa (zilizotolewa kutoka `lift-standard` pamoja na sarufi ya msingi ya LIFT) — kila faili ya masafa ya nje inayofuatiliwa hukaguliwa kila wakati `.lift` inapothibitishwa — bila mpangilio kama huo (au ukaguzi) katika ulimwengu wa C#. Hakuna njia ya kuthibitisha faili ya `.lift-ranges` peke yake, bila kuwa na faili ya `.lift`.

## Upangaji rasmi

`Lexicon.sort()` inaakisi kanuni za msingi za `LiftSorter` (vipengele kwa `guid` isiyozingatia herufi kubwa/ndogo; viwango na vipengele vya kiwango kwa `id`; ufafanuzi wa nyanja za kichwa kwa `tag`; maana zinahifadhiwa kulingana na mpangilio wa faili; nafasi tupu ndani ya `<text>` haibadilishwi kamwe), na tofauti tatu:

- Ingizo bila guid huorodheshwa kwa utaratibu wa uhakika kulingana na id (`LiftSorter` huchukulia kuwa guid ipo);
- Uagizaji hautegemei eneo (alama za kawaida zilizopinduliwa kwa herufi, si upangaji wa .NET wa utamaduni usiobadilika);
- Orodha za aina moja kama vile dondoo, mahusiano, na fomu zinadumisha mpangilio wao wa hati badala ya kupangwa upya kwa kutumia funguo — upangaji wa makundi tayari ni wa uhakika, na kuzipanga upya kunazidisha tu kelele za utofauti.

`canonicalizeLift.xsl` ya repo ya spec haitumiki kabisa: inafuta nafasi tupu ndani ya maandishi ya kileksiki (huharibu) na vitambulisho vyake vinavyotengenezwa hutofautiana kila inapotekelezwa.

## Haijahamishwa

- Vifaa maalum vya WeSay (udhibiti wa dashibodi/usanidi kuhusu faili za LIFT).
- `SynchronicMerger` (Uunganishaji wa masasisho ya kwaya) — wazo la kugawanya baiti katika vipande linaendelea kuishi katika safu ya uaminifu, lakini uunganishaji wenyewe hauendelei.
- Uchanganuzi wa mfumo wa uandishi wa LDML: faili zilizo katika `WritingSystems/` zinachukuliwa kama yaliyomo yasiyoonekana ya folda.
