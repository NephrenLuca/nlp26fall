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
# 【步骤3】分步比较（结构化思维链 + 领域判据；日期差不作为判据）
# ---------------------------------------------------------------------------
COT_SYSTEM = """You are an expert in scientometrics. Your job is to predict which of two papers has more citations. Citation counts are driven mainly by: (1) the size and activity of the research community of the topic; (2) how broadly useful the contribution is (new general methods, datasets, benchmarks, software tools, surveys and foundational theory are cited far more than narrow case studies or incremental variants); (3) the strength and novelty of the claims. The two papers were published close in time (usually within a year), so the date gap has almost no effect: do not favor a paper just because it is older."""

COT_USER = """Predict which paper had received MORE citations at the time the data was recorded.

{pair}

Compare the papers step by step:
1. Field and community size of each paper (is it a hot, large area or a small niche?).
2. Type of contribution (method / dataset / benchmark / tool / survey / theory / application / case study) and how widely reusable it is.
3. Significance and generality of the results as claimed in the abstract.
Then weigh these factors and decide.

The LAST line of your reply must be exactly "Answer: A" or "Answer: B"."""

# ---------------------------------------------------------------------------
# 【步骤5】单独打分：先给每篇论文的引用潜力独立打1-10分，再比较分数
# ---------------------------------------------------------------------------
SCORE_SYSTEM = """You are an expert in scientometrics who estimates the citation potential of research papers. Judge each paper on its own merits: the size and activity of its research field, the type and reusability of its contribution, and the significance of its claims."""

SCORE_USER = """Below are two research papers. Rate the citation potential of EACH paper independently, as if you had not seen the other one, on a 1-10 scale (1 = rarely cited niche work, 10 = highly influential work in a large, active field).

{pair}

For each paper, briefly consider:
- how large and active its research field is;
- what kind of contribution it makes (method / dataset / benchmark / tool / survey / theory / application / case study) and how widely reusable it is;
- how significant and general its claims are.
The papers were published close in time, so ignore the date gap. Rate Paper A first, then Paper B, and avoid giving both papers the same score.

End your reply with exactly these three lines:
Score A: <1-10>
Score B: <1-10>
Answer: <A or B, the paper with the higher score>"""

# ---------------------------------------------------------------------------
# 【步骤4】混合投票 + 交换A/B位置去偏（最终方案）
# 不需要新提示词：分步比较×3 + 单独打分×2，见 solution.py 的 VOTE_PLAN 与 method_vote。
# ---------------------------------------------------------------------------
