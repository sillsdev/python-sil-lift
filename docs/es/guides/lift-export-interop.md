# Creación de un LIFT conforme

Esta guía está dirigida a cualquier persona que esté desarrollando un _exportador_ de LIFT, es decir, código en cualquier lenguaje de programación que convierta el modelo de datos de otra aplicación al formato LIFT 0.13. `sil-lift` desempeña dos funciones en ese trabajo: por un lado, actúa como filtro de conformidad que comprueba que la salida se ajuste al esquema y a la semántica que este no puede expresar; y, por otro, sirve de referencia para las formas y las reglas de texto que debe respetar la salida.

Escribir en LIFT es mucho más fácil que analizarlo sintácticamente: un exportador solo genera el subconjunto de construcciones que produce su propio modelo y nunca tiene que lidiar con todas las opciones de la especificación completa. Lo complicado son los detalles —el complemento `.lift-ranges`, el texto específico para cada sistema de escritura, los identificadores estables y el escape de XML— y eso es precisamente lo que detectan las comprobaciones que se indican a continuación.

## Paquetes comprimidos

LIFT suele transportarse como un único archivo `.zip` —tanto FieldWorks como The Combine importan y exportan de esa forma—, por lo que `sil-lift` lee y escribe paquetes comprimidos directamente, independientemente de la estructura que utilice el ecosistema: ya sea con los archivos en la raíz del archivo comprimido o anidados dentro de una carpeta de nivel superior.

- **Nota:** `sil_lift.load("package.zip")` descomprime el archivo en un directorio temporal, localiza el único archivo `.lift` y lo carga (los archivos complementarios y multimedia se resuelven como de costumbre).
  - Los comandos de la CLI `validate`, `stats`, `check-media` y `export` también admiten una ruta `.zip`, por lo que el proceso que se muestra a continuación se ejecuta sobre un paquete tal cual.
  - `stats` y `export`, y extraer solo el archivo `.lift` en lugar de todo el paquete, de modo que el coste siga siendo reducido en un paquete con gran volumen de datos multimedia, y el límite de extracción se aplique únicamente al archivo `.lift` y no al resto de elementos que lo rodean.
  - La extracción tiene un límite máximo de 10 GiB y 100 000 elementos; cualquier paquete que supere cualquiera de estos límites se rechaza con un `LiftParseError`, al igual que aquellos cuyos caminos de acceso a los elementos se salgan del directorio de extracción.
- **Escribe:** `Lexicon.save_zip("out.zip", wrap_folder="MyDict")` empaqueta el archivo `.lift`, sus archivos `.lift-ranges` y todos los demás archivos de la carpeta de origen (archivos multimedia, `WritingSystems/`, `consent/`, ...) en un archivo zip.
  - `wrap_folder` toma por defecto una carpeta de nivel superior cuyo nombre coincide con el del archivo zip (según la convención de importación de FieldWorks/Combine); pasa `False` para obtener un archivo comprimido sin subcarpetas.

Los archivos `.lift` y `.lift-ranges` conservan su fidelidad a nivel de byte dentro del paquete; el propio contenedor zip no es reproducible a nivel de byte.

## Validar el resultado como criterio de conformidad

Dirige el comando «sil-lift validate» al archivo «.lift» generado. Ejecuta RELAX NG (tanto sobre el `.lift` como sobre su complemento `.lift-ranges`) y realiza comprobaciones semánticas que la gramática no puede expresar: referencias sueltas a `relation`/`variant`, GUID duplicados, integridad del elemento padre del rango, valores de rasgos e información gramatical no definidos en su rango, y referencias del encabezado `range/@href` que no se resuelven en ningún complemento.

En el caso de la CI, si se produce un error en cualquier paso, se deben generar resultados legibles por máquina:

```
sil-lift validate export.lift --strict --no-check-media --format json
```

- La opción `--strict` hace que las advertencias (y no solo los errores) provoquen el fallo de la ejecución.
- `--no-check-media` omite la comprobación de la presencia de archivos multimedia en el sistema de archivos, cuyos resultados de `missing-media` son falsos positivos cuando los archivos de audio o fotos no se encuentran en la misma carpeta que el archivo `.lift` en la integración continua (CI).
- `--format json` muestra un único objeto JSON (`{"problems": [...], "summary": {...}}`) en lugar de texto legible para el usuario; sus códigos de salida y su esquema constituyen una interfaz compatible y sujeta a SemVer (véase [la guía de la línea de comandos](cli.md)).
- `--require-ids` genera además un error si hay entradas a las que les falte un `guid` o detecta que faltan `id`s; esto resulta útil cuando, en una reimportación posterior, es necesario actualizar los datos en lugar de duplicarlos.

Evita la pérdida silenciosa de datos (el modo de fallo que hace que la exportación a CSV plano conlleve pérdidas) comprobando los recuentos con `stats --format json` en tu modelo de origen:

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
    format: json
```

o la imagen del contenedor, creada a partir del `Dockerfile` del repositorio:

```
docker build -t sil-lift .
docker run --rm -v "$PWD:/work" -w /work sil-lift validate export.lift --strict
```

## El complemento `.lift-ranges`

Los vocabularios controlados —partes del discurso, dominios semánticos y cualquier otro conjunto de valores basados en rasgos— se encuentran en un archivo `.lift-ranges` asociado, al que se hace referencia desde el archivo `<header>`:

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

A continuación, una entrada hace referencia a un valor mediante su identificador: la categoría gramatical de un sentido es `<grammatical-info value="Noun"/>`, y un dominio semántico es `<trait name="semantic-domain-ddp4" value="1.6.1.2"/>`. `sil-lift validate` muestra una advertencia (`undefined-range-value`) cuando un valor no está definido en su rango y genera un error (`range-parent`) cuando un `parent` no es un identificador de elemento hermano; por lo tanto, indica los rangos que tus datos utilizan realmente. Esas comparaciones están normalizadas según la norma NFC, por lo que un identificador y el valor o el `parent` al que hace referencia pueden presentar diferencias en la normalización Unicode; esa diferencia genera una advertencia de `normalization-mismatch` en lugar de un error, pero, si es posible, utiliza una normalización coherente: los usuarios que comparen cadenas sin procesar no resolverán esas referencias. Véase también [Rangos y medios](folder-media.md).

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

El escape de XML es la única parte en la que realmente importa la precisión. En el texto de los elementos, los caracteres `&`, `<`, and `>` deben escaparse (`&amp;`, `&lt;`, `&gt;`); en los valores de los atributos, también debe escaparse el carácter de comilla. El autor de `sil-lift` aplica exactamente estas reglas y nunca modifica los espacios en blanco dentro de `<text>`: no añade sangría en ese lugar, ya que eso corrompería los datos léxicos. Si quieres que el resultado sea idéntico, reutiliza el escape de un serializador XML auténtico (no una sustitución hecha a mano en la que se olvide el símbolo `&`) y deja el contenido de `<text>` tal y como aparece en el archivo original, byte a byte.
