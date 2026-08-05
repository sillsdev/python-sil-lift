# Folda ya LIFT: masafa na vyombo vya habari

Kamusi ya LIFT kawaida ni _folda_: faili ya `.lift`, moja au zaidi ya faili za `.lift-ranges` zinazohusiana, na media za `audio/` / `pictures/`.

## Vipimo

```python
lex = sil_lift.load("dictionary.lift")      # wenzao hufuatiliwa kiotomatiki

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # mtazamo uliounganishwa wa {id: Range}
lex.all_ranges()["grammatical-info"].elements
```

Ugunduzi wa Companion unashughulikia ulimwengu halisi: `range/@href` inayoelekeza kwenye faili iliyopo hutumika; Viungo kamili vilivyokatika vya FieldWorks (`file://C:/...`) hurudi kwenye jina la msingi la faili lililo kwenye `.lift`; na ndugu wa kawaida `<name>.lift-ranges` huchukuliwa hata kama hakuna kinachorejelea.

`lex.save()` huandika `.lift` na kila mwandani aliyefuatiliwa pamoja. Marekebisho kwenye `RangesFile` huhifadhiwa tena kwenye faili yake; vipimo visivyoguswa hubaki na baiti zao halisi. Matumizi ya peke yake:

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

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
