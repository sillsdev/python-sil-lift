# Soma, hariri, andika

## Inapakia

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` accepts any well-formed LIFT **0.13** document, including schema-invalid real-world files. Chochote ambacho mfano haujafafanua (vipengele/sifa zisizojulikana, maoni) huhifadhiwa bila kupoteza kama mabaki ya LIFT katika uwanja wa `extra` usio wazi wa kila node. Toleo zingine za LIFT hutoa `LiftParseError` ikitaja toleo.

## Mfano

Every LIFT element is a typed dataclass: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, and so on.

### Multilingual text

Maandishi ya lugha nyingi ni `Multitext`, ambayo ni `Mapping` kutoka kwa msimbo wa lugha hadi `Text`:

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # plain strings are coerced
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` is structured (an ordered list of `str` and `Span` fragments) because `<text>` can contain nested `<span>` markup. `str(text)` inageuza kuwa maandishi ya kawaida; vipande vinabaki na alama za uandishi ili kuruhusu kurudi nyuma.

The mapping shows one value per language. Underneath, `forms` holds every `<form>` in file order. A schema-valid document has at most one form per language, but real files sometimes repeat one.

Because the mapping is keyed by language, `len()` counts languages rather than forms, and the `keys()`, `values()` and `items()` views list each language once. Both mutators also act on the whole language: `del entry.lexical_unit["en"]` removes every English form, and assigning to `"en"` leaves exactly one.

For a repeated language, `entry.lexical_unit["en"]`, `get()`, `values()` and `items()` all answer with its first form, and [`validate`](validate.md#problem-codes) reports `duplicate-form-lang` until you assign to that language.

A form carrying no `lang` at all cannot be created through the mapping. It is reported as `form-missing-lang`, and is dropped when its node re-serializes.

### Senses and glosses

Glosses ni _form-shaped_ katika LIFT (kila `<gloss>` lina lugha yake mwenyewe), hivyo sense ina `glosses: list[Form]` pamoja na vifaa vya msaada:

```python
sense = entry.senses[0]       # top level only
sense.gloss("en")             # Text | None
entry.all_senses()            # every sense and subsense, document order
entry.gloss_langs()           # {"en", "id"}, subsenses included
```

Tumia `all_senses()` kila unapouliza swali linalohusu kijumla kiingizo: kuhesabu maana, kukusanya lugha, kupata vyombo vya habari. `entry.senses` hutoa ngazi ya juu, ambayo ni kile unachotaka tu wakati muingiliano wenyewe ndio muhimu.

## Akiba

```python
lex.save()                    # back to where it was loaded from
lex.save("elsewhere.lift")
```

Maingizo ambayo hukuyabadilisha yamerudishwa **sawa kwa baiti**; hati ambayo hukuyabadilisha kabisa ni sawa kwa baiti kuanzia baiti ya kwanza hadi ya mwisho. Tazama [Dhamana za Fidelity](../fidelity.md) kwa mkataba sahihi.

### Alama za muda

Maingizo uliyoyabadilisha yanatoka na `dateModified` mpya (na `dateCreated` ikiwa haikuwa na moja), hivyo uhariri hauwasilishwi chini ya tarehe iliyopakiwa nayo. Tools that merge LIFT decide what changed from that attribute. Two arguments adjust the stamping:

- `lex.save(stamp=False)` writes the dates the model holds and nothing more.
- `lex.save(when=...)` pins the moment instead of reading the clock.

Tazama [Generated timestamps](../fidelity.md#generated-timestamps) kwa sheria zilizobaki.

### Skipping a save that changes nothing

Ili kuruka uhifadhi ambao hautabadilisha chochote, ulinde kwa kutumia `lex.changes()`:

```python
ikiwa lex.changes():
    lex.save()
```

Inarudisha `False` tu wakati `save()` ingeweza kuzalisha tena baiti za chanzo, ikijumuisha maingizo, kichwa, kipengele msingi, na kila mwenza wa `.lift-ranges`. Skipping the write leaves the file's modification time alone and avoids a spurious diff.

The check is cheap. Inasimama tofauti ya kwanza, hivyo kwenye kamusi iliyohaririwa haigharimu karibu chochote. Kamusi isiyobadilika lazima iwekwe katika muundo wa mfululizo kikamilifu ili kuthibitisha kuwa haijabadilika, lakini bado gharama yake ni ndogo kuliko ile ya kuhifadhi inayokosa.

Inalinganisha yaliyomo, sio mahali pa mwisho, kwa hivyo linda tu uhifadhi mahali pake. `lex.save("elsewhere.lift")` writes the document and its companions to the new path even when `changes()` is `False`, so guarding it would skip that copy.

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
