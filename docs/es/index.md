# sil-lift

Una biblioteca de Python para [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon Interchange FormaT) 0.13: lectura y escritura sin pérdidas de la carpeta LIFT (`.lift` + `.lift-ranges` + referencias a medios), validación semántica y del esquema, y ordenación canónica, con API de streaming para léxicos de gran tamaño.

**Estado: versión preliminar, en fase de desarrollo activo.**

## Instalar

De [PyPI](https://pypi.org/project/sil-lift/):

```
pip install sil-lift   # biblioteca + el comando sil-lift
```

Requiere Python 3.11 o superior. La única dependencia de ejecución es lxml.

## El recorrido de 30 segundos

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # también rastrea los términos asociados a los rangos .lift

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("seh") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # o lex.find(id="hoofd_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"

lex.save()   # las entradas no modificadas son idénticas a nivel de bytes; la entrada editada se vuelve a serializar
```
