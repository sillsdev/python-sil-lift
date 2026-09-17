# Garantías de Fidelity

LIFT es un formato de _intercambio_, por lo que la primera regla es **no descartar nunca lo que no entiendas**. El contrato de `sil-lift`, verificado por el conjunto de pruebas en cada ejecución (archivos del corpus más generación basada en propiedades):

## Lectura

Cualquier documento LIFT 0.13 bien formado se carga, incluso si el contenido no cumple con el esquema. Todo aquello que el modelo no defina se traslada al contenedor opaco `Extras` del nodo más cercano como _residuo LIFT_ —nombre que utiliza FieldWorks para referirse a este mismo concepto, y que almacena en un campo `LiftResidue`—: atributos y elementos desconocidos, comentarios XML e instrucciones de procesamiento, texto extrañado y atributos tipificados mal formados (una fecha incorrecta se mantiene como la cadena original en `Extras`; el campo tipado es `None`).

## Guardar un documento sin modificaciones

`load()` → `save()` sin modificaciones genera una **salida idéntica a nivel de bytes**: sin reformateo, sin reescapado, sin reordenación, incluyendo las marcas de orden de bytes y las declaraciones XML. Actualmente no hay ninguna lista de normalización: la identidad es exacta. Las marcas de tiempo se generan a partir del contenido, por lo que un documento que no haya sufrido modificaciones tampoco tiene ninguna.

Excepciones (el escritor recurre a la serialización canónica completa, que es semánticamente completa pero no conserva los bytes):

- la codificación de origen no es compatible con ASCII (no es UTF-8/US-ASCII), o
- el código fuente contiene un DOCTYPE, o
- el escáner de bytes y el analizador sintáctico no coinciden en cuanto a la estructura de nivel superior del documento —por ejemplo, un segundo `<header>` que no cumple con las especificaciones, que el analizador sintáctico conserva solo una vez (el escáner es deliberadamente conservador: ante cualquier duda, no captura ningún byte del código fuente)—, o
- El código fuente se compiló en memoria, en lugar de cargarse desde un archivo.

## Guardar un documento editado

- **Las entradas no modificadas se emiten tal cual, a partir de sus bytes originales.** Una entrada se considera modificada si alguna parte de su objeto de modelo ha cambiado desde el análisis (lo cual se detecta mediante una instantánea de serialización canónica, no mediante un indicador de cambios).
- **Las entradas modificadas se vuelven a serializar de forma canónica y completa.** La forma canónica es:
  - UTF-8.
  - Sangría de 2 espacios _fuera_ del contenido mixto; los espacios en blanco dentro de `<text>` y `<span>` nunca se modifican.
  - Un conjunto documentado de elementos secundarios por elemento; para `<entry>`: unidad léxica, cita, pronunciaciones, variantes, acepciones, notas, relaciones, etimologías, anotaciones, rasgos, campos.
  - Se ha corregido el orden de los atributos.
  - Fechas en formato ISO-8601 (`Z` para UTC).
