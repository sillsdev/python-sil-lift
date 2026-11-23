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

Parser ya `SIL.Lift` inaendeshwa na callback (`ILexiconMerger`): inasukuma matukio ya uchanganuzi kwa mtumiaji. sil-lift instead returns a plain object graph (typed dataclasses for every LIFT element) because Python scripters want objects, not callbacks.

`SIL.DictionaryServices` does layer a `LexEntry`/`LexSense` object model over `SIL.Lift`, but it is an application model: it represents only the constructs those apps use. Re-serializing through it therefore can't preserve out-of-model content the way sil-lift's LIFT residue handling and byte fidelity do (see below).

API ya utiririshaji hutoa aina ile ile ya `Entry`, kwa hivyo hakuna modeli ya pili iliyopunguzwa ya kujifunza.

## Uaminifu wa safari ya kwenda na kurudi

Tofauti iliyokusudiwa yenye nguvu zaidi. Kuhifadhi kwa kutumia `SIL.Lift` kunaserialisha tena hati nzima. sil-lift inahakikisha:

- Hati isiyobadilika huhifadhi **byte-identically**, na
- untouched entries keep their exact source bytes even when other entries change: per-entry byte chunking, applied automatically.

Tazama [Dhamana za Fidelity](fidelity.md).

## Uthibitishaji

Validator ya C# hufanya upitaji mmoja wa RELAX NG na kuripoti makosa ya kwanza kama nyuzi. sil-lift reports a structured `Problem` stream, each carrying the file, entry, and line it concerns. Its schema layer knowingly diverges in three places:

- **URI zisizo halali ni maonyo, si makosa.** Injini ya C# RELAX NG haijawahi kulazimisha aina ya data `anyURI`, hivyo FieldWorks (FLEx) imekuwa ikiandika hrefs za `file://C:/...` katika kamusi halisi kwa miaka mingi. Kukataa faili hizo kungeweka alama karibu kila toleo la FLEx.
- **Schematron rules are enforced** (as semantic checks): duplicate form languages and similar co-constraints in the LIFT grammar were silently ignored by C# validation.
- **Range id comparisons are Unicode-normalized** (NFC), because FLEx exports mix NFC and NFD ids. References that resolve only after normalizing are reported as `normalization-mismatch` warnings, a check with no C# counterpart. See [Real-world FieldWorks (FLEx) output](guides/validate.md#real-world-fieldworks-flex-output).

When sil-lift validates a `.lift`, it also validates the `.lift-ranges` companions against a schema for standalone ranges documents, vendored from `lift-standard`. The C# `Validator` does not check `.lift-ranges` files.

## Upangaji rasmi

`Lexicon.sort()` inaakisi kanuni za msingi za `LiftSorter` (vipengele kwa `guid` isiyozingatia herufi kubwa/ndogo; viwango na vipengele vya kiwango kwa `id`; ufafanuzi wa nyanja za kichwa kwa `tag`; maana zinahifadhiwa kulingana na mpangilio wa faili; nafasi tupu ndani ya `<text>` haibadilishwi kamwe), na tofauti tatu:

- Ingizo bila guid huorodheshwa kwa utaratibu wa uhakika kulingana na id (`LiftSorter` huchukulia kuwa guid ipo);
- Uagizaji hautegemei eneo (alama za kawaida zilizopinduliwa kwa herufi, si upangaji wa .NET wa utamaduni usiobadilika);
- same-type lists such as notes, relations, and forms keep their document order rather than being re-sorted by key; grouping is already deterministic, and reordering them only adds diff noise.

`canonicalizeLift.xsl` ya repo ya spec haitumiki kabisa: inafuta nafasi tupu ndani ya maandishi ya kileksiki (huharibu) na vitambulisho vyake vinavyotengenezwa hutofautiana kila inapotekelezwa.

## Haijahamishwa

- Vifaa maalum vya WeSay (udhibiti wa dashibodi/usanidi kuhusu faili za LIFT).
- `SynchronicMerger` (LIFT update-file merging): the byte-chunking idea lives on in the fidelity layer, the merging does not.
- Uchanganuzi wa mfumo wa uandishi wa LDML: faili zilizo katika `WritingSystems/` zinachukuliwa kama yaliyomo yasiyoonekana ya folda.
