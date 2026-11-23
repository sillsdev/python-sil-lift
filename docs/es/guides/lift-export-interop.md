# Creación de un LIFT conforme

Esta guía está dirigida a cualquier persona que esté desarrollando un _exportador_ de LIFT: código en cualquier lenguaje que convierta el modelo de datos de otra aplicación al formato LIFT 0.13. `sil-lift` cumple dos funciones en ese trabajo:

- una puerta de conformidad que comprueba si la salida se ajusta tanto al esquema como a la semántica que un esquema no puede expresar;
- una guía sobre las formas y las normas de texto que debe respetar el resultado final.

Escribir en LIFT es mucho más fácil que analizarlo sintácticamente: un exportador solo genera el subconjunto de construcciones que produce su propio modelo y nunca tiene que lidiar con todas las opciones de la especificación completa. Lo complicado son los detalles (el complemento `.lift-ranges`, el texto específico de cada sistema de escritura, los identificadores estables y el escape de XML), y eso es precisamente lo que detectan las comprobaciones que se indican a continuación.

## Paquetes comprimidos

LIFT suele transferirse como un único archivo `.zip`; tanto FieldWorks como The Combine importan y exportan de esa forma. `sil-lift` lee y escribe paquetes comprimidos directamente, independientemente de la estructura que utilice el ecosistema: ya sea con los archivos en la raíz del archivo comprimido o anidados dentro de una carpeta de nivel superior.

### Leer un paquete

`sil_lift.load("package.zip")` descomprime el archivo en un directorio temporal, localiza el único archivo `.lift` y lo carga (los archivos complementarios y multimedia se resuelven como de costumbre).

- Los comandos de la CLI `validate`, `stats`, `check-media` y `export` también admiten una ruta `.zip`, por lo que el proceso que se muestra a continuación se ejecuta sobre un paquete tal cual.
- los flujos `stats` y `export`, y extraer solo el archivo `.lift` en lugar de todo el paquete. Siguen siendo baratos en una configuración con gran cantidad de medios, y el límite de extracción se aplica únicamente al `.lift`, y no a todo lo que hay a su alrededor.
- La extracción tiene un límite máximo de 10 GiB y 100 000 elementos. Se rechaza cualquier paquete que supere cualquiera de los dos límites con un `LiftParseError`, al igual que aquellos cuyos caminos de los miembros se salgan del directorio de extracción.

### Cómo crear un paquete

`Lexicon.save_zip("out.zip", wrap_folder="MyDict")` empaqueta el archivo `.lift`, sus archivos `.lift-ranges` y todos los demás archivos de la carpeta de origen (archivos multimedia, `WritingSystems/`, `consent/`, etc.) en un archivo zip.

