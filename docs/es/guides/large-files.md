# Archivos de gran tamaño (reproducción en streaming)

`load()` construye todo el grafo de objetos. En el caso de léxicos de varios cientos de MB, la API de streaming procesa una entrada cada vez en una memoria limitada —el mismo tipo `Entry`—, por lo que el código escrito para un modo funciona también en el otro.

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # analizado al principio (precede a las entradas)
    for entry in reader:              # iterador perezoso [Entry]
        ...
```

```python
con sil_lift.open_reader("big.lift") como reader, sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) como writer:
    for entry in reader:
        if not entry.date_deleted:    # p. ej., eliminar entradas obsoleta
            writer.write(entry)
```

Notas:

- El resultado del escritor es exactamente el mismo que produciría el serializador canónico de documento completo para el mismo contenido; los dos modos nunca se desvían entre sí.
- El modo de transmisión en continuo no cuenta con una capa de paso directo de bytes: la salida es siempre canónica. Los residuos de nivel raíz —comentarios entre entradas y atributos fuera del esquema en `<lift>`— no se transfieren; las entradas y el encabezado están completos, incluidos los residuos.
- Si se produce un error en el cuerpo de un bloque `open_writer`, el archivo queda visiblemente sin terminar (sin el cierre `</lift>`); un léxico a medio escribir no debe parecer completo.
