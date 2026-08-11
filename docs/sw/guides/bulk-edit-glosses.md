# Mfano uliofanyiwa kazi: kuhariri kwa wingi tafsiri fupi

Kazi ya kawaida ya matengenezo: kurekebisha tahajia ili iwe sawa katika kila fasili ya Kiingereza kwenye kamusi (kutoka Kiingereza cha Uingereza hadi Kiingereza cha Marekani, au kinyume chake) bila kuathiri chochote kingine katika faili. Hii inaelezea hatua kwa hatua skripti moja inayopakia, kuhariri, kuthibitisha, na kuhifadhi — ikionyesha API ya uhariri na dhamana ya uaminifu zikifanya kazi pamoja.

## Maandishi

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)


def iter_senses(senses):
    """Yield every sense, including subsenses (recursive)."""
    for sense in senses:
        yield sense
        yield from iter_senses(sense.subsenses)


edited_glosses = 0

for entry in lex.entries:
    for sense in iter_senses(entry.senses):
        for gloss in sense.glosses:
            if gloss.lang != "en":
                continue
            old = str(gloss.text)
            new = old.replace("colour", "color")
            if new != old:
                gloss.text = sil_lift.Text([new])
                edited_glosses += 1

changed = lex.changed_entries()

errors = [p for p in lex.iter_problems() if p.level == "error"]
if errors:
    for problem in errors:
        print(problem)
    sys.exit(f"aborting: {len(errors)} validation error(s), nothing saved")

lex.save()
print(f"edited {edited_glosses} gloss(es) across {len(changed)} entry(ies)")
```

Mambo machache ya kuzingatia:

- `Sense.subsenses` ni `list[Sense]` yenyewe, kwa hivyo `iter_senses` inarudia ndani yake — uhariri wa jumla ambao ungepitia tu `entry.senses` ungeacha kimya kimya fasili yoyote iliyoko chini ya subsense.
- `gloss.text` ni `Text`, si mfululizo wa kawaida: `str(gloss.text)` huifanya iwe mfululizo wa kawaida kwa ajili ya kulinganisha, na mbadala huandikwa tena kwa kutumia `sil_lift.Text([new])` badala ya kubadilisha mfululizo mahali pake.
- `lex.changed_entries()` reports which entries differ from the file as loaded. Since an entry's digest covers its whole subtree, an edit to a nested subsense reports the entry that contains it.
  - It compares serialized content, so assigning a field the value it already had isn't reported.
  - It reports content changes only; `lex.added_entries()` and `lex.removed_entries()` cover entries that appeared or disappeared since loading.
  - It returns the entries themselves, unaffected by `id` being duplicated or absent (which LIFT allows).
  - As a count, it is meaningful only where there is something to compare against. When the passthrough layer declines to byte-scan the source — an encoding that is not ASCII-compatible, or a scanner/parser disagreement — there is no baseline, and `changed_entries()` reports _every_ entry. That is the honest answer for a write guard, since `save()` re-serializes the whole file in that case, but it means the count is the size of the lexicon rather than the size of the edit.
- `lex.changes()` reports whether the document changed _at all_. It covers not just the entries, but also the header, the root element, and every `.lift-ranges` companion.
  - It is falsy only when `save()` would reproduce the source bytes, which makes `if not lex.changes(): ...` the right way to skip an unnecessary write. The guarantee runs one way: it never reports "nothing to write" for a document that would be rewritten, while a change that forces a full re-serialization can land back on the original bytes and still be reported.
  - It compares content, not destination, so guard only an in-place save with it: `lex.save(some_other_dir / "dictionary.lift")` writes the document and its companions to a location that has nothing in it yet, whether or not anything changed.
  - It is a guard, not a speed-up — answering it digests every entry, which is the same work `save()` does to decide passthrough, so what you skip is the write itself (an untouched mtime, no spurious diff), not the effort of deciding.
- Uhakiki katika kumbukumbu (`lex.iter_problems()`) huweka kwanza hali iliyohaririwa kwa mpangilio, hivyo inaonyesha kwa usahihi mabadiliko kabla ya chochote kuandikwa kwenye diski. Kukata shughuli kwa `Problem` yoyote ya kiwango cha `"error"` — maonyo huachwa kwa mtu anayeita ili ahukumu — kunamaanisha kuwa uhariri mbaya hauwahi kufikia `save()`.

Si glosi pekee ndizo zinazostahili kuguswa kwa njia hii. Uso uleule wa ramani wa `Multitext` unatumika kwa ufafanuzi na kila uwanja mwingine wa lugha nyingi kwenye kipengee au maana:

```python
maana.fasili["en"] = "rangi ya kitu"
```

## Kuendesha

Fanya utafutaji dhidi ya kamusi ndogo yenye fasili na fasili ya aina ndogo, zote zikisema "rangi":

```
Imehaririwa: tafsiri 2 katika kipengee 1
```

## Faida ya uaminifu

Dhamana ni kwa kila _entry_: entry ambayo mfano wake haukubadilika hurudi **byte-identical** kama ilivyosomwa, na ni tu entries ulizogusa ndizo zinazotengenezwa tena. Katika mfululizo hapo juu, kipengee kimoja kilikuwa na tafsiri zilizohaririwa — kila kipengee kingine katika faili kilidumisha baiti zake hasa. (Kumbuka kiwango cha undani: kuhariri sehemu yoyote ya kumbukumbu kunasababisha kumbukumbu yote kusimbwa upya kwa mpangilio, ikiwemo hisia zake ndugu ambazo hazijaguswa.) Kurekebisha fasili moja katika kamusi yenye maingizo 50,000 kwa hivyo hutoa tofauti inayogusa kiingizo kimoja, si faili iliyopangwa upya. Tazama [Dhamana za Fidelity](../fidelity.md) kwa mkataba sahihi.
