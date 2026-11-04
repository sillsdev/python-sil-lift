# Dhamana za uaminifu

LIFT ni muundo wa kubadilishana, kwa hivyo kanuni ya kwanza ni **kamwe usitupe kile usichokielewa**. Mkataba wa `sil-lift`, uliothibitishwa na mkusanyiko wa majaribio katika kila utekelezaji (faili za koropusi pamoja na uundaji unaotegemea sifa):

## Kusoma

Hati yoyote ya LIFT 0.13 iliyoundwa vizuri hupakiwa — ikijumuisha maudhui yasiyoendana na skema. Chochote ambacho mfano haujafafanua huhifadhiwa kwenye kontena la `Extras` lisilo wazi la nodi iliyo karibu zaidi kama _baki ya LIFT_ — jina la FieldWorks kwa wazo lile lile, ambalo huhifadhiwa katika uwanja wa `LiftResidue`: sifa na vipengele visivyojulikana, maoni ya XML na maagizo ya usindikaji, maandishi yaliyotapakaa, na sifa za aina zisizojengwa ipasavyo (tarehe isiyo sahihi hubaki kama msururu wa awali katika `Extras`; uwanja uliopangwa ni `None`).

## Kuhifadhi hati bila mabadiliko

`load()` → `save()` bila mabadiliko huandika **matokeo yanayofanana kabisa kwa baiti** — hakuna kupanga upya muundo, hakuna kurejesha tena alama za kutoroka, hakuna kupanga upya mpangilio, alama za mpangilio wa baiti na matangazo ya XML zimejumuishwa. Kwa sasa hakuna orodha ya kawaida: utambulisho ni sahihi kabisa. Alama za muda hutolewa kutoka kwa maudhui, hivyo hati ambayo haijabadilika pia haina alama zozote zilizotolewa.

Vilevyo vya kipekee (mwandishi anarudi kwenye mfululizo kamili wa kanoniki, ambao kimaana ni kamili lakini hauhifadhi baiti):

- Ukodishaji wa chanzo hauendani na ASCII (sio UTF-8/US-ASCII), au
- chanzo kina DOCTYPE, au
- Kichanganuzi cha baiti na kichanganaji havikubaliani kuhusu muundo wa ngazi ya juu wa hati — kwa mfano `<header>` ya pili isiyoendana na vigezo, ambayo kichanganaji huihifadhi mara moja tu (kichanganuzi cha baiti kinajihifadhi kwa tahadhari: kinapokuwa na shaka hakichukui baiti zozote za chanzo), au
- Chanzo kilijengwa kwenye kumbukumbu badala ya kupakiwa kutoka kwenye faili.

## Kuhifadhi hati iliyohaririwa

- **Maingizo yasiyoguswa hutolewa neno kwa neno kutoka kwa baiti zao za awali.** Ingizo linahesabiwa kuwa limeguswa ikiwa sehemu yoyote ya kitu chake cha mfano imebadilika tangu uchanganuzi (inagunduliwa na picha ya kanonali-serialization, si bendera ya uchafu).
- Maingizo yaliyoguswa yanarudishwa katika mpangilio rasmi na kamili.   Fomu rasmi ni:
  - UTF-8.
  - Uingizaji wa nafasi mbili _nje_ ya maudhui mchanganyiko; nafasi tupu ndani ya `<text>` na `<span>` haibadilishwi kamwe.
  - Uainishaji wa watoto uliodokumentishwa kwa kila kipengele; kwa `<entry>`: kitengo cha kisarufi, nukuu, matamshi, matoleo, maana, maelezo, uhusiano, etimolojia, maelezo ya ziada, sifa, nyanja.
  - Mpangilio wa sifa umewekwa.
  - Tarehe kwa ISO-8601 (`Z` kwa UTC).
