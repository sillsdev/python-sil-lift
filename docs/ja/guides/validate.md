# 検証

検証は常に明示的に行われます。読み込みや保存の際、暗黙的に検証が行われることはありません。

```python
import sil_lift

# 網羅的：Problem（スキーマ層＋セマンティック層）の遅延ストリーム。
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # エラー [dangling-ref] dictionary.lift:88 (entry apu): ref 'nope' matches ...

# フェイルファースト：最初のエラーレベルの問題で LiftValidationError を発生させます。
sil_lift.validate_file("dictionary.lift")

# メモリ内状態（最初にシリアライズされる — 大規模な辞書では、ドキュメントに記載されているようにコストがかかる）：
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

各 `Problem` には、`level`（`"error"`/`"warning"`）、一意の `code`、`message`、および `file`、`entry_id`、`guid`、`line` というアドレス情報が含まれています。

## レイヤー

1. **RELAX NG** を、LIFT 0.13 の文法（lift-standard からベンダー提供されているもの）に対して適用します。
2. **Rangesスキーマ** — このプロジェクトの `lift-ranges-0.13.rng` — は、追跡対象のすべての `.lift-ranges` コンパニオンに対して適用されます。
3. **文法では表現できないセマンティックチェック**：`duplicate-guid`、`dangling-ref`、`range-parent`、`undefined-range-value`、`duplicate-form-lang`、`missing-media`。

## 実環境におけるFieldWorks（FLEx）の出力結果

FieldWorksは、厳格なツールによって拒否されるようなコンテンツを体系的に生成してしまう。 実際の辞書が有用に検証されるよう、sil-liftの方針は以下の通りです：

- `file://C:/...` という href（無効な URI）は、スキーマエラーではなく**警告**（`uri-not-rfc`）として報告されます。C# バリデータはこれらを拒否したことはありません。
- 法的に交互に配置された子要素（ある意味では `field, note, field, note` など）にはフラグが付けられず、これにより libxml2 における誤検知を回避しています。
- 範囲値は、UnicodeのNFC正規化に基づいて比較されます。FLExは、同じエクスポート内で`.lift`をNFCで記述しますが、`.lift-ranges`はNFDで記述します。
- `range-element` 内の FLEx の `trait`/`field` 拡張は、**報告される**（range スキーマに対するスキーマエラーとして）：これらは紛れもない仕様からの逸脱である。
