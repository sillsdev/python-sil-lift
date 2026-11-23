# Dhamana za uaminifu

LIFT ni muundo wa kubadilishana, kwa hivyo kanuni ya kwanza ni **kamwe usitupe kile usichokielewa**. Mkataba wa `sil-lift`, uliothibitishwa na mkusanyiko wa majaribio katika kila utekelezaji (faili za koropusi pamoja na uundaji unaotegemea sifa):

## Kusoma

Any well-formed LIFT 0.13 document loads, schema-invalid content included. Whatever the model does not define is carried in the nearest node's opaque `Extras` container as _LIFT residue_. (That is FieldWorks' name for the same idea, which it stores in a `LiftResidue` field.) Residue includes:

- unknown attributes and elements;
- XML comments and processing instructions;
- stray text;
- malformed typed attributes: a bad date stays as the original string in `Extras`, and the typed field is `None`.

## Kuhifadhi hati bila mabadiliko

`load()` → `save()` with no edits writes **byte-identical output**: no reformatting, no re-escaping, no reordering, byte-order marks and XML declarations included. Kwa sasa hakuna orodha ya kawaida: utambulisho ni sahihi kabisa. Alama za muda hutolewa kutoka kwa maudhui, hivyo hati ambayo haijabadilika pia haina alama zozote zilizotolewa.

Vilevyo vya kipekee (mwandishi anarudi kwenye mfululizo kamili wa kanoniki, ambao kimaana ni kamili lakini hauhifadhi baiti):

- Ukodishaji wa chanzo hauendani na ASCII (sio UTF-8/US-ASCII), au
- chanzo kina DOCTYPE, au
- the byte scanner and the parser disagree about the document's top-level structure, for instance an out-of-spec second `<header>`, which the parser keeps only once, or
- Chanzo kilijengwa kwenye kumbukumbu badala ya kupakiwa kutoka kwenye faili.

The byte scanner is deliberately conservative: on any doubt it captures no source bytes at all.

## Kuhifadhi hati iliyohaririwa

- **Maingizo yasiyoguswa hutolewa neno kwa neno kutoka kwa baiti zao za awali.** Ingizo linahesabiwa kuwa limeguswa ikiwa sehemu yoyote ya kitu chake cha mfano imebadilika tangu uchanganuzi (inagunduliwa na picha ya kanonali-serialization, si bendera ya uchafu).
- Maingizo yaliyoguswa yanarudishwa katika mpangilio rasmi na kamili.   Fomu rasmi ni:
  - UTF-8.
  - Uingizaji wa nafasi mbili _nje_ ya maudhui mchanganyiko; nafasi tupu ndani ya `<text>` na `<span>` haibadilishwi kamwe.
  - Uainishaji wa watoto uliodokumentishwa kwa kila kipengele; kwa `<entry>`: kitengo cha kisarufi, nukuu, matamshi, matoleo, maana, maelezo, uhusiano, etimolojia, maelezo ya ziada, sifa, nyanja.
  - Mpangilio wa sifa umewekwa.
  - Tarehe kwa ISO-8601 (`Z` kwa UTC).
