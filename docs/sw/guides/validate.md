# Thibitisha

Uthibitishaji daima ni wazi — kupakia na kuhifadhi kamwe havithibitishi kwa njia fiche.

```python
import sil_lift

# Exhaustive: mtiririko wa vigezo (schema + tabaka za semantiki).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # kosa [dangling-ref] dictionary.lift:88 (entry apu): ref 'nope' inalingana ...

# Fail-fast: inasababisha LiftValidationError kwenye tatizo la kwanza la kiwango cha kosa.
sil_lift.validate_file("dictionary.lift")

# Hali ya kumbukumbu (inayosafirishwa kwanza — gharama iliyoorodheshwa kwa kamusi kubwa):
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Kila `Problem` ina `level` (`"error"`/`"warning"`), `code` thabiti, `message`, na anwani: `file`, `entry_id`, `guid`, `line`.

## Tabaka

1. **RELAX NG** dhidi ya sarufi ya LIFT 0.13 (iliyotolewa na lift-standard).
2. **Rangi za schema** — `lift-ranges-0.13.rng` ya mradi huu — juu ya kila kiambatisho cha `.lift-ranges` kinachofuatiliwa.
3. **Ukaguzi wa semantiki** ambao sarufi haiwezi kuonyesha: `duplicate-guid`, `dangling-ref`, `range-parent`, `undefined-range-value`, `duplicate-form-lang`, `missing-media`.

## Matokeo halisi ya FieldWorks (FLEx)

FieldWorks kwa utaratibu huandika baadhi ya maudhui ambayo zana kali hupinga. Hapa kuna sera ya sil-lift, ili kamusi halisi ziwe na manufaa:

- Viungo vya `file://C:/...` (URI zisizofaa) huripotiwa kama **maonyo** (`uri-not-rfc`), si makosa ya skema — mhakiki wa C# haujawahi kuzikataa.
- Watoto waliopangwa kisheria (kwa mfano `field, note, field, note`) hawapati alama, hivyo kuepuka matokeo ya uongo chanya katika libxml2.
- Thamani za masafa zinalinganishwa chini ya usawa wa Unicode NFC — FLEx huandika `.lift` katika NFC lakini `.lift-ranges` katika NFD ndani ya usafirishaji uleule.
- Nyongeza za `trait`/`field` za FLEx ndani ya `range-element` zinaripotiwa (makosa ya schema dhidi ya schema ya rangi): ni upotovu halisi wa vipimo.
