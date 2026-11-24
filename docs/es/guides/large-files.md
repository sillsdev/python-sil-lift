# Archivos de gran tamaño (reproducción en streaming)

`load()` construye todo el grafo de objetos. En el caso de léxicos de varios cientos de MB, la API de streaming procesa una entrada cada vez en una memoria limitada. Devuelve el mismo tipo `Entry`, por lo que el código escrito para un modo funciona en el otro.

## Lectura

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # analizado al principio (precede a las entradas)
    for entry in reader:              # iterador perezoso [Entry]
        ...
```

## Redacción

```python
con sil_lift.open_reader("big.lift") como reader, sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) como writer:
    for entry in reader:
        if not entry.date_deleted:    # p. ej., omitir las entradas marcadas como eliminadas
            writer.write(entry)
```

Notas:

- El resultado generado por el escritor es exactamente el mismo que produciría el serializador canónico de documento completo para el mismo contenido; ambos modos nunca se desvían entre sí.
- El modo de transmisión no reutiliza ningún byte de origen: la salida es siempre canónica. Se elimina el residuo LIFT del nivel raíz (comentarios entre entradas y atributos fuera del esquema en `<lift>`), pero las entradas y el encabezado conservan su propio residuo.
- A diferencia de [`Lexicon.save()`](../fidelity.md#saving-an-edited-document), el modo de transmisión no genera marcas de tiempo. Una entrada se escribe con las fechas que ya tiene: un pase de streaming nunca ve el documento tal y como era, por lo que no puede saber qué entradas has modificado. Establece tú mismo el valor de `entry.date_modified` en aquellos que esta pasada reescriba.
- Si se produce un error en el cuerpo de un bloque `open_writer`, el archivo queda visiblemente sin cerrar (sin la instrucción de cierre `</lift>`). Esto evita que un léxico a medio escribir parezca completo.
