# La carpeta LIFT: gamas y soportes

Un léxico de LIFT suele ser una _carpeta_: el archivo `.lift`, uno o varios archivos complementarios `.lift-ranges` (archivos «sidecar») y los archivos multimedia de las carpetas `audio/` y `pictures/`.

## Gamas

```python
lex = sil_lift.load("dictionary.lift")      # los «companions» se registran automáticamente

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # vista fusionada {id: Range}
lex.all_ranges()["grammatical-info"].elements
```

`lex.save()` guarda el archivo `.lift` y todos los archivos complementarios de los que se lleva un registro. Las modificaciones realizadas en un `RangesFile` se guardan de nuevo en _su_ archivo; los rangos que no se han modificado conservan sus bytes exactos. Uso independiente:

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

### Descubrimiento de planetas compañeros

Se prueban varios candidatos y se carga cada uno de los archivos distintos que hay entre ellos.

- Un encabezado `range/@href` que apunte a un archivo existente se utiliza tal cual.
- Un atributo `href` que no resuelve a nada recurre a su nombre base junto a `.lift`. FieldWorks escribe rutas absolutas incompletas `file://C:/...` desde el equipo de exportación, y esa solución alternativa es lo que hace que funcionen a nivel local.
- El elemento hermano convencional «<name>.lift-ranges» se detecta incluso cuando no hay ninguna referencia a él.

Los nombres que solo difieren en mayúsculas y minúsculas o en la normalización Unicode siguen coincidiendo (`Dict.LIFT` encuentra `Dict.lift-ranges`), a menos que varios archivos coincidan con un mismo nombre, en cuyo caso no se carga ninguno de ellos y se notifica como [`ambiguous-ranges-file`](validate.md#problem-codes).

Un candidato que no se pueda leer como un documento `<lift-ranges>` (por ejemplo, un archivo de cero bytes procedente de una exportación interrumpida) se omite, en lugar de provocar un error en la carga, y se notifica como [`unreadable-ranges-file`](validate.md#problem-codes). Sin embargo, al cargar uno directamente con `RangesFile.load()`, se produce un error.

Pasa `resolve_ranges=False` a `load()` para omitir la detección de componentes complementarios.

## Medios de comunicación

```python
for ref in lex.media_refs():        # todos los <media> y <illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.check_media()                   # referencias que no se resuelven correctamente
```

La resolución sigue el esquema convencional: se comprueba que un enlace «href» relativo se haya especificado correctamente y se encuentre en la carpeta «audio/» (para archivos de audio con la pronunciación) o en la carpeta «pictures/» (para ilustraciones). Las barras invertidas se interpretan como barras normales, ya que WeSay escribe los enlaces `pictures\photo with space.png`. Los enlaces «href» remotos y absolutos no se pueden comprobar y se omiten.

La función `check_media()` solo muestra las referencias que no se han resuelto correctamente, una `MediaResolution` por cada una:

- `status="missing"`: ningún archivo se correspondía con el enlace «href», independientemente de la ortografía utilizada.
- `status="mismatch"`: uno sí lo hizo, pero solo con conversión de mayúsculas y minúsculas o NFC; `found` indica el nombre del archivo en el disco.

Se notifica una discrepancia aunque se haya encontrado el archivo. Un nombre de archivo asociado se empareja de forma aproximada sin comentarios, pero el enlace «href» del archivo multimedia también es leído por cualquier servidor que alimente la carpeta posteriormente, y un servidor que distinga entre mayúsculas y minúsculas no encontrará el archivo. La validación señala el mismo caso que [`media-href-mismatch`](validate.md#problem-codes).

## Otros contenidos de la carpeta

Una carpeta LIFT suele contener archivos que sil-lift no modela, como el sistema de escritura LDML en `WritingSystems/` o los archivos de consentimiento de los hablantes de The Combine en `consent/`. Las funciones `load()` y `save()` no modifican estos archivos, y [`Lexicon.save_zip()`](lift-export-interop.md) los incluye tal cual al empaquetar la carpeta.
