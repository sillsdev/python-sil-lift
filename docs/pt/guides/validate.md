# Validar

A validação é sempre explícita — o carregamento e o guardamento nunca validam implicitamente.

```python
import sil_lift

# Exaustivo: um fluxo preguiçoso de Problemas (esquema + camadas semânticas).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # erro [dangling-ref] dictionary.lift:88 (entrada apu): a referência 'nope' corresponde a ...

# Falha rápida: lança um LiftValidationError no primeiro problema de nível de erro.
sil_lift.validate_file("dictionary.lift")

# Estado na memória (serializa primeiro — um custo documentado em léxicos de grande dimensão):
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Cada `Problema` contém um `nível` (`"erro"`/`"aviso"`), um `código` fixo, uma `mensagem` e um endereço: `ficheiro`, `entry_id`, `guid`, `linha`.

## As camadas

1. **RELAX NG** em relação à gramática LIFT 0.13 (fornecida pelo lift-standard).
2. **Esquema de intervalos** — o ficheiro `lift-ranges-0.13.rng` deste projeto — sobre todos os companheiros `.lift-ranges` monitorizados.
3. **Verificações semânticas** que a gramática não consegue expressar: `duplicate-guid`, `dangling-ref`, `range-parent`, `undefined-range-value`, `duplicate-form-lang`, `missing-media`.

## Resultados do FieldWorks (FLEx) em condições reais

O FieldWorks cria sistematicamente algum conteúdo que as ferramentas de verificação rigorosas rejeitam. Eis a política do sil-lift, para que os léxicos reais sejam validados de forma útil:

- Os hrefs do tipo `file://C:/...` (URIs inválidas) são assinalados como **avisos** (`uri-not-rfc`), e não como erros de esquema — o validador C# nunca os rejeitou.
- Os elementos filhos intercalados legalmente (por exemplo, `field, note, field, note`, de certa forma) **não** são assinalados, o que permite contornar um falso positivo na libxml2.
- Os valores dos intervalos são comparados de acordo com a normalização NFC do Unicode — o FLEx grava o ficheiro `.lift` em NFC, mas o ficheiro `.lift-ranges` em NFD, dentro da mesma exportação.
- As extensões `trait`/`field` do FLEx dentro de `range-element` **são** assinaladas (erros de esquema em relação ao esquema de intervalos): tratam-se de verdadeiros desvios em relação à especificação.
