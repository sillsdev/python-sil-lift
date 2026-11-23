# sil-lift

Una biblioteca de Python para [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon Interchange FormaT) 0.13: lectura y escritura sin pérdida de datos de la carpeta LIFT (`.lift` + `.lift-ranges` + referencias a medios), validación del esquema y semántica, y ordenación canónica, además de API de streaming para léxicos de gran tamaño.

**Estado: versión preliminar, en fase de desarrollo activo.**

## Instalar

De [PyPI](https://pypi.org/project/sil-lift/):

```
pip install sil-lift   # biblioteca + el comando sil-lift
```

Requiere Python 3.11 o superior. La única dependencia de ejecución es lxml.

## El recorrido de 30 segundos

Carga un léxico, busca las entradas en hawaiano que no tengan glosa en inglés, edita una definición y guarda:

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # también rastrea los términos asociados de los rangos .lift

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("haw") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # o lex.find(id="poʻo_a1b2")
entry.senses[0].definition["en"] = "cabeza (anatomía)"

lex.save()   # la entrada editada se vuelve a serializar y se le asigna un nuevo sello; el resto es idéntico byte a byte
```
