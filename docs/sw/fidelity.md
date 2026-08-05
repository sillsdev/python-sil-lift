# Dhamana za uaminifu

LIFT ni muundo wa kubadilishana: kanuni kuu ni **usitupe kile usichokielewa**. Mkataba wa `sil-lift`, uliothibitishwa na mkusanyiko wa majaribio katika kila utekelezaji (faili za koropusi pamoja na uundaji unaotegemea sifa):

## Kusoma

Hati yoyote ya LIFT 0.13 iliyoundwa vizuri hupakiwa — ikijumuisha maudhui yasiyoendana na skema. Chochote ambacho mfano haujafafanua huhifadhiwa kwenye baketi isiyoeleweka ya `Extras` ya nodi iliyo karibu zaidi: sifa na vipengele visivyojulikana, maoni ya XML na maagizo ya usindikaji, maandishi yaliyotapakaa, na sifa za aina zisizojengwa ipasavyo (tarehe isiyo sahihi inabaki kama msururu wa awali katika `Extras`; uwanja wa aina ni `None`).

## Kuhifadhi hati bila mabadiliko

`load()` → `save()` bila mabadiliko huandika **matokeo yanayofanana kabisa kwa baiti** — hakuna kupanga upya muundo, hakuna kurejesha tena alama za kutoroka, hakuna kupanga upya mpangilio, alama za mpangilio wa baiti na matangazo ya XML zimejumuishwa. Kwa sasa hakuna orodha ya kawaida: utambulisho ni sahihi kabisa.

Vilevyo vya kipekee (mwandishi anarudi kwenye mfululizo kamili wa kanoniki, ambao kimaana ni kamili lakini hauhifadhi baiti):

- Ukodishaji wa chanzo hauendani na ASCII (sio UTF-8/US-ASCII), au
- chanzo kina DOCTYPE, au
- kikagua baiti na mchanganuzi havikubaliani kuhusu muundo wa ngazi ya juu wa hati — kwa mfano `<header>` ya pili isiyoendana na vipimo, ambayo mchanganuzi huihifadhi mara moja tu (kikagua baiti hakiamini kwa makusudi: shaka yoyote inamaanisha hakuna baiti za chanzo zinazoshikiliwa kabisa), au
- Chanzo kilijengwa kwenye kumbukumbu badala ya kupakiwa kutoka kwenye faili.

## Kuhifadhi hati iliyohaririwa

- **Maingizo yasiyoguswa hutolewa neno kwa neno kutoka kwa baiti zao za awali.** Ingizo linahesabiwa kuwa limeguswa ikiwa sehemu yoyote ya kitu chake cha mfano imebadilika tangu uchanganuzi (inagunduliwa na picha ya kanonali-serialization, si bendera ya uchafu).
- **Maingizo yaliyoguswa yanaserializwa tena kwa kanuni na kikamilifu**: UTF-8, uingizaji wa nafasi mbili _nje_ ya maudhui mchanganyiko (nafasi tupu ndani ya `<text>` na `<span>` haibadilishwi kamwe), upangaji wa vikundi vya watoto uliodokumentishwa kwa kila kipengele (mfano: ingizo: kitengo-cha-msamiati, nukuu, matamshi, aina-tofauti, maana, dondoo, uhusiano, asili-ya-neno, maelezo-ya-nyongeza, sifa, nyanja), mpangilio thabiti wa sifa, tarehe kwa ISO-8601 (`Z` kwa UTC). Baki yote inatolewa tena; nafasi yake inarejeshwa kwenye kiashiria cha awali cha mtoto, na kufungwa kwenye orodha mpya ya watoto (ni makadirio — nafasi halisi za baiti zinahakikishwa tu kwa vipengee visivyoguswa).
- Kuongeza, kuondoa, au kupanga upya maingizo kunasababisha muundo wa hati kusiriwa upya kwa mpangilio wa mfululizo, lakini bado hutoa baiti za kila kiingizo kisichobadilika neno kwa neno.

## Makadirio yanayojulikana (nodsi zilizoguswa pekee)

- Maoni ndani ya utekelezaji wa `<text>` yanahifadhiwa lakini huwekwa juu kando ya utekelezaji, badala ya mahali pao halisi pa herufi.
- Agizo la mtoto la aina ya msalaba ndani ya kipengele kilichohaririwa linawekwa katika muundo wa kawaida wa makundi (shemia ya LIFT `interleave` hufanya mpangilio huu usiwe na maana kimaana).
- Kipengele cha multitext kilichopo lakini hakibebi chochote — hakuna fomu, hakuna mabaki, mfano `<definition></definition>` — hakitolewa tena. Mfano unawakilisha nyanja hizi kama `Multitext` inayopatikana kila wakati (`lexical-unit`, `citation`, `definition`, `usage` ya uhusiano, na `label` / `abbrev` / `description` kwenye marejeleo ya URL, vipimo, vipengele vya kipimo na kichwa), hivyo tupu haiwezi kutofautishwa na kutokuwepo baada ya uchanganuzi. Hakuna kitu cha kisemantiki kinachopotea.
