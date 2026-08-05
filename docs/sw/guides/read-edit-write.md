# Soma, hariri, andika

## Inapakia

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` hukubali hati yoyote ya LIFT **0.13** iliyopangwa vizuri — ikiwa ni pamoja na faili halisi zisizoendana na skema. Chochote ambacho mfano haujatambua (vipengele/sifa zisizojulikana, maoni) huhifadhiwa bila kupoteza katika kikapu kisichoeleweka cha `extra` cha kila node. Toleo zingine za LIFT hutoa `LiftParseError` ikitaja toleo.

## Mfano

Kila kipengele cha LIFT ni dataclass iliyotengwa aina: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, na kadhalika. Maandishi ya lugha nyingi ni `Multitext`, ambayo hufanya kazi kama uhusiano kutoka kwa msimbo wa lugha hadi `Text`:

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # "abat"
entry.lexical_unit["en"] = "grove"      # nyuzi rahisi zinageuzwa
"en" in entry.citation                  # Si kweli
```

`Text` imepangwa — orodha iliyopangwa ya vipande vya `str` na `Span` — kwa sababu `<text>` inaweza kuwa na markup ya `<span>` iliyojificha ndani yake. `str(text)` inageuza kuwa maandishi ya kawaida; vipande vinabaki na alama za uandishi ili kuruhusu kurudi nyuma.

Glosses ni _form-shaped_ katika LIFT (kila `<gloss>` lina lugha yake mwenyewe), hivyo sense ina `glosses: list[Form]` pamoja na kisaidizi:

```python
sense = entry.senses[0]
sense.gloss("en")                       # Text | None
entry.gloss_langs()                     # {"en", "id"}
```

## Akiba

```python
lex.save()                # kurudi mahali ilipopakiwa kutoka
lex.save("elsewhere.lift")
```

Maingizo ambayo hukuyabadilisha yamerudishwa **sawa kwa baiti**; hati ambayo hukuyabadilisha kabisa ni sawa kwa baiti kuanzia baiti ya kwanza hadi ya mwisho. Tazama [Dhamana za Fidelity](../fidelity.md) kwa mkataba sahihi.

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
