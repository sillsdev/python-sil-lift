# Validar

La validación siempre es explícita: al cargar y guardar nunca se realiza una validación implícita.

```python
import sil_lift

# Exhaustivo: un flujo diferido de problemas (esquema + capas semánticas).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # error [dangling-ref] dictionary.lift:88 (entrada apu): la referencia 'nope' coincide con...

# Detección rápida de fallos: se detiene ante el primer problema de nivel de error.
if any(p.level == "error" for p in sil_lift.iter_problems("dictionary.lift")):
    raise SystemExit(1)

# Estado en memoria (se serializa primero, un coste documentado en léxicos grandes):
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Cada `Problema` incluye un `nivel` (`"error"`/`"advertencia"`), un `código` fijo y un `mensaje`, además de la parte de la dirección que corresponda al hallazgo:

- `archivo`: `None` cuando el léxico no tiene ruta.
- `entry_id`: se establece cuando el hallazgo se refiere a una sola entrada.
- `guid`: se establece cuando el objeto al que se refiere tiene uno (una entrada o un elemento de un rango).
- `línea`: se establece cuando el resultado se corresponde con una línea del documento.

Una conclusión sobre un rango se dirige al compañero `.lift-ranges` que lo define y no incluye ninguna entrada. Los campos no definidos son `None` (`null` en `--format json`, donde todas las claves están siempre presentes).

## Las capas

1. **Esquema LIFT** (`lift-0.13.rng`, la gramática RELAX NG de LIFT 0.13, proporcionada por el proveedor con el mismo contenido binario que lift-standard) sobre el archivo `.lift`.
2. **Esquema de rangos** (`lift-ranges-0.13.rng`, también incluido como dependencia de lift-standard) que abarca todos los componentes complementarios `.lift-ranges` rastreados, dirigido al componente complementario en lugar de a `.lift`.
3. **Comprobaciones semánticas** que los esquemas no pueden expresar: trece en total, una por cada código.

## Códigos de error

Cada resultado incluye uno de estos elementos, independientemente de la capa en la que se haya generado: «schema» y «uri-not-rfc» proceden de las capas de esquema, mientras que los demás son comprobaciones semánticas. Por defecto, se comprueba cada código, excepto «missing-id», que es opcional: pasa «require_ids=True» (o «--require-ids») para activarlo. Los códigos son estables, por lo que los scripts pueden realizar búsquedas basándose en ellos. `--strict` convierte todas las advertencias en errores. El comando `sil-lift validate --allow CODE` excluye un código de la decisión de aprobado/suspenso.

| código                           | nivel       | lo que señala                                                                                                                         |
| -------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `archivo-de-intervalos-ambiguos` | advertencia | varios archivos que responden a un mismo nombre de compañero, tanto en modo de conversión de mayúsculas y minúsculas como en NFC      |
| `dangling-ranges-href`           | advertencia | un encabezado `range/@href` que no remite a ningún archivo asociado                                                                   |
| `dangling-ref`                   | error       | una `relation/@ref` o `variant/@ref` que no coincide con ninguna entrada ni acepción                                                  |
| `duplicate-form-lang`            | advertencia | dos formas en un multitexto que comparten un idioma                                                                                   |
| `duplicate-guid`                 | error       | un identificador reutilizado entre entradas, o entre los rangos o elementos de rango de un mismo documento                            |
| `form-missing-lang`              | error       | un `<form>` o `<gloss>` sin el atributo `lang` que exige el esquema                                                                   |
| `media-href-mismatch`            | advertencia | un enlace «href» de un archivo multimedia que solo permite acceder al archivo mediante la conversión de mayúsculas a minúsculas o NFC |
| `id-faltante`                    | error       | **[opt-in]** una entrada sin GUID, un sentido sin ID                              |
| `archivos-que-faltan`            | advertencia | un archivo de audio o imagen al que se hace referencia y que no se encuentra en el disco                                              |
| `desajuste de normalización`     | advertencia | un nombre que solo permite acceder al identificador al que hace referencia mediante NFC                                               |
| `range-parent`                   | error       | un `range-element/@parent` sin ID de elemento hermano definido                                                                        |
| `esquema`                        | error       | una infracción de la gramática RELAX NG, en el archivo `.lift` o en un archivo complementario                                         |
| `valor-de-rango-indefinido`      | advertencia | un valor de rasgo con clave gramatical o de rango que no figura en la lista del rango                                                 |
| `archivo de rangos ilegibles`    | advertencia | un candidato asociado que existe pero que no es un documento de rangos legible                                                        |
| `uri-not-rfc`                    | advertencia | un atributo `href` que no es un URI válido (por ejemplo, `file://C:/...` en FLEx)                                  |

