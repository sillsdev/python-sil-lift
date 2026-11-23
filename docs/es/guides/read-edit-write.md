# Leer, editar, escribir

## Cargando

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` accepts any well-formed LIFT **0.13** document, including schema-invalid real-world files. Todo aquello que el modelo no defina (elementos o atributos desconocidos, comentarios) se transmite sin pérdida de información como residuo LIFT en el campo opaco `extra` de cada nodo. Otras versiones de LIFT generan un error `LiftParseError` indicando la versión.

## El modelo

Every LIFT element is a typed dataclass: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, and so on.

### Multilingual text

Un texto multilingüe es un `Multitext`, que es una `Mapping` del código de idioma a `Text`:

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # plain strings are coerced
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` is structured (an ordered list of `str` and `Span` fragments) because `<text>` can contain nested `<span>` markup. `str(text)` convierte el contenido en texto sin formato; los fragmentos conservan el marcado para facilitar la conversión de ida y vuelta.

The mapping shows one value per language. Underneath, `forms` holds every `<form>` in file order. A schema-valid document has at most one form per language, but real files sometimes repeat one.

Because the mapping is keyed by language, `len()` counts languages rather than forms, and the `keys()`, `values()` and `items()` views list each language once. Both mutators also act on the whole language: `del entry.lexical_unit["en"]` removes every English form, and assigning to `"en"` leaves exactly one.

For a repeated language, `entry.lexical_unit["en"]`, `get()`, `values()` and `items()` all answer with its first form, and [`validate`](validate.md#problem-codes) reports `duplicate-form-lang` until you assign to that language.

A form carrying no `lang` at all cannot be created through the mapping. It is reported as `form-missing-lang`, and is dropped when its node re-serializes.

### Senses and glosses

En LIFT, los glosas tienen forma de _forma_ (cada `<gloss>` tiene su propio lenguaje), por lo que un sentido tiene `glosses: list[Form]`, además de funciones auxiliares:

```python
sense = entry.senses[0]       # top level only
sense.gloss("en")             # Text | None
entry.all_senses()            # every sense and subsense, document order
entry.gloss_langs()           # {"en", "id"}, subsenses included
```

Recurre a `all_senses()` siempre que una pregunta se refiera a toda la entrada: contar acepciones, recopilar idiomas o buscar archivos multimedia. `entry.senses` proporciona el nivel superior, que es lo que te interesa únicamente cuando el propio anidamiento es relevante.

## Ahorro

```python
lex.save()                    # back to where it was loaded from
lex.save("elsewhere.lift")
```

Las entradas que no hayas modificado se vuelven a escribir **con los mismos bytes**; un documento que no hayas modificado en absoluto es idéntico, byte a byte, desde el primer byte hasta el último. Consulta [las garantías de Fidelity](../fidelity.md) para conocer los términos exactos del contrato.

### Marcas de tiempo

Las entradas que has modificado se publican con una nueva `dateModified` (y una `dateCreated` si no tenían ninguna), por lo que una modificación no se publica con la fecha con la que se cargó. Tools that merge LIFT decide what changed from that attribute. Two arguments adjust the stamping:

- `lex.save(stamp=False)` writes the dates the model holds and nothing more.
- `lex.save(when=...)` pins the moment instead of reading the clock.

Consulta [Marcas de tiempo generadas](../fidelity.md#generated-timestamps) para ver el resto de las reglas.

### Skipping a save that changes nothing

Para omitir un guardado que no supondría ningún cambio, protégelo con `lex.changes()`:

```python
si lex.changes():
    lex.save()
```

Devuelve `False` únicamente cuando `save()` reproduciría los bytes de origen, incluyendo las entradas, el encabezado, el elemento raíz y todos los elementos `.lift-ranges` asociados. Skipping the write leaves the file's modification time alone and avoids a spurious diff.

The check is cheap. Se detiene ante la primera diferencia, por lo que, con un léxico editado, no supone prácticamente ningún coste. Para demostrar que un léxico no ha sufrido cambios, es necesario serializarlo íntegramente, pero eso sigue costando menos que el proceso de guardado que se omite.

Compara el contenido, no el destino, así que asegúrate de que solo se guarde en el mismo lugar. `lex.save("elsewhere.lift")` writes the document and its companions to the new path even when `changes()` is `False`, so guarding it would skip that copy.

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
