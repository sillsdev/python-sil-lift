# Faili kubwa (mtiririko)

`load()` huunda grafu nzima ya vitu. Kwa kamusi zenye mamia ya MB, API ya utiririshaji huchakata kipengee kimoja kwa wakati katika kumbukumbu yenye ukomo. Inatoa aina ile ile ya `Entry`, hivyo msimbo ulioandikwa kwa ajili ya hali moja unafanya kazi katika hali nyingine.

## Kusoma

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # imeparswa mapema (kabla ya entries)
    for entry in reader:              # lazy Iterator[Entry]
        ...
```

## Uandishi

```python
with sil_lift.open_reader("big.lift") as reader, sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) as writer:
    for entry in reader:
        if not entry.date_deleted:      # mfano, ruka maingizo yaliyowekwa kuwa yamefutwa
            writer.write(entry)
```

Maelezo:

- Matokeo ya mwandishi ni sawa kabisa na kile ambacho serializer kanoniki ya hati kamili ingetengeneza kwa maudhui yale yale; modi hizo mbili hazitawahi kutofautiana.
- Modi ya utiririshaji haitumii tena baiti zozote za chanzo: pato daima ni sahihi. Residue ya LIFT ya kiwango cha mizizi (maoni kati ya vipengele na sifa zisizo za mpangilio kwenye `<lift>`) imepuuzwa, lakini vipengele na kichwa vinabaki na residue zao wenyewe.
- Tofauti na [`Lexicon.save()`](../fidelity.md#saving-an-edited-document), modi ya mtiririko haizalishi alama za muda. Kuingia huandikwa kwa tarehe zilizopo tayari: pasi ya kutiririsha haioni kamwe hati kama ilivyokuwa, hivyo haiwezi kusema ni vipengele gani ulivyobadilisha. Weka `entry.date_modified` mwenyewe kwenye zile ambazo toleo hili linazirekebisha.
- Ikiwa kosa la ndani ya bloku ya `open_writer` litaibuka, faili itaachwa ikiwa haijakamilika waziwazi (hakuna `</lift>` ya kufunga). Hii inazuia kamusi iliyoandikwa nusu ionekane imekamilika.
