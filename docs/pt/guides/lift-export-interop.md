# Produção de LIFT em conformidade

Este guia destina-se a quem estiver a desenvolver um _exportador_ LIFT — código em qualquer linguagem de programação que converta o modelo de dados de outra aplicação para o formato LIFT 0.13. O `sil-lift` desempenha duas funções nesse trabalho: uma verificação de conformidade que compara a saída com o esquema e com a semântica que o esquema não consegue expressar, e uma referência para as formas e regras de texto que a saída deve seguir.

Escrever LIFT é muito mais fácil do que analisá-lo: um exportador apenas emite o subconjunto de construções que o seu próprio modelo produz e nunca se depara com todas as opções da especificação completa. A parte mais complicada são os detalhes — o complemento `.lift-ranges`, o texto específico para cada sistema de escrita, os identificadores estáveis e o escape de XML — e é precisamente isso que as verificações abaixo detetam.

## Pacotes compactados

O LIFT é normalmente transferido como um único ficheiro `.zip` — tanto o FieldWorks como o The Combine importam e exportam dessa forma — pelo que o `sil-lift` lê e grava pacotes compactados diretamente, independentemente do formato utilizado pelo ecossistema: os ficheiros na raiz do arquivo ou aninhados numa pasta de nível superior.

- **Nota:** `sil_lift.load("package.zip")` extrai o conteúdo para um diretório temporário, localiza o único ficheiro `.lift` e carrega-o (os ficheiros complementares e os ficheiros multimédia são resolvidos como habitualmente).
  - Os comandos da CLI `validate`, `stats`, `check-media` e `export` também aceitam um caminho `.zip`, pelo que o gate abaixo é executado diretamente sobre um pacote tal como está.
  - `stats` e `export`, e extrair apenas o `.lift` em vez de todo o pacote — para que continuem a ser eficientes num pacote com muitos ficheiros multimédia, e para que o limite de extração se aplique apenas ao `.lift`, em vez de a tudo o que o rodeia.
  - A extração está limitada a 10 GiB e 100 000 elementos; um pacote que exceda qualquer um desses limites é rejeitado com um erro `LiftParseError`, tal como acontece com um pacote cujos caminhos dos elementos estejam fora do diretório de extração.
- **Escreva:** `Lexicon.save_zip("out.zip", wrap_folder="MyDict")` compacta o ficheiro `.lift`, os seus `.lift-ranges` e todos os outros ficheiros da pasta de origem (multimédia, `WritingSystems/`, `consent/`, ...) num ficheiro zip.
  - O `wrap_folder` tem, por predefinição, uma pasta de nível superior com o nome do ficheiro zip (conforme a convenção de importação do FieldWorks/Combine); passe `False` para obter um arquivo simples.

Os ficheiros `.lift` e `.lift-ranges` mantêm a sua fidelidade ao nível do byte dentro do pacote; o próprio ficheiro zip não é reproduzível ao nível do byte.

## Validar o resultado como um critério de conformidade

Execute o comando `sil-lift validate` no ficheiro `.lift` gerado. Executa o RELAX NG (tanto no `.lift` como no seu complemento `.lift-ranges`) e realiza verificações semânticas que a gramática não consegue expressar: referências pendentes a `relation`/`variant`, GUIDs duplicados, integridade do elemento pai do intervalo, valores de características e de informação gramatical não definidos no respetivo intervalo e referências `range/@href` no cabeçalho que não remetem para nenhum elemento correspondente.

No caso da CI, em caso de falha em qualquer etapa, gerar resultados legíveis por máquina:

```
sil-lift validate export.lift --strict --no-check-media --format json
```

- A opção `--strict` faz com que os avisos (e não apenas os erros) provoquem o falhanço da execução.
- `--no-check-media` ignora a verificação da presença de ficheiros multimédia no sistema de ficheiros, cujos resultados de `missing-media` são irrelevantes quando os ficheiros de áudio/fotografias não se encontram na mesma pasta que o ficheiro `.lift` na CI.
- `--format json` apresenta um único objeto JSON (`{"problems": [...], "summary": {...}}`) em vez de texto legível; os seus códigos de saída e esquema constituem uma interface suportada e abrangida pela SemVer (ver [o guia da linha de comandos](cli.md)).
- `--require-ids` também apresenta erros em entradas que não tenham um `guid` ou que não tenham um `id` — útil quando uma reimportação posterior tiver de atualizar, em vez de duplicar.

Proteja-se contra a perda silenciosa de dados (o modo de falha que torna a exportação em CSV simples propensa a perdas) verificando as contagens com o comando `stats --format json` no seu modelo de origem:

