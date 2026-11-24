# Diferencias con respecto a las bibliotecas de C\#

sil-lift es, a grandes rasgos, análogo a las herramientas LIFT de SIL para C#, concretamente a dos componentes de [libpalaso](https://github.com/sillsdev/libpalaso):

- `SIL.Lift`: analizador, validador, migrador, `LiftSorter`.
- `SIL.DictionaryServices`: el modelo `LexEntry`/`LexSense`, con su propio lector y escritor LIFT, que utilizan The Combine y WeSay.

sil-lift es una implementación nueva, no una adaptación. En esta página se resumen los aspectos en los que el comportamiento difiere deliberadamente.

## Ámbito de aplicación

| Capacidad              | Bibliotecas de C#                                       | sil-lift                                                                    |
| ---------------------- | ------------------------------------------------------- | --------------------------------------------------------------------------- |
| Versiones de LIFT      | 0,10–0,13 (migración incluida)       | **Solo 0,13**; las versiones anteriores se rechazan con un error claro      |
| Migración de versiones | `Migrator` (cadena XSLT)             | ninguna; utiliza los XSLT de «lift-standard» para actualizaciones puntuales |
| Validación             | Solo RELAX NG (`Validator`)          | RELAX NG + comprobaciones de esquema y semánticas                           |
| Streaming              | análisis sintáctico interno con granularidad de entrada | API pública `open_reader` / `open_writer`                                   |

## Formato de la API

El analizador de `SIL.Lift` funciona mediante callbacks (`ILexiconMerger`): envía eventos de análisis a un consumidor. En cambio, sil-lift devuelve un grafo de objetos simple (clases de datos tipadas para cada elemento LIFT), ya que los programadores de Python quieren objetos, no funciones de devolución de llamada.

`SIL.DictionaryServices` superpone un modelo de objetos `LexEntry`/`LexSense` sobre `SIL.Lift`, pero se trata de un modelo de aplicación: solo representa las estructuras que utilizan esas aplicaciones. Por lo tanto, la reserialización a través de él no puede conservar el contenido fuera del modelo de la misma forma que lo hacen el manejo de residuos LIFT y la fidelidad de bytes de sil-lift (véase más abajo).

La API de streaming devuelve el _mismo_ tipo `Entry`, por lo que no hay que aprender un segundo modelo simplificado.

## Fidelidad de ida y vuelta

La diferencia más marcada y deliberada. Al guardar con `SIL.Lift`, se vuelve a serializar todo el documento. sil-lift garantiza:

- un documento que no ha sufrido modificaciones se guarda **con los mismos bytes**, y
- Las entradas que no se modifican conservan exactamente los mismos bytes de origen, incluso cuando cambian otras entradas: se aplica automáticamente la división en bloques de bytes por entrada.

Consulta [las garantías de Fidelity](fidelity.md).

## Validación

El `Validator` de C# ejecuta una pasada de RELAX NG y devuelve los primeros errores en forma de cadenas de caracteres. sil-lift genera un flujo estructurado de «Problemas», cada uno de los cuales incluye el archivo, la entrada y la línea a los que se refiere. Su capa de esquema presenta tres divergencias deliberadas:

- **Los URI no válidos son advertencias, no errores.** El motor RELAX NG de C# nunca ha aplicado el tipo de datos `anyURI`, por lo que FieldWorks (FLEx) lleva años incluyendo enlaces `file://C:/...` en léxicos reales. Si se rechazaran esos archivos, se marcarían prácticamente todas las exportaciones de FLEx.
- **Se aplican las reglas de Schematron** (como comprobaciones semánticas): la validación en C# ignoraba silenciosamente los lenguajes de formulario duplicados y las coconstrucciones similares en la gramática LIFT.
- **Las comparaciones de identificadores de rango están normalizadas según Unicode** (NFC), ya que las exportaciones de FLEx mezclan identificadores NFC y NFD. Las referencias que solo se resuelven tras la normalización se señalan como advertencias de «normalization-mismatch», una comprobación que no tiene equivalente en C#. Consulta [los resultados de FieldWorks (FLEx) en el mundo real](guides/validate.md#real-world-fieldworks-flex-output).

Cuando sil-lift valida un `.lift`, también valida los componentes `.lift-ranges` según un esquema para documentos de rangos independientes, importado desde `lift-standard`. El `Validator` de C# no comprueba los archivos `.lift-ranges`.

## Ordenación canónica

`Lexicon.sort()` refleja las reglas básicas de `LiftSorter` (las entradas se ordenan por GUID sin distinguir entre mayúsculas y minúsculas; los rangos y los elementos de los rangos, por ID; las definiciones de los campos de encabezado, por etiqueta; los significados se mantienen en el orden del archivo; los espacios en blanco dentro de `<text>` nunca se modifican), con tres diferencias:

- Las entradas sin un GUID se ordenan de forma determinista por ID (`LiftSorter` da por hecho que existe un GUID);
- el orden es independiente de la configuración regional (puntos de código con mayúsculas y minúsculas ignoradas, no la clasificación de «cultura invariante» de .NET);
- Las listas del mismo tipo, como notas, relaciones y formularios, mantienen el orden del documento en lugar de volver a ordenarse por clave; la agrupación ya es determinista, y reordenarlas solo añade ruido en las diferencias.

El archivo `canonicalizeLift.xsl` del repositorio de especificaciones no se utiliza en absoluto: elimina los espacios en blanco dentro del texto léxico (de forma destructiva) y los identificadores que genera varían en cada ejecución.

## No se ha trasladado

- Funcionalidades específicas de WeSay (panel de control y gestión de la configuración relacionada con los archivos LIFT).
- `SynchronicMerger` (fusión de archivos de actualización de LIFT): la idea de la división en bloques de bytes se mantiene en la capa de fidelidad, pero la fusión no.
- Análisis sintáctico del sistema de escritura LDML: los archivos de la carpeta `WritingSystems/` se tratan como contenido opaco de la carpeta.
