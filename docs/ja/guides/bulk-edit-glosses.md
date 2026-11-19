# 実践例：注釈の一括編集

よくあるメンテナンス作業：辞書内のすべての英語用語について、ファイル内の他の部分を一切変更することなく、綴りを統一すること（英国式→米国式、またはその逆）。ここでは、読み込み、編集、検証、保存を行う1つのスクリプトの手順を解説します。これにより、編集APIとフィデリティ保証が連携して機能する様子を確認できます。

## 脚本

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)

edited_glosses = 0

for entry in lex.entries:
    for sense in entry.all_senses():
        for gloss in sense.glosses:
            if gloss.lang != "en":
                continue
            old = str(gloss.text)
            new = old.replace("colour", "color")
            if new != old:
                gloss.text = sil_lift.Text([new])
                edited_glosses += 1

changed = lex.changed_entries()

errors = [p for p in lex.iter_problems() if p.level == "error"]
if errors:
    for problem in errors:
        print(problem)
    sys.exit(f"aborting: {len(errors)} validation error(s), nothing saved")

lex.save()
print(f"edited {edited_glosses} gloss(es) across {len(changed)} entry(ies)")
```

いくつか注目すべき点があります：

- `entry.all_senses()` は、すべての意味 _および下位の意味_ を、ドキュメント順に深さ優先で返します。
  - `entry.senses` には最上位レベルのみが格納されているため、これを順に処理する一括編集では、サブセンスの下にネストされた語義は何も表示されずにスキップされてしまいます。
- `gloss.text` は単なる文字列ではなく `Text` です。`str(gloss.text)` は照合のためにこれを平坦化し、置換結果は文字列そのものを変更するのではなく、`sil_lift.Text([new])` を使って書き戻されます。
- `lex.changed_entries()` は、読み込まれたファイルと異なるエントリを報告します。エントリのダイジェストはそのサブツリー全体を網羅しているため、ネストされたサブセンスを編集すると、それを含むエントリが報告されますが、フィールドに既存の値を割り当てる場合は報告されません。
- `changed_entries()` はエントリの内容のみを対象としているため、これはカウントであり、書き込み保護機能ではありません。何も変更しない保存をスキップするには、`lex.changes()` を使用してください。詳しくは [保存](read-edit-write.md#saving) を参照してください。
- メモリ内での検証（`lex.iter_problems()`）では、まず編集後の状態をシリアル化するため、ディスクへの書き込みが行われる前に、編集内容が正しく反映されます。 `"error"` レベルの `Problem` が発生した場合は処理を中止します（警告については呼び出し側が判断することになります）。これにより、不正な編集内容が `save()` に到達することはありません。
- `lex.save()` は、このスクリプトによって変更されたエントリのみに新しい `dateModified` を付与し、空白だった `dateCreated` を埋めます。これがなければ、このスクリプトによって書き換えられた語彙集は、FieldWorks や The Combine の LIFT インポート機能にとっては変更されていないように見えてしまいます。これらはいずれも、その属性から何を更新するかを決定する仕組みになっており、編集の深さにかかわらず、`<entry>` を付加するのは、編集されたサブセンスの解説を含むエントリのみであり、センスそのものではありません。

この方法で触れてみる価値があるのは、グロスだけではありません。この `Multitext` マッピング領域は、定義や、エントリや意味に含まれるその他のすべての多言語フィールドにも同様に適用されます：

```python
sense.definition["en"] = "物体の色"
```

## 実行する

「colour」と記載された語義説明と、その下位意味の語義説明の両方が含まれる小規模な語彙リストに対して照合を行う：

```
1件のエントリに含まれる2つの用語を編集しました
```

## 忠実度の見返り

この保証は「エントリ」単位で適用されます。モデルが変更されていないエントリは、読み込まれたときと**バイト単位で同一**な状態で返され、実際に変更を加えたエントリのみが再シリアル化されます。上記の実行では、1つのエントリの注釈が編集されましたが、ファイル内のその他のエントリはすべて、バイト単位でそのままの状態で保持されました。（粒度に注意してください：エントリの任意の部分を編集すると、変更されていない同義語を含め、そのエントリ全体が再シリアライズされます。）したがって、5万項目の辞書にある1つの用語を編集しても、再フォーマットされたファイルが生成されるのではなく、1つの項目に影響する差分が生成されるだけである。契約の詳細については、[フィデリティの保証](../fidelity.md)をご覧ください。
