# Folda ya LIFT: masafa na vyombo vya habari

Kamusi ya LIFT kawaida ni _folda_: faili ya `.lift`, moja au zaidi ya faili wasaidizi za `.lift-ranges` (faili za pembeni), na midia ya `audio/` / `pictures/`.

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
- An href ambayo haipati chochote hurudi kwenye jina lake la msingi kando ya `.lift` — FieldWorks huandika njia kamili zisizo na mwisho `file://C:/...` kutoka kwenye mashine ya kusafirisha, na kurejea huko ndiko kunafanya zifanye kazi ndani ya eneo.
- Ndugu wa kawaida wa `<name>.lift-ranges` huchaguliwa hata wakati hakuna kinachorejelea.

Majina yanayotofautiana tu kwa herufi kubwa/ndogo au kwa usawazishaji wa Unicode bado yanalingana — `Dict.LIFT` hupata `Dict.lift-ranges` — isipokuwa faili kadhaa zinapolingana na jina moja, ambalo halipaki yoyote kati yao na linaripotiwa kama [`ambiguous-ranges-file`](validate.md#problem-codes).

Pitisha `resolve_ranges=False` kwenye `load()` ili kupuuza ugunduzi wa vifaa viendani.

## Vyombo vya habari

```python
kwa ref katika lex.media_refs():        # kila <media> na <illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.missing_media()                 # marejeleo ambayo faili zao hazipo
```

Resolution inafuata mpangilio wa kawaida: href ya jamaa inachunguzwa kama ilivyo (backslashes zimewekwa sawa — WeSay inaandika `pictures\photo with space.png`) na chini ya `audio/` (kwa vyombo vya matamshi) au `pictures/` (kwa michoro). Href za mbali/kamili haziwezi kukaguliwa na hupitishwa.

## Maudhui mengine ya folda

Folda ya LIFT mara nyingi huwa na faili ambazo sil-lift haizifanyi modeli — LDML ya mfumo wa uandishi chini ya `WritingSystems/`, faili za sauti/picha za idhini za The Combine chini ya `consent/`, na kadhalika; `load()`/`save()` hazibadilishi hizi, na [`Lexicon.save_zip()`](lift-export-interop.md) huzihamisha neno kwa neno wakati wa kufunga folda.
