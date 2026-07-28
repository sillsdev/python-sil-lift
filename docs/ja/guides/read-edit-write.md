# 読む、編集する、書く

## 読み込み中

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` は、スキーマに準拠していない実世界のファイルを含め、形式が正しい LIFT **0.13** ドキュメントであればどれでも受け付けます。 モデルで定義されていないもの（未知の要素や属性、コメントなど）は、各ノードの不透明な `extra` バケットにロスレスで格納されます。 その他の LIFT バージョンでは、そのバージョン名を指定した `LiftParseError` が発生します。

## モデル

LIFTの各要素は、型付きデータクラスです。具体的には、`Entry`、`Sense`、`Example`、`Pronunciation`、`Variant`、`Relation`、`Etymology`、`Reversal`などがあります。 多言語テキストは `Multitext` であり、言語コードから `Text` へのマッピングのように動作します：

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # "abat"
entry.lexical_unit["en"] = "grove"      # プレーン文字列は型変換される
"en" in entry.citation                  # False
```

`Text` は、`str` および `Span` のフラグメントからなる順序付きリストとして構成されています。これは、`<text>` にネストされた `<span>` マークアップが含まれる可能性があるためです。 `str(text)` はプレーンテキストに変換されますが、フラグメントは往復処理のためにマークアップを維持します。

LIFT では、グロスは _Form 型_ です（各 `<gloss>` は独自の言語を持ちます）。したがって、センスには `glosses: list[Form]` と、ヘルパー関数が定義されています：

```python
sense = entry.senses[0]
sense.gloss("en")                       # Text | None
entry.gloss_langs()                     # {"en", "id"}
```

## 保存

```python
lex.save()                # 読み込まれた場所に戻す
lex.save("elsewhere.lift")
```

変更を加えなかったエントリは、**バイト単位で同一**な状態で書き戻されます。まったく変更を加えなかったドキュメントは、最初のバイトから最後のバイトまでバイト単位で同一です。 契約の詳細については、[フィデリティの保証](../fidelity.md)をご覧ください。

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
