# La línea de comandos

Al instalar el paquete (`pip install sil-lift`) también se instala el comando `sil-lift`, una herramienta compatible con el espíritu de LiftTools que se incluye con el paquete (y, en el caso de `validate`, un ejemplo práctico de la API de la biblioteca).

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media] [--allow CODE[,CODE...]]...
                  [--require-ids]
                                           todos los problemas, con archivo/entrada/línea; sale con código de salida 1 en caso de error
sil-lift stats PATH [--format {text,json}]
                                           recuentos de entradas/significados/idiomas (en tiempo real; cualquier tamaño)
sil-lift sort PATH [-o OUT]               copia ordenada canónicamente y lista para comparar diferencias (por defecto: in situ)
sil-lift check-media PATH                 informe de medios que faltan, mal escritos y huérfanos; sale con código de error 1 si faltan o están mal escritos
sil-lift export PATH [-o OUT] [--langs L] [--tsv]
                                           una fila por sentido hoja (subsentidos aplanados) a CSV/TSV (en streaming)
```

Opciones de `validate`:

- `--format json` escribe un único objeto JSON en la salida estándar (y nada más) para su uso en CI/automatización; consulta el esquema del ejemplo que aparece a continuación.
- `--strict` trata las advertencias como errores y devuelve el valor 1 si se encuentra alguna; utilízalo para condicionar la compilación a que no haya ninguna advertencia, en lugar de basarte únicamente en los errores.
- `--no-check-media` omite la comprobación de la presencia de archivos multimedia en el sistema de archivos, lo que suprime los hallazgos `missing-media` y `media-href-mismatch`. Resulta útil a la hora de validar una exportación recién generada cuyos archivos de audio o fotos se encuentren en otra ubicación y no en la misma carpeta.
- `--allow CODE[,CODE...]` (repetible) muestra los resultados correspondientes a los códigos indicados, pero no los tiene en cuenta a la hora de decidir si se aprueba o se suspende. Esto se aplica tanto a los errores como a las advertencias, por lo que una advertencia permitida tampoco activa la opción `--strict`. La línea de resumen recoge los resultados permitidos por código; el campo `allowed` del resumen JSON indica su total. Un código que nunca aparece se ignora, por lo que una lista de permitidos sigue funcionando incluso después de que se haya retirado una comprobación.
- `--require-ids` también da error (un error de `missing-id`) en cualquier entrada que carezca de un `guid` o en cualquier sentido que carezca de un `id` — es más estricto que LIFT, para flujos de trabajo que vuelven a importar mediante un identificador estable.

Si se pasa `-` como ruta, el documento se lee desde la entrada estándar (stdin). Un documento «piped» no tiene carpeta, por lo que su archivo `.lift-ranges` asociado y los archivos multimedia no se resuelven.

`stats` también admite la opción `--format json`, con lo que muestra los recuentos en forma de un único objeto JSON.

!!! note
    Los códigos de salida de `validate` y el esquema de `--format json` constituyen una interfaz de automatización compatible: ambos están cubiertos por pruebas y solo cambian según las normas de SemVer.

`sort` solo reescribe el archivo `.lift`; los archivos complementarios `.lift-ranges` se mantienen sin modificar
(ordénalos por separado con la API `RangesFile`).

`validate`, `stats`, `check-media` y `export` también admiten un paquete LIFT comprimido (un archivo `.zip` con cualquiera de las dos estructuras: archivos en la raíz del archivo comprimido o anidados dentro de una carpeta de nivel superior); este se extrae a un directorio temporal y se elimina una vez finalizado el comando. Los comandos de streaming `stats` y `export` extraen únicamente el archivo `.lift` en sí, por lo que su ejecución no consume muchos recursos en paquetes con gran cantidad de archivos multimedia; en cambio, `validate` y `check-media` necesitan la carpeta completa y la extraen en su totalidad.

Ejemplos:

```
$ sil-lift validate dictionary.lift
error [dangling-ref] dictionary.lift:88 (entrada apu): la referencia «nope» no coincide con ningún ID de entrada/GUID ni con ningún ID de acepción
advertencia [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: Se ha utilizado una letra de unidad de Windows como autoridad URI (estilo FLEx: file://C:/)
1 error(es), 1 advertencia(s)

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "la referencia 'nope' no coincide con ningún ID de entrada/GUID ni ID de sentido",
      "file": "dictionary.lift",
      "entry_id": "apu",
      "guid": null,
      "line": 88
    },
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: Se ha utilizado una letra de unidad de Windows como autoridad URI (estilo FLEx: file://C:/)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    }
  ],
  «summary»: {
    «errors»: 1,
    «warnings»: 1,
    «allowed»: 0
  }
}

$ sil-lift stats sango.lift
entradas:   3507
sentidos:    4541
...

$ sil-lift export dictionary.lift --langs en,fr -o dictionary.csv
```

Toda la salida es en UTF-8, en cualquier plataforma y tanto si se envía a una consola, a una tubería o a una redirección `>`; nunca se utiliza la codificación de la configuración regional (cp1252 en Windows, ASCII en una configuración regional C/POSIX), ya que esta no puede representar contenido LIFT. Por lo tanto, el comando `sil-lift export dictionary.lift > dictionary.csv` escribe exactamente los mismos bytes que el comando `-o dictionary.csv`, incluidos los caracteres de fin de línea CRLF.

Códigos de salida: `0` éxito (las advertencias no provocan el fallo de la ejecución a menos que se utilice `--strict`), `1` resultados (errores de validación / medios que faltan o con errores ortográficos / advertencias con `--strict`, sin contar los códigos asignados a `--allow`), `2`: un fallo de E/S en cualquiera de los extremos —entrada que no se puede leer o salida que no se puede escribir (un lector como `head` que cierra la tubería, un disco lleno).
