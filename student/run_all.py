"""一键按顺序运行全部实验步骤（1 直接指令 → 2 few-shot → 3 分步比较 → 5 单独打分 → 4 混合投票），
并把每一步的完整控制台输出与评测指标追加记录到 llm_output.md（不存在则新建）。

用法（在模型服务已启动、并已激活 .lab-runtime 环境的终端中）：
    python run_all.py                 # 先跑3题冒烟测试，再依次跑步骤1、2、3、5、4的完整公开集
    python run_all.py --no-smoke      # 跳过冒烟测试
    python run_all.py --steps 3 5 4   # 只跑指定步骤
    python run_all.py --limit 10      # 每一步只跑前10题（小批调试）
结束后 solution.py 中的 STEP 会恢复为运行前的值（默认 4，即最终提交方案）。
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
SOLUTION = ROOT/'solution.py'
OUTPUT = ROOT/'llm_output.md'
STEP_LINE = re.compile(r'^STEP = (\d+)', re.M)
STEP_NAMES = {
    1: '步骤1 直接指令（zero-shot）',
    2: '步骤2 few-shot（检索相似示例）',
    3: '步骤3 分步比较（结构化CoT，无日期差）',
    4: '步骤4 混合投票（分步比较×3 + 单独打分×2）+ A/B交换去偏',
    5: '步骤5 单独打分（独立打1-10分后比较）',
}


def now():
    return dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_step():
    found = STEP_LINE.search(SOLUTION.read_text(encoding='utf8'))
    if not found:
        raise SystemExit('solution.py 中找不到 "STEP = <数字>" 这一行')
    return int(found.group(1))


def set_step(step):
    source = SOLUTION.read_text(encoding='utf8')
    SOLUTION.write_text(STEP_LINE.sub(f'STEP = {step}', source, count=1), encoding='utf8')


def append(text):
    with OUTPUT.open('a', encoding='utf8') as stream:
        stream.write(text)


def run_command(args):
    """运行子进程，实时打印并返回 (退出码, 完整输出, 耗时秒)。"""
    env = dict(os.environ, PYTHONUNBUFFERED='1', PYTHONIOENCODING='utf-8')
    began = time.monotonic()
    process = subprocess.Popen([sys.executable, '-X', 'utf8', *args], cwd=ROOT, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding='utf8', errors='replace')
    lines = []
    for line in process.stdout:
        print(line, end='', flush=True)
        lines.append(line)
    return process.wait(), ''.join(lines), time.monotonic() - began


def load_metrics(output):
    """从 run.py 输出的“已保存：<目录>”找到本次运行目录，读取最新评测结果。"""
    found = re.findall(r'^已保存：(.+)$', output, re.M)
    if not found:
        return None, None
    folder = Path(found[-1].strip())
    snapshots = sorted((folder/'evaluations').glob('evaluation_*.json'))
    if not snapshots:
        return folder, None
    return folder, json.loads(snapshots[-1].read_text(encoding='utf8'))['metrics']


def metrics_markdown(folder, metrics):
    if folder is None:
        return '- 未找到运行目录（运行可能未完成）\n'
    lines = [f'- 运行目录：`{folder}`']
    html = sorted((folder/'evaluations').glob('evaluation_*.html'))
    if html:
        lines.append(f'- 逐题详情（含完整提示词、模型回答与思考）：`{html[-1]}`')
    if metrics is None:
        lines.append('- 未计算准确率（数据集没有标签）')
        return '\n'.join(lines) + '\n'
    usage = metrics['usage']
    attempted = {json.loads(x)['id'] for x in (folder/'predictions.jsonl').read_text(encoding='utf8').splitlines() if x.strip()}
    wrong = [d['id'] for d in metrics['details'] if d['id'] in attempted and not d['correct']]
    partial = '（小批运行：按完整集题数计分，仅供检查流程）' if len(attempted) < metrics['n'] else ''
    lines += [
        f"- 准确率：**{metrics['accuracy']:.2%}**（{metrics['correct']}/{metrics['n']}）{partial}",
        f"- 已提交 {metrics['submitted']} 题，缺失 {metrics['missing']}，无效/缺失 {metrics['invalid']}",
        f"- 调用 {metrics['calls']}/{metrics['budget_limit']}；模型请求错误 {metrics['model_errors']}；"
        f"因长度截断 {metrics['length_finishes']}",
        f"- Token：prompt {usage['prompt_tokens']}，completion {usage['completion_tokens']}，"
        f"total {usage['total_tokens']}",
        f"- 运行耗时：{metrics['wall_seconds']} 秒",
        f"- 已运行题目中答错的题号（{len(wrong)}/{len(attempted)}）：{', '.join(wrong) if wrong else '无'}",
    ]
    return '\n'.join(lines) + '\n'


def record_run(title, args, step):
    print(f'\n========== {title} ==========', flush=True)
    started = now()
    code, output, seconds = run_command(args)
    folder, metrics = load_metrics(output)
    append(f'\n## {title}\n\n'
           f'- 开始时间：{started}；总耗时 {seconds:.1f} 秒；退出码 {code}\n'
           f"- 命令：`python {' '.join(args)}`（solution.py 中 STEP = {step}）\n"
           + metrics_markdown(folder, metrics) +
           f'\n<details><summary>完整控制台输出</summary>\n\n```text\n{output.rstrip()}\n```\n\n</details>\n')
    return code, metrics


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--steps', type=int, nargs='+', default=[1, 2, 3, 5, 4], choices=sorted(STEP_NAMES),
                   help='要运行的步骤，按给定顺序执行；默认 1 2 3 5 4')
    p.add_argument('--limit', type=int, help='每一步只跑前几题；不填则跑完整公开集')
    p.add_argument('--data', help='测试集文件；默认公开集')
    p.add_argument('--no-smoke', action='store_true', help='跳过开始时的3题冒烟测试')
    a = p.parse_args()
    if a.limit is not None and a.limit < 1:
        p.error('--limit须为正整数')

    extra = (['--limit', str(a.limit)] if a.limit else []) + (['--data', a.data] if a.data else [])
    original = get_step()
    created = not OUTPUT.exists()
    append(('# 实验运行记录\n' if created else '') +
           f'\n---\n\n# 一键运行 {now()}\n\n'
           f"- 步骤：{' → '.join(str(s) for s in a.steps)}；"
           f"题目范围：{'前 ' + str(a.limit) + ' 题' if a.limit else '全部'}；"
           f"数据：{a.data or 'data/public.jsonl'}\n")
    print(f'输出记录：{OUTPUT}', flush=True)

    code, output, _ = run_command(['check_server.py'])
    append(f'\n## 模型服务检查\n\n```text\n{output.rstrip()}\n```\n')
    if code != 0:
        append('\n**模型服务不可用，已中止。**\n')
        raise SystemExit('模型服务检查失败，已中止。请先在另一个终端运行 bash deploy/start.sh。')

    results = []
    try:
        if not a.no_smoke:
            set_step(a.steps[0])
            code, _ = record_run(f'冒烟测试：{STEP_NAMES[a.steps[0]]}（前3题）',
                                 ['run.py', '--limit', '3'] + (['--data', a.data] if a.data else []),
                                 a.steps[0])
            if code != 0:
                append('\n**冒烟测试失败，已中止后续步骤。**\n')
                raise SystemExit('冒烟测试失败，已中止。详见 llm_output.md。')
        for step in a.steps:
            set_step(step)
            code, metrics = record_run(STEP_NAMES[step], ['run.py'] + extra, step)
            results.append((step, code, metrics))
    except KeyboardInterrupt:
        append('\n**运行被手动中断。**\n')
        print('\n已中断。', flush=True)
    finally:
        set_step(original)

    if results:
        rows = ['| 步骤 | 准确率 | 正确/总数 | 调用/预算 | 无效 | 退出码 |', '|---|---:|---:|---:|---:|---:|']
        for step, code, m in results:
            if m:
                rows.append(f"| {STEP_NAMES[step]} | {m['accuracy']:.2%} | {m['correct']}/{m['n']} | "
                            f"{m['calls']}/{m['budget_limit']} | {m['invalid']} | {code} |")
            else:
                rows.append(f'| {STEP_NAMES[step]} | — | — | — | — | {code} |')
        append('\n## 本次汇总\n\n' + '\n'.join(rows) + '\n')
        print('\n' + '\n'.join(rows), flush=True)

    _, output, _ = run_command(['evaluate.py'])
    append(f'\n## 历史结果汇总（evaluate.py）\n\n```text\n{output.rstrip()}\n```\n')
    print(f'\n全部完成，记录已写入：{OUTPUT}', flush=True)


if __name__ == '__main__':
    main()
