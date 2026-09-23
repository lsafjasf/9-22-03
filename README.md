# textseg — 文本分段与规范化引擎

纯 Python 3 标准库实现。**不调用**任何运行时自带的断词 / 分词 / 分段能力；
`unicodedata` 仅作为*字符数据库*使用（general category、combining class、
分解映射），分段规则与规范化算法均为本库自行实现。测试中使用
`unicodedata.normalize` 作为独立参照（oracle）进行对拍。

## 功能

- **三类边界判定**（规则集参照 UAX #29，逐条以 GB/WB/SB 编号注释）：
  - 字形簇（grapheme cluster）：组合记号（GB9/GB9a/GB9b）、区域指示符成对
    （GB12/GB13）、表情修饰序列（emoji modifier 归类为 Extend）、零宽连接
    序列（GB11 `ExtPict Extend* ZWJ × ExtPict`）、谚文音节组合（GB6–GB8）、
    CR×LF（GB3）、控制字符（GB4/GB5）。
  - 词边界：字母/数字/假名/希伯来文连接（WB5–WB13）、MidLetter/MidNum
    （`can't`、`3.5`、`a.b`）、连接符（WB13a/13b）、RI 成对（WB15/16）、
    ZWJ 表情（WB3c）、Extend/Format/ZWJ 透明（WB4）。
  - 句子边界：终止符吸收闭标点与空白（SB9/SB10/SB11）、缩写抑制
    （SB6/SB7/SB8/SB8a 简化版）、CR/LF/分段符（SB3/SB4）。
- **规范化**：NFC / NFD / NFKC / NFKD（UAX #15），含 Hangul 算法合成、
  规范重排、组合排除表（CompositionExclusions）。
- **流式输入**：`feed()` 增量接收分块，只输出已确定为最终的段；
  `flush()` 收尾。与整体分段结果逐段一致（有对拍脚本验证）。
- **辅助 API**：按字形簇计数 / 截断、按词统计、按句拆分、按边界切分
  成长度不超过给定字形簇数的片段。

## 运行方式

```bash
# 全部自测（规则逐条 + 规范化对拍 + 流式一致 + API）
python3 -m unittest discover -s tests -v

# 流式 vs 整体 随机对拍（可指定迭代数与种子）
python3 scripts/diff_stream.py --iterations 500 --seed 42

# 或使用封装脚本
./run_tests.sh
```

## API 速览

```python
import textseg as ts

ts.graphemes('áb👩‍👧🇨🇳')          # ['á', 'b', '👩‍👧', '🇨🇳']
ts.count_graphemes('áb👩‍👧🇨🇳')    # 4
ts.truncate_graphemes('áb👩‍👧🇨🇳', 2, suffix='…')   # 'áb…'
ts.words("can't 3.5")               # ["can't", ' ', '3.5']
ts.count_words('中文测试')            # 4（表意文字按 UAX #29 默认逐字成词）
ts.sentences('One. Two!')           # ['One. ', 'Two!']
ts.chunk_text('áb👩‍👧🇨🇳cd', 2)      # 每片 ≤ 2 个字形簇，拼接还原原文
ts.normalize('é', 'NFC')           # 'é'

from textseg.stream import GraphemeStream, WordStream, SentenceStream
s = GraphemeStream()
out = s.feed('👩‍') + s.feed('👧') + s.flush()   # ['👩‍👧']
```

## 流式保留策略（需要多少前文才能判定）

- **GraphemeStream**：仅保留*当前未完成的一个簇*。所有 GB 规则判定某字符
  前的边界只需该字符本身 + 当前簇内上下文（GB11 的 `ExtPict Extend* ZWJ`
  回溯与 GB12/13 的 RI 奇偶性都不会跨越簇边界）。病态输入（无限组合记号
  序列）下保留量无界，但这是固有的——那样的序列本身就是单个簇。
- **WordStream**：保留*当前词 + 之后 1 个有效字符*。WB6/WB12
  （`AHLetter × MidLetter AHLetter` 等）最多需要看到边界字符之后的 1 个
  有效字符；Extend/Format/ZWJ 按 WB4 透明。
- **SentenceStream**：保留*自上一个已发射句界以来的全部文本*。终止符后的
  断点位置只有在出现一个"决定性"字符（非 Sp）后才最终确定（SB9/SB10 可
  吸收任意长的空白串，SB8 需要看到下一个字母）；结尾的孤立 CR 也会保留
  （SB3: CR×LF）。病态情况（`!` 后接无限空格）保留量无界，属规则集固有。

## 规范化前后分段一致性

Extend/Format/ZWJ 在词与句规则中透明、组合记号在字形簇规则中向左依附，
因此**规范等价**（NFC ↔ NFD）下分段结果保持一致：段数相同且逐段规范等价
（`tests/test_normalization.py::SegmentationInvariance` 验证）。若需要字节
级完全一致的结果，先 `normalize(text, 'NFC')` 再分段即可（兼容等价
NFKC/NFKD 按定义会改变字符本身，如 `ﬁ→fi`，不在此保证范围内）。

## 已记录的简化

- 未实现 GB9c（Unicode 15.1 印地语连字 InCB 规则）。
- SB8 简化为 `ATerm Close* Sp* × Lower`（不做多词前瞻）。
- 换行/分段符（LF/CR/NEL/U+2028/U+2029）总是独立成段（CR+LF 为一段），
  而非按 SB11 并入前一句。
- Extended_Pictographic、Prepend、STerm 等属性表为常用子集的近似
  （见 `textseg/properties.py` 注释），可按需扩充。

## 目录结构

```
textseg/
  properties.py     # GCB/WB/SB 属性表（由 unicodedata 字符数据派生）
  normalization.py  # NFC/NFD/NFKC/NFKD 实现
  segmentation.py   # 字形簇/词/句 批量分段
  stream.py         # 流式分段器
  api.py            # 计数/截断/切分等辅助函数
tests/              # 逐条规则自测 + 规范化对拍 + 流式一致 + API 测试
scripts/diff_stream.py  # 流式 vs 整体 随机对拍脚本
run_tests.sh
```
