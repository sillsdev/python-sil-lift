# 読む、編集する、書く

## 読み込み中

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` は、スキーマに準拠していない実世界のファイルを含め、形式が正しい LIFT **0.13** ドキュメントであればどれでも受け付けます。モデルで定義されていないもの（未知の要素や属性、コメントなど）は、各ノードの不透明な `extra` フィールドに LIFT 残余として、情報を失うことなく保持されます。その他の LIFT バージョンでは、そのバージョン名を指定した `LiftParseError` が発生します。

## モデル

LIFTの各要素は、型付きデータクラスです。具体的には、`Entry`、`Sense`、`Example`、`Pronunciation`、`Variant`、`Relation`、`Etymology`、`Reversal`などがあります。多言語テキストは `Multitext` であり、これは言語コードから `Text` への `Mapping` です：

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # "abat"
entry.lexical_unit["en"] = "grove"      # プレーン文字列は型変換される
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["seh", "en"]
```

`keys()`、`values()`、`items()` はビューであり、言語ごとに 1 つのキーが割り当てられ、`len()` はフォームの数ではなく言語の数を数えます。どちらのミューテータも、特定の語形ではなく言語全体に対して作用します。`del entry.lexical_unit["en"]` はすべての英語の語形を削除し、`"en"` に代入すると、ちょうど 1 つだけが残ります。

スキーマに準拠したドキュメントにはそれ以上の要素は含まれていませんが、実際のファイルでは言語が重複することがあります。 `forms` にはファイル順にすべてのフォームが格納されており、最初のフォームから回答を読み込み、[`validate`](validate.md#problem-codes) はその言語を割り当てるまで `duplicate-form-lang` を報告します。 `lang` がまったく指定されていないフォームは、マッピングを通じて作成することができず、`form-missing-lang` として報告され、そのノードが再シリアル化される際に破棄されます。

`Text` は、`str` および `Span` のフラグメントからなる順序付きリストとして構成されています。これは、`<text>` にネストされた `<span>` マークアップが含まれる可能性があるためです。 `str(text)` はプレーンテキストに変換されますが、フラグメントは往復処理のためにマークアップを維持します。

LIFT では、グロスは _form の形_ をとります（各 `<gloss>` は独自の言語を持ちます）。したがって、センスには `glosses: list[Form]` と、以下のヘルパー関数が用意されています：

```python
sense = entry.senses[0]                 # 最上位の意味のみ
sense.gloss("en")                       # Text | None
entry.all_senses()                      # すべての意味と下位の意味、文書順
entry.gloss_langs()                     # {"en", "id"}、下位の意味を含む
```

項目全体に関する質問（語義の数を数えたり、使用言語をまとめたり、メディアを探したりすることなど）がある場合は、いつでも `all_senses()` を利用してください。 `entry.senses` は最上位レベルを示しますが、これはネスト構造そのものが重要である場合にのみ必要な情報です。

## 保存

```python
lex.save()                # 読み込まれた場所に戻す
lex.save("elsewhere.lift")
```

変更を加えなかったエントリは、**バイト単位で同一**な状態で書き戻されます。まったく変更を加えなかったドキュメントは、最初のバイトから最後のバイトまでバイト単位で同一です。契約の詳細については、[フィデリティの保証](../fidelity.md)をご覧ください。

変更を加えたエントリは、新しい `dateModified` （および、もし `dateCreated` が存在しなかった場合はそれ）とともに送信されるため、編集内容は読み込まれた日付で送信されることはありません。LIFTをマージするツールが、その属性から何が変更されたかを判断します。 `lex.save(stamp=False)` は、モデルが保持している日付のみを書き込み、それ以外は書き込みません。一方、`lex.save(when=...)` は、時計の時刻を読み取るのではなく、その瞬間を固定します。その他のルールについては、[生成されたタイムスタンプ](../fidelity.md#generated-timestamps)を参照してください。

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
