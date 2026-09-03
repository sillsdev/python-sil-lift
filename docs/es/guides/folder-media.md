# La carpeta LIFT: gamas y soportes

Un léxico de LIFT suele ser una _carpeta_: el archivo `.lift`, uno o varios archivos complementarios `.lift-ranges` (archivos «sidecar») y los archivos multimedia de las carpetas `audio/` y `pictures/`.

## Gamas

```python
lex = sil_lift.load("dictionary.lift")      # los «companions» se registran automáticamente

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # vista fusionada {id: Range}
lex.all_ranges()["grammatical-info"].elements
```

La función «Companion discovery» se adapta al mundo real: se utiliza un `range/@href` que apunta a un archivo existente; los enlaces `file://C:/...` absolutos sin referencia de FieldWorks recurren al nombre base del enlace junto al `.lift`; y el elemento hermano convencional `<name>.lift-ranges` se detecta incluso cuando nada hace referencia a él.

`lex.save()` guarda el archivo `.lift` y todos los archivos complementarios de los que se lleva un registro. Las modificaciones realizadas en un `RangesFile` se guardan de nuevo en _su_ archivo; los rangos que no se han modificado conservan sus bytes exactos. Uso independiente:

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

Pasa `resolve_ranges=False` a `load()` para omitir la detección de componentes complementarios.

## Medios de comunicación

```python
for ref in lex.media_refs():        # todos los <media> y <illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.missing_media()                 # referencias cuyos archivos no existen
```

La resolución sigue el esquema convencional: se comprueba un enlace «href» relativo tal y como se ha indicado (con las barras invertidas normalizadas — WeSay escribe «pictures\photo con espacio.png») y dentro de «audio/» (para archivos de audio con pronunciación) o «pictures/» (para ilustraciones). Los enlaces «href» remotos o absolutos no se pueden comprobar y se omiten.

## Otros contenidos de la carpeta

Una carpeta LIFT suele contener archivos que sil-lift no modela —el sistema de escritura LDML en `WritingSystems/`, los archivos de audio e imagen de consentimiento de los hablantes de The Combine en `consent/`, y similares—; Las funciones `load()` y `save()` no modifican estos archivos, y [`Lexicon.save_zip()`](lift-export-interop.md) los incluye tal cual al empaquetar la carpeta.
