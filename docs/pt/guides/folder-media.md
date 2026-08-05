# A pasta LIFT: gamas e suportes

Um léxico LIFT é normalmente uma _pasta_: o ficheiro `.lift`, um ou mais ficheiros complementares `.lift-ranges` e os ficheiros multimédia nas pastas `audio/` e `pictures/`.

## Intervalos

```python
lex = sil_lift.load("dictionary.lift")      # companheiros rastreados automaticamente

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # vista {id: Range} combinada
lex.all_ranges()["grammatical-info"].elements
```

A descoberta de ficheiros associados lida com o mundo real: é utilizado um `range/@href` que aponta para um ficheiro existente; Os hrefs absolutos «file://C:/...» do FieldWorks que não têm referência recuam para o nome base do href junto ao «.lift»; e o irmão convencional «<name>.lift-ranges» é selecionado mesmo quando nada o referencia.

A função `lex.save()` grava o ficheiro `.lift` e todas as funções complementares monitorizadas em conjunto. As alterações feitas num `RangesFile` são guardadas no _seu_ ficheiro; os intervalos que não foram alterados mantêm os seus bytes exatos. Utilização autónoma:

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

Passe `resolve_ranges=False` à função `load()` para ignorar a deteção de componentes associados.

## Meios de comunicação

```python
for ref in lex.media_refs():        # todos os <media> e <illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.missing_media()                 # referências cujos ficheiros não existem
```

A resolução segue o esquema convencional: um link «href» relativo é verificado tal como fornecido (barras invertidas normalizadas — o WeSay escreve «pictures\photo with space.png») e na pasta «audio/» (para ficheiros de pronúncia) ou «pictures/» (para ilustrações). Os links «href» remotos/absolutos não podem ser verificados e são ignorados.

## Outros conteúdos da pasta

Uma pasta LIFT contém frequentemente ficheiros que o sil-lift não modela — o sistema de escrita LDML em `WritingSystems/`, os ficheiros de áudio/imagem relativos ao consentimento dos oradores do Combine em `consent/`, e outros semelhantes; As funções `load()`/`save()` não alteram estes ficheiros, e [`Lexicon.save_zip()`](lift-export-interop.md) transfere-os na íntegra ao empacotar a pasta.
