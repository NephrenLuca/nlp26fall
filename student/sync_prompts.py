"""把prompts.py内联到solution.py的PROMPTS区块。run.py运行前会自动调用；也可直接执行：python sync_prompts.py。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BEGIN = '# ===== PROMPTS BEGIN（由 sync_prompts.py 从 prompts.py 自动生成，请勿在此处手改）====='
END = '# ===== PROMPTS END ====='


def sync():
    prompts = (ROOT/'prompts.py').read_text(encoding='utf8').strip('\n')
    solution_path = ROOT/'solution.py'
    solution = solution_path.read_text(encoding='utf8')
    head, sep, rest = solution.partition(BEGIN)
    _, sep2, tail = rest.partition(END)
    if not sep or not sep2:
        raise ValueError('solution.py中缺少PROMPTS BEGIN/END标记')
    updated = head + BEGIN + '\n' + prompts + '\n' + END + tail
    if updated != solution:
        solution_path.write_text(updated, encoding='utf8')
        print('已将prompts.py同步到solution.py')


if __name__ == '__main__':
    sync()