- `wrap_folder` toma por defecto una carpeta de nivel superior cuyo nombre coincide con el del archivo zip (según la convención de importación de FieldWorks/Combine); pasa `False` para obtener un archivo comprimido sin subcarpetas.
- Las entradas cuyo contenido haya cambiado desde la carga se marcan con una nueva `dateModified` al salir, exactamente igual que en `save()`.
  - Un paquete es la fuente a partir de la cual una herramienta de importación realiza la conciliación, por lo que una fecha obsoleta en él haría que un léxico actualizado pareciera no haber sido modificado.
  - Acepta las mismas opciones `stamp=` y `when=` que `save()`; consulta [Cómo se aplica la marca de fecha](../fidelity.md#how-the-stamp-is-applied).

Los archivos `.lift` y `.lift-ranges` conservan su fidelidad a nivel de byte dentro del paquete; el propio contenedor zip no es reproducible a nivel de byte.

## Validar el resultado como criterio de conformidad

Dirige el comando «sil-lift validate» a un archivo «.lift». Ejecuta RELAX NG tanto sobre el `.lift` como sobre su complemento `.lift-ranges`, además de realizar comprobaciones semánticas que la gramática no puede expresar:

- referencias «relation»/«variant» sin asignar;
- GUID duplicados;
- integridad de los elementos del rango y de sus elementos principales;
- valores de rasgos e información gramatical no definidos en su rango;
- Las referencias de encabezado `range/@href` que no tienen ningún elemento asociado.

En el caso de la CI, si se produce un error en cualquier paso, se deben generar resultados legibles por máquina:

```
sil-lift validate export.lift --strict --no-check-media --format json
```

- La opción `--strict` hace que las advertencias (y no solo los errores) provoquen el fallo de la ejecución.
- `--no-check-media` omite la comprobación de la presencia de archivos multimedia en el sistema de archivos, cuyos resultados de `missing-media` son falsos positivos cuando los archivos de audio o fotos no se encuentran en la misma carpeta que el archivo `.lift` en la integración continua (CI).
- `--format json` muestra un único objeto JSON (`{"problems": [...], "summary": {...}}`) en lugar de texto legible para el usuario; sus códigos de salida y su esquema constituyen una interfaz compatible y sujeta a SemVer (véase [la guía de la línea de comandos](cli.md)).
- `--allow CODE[,CODE...]` (repetible) evita que un código tolerado, como el `uri-not-rfc` de FLEx, provoque un error en la ejecución. Sus resultados se imprimen, pero no se cuentan.
- `--require-ids` además genera un error si hay entradas a las que les falte un `guid` o detecta que faltan `id`, lo cual resulta útil cuando una reimportación posterior debe actualizar los datos en lugar de duplicarlos.

### Prevención de la pérdida silenciosa de datos

La pérdida silenciosa de datos es el modo de fallo que hace que la exportación a CSV plano conlleve pérdida de datos. Evítalo aplicando el comando `stats --format json` a tu modelo de origen para obtener los recuentos:

```
sil-lift stats export.lift --format json
```

Muestra los recuentos de «entradas», «significados», «ejemplos», «referencias multimedia», «idiomas» y «características» por nombre.

### Ejecutar Gate sin el entorno de desarrollo de Python

La integración continua (CI) de un proyecto de TypeScript o C# puede ejecutar la misma comprobación sin necesidad de instalar Python, mediante la acción de GitHub incluida:

```yaml
- uses: sillsdev/python-sil-lift@v0.1.0
  with:
    path: export.lift
    strict: "true"
    no-check-media: "true"
    allow: "uri-not-rfc"
    format: json
```

o la imagen del contenedor, creada a partir del `Dockerfile` del repositorio:

```
docker build -t sil-lift .
docker run --rm -v "$PWD:/work" -w /work sil-lift validate export.lift --strict
```

## El complemento `.lift-ranges`

Los vocabularios controlados (clases gramaticales, dominios semánticos y cualquier otro conjunto de valores basados en rasgos) se encuentran en un archivo `.lift-ranges` asociado, al que se hace referencia desde el archivo `<header>`:

```xml
<header>
  <ranges>
    <range id="grammatical-info" href="mydict.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="mydict.lift-ranges"/>
  </ranges>
</header>
```

La guía incluye la descripción completa de cada gama. Los valores son «<range-element> »; «parent» establece una jerarquía; «label», «abbrev» y «description» son textos múltiples:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
  <range id="grammatical-info">
    <range-element id="Noun">
      <label><form lang="en"><text>sustantivo</text></form></label>
      <abbrev><form lang="en"><text>n</text></form></abbrev>
    </range-element>
  </range>
  <range id="semantic-domain-ddp4">
    <range-element id="1.6.1.2">
      <label><form lang="en"><text>Ave</text></form></label>
    </range-element>
  </range>
</lift-ranges>
```

A continuación, una entrada hace referencia a un valor mediante su identificador: la categoría gramatical de un sentido es `<grammatical-info value="Noun"/>`, y un dominio semántico es `<trait name="semantic-domain-ddp4" value="1.6.1.2"/>`. `sil-lift validate` comprueba esas referencias, así que indica los rangos que tus datos utilizan realmente:

- un valor que no está definido en su rango da lugar a una advertencia de `undefined-range-value`;
- Un «parent» que no sea un identificador de elemento hermano da lugar a un error de «range-parent».

Esas comparaciones están normalizadas según la NFC, por lo que un identificador y el valor o el «parent» al que hace referencia pueden diferir en cuanto a la normalización Unicode. Esa diferencia es una advertencia de «desajuste de normalización», en lugar de un error. Aun así, si puedes, escribe una normalización coherente: los consumidores que comparen cadenas sin procesar no resolverán esas referencias. Véase también [Rangos y medios](folder-media.md).

Si creas la exportación en Python, `Lexicon.add_ranges_file()`, `RangesFile.add_range()` y `Range.add_element()` construyen el archivo complementario y añaden las referencias de encabezado por ti; `open_writer(..., ranges=...)` hace lo mismo en la ruta de transmisión.

## Texto y multitexto

Cada cadena de lenguaje humano en LIFT es un _multitexto_: un `<form>` por sistema de escritura, cada uno de los cuales envuelve un `<text>`:

```xml
<lexical-unit>
  <form lang="seh"><text>kanga</text></form>
  <form lang="pt"><text>gallina</text></form>
</lexical-unit>
```

Un modelo que indexa cadenas por código de idioma (un `MultiString`, un `Record<code, string>`, un `dict[str, str]`) se corresponde con este de forma biunívoca: cada entrada por clave se convierte en un `<form lang="…">`. En un mismo multitexto solo se permite una forma por idioma; de lo contrario, `sil-lift` muestra el aviso `duplicate-form-lang`.

El escape de XML es la única parte en la que realmente hay que prestar atención a la corrección:

- En el texto de los elementos, los caracteres `&`, `<`, and `>` deben escaparse (`&amp;`, `&lt;`, `&gt;`);
- En los valores de los atributos, también hay que escapar el carácter de comillas.

El autor de `sil-lift` aplica exactamente estas reglas y nunca modifica los espacios en blanco dentro de `<text>`: no añade sangría en ese lugar, ya que eso corrompería los datos léxicos. Para que coincida con el resultado, utiliza una biblioteca XML para aplicar los caracteres de escape y deja el contenido de `<text>` tal y como aparece en el archivo original, byte a byte.
