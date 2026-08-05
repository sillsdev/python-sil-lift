# 実践例：注釈の一括編集

よくあるメンテナンス作業：辞書内のすべての英語用語について、ファイル内の他の部分を一切変更することなく、綴りを統一すること（英国式→米国式、またはその逆）。 ここでは、読み込み、編集、検証、保存を行う1つのスクリプトの手順を解説します。これにより、編集APIとフィデリティ保証が連携して機能する様子を確認できます。

## 脚本

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)


def iter_senses(senses):
    """すべての意味（サブセンスを含む）を再帰的にイテレートする。"""
    for sense in senses:
        yield sense
        yield from iter_senses(sense.subsenses)


edited_glosses = 0
touched_entries = set()

for entry in lex.entries:
    for sense in iter_senses(entry.senses):
        for gloss in sense.glosses:
            if gloss.lang != "en":
                continue
            old = str(gloss.text)
            new = old.replace("colour", "color")
            if new != old:
                gloss.text = sil_lift.Text([new])
                edited_glosses += 1
                touched_entries.add(entry.id)

errors = [p for p in lex.iter_problems() if p.level == "error"]
if errors:
    for problem in errors:
        print(problem)
    sys.exit(f"aborting: {len(errors)} validation error(s), nothing saved")

lex.save()
print(f"edited {edited_glosses} gloss(es) across {len(touched_entries)} entry(ies)")
```

いくつか注目すべき点があります：

- `Sense.subsenses` 自体は `list[Sense]` であるため、`iter_senses` はこのリストを再帰的に処理します。もし `entry.senses` のみを走査する一括編集を行った場合、サブセンスの下にネストされた語義は、何の警告もなくスキップされてしまいます。
- `gloss.text` は単なる文字列ではなく `Text` です。`str(gloss.text)` は照合のためにこれを平坦化し、置換結果は文字列そのものを変更するのではなく、`sil_lift.Text([new])` を使って書き戻されます。
- メモリ内での検証（`lex.iter_problems()`）では、まず編集後の状態をシリアル化するため、ディスクへの書き込みが行われる前に、編集内容が正しく反映されます。 `"error"` レベルの `Problem` が発生した場合は処理を中止します（警告は呼び出し側が判断できるよう残されます）。これにより、不正な編集内容が `save()` に到達することはありません。

この方法で触れてみる価値があるのは、グロスだけではありません。 この `Multitext` マッピング領域は、定義や、エントリや意味に含まれるその他のすべての多言語フィールドにも同様に適用されます：

```python
sense.definition["en"] = "物体の色"
```

## 実行する

「colour」と記載された語義説明と、その下位意味の語義説明の両方が含まれる小規模な語彙リストに対して照合を行う：

```
1件のエントリに含まれる2つの用語を編集しました
```

## 忠実度の見返り

この保証は「エントリ」単位で適用されます。モデルが変更されていないエントリは、読み込まれたときと**バイト単位で同一**な状態で返され、実際に変更を加えたエントリのみが再シリアル化されます。 上記の実行では、1つのエントリの注釈が編集されましたが、ファイル内のその他のエントリはすべて、バイト単位でそのままの状態で保持されました。 （粒度に注意してください：エントリの任意の部分を編集すると、変更されていない同義語を含め、そのエントリ全体が再シリアライズされます。） したがって、5万項目の辞書にある1つの用語を編集しても、再フォーマットされたファイルが生成されるのではなく、1つの項目に影響する差分が生成されるだけである。 契約の詳細については、[フィデリティの保証](../fidelity.md)をご覧ください。
