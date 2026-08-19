# 準拠したLIFTの生成

このガイドは、LIFT _エクスポーター_ を開発するすべての方を対象としています。これは、任意の言語で記述された、他のアプリケーションのデータモデルを LIFT 0.13 形式に変換するコードのことです。 `sil-lift` は、その作業において 2 つの役割を果たします。1 つは、出力がスキーマに準拠しているかを確認する適合性チェック機能と、スキーマでは表現できない意味論のチェック機能であり、もう 1 つは、出力が従わなければならない形状やテキストに関する規則の参照基準としての役割です。

LIFTの記述は、その解析よりもはるかに簡単です。エクスポート機能は、自身のモデルが生成する構文のサブセットのみを出力するため、仕様全体のオプション性に対処する必要が一切ないからです。 難しいのは細部、つまり `.lift-ranges` コンパニオン、文字体系ごとのテキスト、安定した ID、XML エスケープなどですが、これらはまさに以下のチェックで検出される項目です。

## ZIP形式のパッケージ

LIFTは通常、単一の`.zip`ファイルとして移動されます（FieldWorksとThe Combineはどちらもこの形式でインポートおよびエクスポートを行います）。そのため、`sil-lift`は、エコシステムで使用されるいずれのレイアウト（アーカイブのルートにファイルが配置されている場合、またはトップレベルのフォルダの下にネストされている場合）においても、zip形式のパッケージを直接読み書きします。

- **解説：** `sil_lift.load("package.zip")` は、一時ディレクトリに解凍を行い、単一の `.lift` ファイルを検出して読み込みます（コンパニオンやメディアは通常通り解決されます）。
  - `validate`、`stats`、`check-media`、および`export`の各CLIコマンドも`.zip`形式のパスを指定できるため、以下のゲートはパッケージをそのままの状態で実行します。
  - `stats` および `export` ストリームから、パッケージ全体ではなく `.lift` のみを抽出します。これにより、メディアデータが大量に含まれるパッケージでも処理負荷を抑えることができ、抽出制限は `.lift` に対してのみ適用され、それ以外の部分には適用されません。
  - 抽出の上限は10 GiBおよび100,000個のメンバーです。いずれかの制限を超えるパッケージは、メンバーのパスが抽出ディレクトリの範囲外にある場合と同様に、`LiftParseError`が発生して拒否されます。
- **記述例：** `Lexicon.save_zip("out.zip", wrap_folder="MyDict")` とすると、`.lift`、その `.lift-ranges`、およびソースフォルダ内のその他のすべてのファイル（media、`WritingSystems/`、`consent/` など）がまとめてパッケージ化されます。 zipファイルにまとめる。
  - `wrap_folder` のデフォルト値は、zip ファイル名と同じ名前の最上位フォルダです（FieldWorks/Combine のインポート規約に従います）。フラットなアーカイブにする場合は、`False` を指定してください。

`.lift` および `.lift-ranges` は、パッケージ内ではバイト単位の忠実性を維持しますが、zip コンテナ自体はバイト単位で再現可能ではありません。

## 出力を適合性ゲートとして検証する

生成された `.lift` ファイルを `sil-lift validate` の対象として指定します。 RELAX NG（`.lift` およびそのコンパニオンである `.lift-ranges` の両方に対して）を実行するほか、文法では表現できないセマンティックチェックも行います： ぶら下がった `relation`/`variant` の参照、重複する GUID、範囲要素の親の整合性、範囲内で定義されていない特性および文法情報の値、およびコンパニオンに解決されないヘッダー `range/@href` の参照などです。

CIでは、何か問題が発生した場合は失敗とし、機械可読な結果を出力する：

```
sil-lift validate export.lift --strict --no-check-media --format json
```

- `--strict` を指定すると、エラーだけでなく警告も実行の失敗原因となります。
- `--no-check-media` を指定すると、ファイルシステムのメディア存在確認がスキップされます。CIにおいて、オーディオファイルや写真ファイルが `.lift` ファイルと同じフォルダにない場合、この確認で検出される `missing-media` の結果はノイズとなるためです。
- `--format json` を指定すると、人間が読みやすいテキストの代わりに単一の JSON オブジェクト (`{"problems": [...], "summary": {...}}`) が出力されます。その終了コードとスキーマは、SemVer に準拠したサポート対象のインターフェースとなっています（[コマンドラインガイド](cli.md)を参照してください）。
- `--require-ids` オプションを指定すると、`guid` が欠落しているエントリや `id` が欠落しているエントリに対して追加でエラーが発生します。これは、後で再インポートを行う際に、重複を避けるために更新のみを行う必要がある場合に役立ちます。