- **Baki yote inatolewa tena.** Nafasi yake inarejeshwa kwenye kiashiria cha awali cha mtoto, ikifungwa kwenye orodha mpya ya watoto — ni makadirio tu, kwani nafasi halisi za baiti zinahakikishwa tu kwa maingizo yasiyoguswa.
- Kuongeza, kuondoa, au kupanga upya maingizo kunasababisha muundo wa hati kusiriwa upya kwa mpangilio wa mfululizo, lakini bado hutoa baiti za kila kiingizo kisichobadilika neno kwa neno.
- Kuingia kulichapwa ni kuchapwa na `dateModified` mpya, na `dateCreated` ikiwa haikuwa na moja — tazama [Vichapwa vilivyotengenezwa](#generated-timestamps).

!!! note "&quot;&quot; rasmi hapa haihusiani na XML rasmi nyingine yoyote."
    Fomu kanoniki kwenye ukurasa huu inamaanisha umbo halisi lililoandikwa la `sil-lift`, lililoelezwa katika nukta hapo juu. Haifungamani na mchakato wa W3C wa Canonical XML (C14N). Haijahusiana na darasa la `CanonicalXmlSettings` la `SIL.Core`.

## Alama za muda zilizotengenezwa

Stampu iliyotengenezwa ndicho kitu pekee katika pato ambacho hakitegemei ingizo.

- **Kilichochapishwa.** Kila kipengee ambacho maudhui yake yamebadilika tangu kiliposomwa, kikiwa na `dateModified` mpya na, ikiwa hakikuwa nacho, `dateCreated` ya wakati huo huo. Marekebisho yaliyotumwa chini ya tarehe yake ya kupakia yanaonekana hayajabadilika kwa kila kitu kinacholingana na sifa hiyo, ikiwa ni pamoja na FieldWorks na uingizaji wa LIFT wa The Combine.
- Maingizo pekee. Hakuna nodi chini ya `<entry>`, na hakuna chochote kwenye kichwa.
- **Kile kilichoachwa peke yake.** Kuingia ambako tarehe yake imewekwa kwa makusudi na mtu anayepiga simu, na kuingia iliyoundwa tangu upakiaji ambayo tayari ina moja.
- Kuhakikisha tarehe haijabadilika kunaheshimiwa. `entry.date_modified = None` kwenye kipengee kinaposomwa na thamani moja ni thamani iliyokusudiwa kama nyingine yoyote, hivyo kipengee hicho kinatoka bila `dateModified` iwe yaliyomo yamehamishwa au la. Kuingiza bila moja ni kesi tofauti: `None` hapo tayari iko mahali pake, haiwezi kutofautishwa na kutogusa kabisa uwanja, hivyo uhariri bado unaiweka alama.
- Tarehe isiyoweza kuchakatwa inabadilishwa. Tarehe ambayo mfano haukuweza kuichakata ni [residue](#reading) badala ya tarehe, hivyo stempu inaandikwa juu yake na mstari wa awali unaachwa — ni bora zaidi kwa kumbukumbu iliyohaririwa kubeba tarehe halisi kuliko `dateModified="whenever"`.
- **Muda huu.** UTC kwa usahihi wa sekunde (`YYYY-MM-DDTHH:MM:SSZ`, muundo unaotumiwa na kila usafirishaji wa FieldWorks uliofanyiwa utafiti), uliosomwa kutoka kwenye saa ya ukutani. Sekunde moja ina tarehe moja, hivyo mhariri uliohifadhiwa ndani ya sekunde moja tangu ule uliopita una chapa ile ile.
- `save(when=...)` hutoa wakati badala ya saa ya ukutani, jambo ambalo linafanya matokeo yaliyowekwa alama yawe yanayoweza kurudiwa kwa lango la CI linalotegemea diff. Inapaswa kuwa na ufahamu wa eneo la saa, na imewekwa kwa sekunde kamili za UTC.
- `save(stamp=False)` huandika modeli kama ilivyo, ikijumuisha mabaki.
- Kukamilisha commit kwa `.lift` write. Kitu chochote kinachozuia kuandikwa hicho kutumika kinarudisha tarehe nyuma. Mara inaposhuka, husimama, hata kama jaribio la kuandika la mwenzake litaanguka baadaye.

## Maudhui ya XML hayawezi kuwakilisha

Herufi zisizo za BMP — emoji, CJK Extension B, Adlam, chochote kilicho juu ya U+FFFF — ni maudhui ya kawaida na hubadilishwa na kurudi kwa utambulisho sawa wa baiti. "Jozi mbadala" ni undani wa usimbaji wa UTF-16: nyuzi za Python ni mfululizo wa alama za msimbo, hivyo hakuna chochote katika msomaji, skana ya baiti, au mwandishi kinachoona moja.

Surrogate _peke yake_ (U+D800–U+DFFF) ni tofauti: mstari wa Python unaweza kubeba moja, hati ya XML haiwezi, katika msimbo wowote. Haiwezi kamwe kufika kutoka kwenye faili — mchanganuzi anakataa tahajia zote mbili, rejeleo la alama `&#xD800;` na baiti za CESU-8/WTF-8 — inapatikana tu kutoka kwenye msururu uliopewa kupitia API. Kuhifadhi mfano kama huo kunasababisha `LiftWriteError` inayotaja node na codepoint na hakuna chochote kinachoandikwa; uthibitishaji unaripoti kama kosa moja la `lone-surrogate`, kwa kuwa hati haiwezi kuseriwaliswa ili tabaka za skema ziweze kuikagua.

## Makadirio yanayojulikana (nodsi zilizoguswa pekee)

- Maoni ndani ya utekelezaji wa `<text>` huhifadhiwa lakini huhamishwa kando ya utekelezaji, badala ya kuwekwa mahali pake hasa kulingana na nafasi ya herufi.
- Agizo la mtoto la aina ya msalaba ndani ya kipengele kilichohaririwa linawekwa katika muundo wa kawaida wa makundi (shemia ya LIFT `interleave` hufanya mpangilio huu usiwe na maana kimaana).
- <form>` au `<gloss>` bila `lang` haitolewi tena, na wala chochote kilichohifadhiwa ndani yake; uthibitishaji huripoti ukosefu huo kama `form-missing-lang`. Kichwa kisichoguswa huhifadhi baiti zake za chanzo, hivyo aina hii hudumu hadi kitu ndani ya kichwa chake kihaririwe.
- Kipengele cha multitext kilichopo lakini hakibebi chochote — hakuna fomu, hakuna mabaki, mfano `<definition></definition>` — hakitolewa tena. Mfano unawakilisha nyanja hizi kama `Multitext` inayopatikana kila wakati (`lexical-unit`, `citation`, `definition`, `usage` ya uhusiano, na `label` / `abbrev` / `description` kwenye marejeleo ya URL, vipimo, vipengele vya kipimo na kichwa), hivyo tupu haiwezi kutofautishwa na kutokuwepo baada ya uchanganuzi. Hakuna kitu cha kisemantiki kinachopotea.
