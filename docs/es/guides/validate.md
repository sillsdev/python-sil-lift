# Validar

La validación siempre es explícita: las operaciones de carga y guardado nunca realizan una validación implícita.

```python
import sil_lift

# Exhaustivo: un flujo diferido de problemas (esquema + capas semánticas).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # error [dangling-ref] dictionary.lift:88 (entrada apu): la referencia «nope» coincide con...

# Detección rápida de errores: lanza un LiftValidationError ante el primer problema de nivel de error.
sil_lift.validate_file("dictionary.lift")

# Estado en memoria (se serializa primero — un coste documentado en léxicos grandes):
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Cada `Problema` incluye un `nivel` (`«error»`/`«advertencia»`), un `código` fijo, un `mensaje` y toda la información de ubicación de la que disponga el hallazgo: «archivo» («None» cuando el léxico no tiene ruta), «entry_id» cuando se refiere a una entrada, «guid» cuando el objeto al que se refiere tiene uno (una entrada o un elemento de rango) y «línea» cuando se corresponde con una línea del documento. Una conclusión sobre un rango se dirige al compañero `.lift-ranges` que lo define y no incluye ninguna entrada. Los campos no definidos son `None` — `null` en `--format json`, donde todas las claves están siempre presentes.

## Las capas

1. **RELAX NG** con respecto a la gramática LIFT 0.13 (incluida en lift-standard —una copia idéntica al byte, incorporada a este paquete).
2. **Esquema de rangos** —el archivo `lift-ranges-0.13.rng` de este proyecto— sobre cada compañero `.lift-ranges` al que se realiza un seguimiento, dirigido al compañero en lugar de a `.lift`.
3. **Comprobaciones semánticas** que la gramática no puede expresar: diez en total, una por cada código.

## Códigos de error

Cada resultado incluye uno de estos elementos, independientemente de la capa en la que se haya generado: `schema` y `uri-not-rfc` proceden de las capas de esquema, mientras que los otros diez son comprobaciones semánticas. Las cadenas son una interfaz compatible; la opción `--strict` convierte todas las advertencias en errores.

| código                           | nivel       | lo que señala                                                                                                                    |
| -------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `archivo-de-intervalos-ambiguos` | advertencia | varios archivos que responden a un mismo nombre de compañero, tanto en modo de conversión de mayúsculas y minúsculas como en NFC |
| `dangling-ranges-href`           | advertencia | un encabezado `range/@href` que no remite a ningún archivo asociado                                                              |
| `dangling-ref`                   | error       | una `relation/@ref` o `variant/@ref` que no coincide con ninguna entrada ni acepción                                             |
| `duplicate-form-lang`            | advertencia | dos formas en un multitexto que comparten un idioma                                                                              |
| `duplicate-guid`                 | error       | un identificador reutilizado entre entradas, o entre los rangos o elementos de rango de un mismo documento                       |
| `id-faltante`                    | error       | Inclusión mediante `require_ids`: una entrada sin GUID, un sentido sin ID                                        |
| `archivos-que-faltan`            | advertencia | un archivo de audio o imagen al que se hace referencia y que no se encuentra en el disco                                         |
| `desajuste de normalización`     | advertencia | un nombre que solo permite acceder al identificador al que hace referencia mediante NFC                                          |
| `range-parent`                   | error       | un `range-element/@parent` sin ID de elemento hermano definido                                                                   |
| `esquema`                        | error       | una infracción de la gramática RELAX NG, en el archivo `.lift` o en un archivo complementario                                    |
| `valor-de-rango-indefinido`      | advertencia | un valor de rasgo con clave gramatical o de rango que no figura en la lista del rango                                            |
| `uri-not-rfc`                    | advertencia | un enlace `href` que no es un URI válido — `file://C:/...` de FLEx                                                               |

Las tres capas se basan en lo que escribiría `save()`, por lo que un documento que no se pueda serializar en absoluto se notifica como un único error `lone-surrogate`; véanse las [Garantías de fidelidad](../fidelity.md#content-xml-cannot-represent).

Un nombre de acompañante que coincide con varios archivos no carga ninguno de ellos: los rangos que definen desaparecen hasta que todos, excepto uno, se renombren o se eliminen.

## Resultados de FieldWorks (FLEx) en el mundo real

FieldWorks genera de forma sistemática cierto contenido que las herramientas más estrictas rechazan. A continuación se expone la política de sil-lift, para que los léxicos reales resulten útiles:

- Los enlaces `file://C:/...` (URI no válidos) se señalan como **advertencias** (`uri-not-rfc`), no como errores de esquema; el validador de C# nunca los ha rechazado.
- Los elementos secundarios intercalados legalmente (por ejemplo, «campo, nota, campo, nota», en cierto sentido) **no** se marcan, lo que permite evitar un falso positivo en libxml2.
- Las extensiones `trait`/`field` de FLEx dentro de `range-element` **sí** se señalan (como errores de esquema respecto al esquema de rangos): se trata de auténticas desviaciones respecto a la especificación.
- Los nombres se resuelven en función de los `id` de los rangos y de los elementos de los rangos según la **normalización NFC** de Unicode: enlaces `parent`, valores de rango y el nombre del `trait` o el `id` del encabezado `range` que identifica un rango. FLEx se normaliza a NFC al exportarse, pero algunas operaciones de escritura solían eludir ese paso, por lo que el `id` de un elemento de rango puede ser NFD, mientras que sus etiquetas, su propio `parent` y los valores `.lift` que lo nombran son NFC.
  - Si se comparan exactamente, una exportación válida parece errónea, y un rango cuyo «id» se escribe al revés pasa totalmente desapercibido, ya que un nombre de rasgo que no corresponde a ningún rango se acepta sin avisar.
  - Un nombre que solo coincide tras la normalización se notifica como una **advertencia** de «normalization-mismatch», una vez por cada identificador, independientemente del número de referencias que difieran, dirigida al archivo que lo define. Los datos son correctos, pero un usuario que compare cadenas sin procesar no podrá resolver esas referencias.
  - Los identificadores nunca se reescriben: el archivo conserva la ortografía original.
