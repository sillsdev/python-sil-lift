# sil-lift

一个用于 [LIFT](https://github.com/sillsdev/lift-standard)（词典交换格式）0.13 的 Python 库：支持 LIFT 文件夹（`.lift` + `.lift-ranges` + 媒体引用）的无损读写、模式和语义验证以及规范排序，此外还提供了用于大型词典的流式处理 API。

**状态：预发布版，正在积极开发中。**

## 安装

摘自 [PyPI](https://pypi.org/project/sil-lift/)：

```
pip install sil-lift   # 安装库及 sil-lift 命令
```

需要 Python 3.11 及以上版本。唯一的运行时依赖项是 lxml。

## 30秒导览

加载词汇表，查找没有英语释义的夏威夷语词条，编辑释义，然后保存：

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # 也会追踪 .lift-ranges 关联项

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("haw") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # 或 lex.find(id="poʻo_a1b2")
entry.senses[0].definition["en"] = "头（解剖学）"

lex.save()   # 编辑后的条目被重新序列化并重新标记；其余部分字节内容完全相同
```
