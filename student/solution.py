"""在 predict 中实现你的提示词与模型调用流程。

实验分4步，由下方常量 STEP 选择启用哪一步：
  步骤1 直接指令（zero-shot）
  步骤2 few-shot（检索相似示例）
  步骤3 分步比较（结构化CoT+日期差）
  步骤4 多次采样投票 + A/B交换去偏（最终方案，默认启用）
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
# ===== PROMPTS END =====

STEP = 4                 # 启用的实验步骤：1 直接指令 / 2 few-shot / 3 分步比较 / 4 投票；run_all.py 会逐步改写此行
MAX_CALLS = 5            # 每题平均调用预算（5×n 全局共享，超出会导致其他题目失败）
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


def ask(llm, messages, tries):
    """调用模型并提取答案；失败或无法提取时重试，最多 tries 次（每次都计入预算）。"""
    for _ in range(tries):
        try:
            response = llm.chat(messages)
        except RuntimeError:
            continue
        answer = extract_answer(response["content"])
        if answer is None:
            # 回答被截断时，答案可能只出现在思考末尾
            answer = extract_answer(response["reasoning"][-600:])
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
# 【步骤3】分步比较：结构化判据 + 代码预先算好的日期差（上下文工程），并沿用步骤2的 few-shot 示例
# 依赖步骤2的 select_examples / fewshot_messages，步骤2的代码须保持取消注释状态。
# 想单独测“不带示例的CoT”，把 method_cot 的 k 设为 0 即可。
# ---------------------------------------------------------------------------
def days_from_civil(y, m, d):
    y -= m <= 2
    era = (y if y >= 0 else y - 399) // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def parse_days(date):
    parts = [int(x) for x in re.findall(r"\d+", date)] + [1, 1]
    return days_from_civil(parts[0], parts[1], parts[2])


def date_note(pair):
    gap = parse_days(pair["paper_b"]["date"]) - parse_days(pair["paper_a"]["date"])
    if gap == 0:
        return SAME_DAY_NOTE
    return DATE_NOTE_TEMPLATE.format(older="A" if gap > 0 else "B", newer="B" if gap > 0 else "A", gap=abs(gap))


def cot_fill(pair):
    return {"pair": format_pair(pair), "date_note": date_note(pair)}


def method_cot(pair, examples, llm, tries=2, k=4):
    shots = select_examples(pair, examples, k) if k else []
    messages = fewshot_messages(COT_SYSTEM, COT_USER, shots, COT_USER.format(**cot_fill(pair)), cot_fill)
    return ask(llm, messages, tries)


# ---------------------------------------------------------------------------
# 【步骤4】多次采样投票（self-consistency）+ 交换 A/B 位置抵消位置偏置
# single 传入前几步中效果最好的方法（默认 method_cot）。共 votes 次投票，平票时再追加一次，总调用 ≤ MAX_CALLS。
# ---------------------------------------------------------------------------
def method_vote(pair, examples, llm, single, votes=4):
    counter = Counter()
    first = None
    for i in range(votes):
        swapped = i % 2 == 1
        answer = single(swap_pair(pair) if swapped else pair, examples, llm, tries=1)
        if swapped:
            answer = flip(answer)
        if answer:
            counter[answer] += 1
            first = first or answer
    if counter["A"] == counter["B"] and votes < MAX_CALLS:
        answer = single(pair, examples, llm, tries=1)
        if answer:
            counter[answer] += 1
    if counter["A"] == counter["B"]:
        return first
    return counter.most_common(1)[0][0]


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
    else:
        answer = method_vote(pair, examples, llm, method_cot)

    return answer if answer in ("A", "B") else DEFAULT_ANSWER
