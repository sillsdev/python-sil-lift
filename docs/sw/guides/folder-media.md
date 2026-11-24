# Folda ya LIFT: masafa na vyombo vya habari

Kamusi ya LIFT kawaida ni _folda_: faili ya `.lift`, faili moja au zaidi za `.lift-ranges` (faili za kando), na midia katika folda za `audio/` na `pictures/`.

## Vipimo

```python
lex = sil_lift.load("dictionary.lift")      # wenzao hufuatiliwa kiotomatiki

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # mtazamo uliounganishwa wa {id: Range}
lex.all_ranges()["grammatical-info"].elements
```

`lex.save()` huandika `.lift` na kila mwandani aliyefuatiliwa pamoja. Marekebisho kwenye `RangesFile` huhifadhiwa tena kwenye faili yake; vipimo visivyoguswa hubaki na baiti zao halisi. Matumizi ya peke yake:

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

### Ugunduzi wa mwenzi

Wagombea kadhaa wanajaribiwa, na kila faili tofauti miongoni mwao inapakia.

- Kichwa `range/@href` kinachoelekeza kwenye faili iliyopo kinatumika kama kilivyo.
- An href ambayo haipati chochote hurudi kwenye jina lake la msingi kando ya `.lift`. FieldWorks huandika njia kamili zisizoshikamana za `file://C:/...` kutoka kwenye mashine inayotuma nje, na njia mbadala hiyo ndiyo inazifanya zifanye kazi ndani ya mfumo.
- Ndugu wa kawaida wa `<name>.lift-ranges` huchaguliwa hata wakati hakuna kinachorejelea.

Majina yanayotofautiana tu kwa herufi kubwa/ndogo au kwa usawazishaji wa Unicode bado yanalingana (`Dict.LIFT` hupata `Dict.lift-ranges`) isipokuwa faili kadhaa zinapolingana na jina moja, ambapo hakuna hata moja linalopakiwa na inaripotiwa kama [`ambiguous-ranges-file`](validate.md#problem-codes).

Nyaraka inayoshindwa kusomwa kama hati ya `<lift-ranges>` (kwa mfano, faili yenye baiti sifuri kutokana na usafirishaji uliokatizwa) inapita badala ya kusababisha kushindwa kwa upakiaji, na inaripotiwa kama [`unreadable-ranges-file`](validate.md#problem-codes). Kupakia moja moja kwa `RangesFile.load()` kunasababisha badala yake.

Pitisha `resolve_ranges=False` kwenye `load()` ili kupuuza ugunduzi wa vifaa viendani.

## Vyombo vya habari

```python
kwa ref katika lex.media_refs():        # kila <media> na <illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.check_media()                   # marejeleo ambayo hayatatatuliwa vizuri
```

Resolution inaifuata mpangilio wa kawaida: href ya uhusiano inachunguzwa kama ilivyo na chini ya `audio/` (kwa vyombo vya matamshi) au `pictures/` (kwa michoro). Backslashes huchukuliwa kama slashi za mbele, kwa kuwa WeSay huandika hrefs kama `pictures\photo with space.png`. Href za mbali na za kabisa haziwezi kukaguliwa na hupitishwa.

`check_media()` inaripoti tu marejeleo ambayo hayakutatuliwa vizuri, moja ya `MediaResolution` kila moja:

- `status="missing"`: hakuna faili lililojibu href kwa tahajia yoyote.
- `status="mismatch"`: moja ilifanikiwa, lakini tu chini ya kufinyanga herufi au NFC; `found` huitaja faili kwenye diski.

Kutokulingana kumetoripotiwa ingawa faili imepatikana. Jina la ziada linalinganishwa kwa uhuru bila maelezo, lakini kiungo cha media pia husomwa na chochote kinachohudumia folda baadaye, na mwenyeji anayezingatia herufi haitapata faili. Validation inaripoti kesi ile ile kama [`media-href-mismatch`](validate.md#problem-codes).

## Maudhui mengine ya folda

Folda ya LIFT mara nyingi huwa na faili ambazo sil-lift haizifanyii modeli, kama vile LDML ya mfumo wa uandishi chini ya `WritingSystems/` au faili za idhini za spika za The Combine chini ya `consent/`. `load()` na `save()` hazibadilishi hizi, na [`Lexicon.save_zip()`](lift-export-interop.md) huzihamisha neno kwa neno wakati wa kufunga folda.
