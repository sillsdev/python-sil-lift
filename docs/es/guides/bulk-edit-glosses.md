# Ejemplo práctico: edición masiva de glosas

Una tarea habitual de mantenimiento: armonizar la ortografía de todas las entradas en inglés de un léxico (del inglés británico al americano, o viceversa) sin alterar el resto del archivo. En este ejemplo se muestra paso a paso un script que carga, edita, valida y guarda, lo que permite ver cómo funcionan conjuntamente la API de edición y la garantía de fidelidad.

## El guión

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)

edited_glosses = 0

for entry in lex.entries:
    for sense in entry.all_senses():
        for gloss in sense.glosses:
            if gloss.lang != "en":
                continue
            old = str(gloss.text)
            new = old.replace("colour", "color")
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

- `entry.all_senses()` devuelve todos los significados _y subsignificados_, siguiendo un recorrido en profundidad según el orden del documento.
  - `entry.senses` solo contiene el nivel superior, por lo que una edición masiva que recorriera este campo omitiría sin avisar cualquier glosa anidada bajo un subsignificado.
- `gloss.text` es un `Text`, no una cadena simple: `str(gloss.text)` lo convierte en una cadena para la búsqueda de coincidencias, y la sustitución se vuelve a escribir con `sil_lift.Text([new])` en lugar de modificar la cadena in situ.
- `lex.changed_entries()` indica qué entradas difieren del archivo tal y como se ha cargado. Dado que el resumen de una entrada abarca todo su subárbol, cualquier modificación realizada en un significado secundario anidado se refleja en la entrada que lo contiene, mientras que si se asigna a un campo el valor que ya tenía, esto no se refleja.
- La función `changed_entries()` solo tiene en cuenta el contenido de las entradas, por lo que se trata de un recuento, no de una protección contra la escritura. Para omitir un guardado que no supondría ningún cambio, utiliza `lex.changes()`; consulta [Guardar](read-edit-write.md#saving).
- La validación en memoria (`lex.iter_problems()`) serializa primero el estado editado, de modo que este refleje correctamente los cambios antes de que se guarde nada en el disco. Interrumpir la operación ante cualquier `Problem` de nivel `"error"` —las advertencias se dejan a criterio de quien realiza la llamada— significa que una edición incorrecta nunca llega a `save()`.
- `lex.save()` asigna una nueva `dateModified` exactamente a las entradas que ha modificado este script, y rellena el campo `dateCreated` cuando estaba en blanco. Sin ello, un léxico reescrito por este script parecería inalterado para FieldWorks o para la importación LIFT de The Combine, ya que ambos deciden qué actualizar a partir de ese atributo —y solo marca `<entry>`, independientemente de la profundidad de la edición: la entrada que contiene la glosa del subsentido editado, no el sentido.

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
