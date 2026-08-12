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

Cada «Problema» incluye un «nivel» («error»/«advertencia»), un «código» fijo, un «mensaje» y una dirección: «archivo», «id_entrada», «guid» y «línea».

## Las capas

1. **RELAX NG** con respecto a la gramática LIFT 0.13 (incluida en lift-standard —una copia idéntica al byte, incorporada a este paquete).
2. **Esquema de rangos** —el archivo `lift-ranges-0.13.rng` de este proyecto— sobre cada complemento `.lift-ranges` al que se realiza un seguimiento.
3. **Comprobaciones semánticas** que la gramática no puede expresar: `duplicate-guid`, `dangling-ref`, `range-parent`, `undefined-range-value`, `duplicate-form-lang`, `missing-media`.

## Resultados de FieldWorks (FLEx) en el mundo real

FieldWorks genera de forma sistemática cierto contenido que las herramientas más estrictas rechazan. A continuación se expone la política de sil-lift, para que los léxicos reales resulten útiles:

- Los enlaces `file://C:/...` (URI no válidos) se señalan como **advertencias** (`uri-not-rfc`), no como errores de esquema; el validador de C# nunca los ha rechazado.
- Los elementos secundarios intercalados legalmente (por ejemplo, «campo, nota, campo, nota», en cierto sentido) **no** se marcan, lo que permite evitar un falso positivo en libxml2.
- Los valores de rango se comparan según la normalización NFC de Unicode: FLEx escribe el archivo `.lift` en NFC, pero el `.lift-ranges` en NFD dentro de la misma exportación.
- Las extensiones `trait`/`field` de FLEx dentro de `range-element` **sí** se señalan (como errores de esquema respecto al esquema de rangos): se trata de auténticas desviaciones respecto a la especificación.
