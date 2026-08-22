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

Cada `Problema` contém um `nível` (`"erro"`/`"aviso"`), um `código` fixo, uma `mensagem` e toda a informação de localização disponível sobre a ocorrência: `ficheiro` (`None` quando o léxico não tem caminho), `entry_id` quando se refere a uma entrada, `guid` quando o objeto em questão possui um (uma entrada ou um elemento de intervalo) e `linha` quando corresponde a uma linha no documento. Uma descoberta relativa a um intervalo é dirigida ao companheiro `.lift-ranges` que o define e não contém qualquer entrada. Os campos não definidos são `None` — `null` no `--format json`, onde todas as chaves estão sempre presentes.

## As camadas

1. **RELAX NG** em relação à gramática LIFT 0.13 (fornecida pelo lift-standard — uma cópia byte a byte incorporada neste pacote).
2. **Esquema de intervalos** — o ficheiro `lift-ranges-0.13.rng` deste projeto — para cada companheiro `.lift-ranges` monitorizado, dirigido ao companheiro em vez de ao `.lift`.
3. **Verificações semânticas** que a gramática não consegue expressar — nove no total, uma por código.

## Códigos de problema

Cada resultado inclui um destes, independentemente da camada que o tenha gerado — `schema` e `uri-not-rfc` provêm das camadas de esquema, enquanto os outros nove são verificações semânticas. As cadeias de caracteres são uma interface suportada; a opção `--strict` transforma todos os avisos em erros.

| código                              | nível | o que assinala                                                                                      |
| ----------------------------------- | ----- | --------------------------------------------------------------------------------------------------- |
| `dangling-ranges-href`              | aviso | um cabeçalho `range/@href` que não remete para nenhum ficheiro associado                            |
| `dangling-ref`                      | erro  | um `relation/@ref` ou `variant/@ref` que não corresponde a nenhuma entrada ou significado           |
| `duplicate-form-lang`               | aviso | duas formas num único multitexto que partilham uma língua                                           |
| `duplicate-guid`                    | erro  | um GUID reutilizado entre entradas ou entre intervalos/elementos de intervalo de um mesmo documento |
| `missing-id`                        | erro  | adesão através de `require_ids`: uma entrada sem um GUID, um sentido sem um ID      |
| `failas-de-meios`                   | aviso | um ficheiro de áudio ou de imagem referenciado que não se encontra no disco                         |
| `incompatibilidade de normalização` | aviso | um nome que acede ao ID a que se refere apenas através da tecnologia NFC                            |
| `range-parent`                      | erro  | um `range-element/@parent` sem identificação de elemento irmão definida                             |
| `esquema`                           | erro  | uma violação da gramática RELAX NG, no ficheiro `.lift` ou num ficheiro complementar                |
| `valor-fora-do-intervalo`           | aviso | um valor de característica com chave gramatical ou de intervalo que não conste do intervalo         |
| `uri-não-rfc`                       | aviso | um atributo `href` que não é um URI válido — `file://C:/...` do FLEx                                |

As três camadas baseiam-se no que a função `save()` escreveria; por isso, um documento que não possa ser serializado de todo é sinalizado como um único erro `lone-surrogate` — ver [Garantias de fidelidade](../fidelity.md#content-xml-cannot-represent).

## Resultados do FieldWorks (FLEx) em condições reais

O FieldWorks cria sistematicamente algum conteúdo que as ferramentas de verificação rigorosas rejeitam. Eis a política do sil-lift, para que os léxicos reais sejam validados de forma útil:

- Os hrefs do tipo `file://C:/...` (URIs inválidas) são assinalados como **avisos** (`uri-not-rfc`), e não como erros de esquema — o validador C# nunca os rejeitou.
- Os elementos filhos intercalados legalmente (por exemplo, `field, note, field, note`, de certa forma) **não** são assinalados, o que permite contornar um falso positivo na libxml2.
- As extensões `trait`/`field` do FLEx dentro de `range-element` **são** assinaladas (erros de esquema em relação ao esquema de intervalos): tratam-se de verdadeiros desvios em relação à especificação.
- Os nomes são resolvidos com base nos `id`s dos intervalos e dos elementos dos intervalos, de acordo com a **normalização NFC** do Unicode — ligações `parent`, valores de intervalo e o nome da `característica` ou o `id` do cabeçalho `range` que identifica um intervalo. O FLEx normaliza para NFC na exportação, mas algumas gravações costumavam contornar essa etapa, pelo que o `id` de um elemento de intervalo pode ser NFD, enquanto os seus rótulos, o seu próprio `parent` e os valores `.lift` que o designam são NFC.
  - Se compararmos exatamente, uma exportação de som parece estar incorreta — e um intervalo cujo `id` está escrito de forma diferente passa completamente despercebido, uma vez que um nome de característica que não corresponde a nenhum intervalo é aceite silenciosamente.
  - Um nome que só coincidiu após a normalização é assinalado como um **aviso** de `normalization-mismatch`, uma vez por identificador, independentemente do número de referências que diferem, dirigido ao ficheiro que o define. Os dados estão corretos, mas um utilizador que compare cadeias de caracteres em bruto não conseguirá interpretar essas referências.
  - Os IDs nunca são reescritos: o ficheiro mantém a grafia original.
