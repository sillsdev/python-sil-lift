# Validar

A validação é sempre explícita: o carregamento e o guardamento nunca validam implicitamente.

```python
import sil_lift

# Exaustivo: um fluxo preguiçoso de Problemas (esquema + camadas semânticas).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # erro [dangling-ref] dictionary.lift:88 (entrada apu): a referência 'nope' corresponde a...

# Fail-fast: parar no primeiro problema de nível de erro.
if any(p.level == "error" for p in sil_lift.iter_problems("dictionary.lift")):
    raise SystemExit(1)

# Estado na memória (serializa primeiro, um custo documentado em léxicos de grande dimensão):
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Cada `Problema` inclui um `nível` (`"erro"`/`"aviso"`), um `código` fixo e uma `mensagem`, além da parte do endereço que a deteção tiver:

- `file`: `None` quando o léxico não tem caminho.
- `entry_id`: a definir quando o resultado diz respeito a uma única entrada.
- `guid`: definido quando o objeto a que se refere possui um (uma entrada ou um elemento de intervalo).
- `linha`: define-se quando o resultado corresponde a uma linha no documento.

Uma descoberta relativa a um intervalo é dirigida ao companheiro `.lift-ranges` que o define e não contém qualquer entrada. Os campos não definidos são `None` (`null` no `--format json`, onde todas as chaves estão sempre presentes).

## As camadas

1. **Esquema LIFT** (`lift-0.13.rng`, a gramática RELAX NG do LIFT 0.13, fornecida como dependência com o mesmo conteúdo binário que o `lift-standard`) sobre o `.lift`.
2. **Esquema de intervalos** (`lift-ranges-0.13.rng`, também fornecido pelo `lift-standard`) sobre cada companheiro `.lift-ranges` monitorizado, dirigido ao companheiro em vez de ao `.lift`.
3. **Verificações semânticas** que os esquemas não conseguem expressar: treze no total, uma por código.

## Códigos de problema

Cada resultado inclui um destes, independentemente da camada que o tenha gerado: `schema` e `uri-not-rfc` provêm das camadas de esquema; os restantes são verificações semânticas. Por predefinição, todos os códigos são verificados, exceto o `missing-id`, que é opcional: passe `require_ids=True` (ou `--require-ids`) para o ativar. Os códigos são estáveis, pelo que os scripts podem fazer a correspondência com base neles. `--strict` transforma todos os avisos em erros. O comando `sil-lift validate --allow CODE` exclui um código da decisão de aprovação/reprovação.

| código                              | nível | o que assinala                                                                                                                      |
| ----------------------------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `ficheiro-de-intervalos-ambíguos`   | aviso | vários ficheiros que correspondem a um mesmo nome de companheiro, tanto no modo de conversão de maiúsculas e minúsculas como no NFC |
| `dangling-ranges-href`              | aviso | um cabeçalho `range/@href` que não remete para nenhum ficheiro associado                                                            |
| `dangling-ref`                      | erro  | um `relation/@ref` ou `variant/@ref` que não corresponde a nenhuma entrada ou significado                                           |
| `duplicate-form-lang`               | aviso | duas formas num único multitexto que partilham uma língua                                                                           |
| `duplicate-guid`                    | erro  | um GUID reutilizado entre entradas ou entre intervalos/elementos de intervalo de um mesmo documento                                 |
| `form-missing-lang`                 | erro  | um `<form>` ou `<gloss>` sem o atributo `lang` exigido pelo esquema                                                                 |
| `media-href-mismatch`               | aviso | um href de ficheiro multimédia que acede ao ficheiro apenas com a conversão de maiúsculas e minúsculas ou NFC                       |
| `missing-id`                        | erro  | **[opt-in]** uma entrada sem um guid, um sentido sem um id                      |
| `failas-de-meios`                   | aviso | um ficheiro de áudio ou de imagem referenciado que não se encontra no disco                                                         |
| `incompatibilidade de normalização` | aviso | um nome que acede ao ID a que se refere apenas através da tecnologia NFC                                                            |
| `range-parent`                      | erro  | um `range-element/@parent` sem identificação de elemento irmão definida                                                             |
| `esquema`                           | erro  | uma violação da gramática RELAX NG, no ficheiro `.lift` ou num ficheiro complementar                                                |
| `valor-fora-do-intervalo`           | aviso | um valor de característica com chave gramatical ou de intervalo que não conste do intervalo                                         |
| `ficheiro-de-intervalos-ilegíveis`  | aviso | um candidato associado que existe, mas que não é um documento de intervalos legível                                                 |
| `uri-não-rfc`                       | aviso | um atributo `href` que não é um URI válido (o `file://C:/...` do FLEx)                                           |