ソースモデルに対して `stats --format json` を使用してカウントを確認することで、サイレントデータ損失（フラットな CSV エクスポートでデータが失われる原因となる障害モード）を防ぐことができます：

```
sil-lift の統計データのエクスポート export.lift --format json
```

このレポートでは、`entries`、`senses`、`examples`、`media_refs`、`languages`、および名称ごとの`traits`の件数が報告されます。

### Pythonツールチェーンを使用せずにgateを実行する

TypeScript または C# プロジェクトの CI では、Python をインストールしなくても、バンドルされている GitHub Action を通じて同じチェックを実行できます：

```yaml
- uses: sillsdev/python-sil-lift@v0.1.0
  with:
    path: export.lift
    strict: "true"
    no-check-media: "true"
    format: json
```

あるいは、リポジトリの `Dockerfile` からビルドされたコンテナイメージ：

```
docker build -t sil-lift .
docker run --rm -v "$PWD:/work" -w /work sil-lift validate export.lift --strict
```

## `.lift-ranges` コンパニオン

統制語彙（品詞、意味領域、およびその他の特性キー付き値セット）は、`<header>` から参照される同階層の `.lift-ranges` ファイルに格納されています：

```xml
<header>
  <ranges>
    <range id="grammatical-info" href="mydict.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="mydict.lift-ranges"/>
  </ranges>
</header>
```

このガイドブックには、各シリーズの完全な定義が掲載されています。 値は `<range-element>` です。`parent` は階層を構築します。`label` / `abbrev` / `description` はマルチテキストです：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
  <range id="grammatical-info">
    <range-element id="Noun">
      <label><form lang="en"><text>名詞</text></form></label>
      <abbrev><form lang="en"><text>n</text></form></abbrev>
    </range-element>
  </range>
  <range id="semantic-domain-ddp4">
    <range-element id="1.6.1.2">
      <label><form lang="en"><text>鳥</text></form></label>
    </range-element>
  </range>
</lift-ranges>
```

エントリは、ID によって値を参照します。例えば、品詞は `<grammatical-info value="Noun"/>`、意味領域は `<trait name="semantic-domain-ddp4" value="1.6.1.2"/>` となります。 `sil-lift validate` は、値がその範囲内で定義されていない場合に警告（`undefined-range-value`）を出し、`parent` が兄弟要素の ID ではない場合にエラー（`range-parent`）を返します。したがって、データで実際に使用されている範囲を指定してください。 これらの比較はNFC正規化に基づいているため、IDと、それを参照する値または`parent`との間で、Unicode正規化が異なる場合があります。この違いはエラーではなく`normalization-mismatch`という警告として扱われますが、可能であれば一貫した正規化形式で記述してください。生の文字列を比較する側では、こうした参照は解決されないからです。 「範囲とメディア」も参照してください（folder-media.md）。

Pythonでエクスポートを構築する場合、`Lexicon.add_ranges_file()`、`RangesFile.add_range()`、および`Range.add_element()`がコンパニオンを構築し、ヘッダー参照を自動的に追加してくれます。 `open_writer(..., ranges=...)` は、ストリーミングパス上でも同様の処理を行います。

## テキストおよびマルチテキスト

LIFT におけるすべての自然言語文字列は _マルチテキスト_ です。つまり、各文字体系ごとに 1 つの `<form>` があり、それぞれが `<text>` を囲んでいます：

```xml
<lexical-unit>
  <form lang="seh"><text>カンガ</text></form>
  <form lang="pt"><text>鶏</text></form>
</lexical-unit>
```

言語コードをキーとする文字列のモデル（`MultiString`、`Record<code, string>`、`dict[str, str]`）は、これと一対一で対応します。つまり、キー1つにつき1つのエントリが、1つの `<form lang="… ">` になります。 1つのマルチテキスト内で、1つの言語につき最大1つのフォームまでしか許可されません。それ以外の場合、`sil-lift`は`duplicate-form-lang`という警告を出します。

XMLのエスケープ処理こそが、唯一、正確さが極めて重要となる部分です。 要素のテキスト内では、`&`、`<`, and `>` はエスケープする必要があります（`&amp;`、`&lt;`、`&gt;`）。属性値内では、引用符も同様にエスケープする必要があります。 `sil-lift`の作者はまさにこれらのルールを適用しており、`<text>`内の空白を一切変更しません。そこではインデントを追加しないのは、そうすることで字句データが破損してしまうためです。 その出力を再現したい場合は、本格的なXMLシリアライザのエスケープ処理を再利用し（`&`を忘れるような手作りの置換処理は避ける）、`<text>` のコンテンツはソースにあるまま、バイト単位でそのまま残してください。
