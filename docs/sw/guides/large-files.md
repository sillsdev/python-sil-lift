# Faili kubwa (mtiririko)

`load()` huunda grafu nzima ya vitu. Kwa kamusi zenye mamia ya MB, API ya mtiririko huchakata kipengee kimoja kwa wakati katika kumbukumbu yenye ukomo — aina ile ile ya `Entry`, hivyo msimbo ulioandikwa kwa njia moja unafanya kazi katika njia nyingine.

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # imeparswa mapema (kabla ya entries)
    for entry in reader:              # lazy Iterator[Entry]
        ...
```

```python
with sil_lift.open_reader("big.lift") as reader, sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) as writer:
    for entry in reader:
        if not entry.date_deleted:    # mfano, ondoa tombstones
            writer.write(entry)
```

Maelezo:

- Matokeo ya mwandishi ni sawa kabisa na kile ambacho serializer kanoniki kamili ya hati ingetengeneza kwa maudhui yale yale — modi hizo mbili haziwahi kutofautiana.
- Modi ya utiririshaji haitumii tena baiti zozote za chanzo: pato daima ni sahihi. Baki ya LIFT ya kiwango cha mizizi — maoni kati ya vipengele na sifa zisizo za mpangilio kwenye `<lift>` — haibebwi; vipengele na kichwa ni kamili, ikijumuisha baki.
- Ikiwa bloku ya `open_writer` itapandishwa, faili inabaki haijakamilika wazi (bila `</lift>` ya kufunga) — kamusi iliyoandikwa nusu haipaswi kuonekana imekamilika.
