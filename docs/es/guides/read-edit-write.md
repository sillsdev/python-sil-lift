# Leer, editar, escribir

## Cargando

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` admite cualquier documento LIFT **0.13** bien formado, incluidos los archivos reales que no cumplen con el esquema. Todo aquello que el modelo no defina (elementos o atributos desconocidos, comentarios) se transmite sin pérdida de información como residuo LIFT en el campo opaco `extra` de cada nodo. Otras versiones de LIFT generan un error `LiftParseError` indicando la versión.

## El modelo

Cada elemento de LIFT es una clase de datos tipada: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, etc.

### Texto multilingüe

Un texto multilingüe es un `Multitext`, que es una `Mapping` del código de idioma a `Text`:

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # «poʻo»
entry.lexical_unit["en"] = "head"       # las cadenas simples se convierten
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

El `texto` está estructurado (una lista ordenada de fragmentos `str` y `Span`) porque `<text>` puede contener marcado anidado `<span>`. `str(text)` convierte el contenido en texto sin formato; los fragmentos conservan el marcado para facilitar la conversión de ida y vuelta.

La tabla muestra un valor por idioma. En su interior, `forms` contiene todos los `<form>` en el orden en que aparecen en el archivo. Un documento válido según el esquema tiene, como máximo, un formulario por idioma, pero en los archivos reales a veces se repite uno.

Dado que la correspondencia se organiza por idiomas, `len()` cuenta los idiomas en lugar de los formularios, y las vistas `keys()`, `values()` e `items()` muestran cada idioma una sola vez. Ambos mutadores actúan además sobre todo el lenguaje: `del entry.lexical_unit["en"]` elimina todas las formas en inglés, y al asignar un valor a `"en"` queda exactamente una.

En el caso de un idioma repetido, `entry.lexical_unit["en"]`, `get()`, `values()` e `items()` devuelven su primera forma, y [`validate`](validate.md#problem-codes) muestra el error `duplicate-form-lang` hasta que se le asigne ese idioma.

No es posible crear un formulario que no contenga ningún atributo `lang` mediante la asignación. Se notifica como «form-missing-lang» y se elimina cuando su nodo se vuelve a serializar.

### Significados y glosas

En LIFT, los glosas tienen forma de _forma_ (cada `<gloss>` tiene su propio lenguaje), por lo que un sentido tiene `glosses: list[Form]`, además de funciones auxiliares:

```python
sense = entry.senses[0]       # solo el nivel superior
sense.gloss("en")             # Texto | None
entry.all_senses()            # todos los significados y subsignificados, en el orden del documento
entry.gloss_langs()           # {"en", "id"}, incluidos los subsignificados
```

Recurre a `all_senses()` siempre que una pregunta se refiera a toda la entrada: contar acepciones, recopilar idiomas o buscar archivos multimedia. `entry.senses` proporciona el nivel superior, que es lo que te interesa únicamente cuando el propio anidamiento es relevante.

## Ahorro

```python
lex.save()                    # volver al lugar desde donde se cargó
lex.save("elsewhere.lift")
```

Las entradas que no hayas modificado se vuelven a escribir **con los mismos bytes**; un documento que no hayas modificado en absoluto es idéntico, byte a byte, desde el primer byte hasta el último. Consulta [las garantías de Fidelity](../fidelity.md) para conocer los términos exactos del contrato.

### Marcas de tiempo

Las entradas que has modificado se publican con una nueva `dateModified` (y una `dateCreated` si no tenían ninguna), por lo que una modificación no se publica con la fecha con la que se cargó. Las herramientas que fusionan LIFT determinan qué ha cambiado en ese atributo. Hay dos parámetros que permiten ajustar el estampado:

- `lex.save(stamp=False)` guarda las fechas que contiene el modelo y nada más.
- `lex.save(when=...)` fija el momento en lugar de leer el reloj.

Consulta [Marcas de tiempo generadas](../fidelity.md#generated-timestamps) para ver el resto de las reglas.

### Omitir una partida guardada que no cambia nada

Para omitir un guardado que no supondría ningún cambio, protégelo con `lex.changes()`:

```python
si lex.changes():
    lex.save()
```

Devuelve `False` únicamente cuando `save()` reproduciría los bytes de origen, incluyendo las entradas, el encabezado, el elemento raíz y todos los elementos `.lift-ranges` asociados. Si se omite la escritura, no se modifica la fecha de modificación del archivo y se evita que aparezca una diferencia errónea.

El cheque es barato. Se detiene ante la primera diferencia, por lo que, con un léxico editado, no supone prácticamente ningún coste. Para demostrar que un léxico no ha sufrido cambios, es necesario serializarlo íntegramente, pero eso sigue costando menos que el proceso de guardado que se omite.

Compara el contenido, no el destino, así que asegúrate de que solo se guarde en el mismo lugar. `lex.save("elsewhere.lift")` guarda el documento y sus archivos asociados en la nueva ruta incluso cuando `changes()` es `False`, por lo que, si se protege esta operación, se omitiría esa copia.

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
