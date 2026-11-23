# Diferenças em relação às bibliotecas do C\#

O sil-lift é, de certa forma, análogo às ferramentas LIFT da SIL para C#, consistindo principalmente em duas partes da [libpalaso](https://github.com/sillsdev/libpalaso):

- `SIL.Lift`: analisador, validador, migrador, `LiftSorter`.
- `SIL.DictionaryServices`: o modelo `LexEntry`/`LexSense`, com o seu próprio leitor/gravador LIFT, utilizado pelo The Combine e pelo WeSay.

O sil-lift é uma implementação nova, não uma adaptação. Esta página resume os casos em que o comportamento difere deliberadamente.

## Âmbito

| Capacidade         | Bibliotecas C#                                           | sil-lift                                                                                  |
| ------------------ | -------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Versões do LIFT    | 0,10–0,13 (migração integrada)        | **Apenas 0.13**; as versões mais antigas são rejeitadas com um erro claro |
| Migração de versão | `Migrator` (cadeia XSLT)              | nenhuma; utilize os XSLTs do «lift-standard» para atualizações pontuais                   |
| Validação          | Apenas RELAX NG (`Validator`)         | RELAX NG + verificações de esquema e semânticas                                           |
| Streaming          | análise sintática com granularidade interna das entradas | API pública `open_reader` / `open_writer`                                                 |

## Estrutura da API

O analisador do `SIL.Lift` é orientado por callbacks (`ILexiconMerger`): envia eventos de análise a um consumidor. sil-lift instead returns a plain object graph (typed dataclasses for every LIFT element) because Python scripters want objects, not callbacks.

`SIL.DictionaryServices` does layer a `LexEntry`/`LexSense` object model over `SIL.Lift`, but it is an application model: it represents only the constructs those apps use. Re-serializing through it therefore can't preserve out-of-model content the way sil-lift's LIFT residue handling and byte fidelity do (see below).

A API de streaming devolve o _mesmo_ tipo `Entry`, pelo que não há um segundo modelo simplificado para aprender.

## Fidelidade de ida e volta

A diferença deliberada mais marcante. Ao guardar com o `SIL.Lift`, todo o documento é novamente serializado. A sil-lift garante:

- um documento inalterado é guardado com **identidade de bytes**, e
- untouched entries keep their exact source bytes even when other entries change: per-entry byte chunking, applied automatically.

Consulte [Garantias da Fidelity](fidelity.md).

## Validação

O `Validator` do C# executa uma passagem RELAX NG e apresenta os primeiros erros sob a forma de cadeias de caracteres. sil-lift reports a structured `Problem` stream, each carrying the file, entry, and line it concerns. Its schema layer knowingly diverges in three places:

- **Os URIs inválidos são avisos, não erros.** O motor RELAX NG do C# nunca impôs o tipo de dados `anyURI`, pelo que o FieldWorks (FLEx) tem vindo a inserir hrefs do tipo `file://C:/...` em léxicos reais há anos. A rejeição desses ficheiros faria com que praticamente todas as exportações do FLEx fossem sinalizadas.
- **Schematron rules are enforced** (as semantic checks): duplicate form languages and similar co-constraints in the LIFT grammar were silently ignored by C# validation.
- **Range id comparisons are Unicode-normalized** (NFC), because FLEx exports mix NFC and NFD ids. References that resolve only after normalizing are reported as `normalization-mismatch` warnings, a check with no C# counterpart. See [Real-world FieldWorks (FLEx) output](guides/validate.md#real-world-fieldworks-flex-output).

When sil-lift validates a `.lift`, it also validates the `.lift-ranges` companions against a schema for standalone ranges documents, vendored from `lift-standard`. The C# `Validator` does not check `.lift-ranges` files.

## Ordenação canónica

O `Lexicon.sort()` reflete as regras fundamentais do `LiftSorter` (entradas por GUID, sem distinção entre maiúsculas e minúsculas; intervalos e elementos de intervalo por ID; definições de campos de cabeçalho por etiqueta; significados mantidos na ordem do ficheiro; espaços em branco dentro de `<text>` nunca são alterados), com três diferenças:

- as entradas sem um GUID são ordenadas de forma determinística por ID (o `LiftSorter` pressupõe a existência de um GUID);
- a ordenação é independente da configuração regional (pontos de código com maiúsculas e minúsculas ignoradas, e não a ordenação de cultura invariante do .NET);
- same-type lists such as notes, relations, and forms keep their document order rather than being re-sorted by key; grouping is already deterministic, and reordering them only adds diff noise.

O ficheiro `canonicalizeLift.xsl` do repositório de especificações não é utilizado de todo: elimina os espaços em branco no texto lexical (de forma destrutiva) e os identificadores gerados variam em cada execução.

## Não transitado

- Funcionalidades específicas do WeSay (painel de controlo/gestão de configurações relacionadas com ficheiros LIFT).
- `SynchronicMerger` (LIFT update-file merging): the byte-chunking idea lives on in the fidelity layer, the merging does not.
- Análise do sistema de escrita LDML: os ficheiros na pasta `WritingSystems/` são tratados como conteúdo opaco da pasta.
