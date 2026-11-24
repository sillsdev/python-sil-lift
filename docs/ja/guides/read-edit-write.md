# 読む、編集する、書く

## 読み込み中

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` は、スキーマに準拠していない実世界のファイルを含め、形式が正しい LIFT **0.13** ドキュメントであればどれでも受け付けます。モデルで定義されていないもの（未知の要素や属性、コメントなど）は、各ノードの不透明な `extra` フィールドに LIFT 残余として、情報を失うことなく保持されます。その他の LIFT バージョンでは、そのバージョン名を指定した `LiftParseError` が発生します。

## モデル

LIFTの各要素は、型付きデータクラスです。具体的には、`Entry`、`Sense`、`Example`、`Pronunciation`、`Variant`、`Relation`、`Etymology`、`Reversal`などがあります。

### 多言語テキスト

多言語テキストは `Multitext` であり、これは言語コードから `Text` への `Mapping` です：

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # プレーン文字列は強制変換される
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` は構造化されています（`str` および `Span` フラグメントの順序付きリスト）。これは、`<text>` にネストされた `<span>` マークアップが含まれる可能性があるためです。 `str(text)` はプレーンテキストに変換されますが、フラグメントは往復処理のためにマークアップを維持します。

このマッピングでは、言語ごとに1つの値が表示されています。その下では、`forms` にはファイル順にすべての `<form>` が格納されています。スキーマに準拠したドキュメントには、言語ごとに最大1つのフォームしか含まれませんが、実際のファイルでは同じフォームが重複して含まれていることがあります。

マッピングは言語をキーとしているため、`len()` は形式ではなく言語の数を数え、`keys()`、`values()`、`items()` ビューでは各言語が 1 回ずつリストされます。どちらのミューテーターも言語全体に対して作用します。`del entry.lexical_unit["en"]` はすべての英語の形態を削除し、`"en"` に代入すると、ちょうど 1 つだけが残ります。

反復言語の場合、`entry.lexical_unit["en"]`、`get()`、`values()`、および`items()`はすべてその最初の形式を返します。また、[`validate`](validate.md#problem-codes)は、その言語に値を割り当てるまで`duplicate-form-lang`を報告します。

`lang` がまったく指定されていないフォームは、マッピングを通じて作成することはできません。これは `form-missing-lang` として報告され、そのノードが再シリアライズされると削除されます。

### 語義と注釈

LIFT では、グロスは _form の形_ をとります（各 `<gloss>` は独自の言語を持ちます）。したがって、センスには `glosses: list[Form]` と、以下のヘルパー関数が用意されています：

```python
sense = entry.senses[0]       # 最上位の意味のみ
sense.gloss("en")             # Text | None
entry.all_senses()            # すべての意味とサブ意味（ドキュメント順）
entry.gloss_langs()           # {"en", "id"}（サブ意味を含む）
```

項目全体に関する質問（語義の数を数えたり、使用言語をまとめたり、メディアを探したりすることなど）がある場合は、いつでも `all_senses()` を利用してください。 `entry.senses` は最上位レベルを示しますが、これはネスト構造そのものが重要である場合にのみ必要な情報です。

## 保存

```python
lex.save()                    # 読み込まれた場所に戻す
lex.save("elsewhere.lift")
```

変更を加えなかったエントリは、**バイト単位で同一**な状態で書き戻されます。まったく変更を加えなかったドキュメントは、最初のバイトから最後のバイトまでバイト単位で同一です。契約の詳細については、[フィデリティの保証](../fidelity.md)をご覧ください。

### タイムスタンプ

変更を加えたエントリは、新しい `dateModified`（および、もし `dateCreated` が存在しなかった場合はそれ）が設定された状態で出力されるため、編集内容は読み込まれた日付の下には反映されません。 LIFTをマージするツールは、その属性において何が変更されたかを判断します。スタンピングを調整するには、2つの引数を使用します：

- `lex.save(stamp=False)` は、モデルが保持している日付のみを書き込み、それ以外は書き込みません。
- `lex.save(when=...)` は、時計を読み取るのではなく、その瞬間を固定します。

その他のルールについては、[生成されたタイムスタンプ](../fidelity.md#generated-timestamps)を参照してください。

### 何も変わらないセーブをスキップする

何も変更しない保存をスキップするには、`lex.changes()` を使ってその保存をガードします：

```python
if lex.changes():
    lex.save()
```

`save()` がソースバイトを再現する場合にのみ `False` を返します。これには、エントリ、ヘッダー、ルート要素、およびすべての `.lift-ranges` コンパニオンが含まれます。書き込みをスキップすると、ファイルの最終更新時刻は変更されず、誤った差分が表示されるのを防ぐことができます。

その小切手は額面が低い。最初の差異で停止するため、編集済みの辞書を使用すれば、コストはほぼかかりません。変更のない辞書は、変更がないことを証明するために完全にシリアライズする必要がありますが、それでも、スキップされる保存処理よりもコストは低くなります。

これは保存先ではなく内容を比較するため、その場での保存のみを保護してください。 `lex.save("elsewhere.lift")` は、`changes()` が `False` の場合でも、ドキュメントとその関連ファイルを新しいパスに書き込みます。したがって、これを条件分岐で制御すれば、そのコピー処理をスキップできます。

## ゼロから構築する

```python
lex = sil_lift.Lexicon(producer="my-script 1.0")
entry = sil_lift.Entry(id="hello", guid="...")
entry.lexical_unit["en"] = "hello"
sense = sil_lift.Sense()
sense.glosses.append(sil_lift.Form("fr", sil_lift.Text(["bonjour"])))
entry.senses.append(sense)
lex.entries.append(entry)
lex.save("new.lift")
```

## 規範的順序付け

```python
lex.sort()      # エントリを (guid, id) の順に並べ替え； ID/タグごとの範囲/フィールド定義
lex.save()      # 変更されていないエントリは、新しい順序のまま正確なバイトデータを保持します

sil_lift.canonicalize("in.lift", "out.lift")   # 完全に再シリアル化され、差分比較の準備が整いました
```

関連項目：[実践例：用語の一括編集](bulk-edit-glosses.md)。