- **Todos los residuos se vuelven a emitir.** Su posición se restablece en el índice secundario original, ajustada a la nueva lista secundaria —una aproximación, ya que las posiciones exactas en bytes solo están garantizadas para las entradas que no se han modificado—.
- Al añadir, eliminar o reordenar entradas, se vuelve a serializar la estructura del documento, pero se siguen emitiendo tal cual los bytes de cada entrada que no haya sufrido cambios.
- **A cada entrada modificada se le asigna** un nuevo valor de `dateModified` y, si no tenía ninguno, también un valor de `dateCreated`; véase [Marcas de tiempo generadas](#generated-timestamps).

!!! note "&quot;El XML canónico&quot; que aparece aquí no está relacionado con ningún otro XML canónico."
    En esta página, por «forma canónica» se entiende la forma documentada propia de «sil-lift», descrita en uno de los puntos anteriores. No guarda relación alguna con el proceso «Canonical XML (C14N)» del W3C. No tiene nada que ver con la clase `CanonicalXmlSettings` de `SIL.Core`.

## Marcas de tiempo generadas

Un sello generado es el único elemento de la salida que no depende de la entrada.

- **Lo que se marca.** Cada entrada cuyo contenido haya cambiado desde que se leyó, con un nuevo valor de `dateModified` y, si no tenía ninguno, un valor de `dateCreated` correspondiente al mismo momento. Una modificación enviada antes de su fecha de carga parece no haber sido modificada para todo lo que se reconcilia en ese atributo, incluidos FieldWorks y la importación LIFT de The Combine.
- **Solo entradas.** No debe haber ningún nodo por debajo de un `<entry>`, ni nada en el encabezado.
- **Lo que se deja tal cual.** Una entrada cuya fecha ha fijado deliberadamente quien realiza la llamada, y una entrada creada tras la carga que ya lleva una.
- **Se respeta la eliminación de una fecha.** `entry.date_modified = None` en una entrada leída con este valor es un valor deliberado como cualquier otro, por lo que la entrada se elimina sin `dateModified`, independientemente de si su contenido se ha movido o no. Una entrada que se lee sin ese valor es un caso distinto: `None` ya está ahí, y no se distingue de no haber modificado nunca el campo, por lo que una edición sigue marcándolo.
- **Se sustituye una fecha que no se puede analizar.** Una fecha que el modelo no ha podido analizar se considera un [residuo](#reading) en lugar de una fecha, por lo que un sello la sobrescribe y la cadena original se descarta; es mejor que una entrada editada contenga una fecha real que `dateModified="whenever"`.
- **El momento.** UTC con precisión de segundos (`YYYY-MM-DDTHH:MM:SSZ`, el formato que utiliza toda exportación de FieldWorks analizada), leído del reloj de pared. Cada segundo corresponde a una fecha, por lo que una modificación guardada en el plazo de un segundo respecto a la anterior lleva el mismo sello.
- **`save(when=...)`** proporciona el momento en lugar de la hora del reloj, lo que garantiza que la salida con marca de tiempo sea reproducible para una puerta de CI basada en diferencias. Debe tener en cuenta la zona horaria y está normalizado a segundos enteros en UTC.
- **`save(stamp=False)`** guarda el modelo tal y como está, incluido el residuo.
- **Confirmar cambios con la escritura `.lift`.** Cualquier cosa que impida que esa escritura se aplique hace que las fechas vuelvan a ser las anteriores. Una vez que llega a su destino, se mantienen en pie, aunque una escritura complementaria falle después de ella.

## El XML de contenido no puede representar

Los caracteres que no pertenecen al BMP —emoji, CJK Extension B, Adlam y cualquier carácter situado por encima de U+FFFF — se consideran contenido normal y se transmiten con la misma secuencia de bytes en ambos sentidos. Un «par sustituto» es un detalle de la codificación UTF-16: las cadenas de Python son secuencias de puntos de código, por lo que ni el lector, ni el escáner de bytes, ni el escritor llegan a verlo nunca.

Un carácter de sustitución _único_ (U+D800–U+DFFF) es diferente: una cadena de Python puede contener uno, pero un documento XML no, independientemente de la codificación. Nunca puede proceder de un archivo —el analizador rechaza ambas formas de escritura, tanto la referencia de carácter `&#xD800;` como los bytes CESU-8/WTF-8—; solo puede proceder de una cadena asignada a través de la API. Al guardar un modelo de este tipo, se produce un error `LiftWriteError` en el que se indican el nombre del nodo y el punto de código, y no se escribe nada; la validación lo señala como un único error de tipo `lone-surrogate`, ya que el documento no se puede serializar para que las capas de esquema lo comprueben.

## Aproximaciones conocidas (solo nodos tocados)

- Los comentarios que se encuentran _dentro_ de una ejecución de `<text>` se conservan, pero se trasladan junto a la ejecución, en lugar de mantenerse en su posición exacta en caracteres.
- El orden de subelementos de tipo «cross» dentro de un elemento editado se normaliza según la agrupación canónica (la propiedad `interleave` del esquema LIFT hace que este orden carezca de importancia semántica).
- Un `<form>` o `<gloss>` sin el atributo `lang` no se vuelve a emitir, y tampoco se emite nada de lo que contenga; la validación señala esta omisión como `form-missing-lang`. Un nodo sin modificar conserva sus bytes de origen, por lo que esa forma se mantiene hasta que se modifique algún dato de su entrada.
- Un elemento multitexto que está presente pero que no contiene nada —ni formas, ni residuos—, por ejemplo, `<definition></definition>`, no se vuelve a emitir. El modelo representa estos campos como un `Multitext` siempre presente (`lexical-unit`, `citation`, `definition`, el `usage` de una relación y `label` / `abreviatura` / `descripción` en referencias URL, rangos, elementos de rango y el encabezado), por lo que uno vacío es indistinguible de uno ausente tras el análisis sintáctico. No se pierde nada a nivel semántico.
