"""在 predict 中实现你的提示词与模型调用流程。

实验分5步，由下方常量 STEP 选择启用哪一步：
  步骤1 直接指令（zero-shot）
  步骤2 few-shot（检索相似示例）
  步骤3 分步比较（结构化CoT，不再提供日期差）
  步骤4 混合投票（分步比较×3 + 单独打分×2）+ A/B交换去偏（最终方案，默认启用）
  步骤5 单独打分（先给每篇论文独立打1-10分，再比较）
一键按顺序运行全部步骤：python run_all.py
提示词只在 prompts.py 中修改；下方 PROMPTS 区块由 sync_prompts.py 自动生成（run.py 会自动同步）。
"""
import re
from collections import Counter

# ===== PROMPTS BEGIN（由 sync_prompts.py 从 prompts.py 自动生成，请勿在此处手改）=====
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
# ===== PROMPTS END =====

STEP = 4                 # 启用的实验步骤：1 直接指令 / 2 few-shot / 3 分步比较 / 4 混合投票 / 5 单独打分；run_all.py 会逐步改写此行
MAX_CALLS = 5            # 每题平均调用预算（5×n 全局共享，超出会导致其他题目失败）
VOTE_RETRIES = 1         # 投票中某票调用失败时，每题最多补调的次数（由提前结束省下的调用覆盖）
MAX_REQUEST_BYTES = 19000  # 框架限制单次请求 20,000 字节，留余量
DEFAULT_ANSWER = "A"     # 所有调用均失败或无法提取答案时的兜底


# ---------------------------------------------------------------------------
# 公共工具（所有步骤共用）
# ---------------------------------------------------------------------------
def clean(text):
    return " ".join(str(text).split())


def format_paper(label, paper):
    return PAPER_TEMPLATE.format(label=label, title=clean(paper["title"]),
                                 date=clean(paper["date"]), abstract=clean(paper["abstract"]))


def format_pair(pair):
    return PAIR_TEMPLATE.format(paper_a=format_paper("A", pair["paper_a"]),
                                paper_b=format_paper("B", pair["paper_b"]))


def swap_pair(pair):
    return {"paper_a": pair["paper_b"], "paper_b": pair["paper_a"]}


def flip(answer):
    return {"A": "B", "B": "A"}.get(answer)


def request_bytes(messages):
    return sum(len(m["content"].encode("utf8")) for m in messages)


ANSWER_PATTERNS = [
    r"(?i:answer)[\"'\s]*(?:(?i:is))?\s*[:：]?[\s\"'*]*(?:(?i:paper)\s*)?\(?\s*([AB])\b",
    r"^\s*\**\s*([AB])\s*\**\s*$",
    r"\*\*\s*(?:(?i:paper)\s*)?([AB])\s*\*\*",
]


def extract_answer(text):
    """从模型回答中提取 A/B：优先“Answer: X”，取最后一次出现。"""
    if not text:
        return None
    for pattern in ANSWER_PATTERNS:
        found = re.findall(pattern, text, re.M)
        if found:
            return found[-1]
    return None


SCORE_PATTERN = r"(?i:score)\s*(?:(?i:paper)\s*)?([AB])\s*\**\s*[:：=]\s*\**\s*(\d+(?:\.\d+)?)"


def extract_score(text):
    """从“Score A: x / Score B: y”中比较分数；缺失或同分时退回“Answer: X”。"""
    if not text:
        return None
    scores = dict(re.findall(SCORE_PATTERN, text))
    if "A" in scores and "B" in scores and float(scores["A"]) != float(scores["B"]):
        return "A" if float(scores["A"]) > float(scores["B"]) else "B"
    return extract_answer(text)


def ask(llm, messages, tries, extract=extract_answer):
    """调用模型并提取答案；失败或无法提取时重试，最多 tries 次（每次都计入预算）。"""
    for _ in range(tries):
        try:
            response = llm.chat(messages)
        except RuntimeError:
            continue
        answer = extract(response["content"])
        if answer is None:
            # 回答被截断时，答案可能只出现在思考末尾
            answer = extract(response["reasoning"][-600:])
        if answer is not None:
            return answer
    return None


# ---------------------------------------------------------------------------
# 【步骤1】直接指令（zero-shot baseline）
# ---------------------------------------------------------------------------
def method_direct(pair, examples, llm, tries=2):
    messages = [
        {"role": "system", "content": DIRECT_SYSTEM},
        {"role": "user", "content": DIRECT_USER.format(pair=format_pair(pair))},
    ]
    return ask(llm, messages, tries)


# ---------------------------------------------------------------------------
# 【步骤2】few-shot：按词重叠（Jaccard）从示例池检索相似样例，A/B 标签各半避免标签偏置
# ---------------------------------------------------------------------------
STOPWORDS = set("""a an the of and or in on for to with by from at as is are was were be been this that these
those we our us it its which can using based via into over under than then also such their they paper
propose proposed show shows present new approach method methods results study model models""".split())


