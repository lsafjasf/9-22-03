# textseg — 文本分段与规范化引擎

纯 Python 3 标准库实现。**所有断词/分段逻辑均为手写**，不调用运行时自带的
断词、分词或分段能力；分段规则遵循 UAX #29（Unicode 16.0.0），属性数据表由
官方 UCD 文件生成。规范化（NFC/NFD/NFKC/NFKD）基于标准库 `unicodedata`
的规范化数据表（规范化不属于被禁止的"断词/分词/分段"能力）。

## 功能

- **三类边界判定**（扩展字形簇 / 词 / 句子），覆盖：
  - 组合记号（GB9、WB4、SB5 的 Extend/Format 忽略规则）
  - 区域指示符成对（GB12/GB13、WB15/WB16），如国旗 🇨🇳
  - 表情修饰序列（GB9 肤色修饰符）与零宽连接序列（GB11、WB3c），如 👨‍👩‍👧‍👦
  - 音节组合类文字：谚文 L/V/T/LV/LVT 合并（GB6–GB8）、印地语系
    连接子 conjunct 合并（GB9c，如 क्ष）
  - Prepend / SpacingMark（GB9a/GB9b）、控制字符（GB4/GB5）等
- **规范化**：规范等价（NFC/NFD）与兼容等价（NFKC/NFKD）；同一文本在
  规范化前后分段结果保持一致（见下"不变性"）。
- **流式输入**：`StreamSegmenter` 按块喂入，只输出已确定不可撤销的段。
- **工具**：按字形簇计数/截断、按词统计、按句拆分、按边界把长文本切成
  不超过给定字形簇数的片段。

## 运行方式

```bash
python3 tools/gen_tables.py        # 一次性：下载 UCD 数据并生成 textseg/_data.py
python3 -m textseg "示例 text 👨‍👩‍👧‍👦"   # 演示
python3 run_tests.py               # 全部自测（规则/边界/官方一致性/流式对拍）
python3 tests/diff_stream.py       # 只跑流式 vs 整体对拍
```

## API 速览

```python
import textseg as ts

ts.graphemes("Café 👍🏽")            # 字形簇列表
ts.grapheme_count(s)                # 字形簇计数
ts.truncate_graphemes(s, 10, "…")   # 按簇截断（不切碎簇）
ts.words(s) / ts.word_count(s)      # 词（含字母数字的段）/ 词数
ts.iter_word_segments(s)            # 全部词边界段（含空白标点）
ts.split_sentences(s)               # 句子拆分
ts.chunk_text(s, 80, prefer_word=True)  # 切成 ≤80 簇的片段，尽量在词边界断开

ts.normalize(s, "NFC")              # NFC/NFD/NFKC/NFKD
ts.canonical_equal(a, b)            # 规范等价
ts.compatibility_equal(a, b)        # 兼容等价

st = ts.StreamSegmenter("grapheme") # 或 "word" / "sentence"
segs = st.feed(chunk)               # 返回新确定的段
st.pending                          # 当前保留的未决前文
tail = st.flush()                   # 输入结束，取回剩余段
```

## 流式保留策略（需要保留多少前文）

分段器只提交"未来输入不可能再改变"的边界，保留的未决前文可通过
`st.pending` 观察：

| 类型   | 前瞻需求 | 说明 |
|--------|----------|------|
| 字形簇 | 1 个字符 | 所有 GB 规则只看边界处字符 + 左侧上下文，因此只需保留当前未完结的簇。病态输入（无限长的 Extend/Prepend/SpacingMark 序列）下保留量无界，这是簇定义本身决定的。 |
| 词     | 2 个有效字符（非 Extend/Format/ZWJ） | WB6/WB7b/WB12 要看边界右侧字符的下一个有效字符（如 `"a."` 需等 `.` 之后的字符才能判定）。 |
| 句子   | 1 个"决定性"字符 | SB8 的右上下文会越过 Close/Sp/SContinue/Numeric/Other 扫描 Lower，因此 `"A. "` 之后若持续来数字/空白，边界一直处于未决状态，保留量随未决尾巴增长（SB8 规则本身决定）。 |

实现上每次 `feed` 后对未决缓冲重算边界，只提交阈值之前的边界，因此
**任意分块方式下结果与整体分段完全一致**——由 `tests/diff_stream.py`
对拍保证（官方全部测试向量 × 多种块长 + 随机模糊，共 1.8 万+ 项检查）。

## 规范化不变性

- **规范等价（NFC/NFD）**：UAX #29 的边界规则对规范等价不变。测试断言
  `normalize(segment(NFC(s))) == segment(NFD(s))`（逐段对应）。
- **兼容等价（NFKC/NFKD）**：一般情况下不保证不变（如 `ﬁ` → `fi` 会
  改变簇数）；对兼容映射不改变边界类别的文本，测试验证了分段与规范化
  可交换。

## 设计要点

- **两阶段忽略规则**（UAX #29 §6.2）：WB3c/WB3d/WB4、SB3/SB4/SB5 在原始
  序列上判定；随后删除被忽略的 Extend/Format（词还包括 ZWJ，行首/换行后
  除外），在约简序列上应用其余规则。
- **句子左上下文**用 O(1) 状态机（TERM/CLOSE/SP/NONE）跟踪
  `SATerm Close* Sp*` 后缀；SB8 的右上下文 `(¬…)* Lower` 用一次反向
  扫描预计算。
- **属性数据**：`textseg/_data.py` 由 `tools/gen_tables.py` 从
  unicode.org 的 UCD 16.0.0 文件生成（Grapheme/Word/Sentence break
  property、emoji-data、DerivedCoreProperties 的 InCB），区间表 + 二分查找。

## 测试

- `tests/test_rules.py` — 逐条规则自测（GB/WB/SB 每条规则 + 规范化不变性）
- `tests/test_edge.py` — 空文本、纯控制字符、上万连续组合记号、不完整
  序列（尾随 ZWJ/virama/单个 RI/孤立 CR/孤立代理项）等
- `tests/test_conformance.py` — 官方 GraphemeBreakTest / WordBreakTest /
  SentenceBreakTest 全量通过
- `tests/diff_stream.py` — 流式与整体结果对拍（官方用例 × 5 种分块 +
  1500 组随机模糊）
