# A pasta LIFT: gamas e suportes

Um léxico LIFT é normalmente uma _pasta_: o ficheiro `.lift`, um ou mais ficheiros complementares `.lift-ranges` (ficheiros «sidecar») e ficheiros multimédia nas pastas `audio/` e `pictures/`.

## Intervalos

```python
lex = sil_lift.load("dictionary.lift")      # companheiros rastreados automaticamente

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # vista {id: Range} combinada
lex.all_ranges()["grammatical-info"].elements
```

A função `lex.save()` grava o ficheiro `.lift` e todas as funções complementares monitorizadas em conjunto. As alterações feitas num `RangesFile` são guardadas no _seu_ ficheiro; os intervalos que não foram alterados mantêm os seus bytes exatos. Utilização autónoma:

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

### Descoberta de planetas companheiros

São testados vários candidatos e cada ficheiro distinto entre eles é carregado.

- Um cabeçalho `range/@href` que aponta para um ficheiro existente é utilizado tal como indicado.
- Um atributo `href` que não remete para nada recorre ao seu nome base, seguido de `.lift`. O FieldWorks grava percursos absolutos incompletos do tipo `file://C:/...` a partir do computador de exportação, e é essa solução alternativa que permite que funcionem localmente.
- O elemento irmão convencional `<name>.lift-ranges` é selecionado mesmo quando nada faz referência a ele.

Os nomes que diferem apenas em maiúsculas e minúsculas ou na normalização Unicode continuam a corresponder-se (`Dict.LIFT` encontra `Dict.lift-ranges`), a menos que vários ficheiros correspondam a um mesmo nome, caso em que nenhum deles é carregado e a situação é indicada como [`ambiguous-ranges-file`](validate.md#problem-codes).

Um candidato que não possa ser lido como um documento `<lift-ranges>` (por exemplo, um ficheiro de zero bytes resultante de uma exportação interrompida) é ignorado, em vez de provocar uma falha no carregamento, e é assinalado como [`unreadable-ranges-file`](validate.md#problem-codes). Carregar um diretamente com `RangesFile.load()` provoca, em vez disso, um erro.

Passe `resolve_ranges=False` à função `load()` para ignorar a deteção de componentes associados.

## Meios de comunicação

```python
for ref in lex.media_refs():        # todos os <media> e <illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.check_media()                   # referências que não são resolvidas corretamente
```

A resolução segue o esquema convencional: um href relativo é verificado tal como indicado e na pasta `audio/` (para ficheiros de pronúncia) ou `pictures/` (para ilustrações). As barras invertidas são tratadas como barras, uma vez que o WeSay escreve os links `pictures\photo with space.png`. Os links «href» remotos e absolutos não podem ser verificados e são ignorados.

A função `check_media()` apresenta apenas as referências que não foram resolvidas corretamente, uma `MediaResolution` por cada uma:

- `status="missing"`: nenhum ficheiro correspondeu ao href, independentemente da grafia.
- `status="mismatch"`: encontrou-se um, mas apenas com a conversão de maiúsculas e minúsculas ou em NFC; `found` indica o nome do ficheiro no disco.

É comunicada uma discrepância, apesar de o ficheiro ter sido encontrado. Um nome de acompanhante é correspondido de forma flexível, sem comentários, mas um href de ficheiro multimédia também é lido por qualquer serviço que forneça a pasta posteriormente, e um servidor que distinga maiúsculas de minúsculas não encontrará o ficheiro. A validação indica o mesmo caso que [`media-href-mismatch`](validate.md#problem-codes).

## Outros conteúdos da pasta

Uma pasta LIFT contém frequentemente ficheiros que o sil-lift não modela, tais como o sistema de escrita LDML na pasta `WritingSystems/` ou os ficheiros de consentimento dos oradores do The Combine na pasta `consent/`. As funções `load()` e `save()` não alteram estes ficheiros, e [`Lexicon.save_zip()`](lift-export-interop.md) transfere-os tal como estão ao compactar a pasta.
