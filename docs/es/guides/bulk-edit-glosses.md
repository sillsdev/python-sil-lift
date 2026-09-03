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

for entry in lex.entries:
    for sense in iter_senses(entry.senses):
        for glosa en sentido.glosas:
            if glosa.idioma != "en":
                continue
            antiguo = str(glosa.texto)
            nuevo = antiguo.replace("colour", "color")
            si new != old:
                gloss.text = sil_lift.Text([new])
                edited_glosses += 1

changed = lex.changed_entries()

errors = [p for p in lex.iter_problems() si p.level == "error"]
si hay errores:
    for problem in errors:
        print(problem)
    sys.exit(f"abortando: {len(errors)} error(es) de validación, nada guardado")

lex.save()
print(f"glosa(s) editada(s) {edited_glosses} en {len(changed)} entrada(s)")
```

Algunas cosas que conviene destacar:

- `Sense.subsenses` es en sí mismo una `lista[Sense]`, por lo que `iter_senses` recorre su contenido de forma recursiva; una edición masiva que solo recorriera `entry.senses` omitiría sin avisar cualquier glosa anidada bajo un subsentido.
- `gloss.text` es un `Text`, no una cadena simple: `str(gloss.text)` lo convierte en una cadena para la búsqueda de coincidencias, y la sustitución se vuelve a escribir con `sil_lift.Text([new])` en lugar de modificar la cadena in situ.
- `lex.changed_entries()` indica qué entradas difieren del archivo tal y como se ha cargado. Dado que el resumen de una entrada abarca todo su subárbol, cualquier modificación en un subsignificado anidado se refleja en la entrada que lo contiene.
  - Comparando contenido serializado, no se registra el hecho de asignar a un campo el valor que ya tenía.
  - Solo informa de los cambios en el contenido; `lex.added_entries()` y `lex.removed_entries()` recogen las entradas que han aparecido o desaparecido desde que se cargó la página.
  - Devuelve las propias entradas, sin que les afecte que el `id` esté duplicado o falte (algo que permite LIFT).
  - Como recuento, solo tiene sentido cuando hay algo con lo que compararlo. Cuando el escáner de bytes no puede leer la fuente —ya sea por una codificación incompatible con ASCII o por una discrepancia entre el escáner y el analizador—, no existe una línea de referencia, y `changed_entries()` muestra _todas_ las entradas. Esa es la respuesta sincera en lo que respecta a la protección contra escritura, ya que `save()` vuelve a serializar todo el archivo en ese caso, pero eso significa que el recuento corresponde al tamaño del léxico y no al tamaño de la modificación.
- `lex.changes()` indica si el documento ha sufrido algún cambio _en absoluto_. Abarca no solo las entradas, sino también el encabezado, el elemento raíz y todos los elementos asociados a `.lift-ranges`.
  - Solo es falso cuando `save()` reproduciría los bytes originales, lo que hace que `if not lex.changes(): ...` sea la forma correcta de omitir una escritura innecesaria. La garantía funciona en un solo sentido: nunca indica «nada que escribir» para un documento que se reescribiría, mientras que un cambio que obligue a una reserialización completa puede volver a los bytes originales y seguir indicándose.
  - Compara el contenido, no el destino, por lo que solo debes utilizarlo para guardar en el mismo lugar: `lex.save(some_other_dir / "dictionary.lift")` escribe el documento y sus archivos asociados en una ubicación que aún está vacía, independientemente de si se ha producido algún cambio o no.
  - Se trata de una medida de seguridad, no de una optimización: al ejecutarla, se procesan todas las entradas, lo cual equivale al trabajo que realiza `save()` para decidir qué bytes de origen puede reutilizar; por lo tanto, lo que se omite es la propia escritura (sin cambios en la fecha de modificación del archivo, sin diferencias espurias), no el esfuerzo de tomar esa decisión.
- La validación en memoria (`lex.iter_problems()`) serializa primero el estado editado, de modo que este refleje correctamente los cambios antes de que se guarde nada en el disco. Interrumpir la operación ante cualquier `Problem` de nivel `"error"` —las advertencias se dejan a criterio de quien realiza la llamada— significa que una edición incorrecta nunca llega a `save()`.

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
