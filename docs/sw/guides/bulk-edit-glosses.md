# Mfano uliofanyiwa kazi: kuhariri kwa wingi tafsiri fupi

Kazi ya kawaida ya matengenezo: kurekebisha tahajia ili iwe sawa katika kila fasili ya Kiingereza kwenye kamusi (kutoka Kiingereza cha Uingereza hadi Kiingereza cha Marekani, au kinyume chake) bila kuathiri chochote kingine katika faili. Hii inaelezea hatua kwa hatua skripti moja inayopakia, kuhariri, kuthibitisha, na kuhifadhi — ikionyesha API ya uhariri na dhamana ya uaminifu zikifanya kazi pamoja.

## Maandishi

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)


def iter_senses(senses):
    """Yeyeza kila hisia, ikiwa ni pamoja na hisia ndogo (kwa kujirudia)."""
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
- `lex.changed_entries()` huripoti ni vipengee gani vinatofautiana na faili kama ilivyoandaliwa. Kwa kuwa muhtasari wa kijumla wa kipengee unajumuisha tawi lake lote, uhariri wa kipengele kidogo kilichojumuishwa huripoti kipengee kinachokijumuisha.
  - Inalinganisha maudhui yaliyopangwa kwa mfululizo, hivyo kutoa uwanja thamani yake ya awali hakuripotiwi.
  - Inaripoti mabadiliko ya maudhui pekee; `lex.added_entries()` na `lex.removed_entries()` zinashughulikia maingizo yaliyoonekana au yaliyotoweka tangu kupakia.
  - Inarudisha maingizo yenyewe, bila kuathiriwa na `id` kurudiwa au kutokuwepo (jambo ambalo LIFT inaruhusu).
  - Kama hesabu, ina maana tu pale panapokuwa na kitu cha kulinganisha nacho. Wakati skana ya baiti inapokataa kusoma chanzo — kodishaji ambao hauendani na ASCII, au kutokubaliana kwa skana na mchanganuzi — hakuna msingi, na `changed_entries()` inaripoti kila kitu. Hiyo ndiyo jibu la kweli kwa kizuiaji cha kuandika, kwa kuwa `save()` inasababisha kusajili tena faili nzima katika kesi hiyo, lakini hiyo inamaanisha kuwa hesabu ni ukubwa wa kamusi badala ya ukubwa wa uhariri.
- `lex.changes()` huripoti kama hati imebadilika _kabisa_. Haijumuishi tu maingizo, bali pia kichwa, kipengele cha mizizi, na kila mwandani wa `.lift-ranges`.
  - Ni uongo tu wakati `save()` ingezaa tena baiti za chanzo, jambo linalofanya `if not lex.changes(): ...` kuwa njia sahihi ya kuepuka uandishi usiohitajika. Dhamana inaendeshwa upande mmoja: hairipoti kamwe "hakuna cha kuandika" kwa hati ambayo ingeandikwa upya, wakati mabadiliko yanayolazimisha urekebishaji kamili wa mfululizo yanaweza kurudi kwenye baiti za awali na bado kuripotiwa.
  - Inalinganisha yaliyomo, si mahali pa mwisho, kwa hivyo linda tu uhifadhi mahali pake: `lex.save(some_other_dir / "dictionary.lift")` huandika hati na viambatisho vyake kwenye eneo ambalo bado halina chochote, bila kujali kama kitu kimebadilika au la.
  - Ni kizuizi, si kiongezi kasi — kujibu hufanyia uchambuzi kila kipengee, kazi ile ile ambayo `save()` hufanya ili kuamua ni baiti gani za chanzo inaweza kutumia tena, hivyo unachokikwepa ni uandishi wenyewe (muda wa mabadiliko ya faili haujabadilika, hakuna tofauti isiyo ya lazima), si jitihada za kuamua.
- Uhakiki katika kumbukumbu (`lex.iter_problems()`) huweka kwanza hali iliyohaririwa kwa mpangilio, hivyo inaonyesha kwa usahihi mabadiliko kabla ya chochote kuandikwa kwenye diski. Kukata shughuli kwa `Problem` yoyote ya kiwango cha `"error"` — maonyo huachwa kwa mtu anayeita ili aamue — kunamaanisha kuwa uhariri mbaya hautawahi kufikia `save()`.

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
