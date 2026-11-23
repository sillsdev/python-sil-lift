# 読む、編集する、書く

## 読み込み中

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` accepts any well-formed LIFT **0.13** document, including schema-invalid real-world files. モデルで定義されていないもの（未知の要素や属性、コメントなど）は、各ノードの不透明な `extra` フィールドに LIFT 残余として、情報を失うことなく保持されます。その他の LIFT バージョンでは、そのバージョン名を指定した `LiftParseError` が発生します。

## モデル

Every LIFT element is a typed dataclass: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, and so on.

### Multilingual text

多言語テキストは `Multitext` であり、これは言語コードから `Text` への `Mapping` です：

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # plain strings are coerced
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` is structured (an ordered list of `str` and `Span` fragments) because `<text>` can contain nested `<span>` markup. `str(text)` はプレーンテキストに変換されますが、フラグメントは往復処理のためにマークアップを維持します。

The mapping shows one value per language. Underneath, `forms` holds every `<form>` in file order. A schema-valid document has at most one form per language, but real files sometimes repeat one.

Because the mapping is keyed by language, `len()` counts languages rather than forms, and the `keys()`, `values()` and `items()` views list each language once. Both mutators also act on the whole language: `del entry.lexical_unit["en"]` removes every English form, and assigning to `"en"` leaves exactly one.

For a repeated language, `entry.lexical_unit["en"]`, `get()`, `values()` and `items()` all answer with its first form, and [`validate`](validate.md#problem-codes) reports `duplicate-form-lang` until you assign to that language.

A form carrying no `lang` at all cannot be created through the mapping. It is reported as `form-missing-lang`, and is dropped when its node re-serializes.

### Senses and glosses

LIFT では、グロスは _form の形_ をとります（各 `<gloss>` は独自の言語を持ちます）。したがって、センスには `glosses: list[Form]` と、以下のヘルパー関数が用意されています：

```python
sense = entry.senses[0]       # top level only
sense.gloss("en")             # Text | None
entry.all_senses()            # every sense and subsense, document order
entry.gloss_langs()           # {"en", "id"}, subsenses included
```

項目全体に関する質問（語義の数を数えたり、使用言語をまとめたり、メディアを探したりすることなど）がある場合は、いつでも `all_senses()` を利用してください。 `entry.senses` は最上位レベルを示しますが、これはネスト構造そのものが重要である場合にのみ必要な情報です。

## 保存

```python
lex.save()                    # back to where it was loaded from
lex.save("elsewhere.lift")
```

変更を加えなかったエントリは、**バイト単位で同一**な状態で書き戻されます。まったく変更を加えなかったドキュメントは、最初のバイトから最後のバイトまでバイト単位で同一です。契約の詳細については、[フィデリティの保証](../fidelity.md)をご覧ください。

### タイムスタンプ

変更を加えたエントリは、新しい `dateModified`（および、もし `dateCreated` が存在しなかった場合はそれ）が設定された状態で出力されるため、編集内容は読み込まれた日付の下には反映されません。 Tools that merge LIFT decide what changed from that attribute. Two arguments adjust the stamping:

- `lex.save(stamp=False)` writes the dates the model holds and nothing more.
- `lex.save(when=...)` pins the moment instead of reading the clock.

その他のルールについては、[生成されたタイムスタンプ](../fidelity.md#generated-timestamps)を参照してください。

### Skipping a save that changes nothing

何も変更しない保存をスキップするには、`lex.changes()` を使ってその保存をガードします：

```python
if lex.changes():
    lex.save()
```

`save()` がソースバイトを再現する場合にのみ `False` を返します。これには、エントリ、ヘッダー、ルート要素、およびすべての `.lift-ranges` コンパニオンが含まれます。 Skipping the write leaves the file's modification time alone and avoids a spurious diff.

The check is cheap. 最初の差異で停止するため、編集済みの辞書を使用すれば、コストはほぼかかりません。変更のない辞書は、変更がないことを証明するために完全にシリアライズする必要がありますが、それでも、スキップされる保存処理よりもコストは低くなります。

これは保存先ではなく内容を比較するため、その場での保存のみを保護してください。 `lex.save("elsewhere.lift")` writes the document and its companions to the new path even when `changes()` is `False`, so guarding it would skip that copy.

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
