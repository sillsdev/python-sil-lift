# La línea de comandos (CLI)

Al instalar el paquete (`pip install sil-lift`) también se instala el comando `sil-lift`.

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media]
                  [--allow CODE[,CODE...]]... [--require-ids]
    todos los problemas, con archivo/entrada/línea; sale con código de salida 1 en caso de error

sil-lift stats PATH [--format {text,json}]
    recuentos de entradas/significados/idiomas (en tiempo real; cualquier tamaño)

sil-lift sort PATH [-o OUT]
    copia ordenada canónicamente y lista para comparar diferencias (por defecto: in situ)

sil-lift check-media PATH
    informe de archivos multimedia faltantes, mal escritos y huérfanos; sale con código 1 si hay archivos faltantes o mal escritos

sil-lift export PATH [-o OUT] [--langs L] [--tsv]
    una fila por sentido de hoja (subsentidos aplanados) a CSV/TSV (en streaming)
```

## validar

`validate` muestra una línea por cada resultado y, a continuación, un resumen. `--format json` ofrece los mismos resultados que un objeto JSON:

```
$ sil-lift validate dictionary.lift
advertencia [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: Se ha utilizado una letra de unidad de Windows como autoridad URI (estilo FLEx: file://C:/)
error [dangling-ref] dictionary.lift:88 (entrada poʻo_a1b2): la referencia «nope» no coincide con ningún ID de entrada/GUID ni ID de sentido
1 error(es), 1 advertencia(s)

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: Se ha utilizado una letra de unidad de Windows como autoridad URI (estilo FLEx: file://C:/)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    },
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "la referencia 'nope' no coincide con ningún id/guid de entrada ni con ningún id de sentido",
      "file": "dictionary.lift",
      "entry_id": "po\u02bbo_a1b2",
      "guid": null,
      "line": 88
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 1,
    "allowed": 0
  }
}
```

Opciones de `validate`:

- `--format json` escribe un único objeto JSON en la salida estándar (y nada más) para su uso en CI/automatización. Consulta el esquema del ejemplo anterior.
- `--strict` trata las advertencias como errores y devuelve el valor 1 si se encuentra alguna. Úsalo para bloquear una compilación si no hay ninguna advertencia, en lugar de hacerlo solo por los errores.
- `--no-check-media` omite la comprobación de la presencia de archivos multimedia en el sistema de archivos, lo que suprime los hallazgos `missing-media` y `media-href-mismatch`. Resulta útil cuando los archivos de audio y fotos de una exportación se guardan en otra ubicación o aún no se han copiado junto al archivo `.lift`.
- `--allow CODE[,CODE...]` (repetible) muestra los resultados correspondientes a los códigos indicados, pero no los tiene en cuenta a la hora de decidir si se aprueba o se suspende.
  - Esto se aplica tanto a los errores como a las advertencias, por lo que una advertencia permitida tampoco activa la opción `--strict`.
  - La línea de resumen recoge los resultados permitidos por código; el campo `allowed` del resumen JSON indica su total.
  - Un código que nunca aparece se ignora, por lo que una lista de permitidos sigue funcionando aunque se elimine una comprobación.
- `--require-ids` también da error (un error de `missing-id`) en cualquier entrada que carezca de un `guid` o en cualquier sentido que carezca de un `id`. Esto es más estricto que LIFT, en el caso de los flujos de trabajo que vuelven a importar mediante un identificador estable.

Si se pasa `-` como ruta, el documento se lee desde la entrada estándar (stdin). Un documento «piped» no tiene carpeta, por lo que su archivo `.lift-ranges` asociado y los archivos multimedia no se resuelven.

!!! note

    Los códigos de salida de `validate` y el esquema de `--format json` constituyen una interfaz de automatización compatible: ambos están cubiertos por pruebas y solo cambian según las normas de SemVer.

## estadísticas

```
$ sil-lift stats sango.lift
entradas:   3507
detecciones:    4541
...
```

`stats` también admite la opción `--format json`, con lo que muestra los recuentos en forma de un único objeto JSON.

## ordenar

`sort` solo reescribe el archivo `.lift`; los archivos `.lift-ranges` asociados no se modifican (ordénalos por separado con la [API `RangesFile`](folder-media.md#ranges)).

## exportar

`export` escribe una fila por cada sentido de hoja. `--langs` determina qué idiomas incluyen las columnas `gloss_` y `definition_`; por defecto, se detectan a partir del documento.

```
$ sil-lift export dictionary.lift --langs en,id -o dictionary.csv
```

## Paquetes comprimidos

`validate`, `stats`, `check-media` y `export` también admiten paquetes LIFT comprimidos (`.zip`). Sus archivos pueden encontrarse en la raíz del archivo o dentro de una carpeta de primer nivel. Todo lo que extraiga un comando se guarda en un directorio temporal y se elimina cuando finaliza el comando.

- Los comandos de streaming `stats` y `export` extraen únicamente el propio archivo `.lift`, por lo que su ejecución no consume muchos recursos en paquetes con gran volumen de datos multimedia.
- Las funciones `validate` y `check-media` necesitan la carpeta completa y extraen todo su contenido.

## Codificación de salida

Toda la salida es UTF-8, en todas las plataformas, independientemente de si se envía a una consola, a una tubería o a una redirección `>`. Nunca es la codificación de la configuración regional (cp1252 en Windows, ASCII en una configuración regional C/POSIX) la que no puede representar el contenido LIFT. Por lo tanto, el comando `sil-lift export dictionary.lift > dictionary.csv` escribe exactamente los mismos bytes que el comando `-o dictionary.csv`, incluidos los caracteres de fin de línea CRLF.

## Códigos de salida

- `0`: éxito. Las advertencias no hacen que la ejecución falle, salvo que se utilice la opción `--strict`.
- `1`: conclusiones. Un error de validación, un archivo multimedia que falte o esté mal escrito, o una advertencia con la opción `--strict` da como resultado el código de salida 1, a menos que se haya especificado el código correspondiente con la opción `--allow`.
- `2`: Error de E/S. No se ha podido leer la entrada o no se ha podido escribir en la salida, por ejemplo, porque el disco está lleno o porque un programa de lectura como `head` ha cerrado la tubería.
