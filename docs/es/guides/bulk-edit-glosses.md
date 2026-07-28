# Ejemplo práctico: edición masiva de glosas

Una tarea habitual de mantenimiento: armonizar la ortografía de todas las entradas en inglés de un léxico (del inglés británico al americano, o viceversa) sin alterar el resto del archivo. En este ejemplo se muestra paso a paso un script que carga, edita, valida y guarda, lo que permite ver cómo funcionan conjuntamente la API de edición y la garantía de fidelidad.

## El guión

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)


def iter_senses(senses):
    """Devuelve cada acepción, incluidas las subacepciones (recursivo)."""
    for sense in senses:
        yield sense
        yield from iter_senses(sense.subsenses)


edited_glosses = 0
touched_entries = set()

for entry in lex.entries:
    for sense in iter_senses(entry.senses):
        for gloss in sense.glosses:
            if gloss.lang != "en":
                continue
            old = str(gloss.text)
            new = old.replace("colour", "color")
            if new != old:
                gloss.text = sil_lift.Text([new])
                edited_glosses += 1
                touched_entries.add(entry.id)

errors = [p for p in lex.iter_problems() if p.level == "error"]
if errors:
    for problem in errors:
        print(problem)
    sys.exit(f"interrupción: {len(errors)} error(es) de validación, nada guardado")

lex.save()
print(f" {edited_glosses} de glosas editadas en {len(touched_entries)} entrada(s)")
```

Algunas cosas que conviene destacar:

- `Sense.subsenses` es en sí mismo una `lista[Sense]`, por lo que `iter_senses` recorre su contenido de forma recursiva; una edición masiva que solo recorriera `entry.senses` omitiría sin avisar cualquier glosa anidada bajo un subsentido.
- `gloss.text` es un `Text`, no una cadena simple: `str(gloss.text)` lo convierte en una cadena para la búsqueda de coincidencias, y la sustitución se vuelve a escribir con `sil_lift.Text([new])` en lugar de modificar la cadena in situ.
- La validación en memoria (`lex.iter_problems()`) serializa primero el estado editado, de modo que este refleje correctamente los cambios antes de que se guarde nada en el disco. Interrumpir la operación ante cualquier `Problem` de nivel «error» —las advertencias se dejan a criterio de quien realiza la llamada— significa que una edición incorrecta nunca llega a `save()`.

Los brillos no son lo único que merece la pena tratar de esta manera. La misma superficie de asignación `Multitext` se aplica a las definiciones y a cualquier otro campo multilingüe de una entrada o un significado:

```python
sense.definition["en"] = "el color de algo"
```

## Ejecutarlo

Compáralo con un léxico reducido que contenga una entrada y una subentrada que, en ambos casos, indiquen «color»:

```
se han editado 2 glosas en 1 entrada
```

## La recompensa de la fidelidad

La garantía se aplica por _entrada_: una entrada cuyo modelo no haya cambiado se devuelve **identica al nivel de bytes** a como se leyó, y solo se vuelven a serializar las entradas en las que realmente se ha realizado algún cambio. En la ejecución anterior, se editaron las glosas de una entrada; el resto de entradas del archivo conservaron sus bytes exactos. (Fíjate en el nivel de detalle: al editar cualquier parte de una entrada, se vuelve a generar el identificador de serie de toda la entrada, incluidos los significados relacionados que no se hayan modificado.) Por lo tanto, al editar una entrada en un léxico de 50 000 entradas, se genera un archivo «diff» que afecta a una sola entrada, y no un archivo reformateado. Consulta [las garantías de Fidelity](../fidelity.md) para conocer los términos exactos del contrato.
