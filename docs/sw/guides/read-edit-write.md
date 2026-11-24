# Soma, hariri, andika

## Inapakia

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` hukubali hati yoyote ya LIFT **0.13** iliyopangwa vizuri, ikiwa ni pamoja na faili halisi zisizoendana na skema. Chochote ambacho mfano haujafafanua (vipengele/sifa zisizojulikana, maoni) huhifadhiwa bila kupoteza kama mabaki ya LIFT katika uwanja wa `extra` usio wazi wa kila node. Toleo zingine za LIFT hutoa `LiftParseError` ikitaja toleo.

## Mfano

Kila kipengele cha LIFT ni dataclass yenye aina: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, na kadhalika.

### Maandishi ya lugha nyingi

Maandishi ya lugha nyingi ni `Multitext`, ambayo ni `Mapping` kutoka kwa msimbo wa lugha hadi `Text`:

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # mistari rahisi hubadilishwa
"en" in entry.citation                  # Si kweli
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` imepangwa (orodha iliyopangwa ya vipande vya `str` na `Span`) kwa sababu `<text>` inaweza kuwa na markup ya `<span>` iliyopachikwa ndani. `str(text)` inageuza kuwa maandishi ya kawaida; vipande vinabaki na alama za uandishi ili kuruhusu kurudi nyuma.

Ramani inaonyesha thamani moja kwa kila lugha. Chini yake, `forms` ina kila `<form>` kwa mpangilio wa faili. Hati iliyothibitishwa na schema ina fomu moja tu kwa kila lugha, lakini faili halisi wakati mwingine hufanya tena fomu moja.

Kwa sababu upangaji umeainishwa kulingana na lugha, `len()` huhesabu lugha badala ya fomu, na mitazamo ya `keys()`, `values()` na `items()` huorodhesha kila lugha mara moja. Mutators zote mbili pia hufanya kazi kwa lugha nzima: `del entry.lexical_unit["en"]` huondoa kila fomu ya Kiingereza, na kuweka thamani kwenye `"en"` huacha moja tu.

Kwa lugha iliyorudiwa, `entry.lexical_unit["en"]`, `get()`, `values()` na `items()` zote hurejesha fomu yake ya kwanza, na [`validate`](validate.md#problem-codes) huripoti `duplicate-form-lang` hadi utakapoiwekea lugha hiyo.

Fomu isiyo na `lang` kabisa haiwezi kuundwa kupitia upangaji. Inaripotiwa kama `form-missing-lang`, na huondolewa wakati node yake inaposerializishwa tena.

### Hisia na tafsiri

Glosses ni _form-shaped_ katika LIFT (kila `<gloss>` lina lugha yake mwenyewe), hivyo sense ina `glosses: list[Form]` pamoja na vifaa vya msaada:

```python
sense = entry.senses[0]       # ngazi ya juu tu
sense.gloss("en")             # Maandishi | Hakuna
entry.all_senses()            # kila maana na maana ndogo, mpangilio wa hati
entry.gloss_langs()           # {"en", "id"}, maana ndogo zimejumuishwa
```

Tumia `all_senses()` kila unapouliza swali linalohusu kijumla kiingizo: kuhesabu maana, kukusanya lugha, kupata vyombo vya habari. `entry.senses` hutoa ngazi ya juu, ambayo ni kile unachotaka tu wakati muingiliano wenyewe ndio muhimu.

## Akiba

```python
lex.save()                    # kurudi mahali ilipopakiwa kutoka
lex.save("elsewhere.lift")
```

Maingizo ambayo hukuyabadilisha yamerudishwa **sawa kwa baiti**; hati ambayo hukuyabadilisha kabisa ni sawa kwa baiti kuanzia baiti ya kwanza hadi ya mwisho. Tazama [Dhamana za Fidelity](../fidelity.md) kwa mkataba sahihi.

### Alama za muda

Maingizo uliyoyabadilisha yanatoka na `dateModified` mpya (na `dateCreated` ikiwa haikuwa na moja), hivyo uhariri hauwasilishwi chini ya tarehe iliyopakiwa nayo. Zana zinazochanganya LIFT huamua ni nini kilichobadilika kutokana na sifa hiyo. Vigezo viwili vinarekebisha upigaji chapa:

- `lex.save(stamp=False)` huandika tarehe tu ambazo mfano una, na hakuna zaidi.
- `lex.save(when=...)` huhifadhi wakati badala ya kusoma saa.

Tazama [Generated timestamps](../fidelity.md#generated-timestamps) kwa sheria zilizobaki.

### Kupuuza uhifadhi ambao haubadilishi chochote

Ili kuruka uhifadhi ambao hautabadilisha chochote, ulinde kwa kutumia `lex.changes()`:

```python
ikiwa lex.changes():
    lex.save()
```

Inarudisha `False` tu wakati `save()` ingeweza kuzalisha tena baiti za chanzo, ikijumuisha maingizo, kichwa, kipengele msingi, na kila mwenza wa `.lift-ranges`. Kupuuza kuandika huacha muda wa mabadiliko wa faili ukiwa kama ulivyo na kuepuka tofauti isiyo ya kweli.

Cheki ni ya bei nafuu. Inasimama tofauti ya kwanza, hivyo kwenye kamusi iliyohaririwa haigharimu karibu chochote. Kamusi isiyobadilika lazima iwekwe katika muundo wa mfululizo kikamilifu ili kuthibitisha kuwa haijabadilika, lakini bado gharama yake ni ndogo kuliko ile ya kuhifadhi inayokosa.

Inalinganisha yaliyomo, sio mahali pa mwisho, kwa hivyo linda tu uhifadhi mahali pake. `lex.save("elsewhere.lift")` huandika hati na viambatisho vyake kwenye njia mpya hata wakati `changes()` ni `False`, hivyo kuiweka chini ya ulinzi kungepuuza nakala hiyo.

## Kujenga kutoka mwanzo

```python
lex = sil_lift.Lexicon(producer="my-script 1.0")
entry = sil_lift.Entry(id="hello", guid="...")
entry.lexical_unit["en"] = "hello"
sense = sil_lift.Sense()
sense.glosses.append(sil_lift.Form("fr", sil_lift.Text(["bonjour"])))
entry.senses.append(sense)
lex.entries.append(entry)
lex.save("new.lift")
```

## Upangaji rasmi

```python
lex.sort()      # maingizo kwa (guid, id); vipimo/ufafanuzi wa uwanja kwa id/tag
lex.save()      # maingizo yasiyoguswa yanabaki na baiti zao halisi, katika mpangilio mpya

sil_lift.canonicalize("in.lift", "out.lift")   # imepangwa tena kikamilifu, tayari kwa tofauti
```

Tazama pia: [Mfano uliofanyiwa kazi: kuhariri kwa wingi tafsiri fupi](bulk-edit-glosses.md).
