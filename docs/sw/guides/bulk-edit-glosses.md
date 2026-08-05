# Mfano uliofanyiwa kazi: kuhariri kwa wingi tafsiri fupi

Kazi ya kawaida ya matengenezo: kurekebisha tahajia ili iwe sawa katika kila fasili ya Kiingereza kwenye kamusi (kutoka Kiingereza cha Uingereza hadi Kiingereza cha Marekani, au kinyume chake) bila kuathiri chochote kingine katika faili. Hii inaelezea hatua kwa hatua skripti moja inayopakia, kuhariri, kuthibitisha, na kuhifadhi — ikionyesha API ya uhariri na dhamana ya uaminifu zikifanya kazi pamoja.

## Maandishi

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)


def iter_senses(senses):
    """Yatoa kila hisia, ikiwa ni pamoja na hisia ndogo (kwa kujirudia)."""
    for sense in senses:
        yield sense
        yield from iter_senses(sense.subsenses)


edited_glosses = 0
touched_entries = set()

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
                touched_entries.add(entry.id)

errors = [p for p in lex.iter_problems() if p.level == "error"]
if errors:
    for problem in errors:
        print(problem)
    sys.exit(f"aborting: {len(errors)} validation error(s), nothing saved")

lex.save()
print(f"edited {edited_glosses} gloss(es) across {len(touched_entries)} entry(ies)")
```

Mambo machache ya kuzingatia:

- `Sense.subsenses` ni `list[Sense]` yenyewe, kwa hivyo `iter_senses` inarudia ndani yake — uhariri wa jumla ambao ungepitia tu `entry.senses` ungeacha kimya kimya fasili yoyote iliyoko chini ya subsense.
- `gloss.text` ni `Text`, si mfululizo wa kawaida: `str(gloss.text)` huifanya iwe mfululizo wa kawaida kwa ajili ya kulinganisha, na mbadala huandikwa tena kwa kutumia `sil_lift.Text([new])` badala ya kubadilisha mfululizo mahali pake.
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
