# Diferenças em relação às bibliotecas do C\#

O sil-lift é, de certa forma, análogo às ferramentas LIFT da SIL para C# — principalmente o `SIL.Lift` em [libpalaso](https://github.com/sillsdev/libpalaso) (analisador sintático, validador, migrador, `LiftSorter`), o `SIL.DictionaryServices` no mesmo repositório (o modelo `LexEntry`/`LexSense`, com o seu próprio leitor/gravador LIFT, utilizado pelo The Combine e pelo WeSay), e os manipuladores LIFT no [Chorus](https://github.com/sillsdev/chorus). Trata-se de uma nova implementação, não de uma adaptação. Esta página resume os casos em que o comportamento difere deliberadamente.

## Âmbito

| Capacidade                      | Bibliotecas C#                                           | sil-lift                                                                                  |
| ------------------------------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Versões do LIFT                 | 0,10–0,13 (migração integrada)        | **Apenas 0.13**; as versões mais antigas são rejeitadas com um erro claro |
| Migração de versão              | `Migrator` (cadeia XSLT)              | nenhuma — utilizar os XSLT do «lift-standard» para atualizações pontuais                  |
| Fusão/sincronização a três vias | Refrão                                                   | fora do âmbito                                                                            |
| Validação                       | Apenas RELAX NG (`Validator`)         | RELAX NG + verificações de esquema e semânticas                                           |
| Streaming                       | análise sintática com granularidade interna das entradas | API pública `open_reader` / `open_writer`                                                 |

## Estrutura da API

O analisador do `SIL.Lift` é orientado por callbacks (`ILexiconMerger`): envia eventos de análise a um consumidor. Em vez disso, o sil-lift devolve um gráfico de objetos simples — classes de dados tipadas para cada elemento LIFT — porque os programadores de Python querem objetos, e não callbacks. O `SIL.DictionaryServices` sobrepõe um modelo de objetos `LexEntry`/`LexSense` ao `SIL.Lift`, mas, enquanto modelo de aplicação, representa apenas as construções que essas aplicações utilizam — pelo que a resserialização através dele não consegue preservar o conteúdo fora do modelo da mesma forma que o tratamento de resíduos LIFT e a fidelidade de bytes do sil-lift o fazem (ver abaixo). A API de streaming devolve o _mesmo_ tipo `Entry`, pelo que não há um segundo modelo simplificado para aprender.

## Fidelidade de ida e volta

A diferença deliberada mais marcante. Ao guardar com o `SIL.Lift`, todo o documento é novamente serializado. A sil-lift garante:

- um documento inalterado é guardado com **identidade de bytes**, e
- As entradas não alteradas mantêm os seus bytes de origem exatos, mesmo quando outras entradas são alteradas — trata-se do mesmo agrupamento de bytes por entrada que o Chorus utiliza, aplicado automaticamente.

Consulte [Garantias da Fidelity](fidelity.md).

## Validação

O `Validator` do C# executa uma passagem RELAX NG e apresenta os primeiros erros sob a forma de cadeias de caracteres. O sil-lift apresenta um fluxo estruturado de `Problemas`, cada um contendo o ficheiro, a entrada e a linha a que se refere, e a sua camada de esquema diverge deliberadamente em três pontos:

- **Os URIs inválidos são avisos, não erros.** O motor RELAX NG do C# nunca impôs o tipo de dados `anyURI`, pelo que o FieldWorks (FLEx) tem vindo a inserir hrefs do tipo `file://C:/...` em léxicos reais há anos. A rejeição desses ficheiros faria com que praticamente todas as exportações do FLEx fossem sinalizadas.
- **As regras do Schematron são aplicadas** (como verificações semânticas): as linguagens de formulário duplicadas e as co-restrições semelhantes na gramática LIFT foram ignoradas silenciosamente tanto pela validação em C# como pela validação direta do lxml.
- **As comparações entre ficheiros são normalizadas segundo o Unicode**, uma vez que o FLEx grava o ficheiro `.lift` em NFC e o ficheiro associado `.lift-ranges` em NFD.

O sil-lift também valida os ficheiros `.lift-ranges` associados a um léxico carregado, comparando-os com um esquema para documentos de intervalos autónomos (fornecido pelo `lift-standard` juntamente com a gramática LIFT de base) — todos os ficheiros de intervalos externos monitorizados são verificados sempre que o `.lift` é validado — sem que exista tal esquema (ou verificação) no mundo do C#. (Não existe um ponto de entrada para validar um ficheiro `.lift-ranges` por si só, separado de um ficheiro `.lift`.)

## Ordenação canónica

O `Lexicon.sort()` reflete as regras fundamentais do `LiftSorter` (entradas por GUID, sem distinção entre maiúsculas e minúsculas; intervalos e elementos de intervalo por ID; definições de campos de cabeçalho por etiqueta; significados mantidos na ordem do ficheiro; espaços em branco dentro de `<text>` nunca são alterados), com três diferenças:

- as entradas sem um GUID são ordenadas de forma determinística por ID (o `LiftSorter` pressupõe a existência de um GUID);
- a ordenação é independente da configuração regional (pontos de código com maiúsculas e minúsculas ignoradas, e não a ordenação de cultura invariante do .NET);
- As listas do mesmo tipo, como notas, relações e formulários, mantêm a ordem do documento em vez de serem reordenadas por chave — o agrupamento já é determinístico e reordená-las apenas acrescenta ruído às diferenças.

O ficheiro `canonicalizeLift.xsl` do repositório de especificações não é utilizado de todo: elimina os espaços em branco no texto lexical (de forma destrutiva) e os identificadores gerados variam em cada execução.

## Não transitado

- Funcionalidades específicas do WeSay (painel de controlo/gestão de configurações relacionadas com ficheiros LIFT).
- `SynchronicMerger` (fusão de atualizações do Chorus) — o conceito de divisão em blocos de bytes mantém-se na camada de fidelidade, mas a fusão já não.
- Análise do sistema de escrita LDML: os ficheiros na pasta `WritingSystems/` são tratados como conteúdo opaco da pasta.
