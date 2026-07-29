# sil-lift

一个用于 [LIFT](https://github.com/sillsdev/lift-standard) 的 Python 库 (词典交换格式) 0.13：支持 LIFT 文件夹（`.lift` + `.lift-ranges` + 媒体引用）的无损读写、模式和语义验证以及规范排序——并为大型词典提供了流式 API。

**状态：预发布版，正在积极开发中。**

## 安装

摘自 [PyPI](https://pypi.org/project/sil-lift/)：

```
pip install sil-lift   # 安装库及 sil-lift 命令
```

需要 Python 3.11 及以上版本。 唯一的运行时依赖项是 lxml。

## 30秒导览

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # 同时追踪 .lift-ranges 关联项

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("seh") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # 或 lex.find(id="hoofd_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"

lex.save()   # 未修改的条目字节内容相同；已编辑的条目将重新序列化
```