### O que a validação verifica

As três camadas funcionam a partir do documento tal como está serializado; por isso, um documento que não possa ser serializado de todo é, em vez disso, assinalado como um único erro `lone-surrogate`. Consulte [Garantias de fidelidade](../fidelity.md#content-xml-cannot-represent).

A validação é de leitura apenas: apresenta o documento tal como está, antes de um registo de gravação atribuir o valor a `dateModified`. Os carimbos nunca dão origem a uma falha, pelo que um documento que passe na validação continua a ser aprovado depois de guardado.

### Códigos das pastas complementares

Um nome de acompanhante que corresponde a vários ficheiros não carrega nenhum deles: os intervalos que definem ficam ausentes até que todos, exceto um, sejam renomeados ou removidos.

Os três códigos de pastas associadas (`ambiguous-ranges-file`, `dangling-ranges-href` e `unreadable-ranges-file`) são comunicados apenas quando a deteção de pastas associadas foi executada:

- Carregar com `resolve_ranges=False` coloca os companheiros fora do âmbito, pelo que nenhum deles é reportado.
- Adicionar um posteriormente com `add_ranges_file()` não os recupera, uma vez que essa função nunca lê a pasta sobre a qual estes códigos informam.

`resolve_ranges=False` não afeta `missing-media` nem `media-href-mismatch`: os ficheiros multimédia nunca são resolvidos no modelo, pelo que não há nada que se possa desativar.

### Códigos de meios de comunicação

O sil-lift procura cada ficheiro multimédia no endereço href indicado, bem como nas pastas `audio/` (ficheiros de pronúncia) ou `pictures/` (ilustrações). Essa pasta é uma suposição do próprio sil-lift, não algo que conste no documento, pelo que se adapta a qualquer forma de escrita (com maiúsculas ou minúsculas) e a sua ortografia nunca é indicada.

Os códigos `missing-media` e `media-href-mismatch` dividem entre si a verificação do ficheiro multimédia: o primeiro significa que nenhum ficheiro correspondeu ao href, independentemente da grafia; o segundo significa que um ficheiro correspondeu, mas o href não o identifica exatamente. A segunda é a constatação relativa à portabilidade: o ficheiro está aqui, mas um servidor que distinga maiúsculas de minúsculas e que aloje esta pasta não o irá encontrar.

Uma _pasta_ com um erro ortográfico é renomeada uma única vez, independentemente do número de referências que a mencionem; por isso, é comunicada uma única vez e não dá origem a qualquer registo. É comunicada uma erro ortográfico no _nome do ficheiro_ por referência, dirigido à entrada que o escreveu.

## Resultados do FieldWorks (FLEx) em condições reais

O FieldWorks cria sistematicamente algum conteúdo que as ferramentas de verificação rigorosas rejeitam. Eis a política do sil-lift, para que os léxicos reais sejam validados de forma útil:

- Os hrefs `file://C:/...` (URIs inválidas) são assinalados como **avisos** (`uri-not-rfc`), e não como erros de esquema; o validador C# nunca os rejeitou.
- Os elementos aninhados legalmente (por exemplo, `field, note, field, note`, de certa forma) **não** são assinalados; isto permite ignorar um falso positivo na libxml2.
- As extensões `trait`/`field` do FLEx dentro de `range-element` **são** assinaladas (erros de esquema em relação ao esquema de intervalos): tratam-se de verdadeiros desvios em relação à especificação.
- Os nomes são resolvidos com base nos intervalos e nos `id`s dos elementos do intervalo, de acordo com a **normalização NFC** do Unicode: ligações `parent`, valores de intervalo e o nome da `característica` ou o `id` do cabeçalho `range` que identifica um intervalo.
  - O FLEx normaliza para NFC na exportação, mas algumas gravações costumavam contornar essa etapa, pelo que o `id` de um elemento de intervalo pode ser NFD, enquanto os seus rótulos, o seu próprio `parent` e os valores `.lift` que o designam são NFC.
  - Uma comparação exata estaria errada em dois aspetos. As referências a um identificador NFD seriam indicadas como inválidas, embora a exportação esteja correta. E um intervalo cujo próprio `id` seja NFD passaria despercebido: nenhum nome de característica corresponderia a ele, e uma característica cujo nome não corresponda a nenhum intervalo é aceite tal como está.
  - Um nome que só coincidiu após a normalização é assinalado como um **aviso** de `normalization-mismatch`, uma vez por ID, em vez de uma vez por referência, dirigido ao ficheiro que o define. Os dados estão corretos, mas um utilizador que compare cadeias de caracteres em bruto não conseguirá interpretar essas referências.
  - Os IDs nunca são reescritos: o ficheiro mantém a grafia original.
