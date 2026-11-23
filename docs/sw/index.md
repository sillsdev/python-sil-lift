# sil-lift

Maktaba ya Python kwa [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon Interchange FormaT) 0.13: kusoma/kuandika bila kupoteza data ya folda ya LIFT (` .lift` + ` .lift-ranges` + marejeleo ya media), uthibitishaji wa schema na semantiki, na upangaji sahihi, pamoja na API za mtiririko kwa kamusi kubwa.

Hali: kabla ya kutolewa, inatengenezwa.

## Sakinisha

Kutoka [PyPI](https://pypi.org/project/sil-lift/):

```
pip install sil-lift # maktaba + amri ya sil-lift
```

Inahitaji Python 3.11 na zaidi. Utegemezi pekee wakati wa utekelezaji ni lxml.

## Ziara ya sekunde 30

Pakia kamusi, tafuta maingizo ya Kihawai yasiyo na tafsiri ya Kiingereza, hariri ufafanuzi, na uhifadhi:

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # tracks .lift-ranges companions too

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("haw") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # au lex.find(id="poʻo_a1b2")
entry.senses[0].definition["en"] = "kichwa (anatomia)"

lex.save()   # kipengee kilichohaririwa kimewekwa tena kwenye mfululizo na kupigwa muhuri tena; sehemu zilizobaki ni sawa byte kwa byte
```
