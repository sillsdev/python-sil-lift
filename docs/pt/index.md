# sil-lift

Uma biblioteca Python para o [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon Interchange FormaT) 0.13: leitura e gravação sem perdas da pasta LIFT (`.lift` + `.lift-ranges` + referências de multimédia), validação do esquema e semântica, e ordenação canónica — com APIs de streaming para léxicos de grande dimensão.

**Estado: pré-lançamento, em desenvolvimento ativo.**

## Instalar

Extraído do [PyPI](https://pypi.org/project/sil-lift/):

```
pip install sil-lift   # biblioteca + o comando sil-lift
```

Requer o Python 3.11 ou superior. A única dependência de execução é o lxml.

## A visita guiada de 30 segundos

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # também rastreia os companheiros dos intervalos .lift

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("seh") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # ou lex.find(id="hoofd_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"

lex.save()   # as entradas não alteradas mantêm-se idênticas em termos de bytes; a entrada editada é novamente serializada
```