```
sil-lift stats export.lift --format json
```

Apresenta as contagens de «entradas», «significados», «exemplos», «referências multimédia», «idiomas» e «características» por nome.

### Executar o gate sem o conjunto de ferramentas do Python

A integração contínua (CI) de um projeto em TypeScript ou C# pode executar a mesma verificação sem instalar o Python, através da GitHub Action incluída:

```yaml
- utiliza: sillsdev/python-sil-lift@v0.1.0
  com:
    caminho: export.lift
    rigoroso: "true"
    sem verificação de mídia: "true"
    formato: json
```

ou a imagem do contentor, criada a partir do ficheiro `Dockerfile` do repositório:

```
docker build -t sil-lift .
docker run --rm -v "$PWD:/work" -w /work sil-lift validate export.lift --strict
```

## O componente complementar `.lift-ranges`

Os vocabulários controlados — classes gramaticais, domínios semânticos e qualquer outro conjunto de valores baseado em características — encontram-se num ficheiro `.lift-ranges` paralelo, referenciado a partir do ficheiro `<header>`:

```xml
<header>
  <ranges>
    <range id="grammatical-info" href="mydict.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="mydict.lift-ranges"/>
  </ranges>
</header>
```

O guia contém a definição completa de cada gama. Os valores são `<range-element>`s; `parent` cria uma hierarquia; `label` / `abbrev` / `description` são multitexts:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
  <range id="grammatical-info">
    <range-element id="Noun">
      <label><form lang="en"><text>substantivo</text></form></label>
      <abbrev><form lang="en"><text>n</text></form></abbrev>
    </range-element>
  </range>
  <range id="semantic-domain-ddp4">
    <range-element id="1.6.1.2">
      <label><form lang="en"><text>Pássaro</text></form></label>
    </range-element>
  </range>
</lift-ranges>
```

Uma entrada remete, então, para um valor através do seu identificador: a classe gramatical de um sentido é `<grammatical-info value="Noun"/>`, e um domínio semântico é `<trait name="semantic-domain-ddp4" value="1.6.1.2"/>`. O `sil-lift validate` emite um aviso (`undefined-range-value`) quando um valor não está definido no seu intervalo e um erro (`range-parent`) quando um `parent` não é um ID de elemento irmão — por isso, indique os intervalos que os seus dados utilizam efetivamente. Essas comparações são normalizadas segundo a NFC, pelo que um identificador e o valor ou o `parent` a que se refere podem apresentar diferenças na normalização Unicode — essa diferença constitui um aviso de `normalization-mismatch` e não um erro, mas, se possível, utilize uma normalização consistente: os consumidores que comparam cadeias de caracteres em bruto não irão resolver essas referências. Ver também [Intervalos e meios de comunicação](folder-media.md).

Se criar a exportação em Python, as funções `Lexicon.add_ranges_file()`, `RangesFile.add_range()` e `Range.add_element()` criam o objeto complementar e adicionam as referências do cabeçalho automaticamente; `open_writer(..., ranges=...)` faz o mesmo no caminho de streaming.

## Texto e multitexto

Cada sequência de caracteres de uma língua humana no LIFT é um _multitexto_: um `<form>` por sistema de escrita, cada um envolvendo um `<text>`:

```xml
<lexical-unit>
  <form lang="seh"><text>kanga</text></form>
  <form lang="pt"><text>galinha</text></form>
</lexical-unit>
```

Um modelo que indexa cadeias de caracteres pelo código do idioma (um `MultiString`, um `Record<code, string>`, um `dict[str, str]`) estabelece uma correspondência um-para-um com este: cada entrada por chave corresponde a um `<form lang="…">`. É permitida, no máximo, uma forma por língua num único multitexto — caso contrário, o `sil-lift` emite um aviso de `duplicate-form-lang`.

A codificação de escape em XML é a única parte em que a precisão é realmente fundamental. No texto dos elementos, os caracteres `&`, `<`, and `>` devem ser escapados (`&amp;`, `&lt;`, `&gt;`); nos valores dos atributos, o caractere de aspas também deve ser escapado. O autor do `sil-lift` aplica exatamente estas regras e nunca altera os espaços em branco dentro de `<text>` — não adiciona qualquer indentação nesse local, pois isso corromperia os dados lexicais. Se pretender obter o mesmo resultado, reutilize o processo de escape de um serializador XML verdadeiro (em vez de uma substituição feita manualmente que se esqueça do `&`) e mantenha o conteúdo de `<text>` byte a byte, tal como aparece na sua fonte.