- **All residue is re-emitted.** Its position is restored to the original child index, clamped to the new child list; that is an approximation, since exact byte positions are only guaranteed for untouched entries.
- Kuongeza, kuondoa, au kupanga upya maingizo kunasababisha muundo wa hati kusiriwa upya kwa mpangilio wa mfululizo, lakini bado hutoa baiti za kila kiingizo kisichobadilika neno kwa neno.
- **A touched entry is stamped** with a fresh `dateModified`, and a `dateCreated` if it had none. See [Generated timestamps](#generated-timestamps).

!!! note "&quot;&quot; rasmi hapa haihusiani na XML rasmi nyingine yoyote."

    Fomu kanoniki kwenye ukurasa huu inamaanisha umbo halisi lililoandikwa la `sil-lift`, lililoelezwa katika nukta hapo juu. Haifungamani na mchakato wa W3C wa Canonical XML (C14N). Haijahusiana na darasa la `CanonicalXmlSettings` la `SIL.Core`.

## Alama za muda zilizotengenezwa

Stampu iliyotengenezwa ndicho kitu pekee katika pato ambacho hakitegemei ingizo.

### Which entries are stamped

- **Kilichochapishwa.** Kila kipengee ambacho maudhui yake yamebadilika tangu kiliposomwa, kikiwa na `dateModified` mpya na, ikiwa hakikuwa nacho, `dateCreated` ya wakati huo huo. Marekebisho yaliyotumwa chini ya tarehe yake ya kupakia yanaonekana hayajabadilika kwa kila kitu kinacholingana na sifa hiyo, ikiwa ni pamoja na FieldWorks na uingizaji wa LIFT wa The Combine.
- Maingizo pekee. Hakuna nodi chini ya `<entry>`, na hakuna chochote kwenye kichwa.
- **Kile kilichoachwa peke yake.** Kuingia ambako tarehe yake imewekwa kwa makusudi na mtu anayepiga simu, na kuingia iliyoundwa tangu upakiaji ambayo tayari ina moja.
- Kuhakikisha tarehe haijabadilika kunaheshimiwa. `entry.date_modified = None` kwenye kipengee kinaposomwa na thamani moja ni thamani iliyokusudiwa kama nyingine yoyote, hivyo kipengee hicho kinatoka bila `dateModified` iwe yaliyomo yamehamishwa au la.
  - Kuingiza bila moja ni kesi tofauti: `None` hapo tayari iko mahali pake, haiwezi kutofautishwa na kutogusa kabisa uwanja, hivyo uhariri bado unaiweka alama.
- **An unparseable date is replaced.** A date the model could not parse is [residue](#reading) rather than a date, so a stamp overwrites it and the original string is dropped. An edited entry is better off carrying a real date than `dateModified="whenever"`.

### How the stamp is applied

- **Muda huu.** UTC kwa usahihi wa sekunde (`YYYY-MM-DDTHH:MM:SSZ`, muundo unaotumiwa na kila usafirishaji wa FieldWorks uliofanyiwa utafiti), uliosomwa kutoka kwenye saa ya ukutani. Sekunde moja ina tarehe moja, hivyo mhariri uliohifadhiwa ndani ya sekunde moja tangu ule uliopita una chapa ile ile.
- `save(when=...)` hutoa wakati badala ya saa ya ukutani, jambo ambalo linafanya matokeo yaliyowekwa alama yawe yanayoweza kurudiwa kwa lango la CI linalotegemea diff. Inapaswa kuwa na ufahamu wa eneo la saa, na imewekwa kwa sekunde kamili za UTC.
- `save(stamp=False)` huandika modeli kama ilivyo, ikijumuisha mabaki.
- Kukamilisha commit kwa `.lift` write. Kitu chochote kinachozuia kuandikwa hicho kutumika kinarudisha tarehe nyuma. Mara inaposhuka, husimama, hata kama jaribio la kuandika la mwenzake litaanguka baadaye.

## Maudhui ya XML hayawezi kuwakilisha

Non-BMP characters (emoji, CJK Extension B, Adlam, anything above U+FFFF) are ordinary content and round-trip byte-identically. "Jozi mbadala" ni undani wa usimbaji wa UTF-16: nyuzi za Python ni mfululizo wa alama za msimbo, hivyo hakuna chochote katika msomaji, skana ya baiti, au mwandishi kinachoona moja.

Surrogate _peke yake_ (U+D800–U+DFFF) ni tofauti: mstari wa Python unaweza kubeba moja, hati ya XML haiwezi, katika msimbo wowote. It can never arrive from a file, because the parser rejects both spellings (a `&#xD800;` character reference and CESU-8/WTF-8 bytes). It can only come from a string assigned through the API.

Saving such a model raises `LiftWriteError` naming the node and the codepoint, and writes nothing. Validation reports it as a single `lone-surrogate` error, since the document cannot be serialized for the schema layers to check.

## Makadirio yanayojulikana (nodsi zilizoguswa pekee)

- Maoni ndani ya utekelezaji wa `<text>` huhifadhiwa lakini huhamishwa kando ya utekelezaji, badala ya kuwekwa mahali pake hasa kulingana na nafasi ya herufi.
- Agizo la mtoto la aina ya msalaba ndani ya kipengele kilichohaririwa linawekwa katika muundo wa kawaida wa makundi (shemia ya LIFT `interleave` hufanya mpangilio huu usiwe na maana kimaana).
- <form>` au `<gloss>` bila `lang` haitolewi tena, na wala chochote kilichohifadhiwa ndani yake; uthibitishaji huripoti ukosefu huo kama `form-missing-lang`. Kichwa kisichoguswa huhifadhi baiti zake za chanzo, hivyo aina hii hudumu hadi kitu ndani ya kichwa chake kihaririwe.
- A multitext element that is present but carries nothing (no forms, no residue, e.g. `<definition></definition>`) is not re-emitted. Hakuna kitu cha kisemantiki kinachopotea.
  - The model represents these fields as an always-present `Multitext`, so an empty one is indistinguishable from an absent one after parsing. The fields are `lexical-unit`, `citation`, `definition`, a relation's `usage`, and `label` / `abbrev` / `description` on url-refs, ranges, range-elements and the header.
