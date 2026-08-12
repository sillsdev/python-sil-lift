# Leer, editar, escribir

## Cargando

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

La función `load()` admite cualquier documento LIFT **0.13** bien formado, incluidos los archivos reales que no cumplen con el esquema. Todo aquello que el modelo no defina (elementos o atributos desconocidos, comentarios) se transmite sin pérdida de información como residuo LIFT en el campo opaco `extra` de cada nodo. Otras versiones de LIFT generan un error `LiftParseError` indicando la versión.

## El modelo

Cada elemento de LIFT es una clase de datos tipada: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, etc. Un texto multilingüe es un `Multitext`, que se comporta como una correspondencia entre un código de idioma y un `Text`:

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # "abat"
entry.lexical_unit["en"] = "grove"      # las cadenas simples se convierten
"en" in entry.citation                  # False
```

El `texto` está estructurado —una lista ordenada de fragmentos `str` y `Span`— porque `<text>` puede contener marcado anidado `<span>`. `str(text)` convierte el contenido en texto sin formato; los fragmentos conservan el marcado para facilitar la conversión de ida y vuelta.

En LIFT, los glosas tienen forma de _forma_ (cada `<gloss>` tiene su propio lenguaje), por lo que un sentido tiene `glosses: list[Form]`, además de una función auxiliar:

```python
sense = entry.senses[0]
sense.gloss("en")                       # Texto | None
entry.gloss_langs()                     # {"en", "id"}
```

## Ahorro

```python
lex.save()                # volver al lugar desde donde se cargó
lex.save("elsewhere.lift")
```

Las entradas que no hayas modificado se vuelven a escribir **con los mismos bytes**; un documento que no hayas modificado en absoluto es idéntico, byte a byte, desde el primer byte hasta el último. Consulta [las garantías de Fidelity](../fidelity.md) para conocer los términos exactos del contrato.

## Construir desde cero

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

## Ordenación canónica

```python
lex.sort()      # entradas ordenadas por (guid, id); rangos/definiciones de campos por id/etiqueta
lex.save()      # las entradas no modificadas conservan sus bytes exactos, en el nuevo orden

sil_lift.canonicalize("in.lift", "out.lift")   # totalmente reserializado, listo para la comparación de diferencias
```

Véase también: [Ejemplo práctico: edición masiva de glosas](bulk-edit-glosses.md).