def tokens(text):
    return set(w for w in re.findall(r"[a-z][a-z0-9\-]+", text.lower()) if w not in STOPWORDS and len(w) > 2)


def pair_tokens(pair):
    return tokens(" ".join(pair[k]["title"] + " " + pair[k]["abstract"] for k in ("paper_a", "paper_b")))


def select_examples(pair, examples, k=4):
    """取与当前题最相似的示例，A/B 各 k/2 条；按相似度升序排列，最相似的离问题最近。"""
    query = pair_tokens(pair)

    def score(ex):
        other = pair_tokens(ex)
        return len(query & other) / max(1, len(query | other))

    ranked = sorted(examples, key=score, reverse=True)
    chosen = [e for e in ranked if e["answer"] == "A"][:k // 2] + [e for e in ranked if e["answer"] == "B"][:k - k // 2]
    return sorted(chosen, key=score)


def fewshot_messages(system, user_template, shots, query_user, fill):
    """shots 依次组成 user/assistant 轮；超出字节上限时先丢弃最不相似的示例。"""
    while True:
        messages = [{"role": "system", "content": system}]
        for ex in shots:
            messages.append({"role": "user", "content": user_template.format(**fill(ex))})
            messages.append({"role": "assistant", "content": FEWSHOT_ANSWER.format(answer=ex["answer"])})
        messages.append({"role": "user", "content": query_user})
        if request_bytes(messages) <= MAX_REQUEST_BYTES or not shots:
            return messages
        shots = shots[1:]


def method_fewshot(pair, examples, llm, tries=2, k=4):
    shots = select_examples(pair, examples, k)
    messages = fewshot_messages(FEWSHOT_SYSTEM, DIRECT_USER, shots,
                                DIRECT_USER.format(pair=format_pair(pair)),
                                lambda ex: {"pair": format_pair(ex)})
    return ask(llm, messages, tries)


# ---------------------------------------------------------------------------
# 【步骤3】分步比较：结构化判据（明确告诉模型日期差基本无影响），并沿用步骤2的 few-shot 示例
# 依赖步骤2的 select_examples / fewshot_messages，步骤2的代码须保持取消注释状态。
# 想单独测“不带示例的CoT”，把 method_cot 的 k 设为 0 即可。
# ---------------------------------------------------------------------------
def cot_fill(pair):
    return {"pair": format_pair(pair)}


def method_cot(pair, examples, llm, tries=2, k=4):
    shots = select_examples(pair, examples, k) if k else []
    messages = fewshot_messages(COT_SYSTEM, COT_USER, shots, COT_USER.format(**cot_fill(pair)), cot_fill)
    return ask(llm, messages, tries)


# ---------------------------------------------------------------------------
# 【步骤5】单独打分：每篇论文独立打1-10分后比较（不带示例，与分步比较形成互补）
# ---------------------------------------------------------------------------
def method_score(pair, examples, llm, tries=2):
    messages = [
        {"role": "system", "content": SCORE_SYSTEM},
        {"role": "user", "content": SCORE_USER.format(pair=format_pair(pair))},
    ]
    return ask(llm, messages, tries, extract_score)


# ---------------------------------------------------------------------------
# 【步骤4】混合投票（self-consistency）+ 交换 A/B 位置抵消位置偏置
# 固定 5 票（奇数，不会平票）：分步比较×3 + 单独打分×2，每种方法都覆盖原序和交换顺序。
# 某一方先达到 3 票即提前结束（剩余票数无法改变结果），省下的调用用于补调失败的票。
# ---------------------------------------------------------------------------
def method_vote(pair, examples, llm, plan):
    counter = Counter()
    first = None
    majority = len(plan) // 2 + 1
    retries = VOTE_RETRIES
    for single, swapped in plan:
        while True:
            answer = single(swap_pair(pair) if swapped else pair, examples, llm, tries=1)
            if answer or retries == 0:
                break
            retries -= 1
        if answer:
            answer = flip(answer) if swapped else answer
            counter[answer] += 1
            first = first or answer
        if max(counter.values(), default=0) >= majority:
            break
    if counter["A"] == counter["B"]:
        return first
    return counter.most_common(1)[0][0]


VOTE_PLAN = [
    (method_cot, False),
    (method_score, True),
    (method_cot, True),
    (method_score, False),
    (method_cot, False),
]


def predict(pair, examples, llm):
    """根据当前论文对返回字符串 "A" 或 "B"。

    pair: paper_a、paper_b 各含 title、abstract、date。
    examples: 100 条示例，另含 id 和 answer。
    llm.chat(messages): 接收消息列表，返回 content 和 reasoning。
    """
    if STEP == 1:
        answer = method_direct(pair, examples, llm)
    elif STEP == 2:
        answer = method_fewshot(pair, examples, llm)
    elif STEP == 3:
        answer = method_cot(pair, examples, llm)
    elif STEP == 5:
        answer = method_score(pair, examples, llm)
    else:
        answer = method_vote(pair, examples, llm, VOTE_PLAN)

    return answer if answer in ("A", "B") else DEFAULT_ANSWER
