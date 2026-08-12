# Garantías de Fidelity

LIFT es un formato de _intercambio_, por lo que la primera regla es **no descartar nunca lo que no entiendas**. El contrato de `sil-lift`, verificado por el conjunto de pruebas en cada ejecución (archivos del corpus más generación basada en propiedades):

## Lectura

Cualquier documento LIFT 0.13 bien formado se carga, incluso si el contenido no cumple con el esquema. Todo aquello que el modelo no defina se traslada al contenedor opaco `Extras` del nodo más cercano como _residuo LIFT_ —nombre que utiliza FieldWorks para referirse a este mismo concepto, y que almacena en un campo `LiftResidue`—: atributos y elementos desconocidos, comentarios XML e instrucciones de procesamiento, texto extrañado y atributos tipificados mal formados (una fecha incorrecta se mantiene como la cadena original en `Extras`; el campo tipado es `None`).

## Guardar un documento sin modificaciones

`load()` → `save()` sin modificaciones genera una **salida idéntica a nivel de bytes**: sin reformateo, sin reescapado, sin reordenación, incluyendo las marcas de orden de bytes y las declaraciones XML. Actualmente no hay ninguna lista de normalización: la identidad es exacta.

Excepciones (el escritor recurre a la serialización canónica completa, que es semánticamente completa pero no conserva los bytes):

- la codificación de origen no es compatible con ASCII (no es UTF-8/US-ASCII), o
- el código fuente contiene un DOCTYPE, o
- el escáner de bytes y el analizador sintáctico no coinciden en cuanto a la estructura de nivel superior del documento —por ejemplo, un segundo `<header>` que no cumple con las especificaciones, que el analizador sintáctico conserva solo una vez (el escáner es deliberadamente conservador: ante cualquier duda, no captura ningún byte del código fuente)—, o
- El código fuente se compiló en memoria, en lugar de cargarse desde un archivo.

## Guardar un documento editado

- **Las entradas no modificadas se emiten tal cual, a partir de sus bytes originales.** Una entrada se considera modificada si alguna parte de su objeto de modelo ha cambiado desde el análisis (lo cual se detecta mediante una instantánea de serialización canónica, no mediante un indicador de cambios).
- **Las entradas modificadas se vuelven a serializar de forma canónica y completa**: UTF-8, sangría de 2 espacios _fuera_ del contenido mixto (los espacios en blanco dentro de `<text>` y `<span>` nunca se modifican), una agrupación de elementos secundarios documentada por cada elemento (p. ej., entrada: unidad léxica, cita, pronunciaciones, variantes, acepciones, notas, relaciones, etimologías, anotaciones, rasgos, campos), orden fijo de los atributos, fechas en formato ISO-8601 (`Z` para UTC). Todos los residuos se vuelven a emitir; su posición se restablece en el índice secundario original, vinculada a la nueva lista secundaria (se trata de una aproximación: las posiciones exactas en bytes solo se garantizan para las entradas que no se han modificado).
- Al añadir, eliminar o reordenar entradas, se vuelve a serializar la estructura del documento, pero se siguen emitiendo tal cual los bytes de cada entrada que no haya sufrido cambios.

!!! note "&quot;El XML canónico&quot; que aparece aquí no está relacionado con ningún otro XML canónico."
    En esta página, por «forma canónica» se entiende la forma documentada propia de «sil-lift», descrita en uno de los puntos anteriores. No guarda relación alguna con el proceso «Canonical XML (C14N)» del W3C. No tiene nada que ver con la clase `CanonicalXmlSettings` de `SIL.Core`.

## Aproximaciones conocidas (solo nodos tocados)

- Los comentarios que se encuentran _dentro_ de una ejecución de `<text>` se conservan, pero se trasladan junto a la ejecución, en lugar de mantenerse en su posición exacta en caracteres.
- El orden de subelementos de tipo «cross» dentro de un elemento editado se normaliza según la agrupación canónica (la propiedad `interleave` del esquema LIFT hace que este orden carezca de importancia semántica).
- Un elemento multitexto que está presente pero que no contiene nada —ni formas, ni residuos—, por ejemplo, `<definition></definition>`, no se vuelve a emitir. El modelo representa estos campos como un `Multitext` siempre presente (`lexical-unit`, `citation`, `definition`, el `usage` de una relación y `label` / `abreviatura` / `descripción` en referencias URL, rangos, elementos de rango y el encabezado), por lo que uno vacío es indistinguible de uno ausente tras el análisis sintáctico. No se pierde nada a nivel semántico.
