# La línea de comandos

Al instalar el paquete (`pip install sil-lift`) también se instala el comando `sil-lift`, una herramienta compatible con el estilo de LiftTools que se incluye con el paquete (y, en el caso de `validate`, un ejemplo práctico de la API de la biblioteca).

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media] [--require-ids]
                                           todos los problemas, por entrada/línea; salida 1 en caso de error
sil-lift stats PATH [--format {text,json}]
                                           recuentos por entrada/sentido/idioma (en streaming; cualquier tamaño)
sil-lift sort PATH [-o OUT]               copia ordenada canónicamente y lista para comparaciones (por defecto: in situ)
sil-lift check-media PATH                 informe de medios que faltan y huérfanos; sale con código 1 si faltan
sil-lift export PATH [-o OUT] [--langs L] [--tsv]
                                           una fila por sentido principal (subsentidos aplanados) a CSV/TSV (en streaming)
```

`--format json` escribe un único objeto JSON en la salida estándar (y nada más) para su uso en CI/automatización; consulta el esquema del ejemplo que aparece a continuación. `--strict` trata las advertencias como errores y devuelve el valor 1 si se encuentra alguna; utilízalo para que la compilación solo se complete si todo está en orden, en lugar de basarte únicamente en los errores. `--no-check-media` omite la comprobación de la presencia de archivos multimedia en el sistema de archivos (suprimiendo los resultados de `missing-media`), lo cual resulta útil a la hora de validar una exportación recién generada cuyos archivos de audio o fotos se encuentran en otra ubicación y no están almacenados en el mismo disco. `--require-ids` también da error (un error de `missing-id`) en cualquier entrada que carezca de un `guid` o en cualquier sentido que carezca de un `id` — es más estricto que LIFT, para flujos de trabajo que vuelven a importar mediante un identificador estable. Si se pasa `-` como ruta, el documento se lee desde la entrada estándar (un documento transmitido por canalización no tiene carpeta, por lo que su archivo asociado `.lift-ranges` y los archivos multimedia no se resuelven). `stats` también admite la opción `--format json`, con lo que muestra los recuentos en forma de un único objeto JSON.

!!! note
    Los códigos de salida de `validate` y el esquema de `--format json` constituyen una interfaz de automatización compatible: ambos están cubiertos por pruebas y solo cambian según las normas de SemVer.

`sort` solo reescribe el archivo `.lift`; los archivos complementarios `.lift-ranges` se mantienen sin modificar
(ordénalos por separado con la API `RangesFile`).

`validate`, `stats`, `check-media` y `export` también admiten un paquete LIFT comprimido (un archivo `.zip` con cualquiera de las dos estructuras: archivos en la raíz del archivo comprimido o anidados dentro de una carpeta de nivel superior); este se extrae a un directorio temporal y se elimina una vez finalizado el comando.

Ejemplos:

```
$ sil-lift validate dictionary.lift
error [dangling-ref] dictionary.lift:88 (entrada apu): la referencia «nope» no coincide con ningún ID de entrada/GUID ni con ningún ID de significado
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
    «warnings»: 1
  }
}

$ sil-lift stats sango.lift
entradas:   3507
acepciones:    4541
...

$ sil-lift export dictionary.lift --langs en,fr -o dictionary.csv
```

Códigos de salida: `0`: éxito (se permiten advertencias, salvo si se utiliza la opción `--strict`); `1`: resultados (errores de validación / medios que faltan / advertencias si se utiliza la opción `--strict`); `2`: entrada ilegible.
