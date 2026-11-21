# 提示词文件：所有提示词只在这里修改。
# 运行 `python run.py` 时会自动执行 sync_prompts.py，把本文件原样内联进 solution.py 的
# PROMPTS 区块（框架只执行 solution.py，且禁止 import 本地文件，最终也只提交 solution.py）。
# 也可手动运行 `python sync_prompts.py` 同步。
# 约束：本文件只写字符串常量和注释；占位符用 {name}，提示词正文中不要出现其他花括号。

# ---------------------------------------------------------------------------
# 公共：单篇论文与论文对的展示格式（所有步骤共用）
# ---------------------------------------------------------------------------
PAPER_TEMPLATE = """Paper {label}
Title: {title}
Date: {date}
Abstract: {abstract}"""

PAIR_TEMPLATE = """{paper_a}

{paper_b}"""

# ---------------------------------------------------------------------------
# 【步骤1】直接指令（zero-shot baseline）
# ---------------------------------------------------------------------------
DIRECT_SYSTEM = """You are an expert in scientometrics who predicts how often research papers get cited."""

DIRECT_USER = """Below are two research papers (title, publication date and abstract). Predict which paper had received MORE citations at the time the data was recorded.

{pair}

Reply with exactly one line in the format:
Answer: A
or
Answer: B"""

# ---------------------------------------------------------------------------
# 【步骤2】few-shot：从示例池检索相似样例，作为多轮对话示范
# 复用步骤1的 DIRECT_SYSTEM；示例的 user 轮复用 DIRECT_USER，assistant 轮用 FEWSHOT_ANSWER。
# ---------------------------------------------------------------------------
FEWSHOT_SYSTEM = """You are an expert in scientometrics who predicts how often research papers get cited. You will first see several solved examples with the correct answers, then a new question. Learn from the examples which kinds of papers tend to be cited more."""

FEWSHOT_ANSWER = """Answer: {answer}"""

# ---------------------------------------------------------------------------
# 【步骤3】分步比较（结构化思维链 + 领域判据 + 代码预先计算的日期差）
# ---------------------------------------------------------------------------
COT_SYSTEM = """You are an expert in scientometrics. Your job is to predict which of two papers has more citations. Citation counts are driven mainly by: (1) the size and activity of the research community of the topic; (2) how broadly useful the contribution is (new general methods, datasets, benchmarks, software tools, surveys and foundational theory are cited far more than narrow case studies or incremental variants); (3) the strength and novelty of the claims; (4) the time a paper has had to accumulate citations (an earlier paper has an advantage, but a gap of a few months matters much less than topic and contribution type)."""

COT_USER = """Predict which paper had received MORE citations at the time the data was recorded.

{pair}

Extra context: {date_note}

Compare the papers step by step:
1. Field and community size of each paper (is it a hot, large area or a small niche?).
2. Type of contribution (method / dataset / benchmark / tool / survey / theory / application / case study) and how widely reusable it is.
3. Significance and generality of the results as claimed in the abstract.
4. Effect of the publication date gap.
Then weigh these factors and decide.

The LAST line of your reply must be exactly "Answer: A" or "Answer: B"."""

DATE_NOTE_TEMPLATE = """Paper {older} was published {gap} days earlier than Paper {newer}."""

SAME_DAY_NOTE = """Both papers were published on the same day."""

# ---------------------------------------------------------------------------
# 【步骤4】多次采样投票 + 交换A/B位置去偏
# 不需要新提示词：复用步骤3（或效果最好那一步）的提示词，见 solution.py 的 method_vote。
# ---------------------------------------------------------------------------