### Lo que detecta la validación

Las tres capas funcionan a partir del documento tal y como está serializado, por lo que, si un documento no se puede serializar en absoluto, se notifica como un único error de tipo `lone-surrogate`. Consulta [las garantías de Fidelity](../fidelity.md#content-xml-cannot-represent).

La validación es de solo lectura: muestra el documento tal y como está, antes de que una operación de guardado marque la `dateModified`. Los sellos nunca provocan un error, por lo que un documento que supera la validación seguirá superándola una vez guardado.

### Códigos de carpetas complementarias

Un nombre de acompañante que coincide con varios archivos no carga ninguno de ellos: los rangos que definen desaparecen hasta que todos, excepto uno, se renombren o se eliminen.

Los tres códigos de carpetas asociadas (`ambiguous-ranges-file`, `dangling-ranges-href` y `unreadable-ranges-file`) solo se notifican cuando se ha ejecutado la detección de carpetas asociadas:

- Al cargar con `resolve_ranges=False`, los «compañeros» quedan fuera del ámbito, por lo que no se muestra ninguno de ellos.
- Añadir uno posteriormente con `add_ranges_file()` no hace que vuelvan a aparecer, ya que nunca lee la carpeta sobre la que informan estos códigos.

`resolve_ranges=False` no afecta a `missing-media` ni a `media-href-mismatch`: los archivos multimedia nunca se resuelven en el modelo, por lo que no hay nada que se pueda desactivar.

### Códigos de medios

sil-lift busca cada archivo multimedia en la URL indicada, así como en las carpetas `audio/` (archivos de audio) o `pictures/` (ilustraciones). Esa carpeta es una suposición de sil-lift, no algo que figure en el documento, por lo que se adapta a cualquier forma de escritura mayúscula y su ortografía nunca se indica.

Los códigos `missing-media` y `media-href-mismatch` se reparten la comprobación de los archivos multimedia: el primero indica que ningún archivo se corresponde con la URL, independientemente de cómo se escriba; el segundo, que sí hay uno, pero que la URL no lo identifica exactamente. La segunda es la observación sobre la portabilidad: el archivo está aquí, y un servidor que distinga entre mayúsculas y minúsculas y que aloje esta carpeta no lo encontrará.

Una _carpeta_ con un error ortográfico se renombra una sola vez, independientemente del número de referencias que haya en ella, por lo que solo se notifica una vez y no se registra ninguna entrada. Se notifica un error ortográfico en el _nombre de archivo_ por cada referencia, dirigido a la entrada que lo escribió.

## Resultados de FieldWorks (FLEx) en el mundo real

FieldWorks genera de forma sistemática cierto contenido que las herramientas más estrictas rechazan. A continuación se expone la política de sil-lift, para que los léxicos reales resulten útiles:

- Los enlaces `file://C:/...` (URI no válidos) se señalan como **advertencias** (`uri-not-rfc`), no como errores de esquema; el validador de C# nunca los ha rechazado.
- Los elementos secundarios intercalados legalmente (por ejemplo, «campo, nota, campo, nota», en cierto sentido) **no** se marcan; esto permite ignorar un falso positivo en libxml2.
- Las extensiones `trait`/`field` de FLEx dentro de `range-element` **sí** se señalan (como errores de esquema respecto al esquema de rangos): se trata de auténticas desviaciones respecto a la especificación.
- Los nombres se resuelven en función de los `id` de rango y de los elementos del rango según la **normalización NFC** de Unicode: enlaces `parent`, valores de rango y el nombre del `trait` o el `id` de encabezado `range` que identifica un rango.
  - FLEx se normaliza a NFC al exportarse, pero algunas operaciones de escritura solían eludir ese paso, por lo que el `id` de un elemento de rango puede ser NFD, mientras que sus etiquetas, su propio `parent` y los valores `.lift` que lo nombran son NFC.
  - Una comparación exacta daría un resultado erróneo en dos aspectos. Las referencias a un identificador NFD se marcarían como erróneas, aunque la exportación sea correcta. Y un rango cuyo propio `id` sea NFD pasaría desapercibido: ningún nombre de rasgo coincidiría con él, y un rasgo cuyo nombre no coincida con ningún rango se acepta tal cual.
  - Un nombre que solo coincide tras la normalización se notifica como una **advertencia** de «normalization-mismatch», una vez por identificador en lugar de una vez por referencia, dirigida al archivo que lo define. Los datos son correctos, pero un usuario que compare cadenas sin procesar no podrá resolver esas referencias.
  - Los identificadores nunca se reescriben: el archivo conserva la ortografía original.
