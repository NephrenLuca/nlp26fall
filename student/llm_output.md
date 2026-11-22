# 实验运行记录

---

# 一键运行 2026-11-22 10:17:17

- 步骤：1 → 2 → 3 → 4；题目范围：全部；数据：data/public.jsonl

## 模型服务检查

```text
服务就绪：health = OK
模型名称：Qwen/Qwen3-4B
本次检查未发起模型生成请求。
```

## 冒烟测试：步骤1 直接指令（zero-shot）（前3题）

- 开始时间：2026-11-22 10:17:17；总耗时 11.7 秒；退出码 0
- 命令：`python run.py --limit 3`（solution.py 中 STEP = 1）
- 运行目录：`/root/shared-nvme/nlp26fall/student/runs/20261122T021717_759134Z_42a5ad_solution`
- 逐题详情（含完整提示词、模型回答与思考）：`/root/shared-nvme/nlp26fall/student/runs/20261122T021717_759134Z_42a5ad_solution/evaluations/evaluation_20261122T021729_239427Z_484a09.html`
- 准确率：**2.00%**（2/100）（小批运行：按完整集题数计分，仅供检查流程）
- 已提交 3 题，缺失 97，无效/缺失 97
- 调用 3/15；模型请求错误 0；因长度截断 0
- Token：prompt 1334，completion 2208，total 3542
- 运行耗时：11.423 秒
- 已运行题目中答错的题号（1/3）：P001

<details><summary>完整控制台输出</summary>

```text
服务就绪：health = OK
模型名称：Qwen/Qwen3-4B
本次检查未发起模型生成请求。
P003: B
P002: B
P001: B
结果汇总：/root/shared-nvme/nlp26fall/student/runs/reports/results_20261122T021729_255754Z_de0bf0.html
已保存：/root/shared-nvme/nlp26fall/student/runs/20261122T021717_759134Z_42a5ad_solution
调用预算 3/15；外部模型请求 3 次
```

</details>

## 步骤1 直接指令（zero-shot）

- 开始时间：2026-11-22 10:17:29；总耗时 95.0 秒；退出码 0
- 命令：`python run.py`（solution.py 中 STEP = 1）
- 运行目录：`/root/shared-nvme/nlp26fall/student/runs/20261122T021729_382614Z_0c4c49_solution`
- 逐题详情（含完整提示词、模型回答与思考）：`/root/shared-nvme/nlp26fall/student/runs/20261122T021729_382614Z_0c4c49_solution/evaluations/evaluation_20261122T021904_259032Z_5d0360.html`
- 准确率：**68.00%**（68/100）
- 已提交 100 题，缺失 0，无效/缺失 0
- 调用 100/500；模型请求错误 0；因长度截断 0
- Token：prompt 56967，completion 87859，total 144826
- 运行耗时：94.821 秒
- 已运行题目中答错的题号（32/100）：P001, P012, P016, P017, P021, P022, P023, P024, P025, P027, P033, P037, P039, P044, P049, P051, P052, P062, P063, P064, P065, P069, P070, P074, P076, P078, P081, P082, P083, P085, P087, P091

<details><summary>完整控制台输出</summary>

```text
服务就绪：health = OK
模型名称：Qwen/Qwen3-4B
本次检查未发起模型生成请求。
P009: A
P003: B
P004: A
P005: B
P006: A
P016: A
P011: A
P010: A
P014: A
P001: B
P008: A
P002: B
P007: B
P015: B
P012: B
P018: A
P013: A
P024: A
P019: A
P020: B
P017: B
P027: B
P028: B
P026: B
P022: B
P025: B
P021: B
P031: A
P034: A
P033: A
P030: B
P032: A
P029: A
P038: B
P040: B
P041: B
P035: A
P044: A
P045: A
P037: A
P039: A
P046: A
P048: A
P036: B
P050: A
P047: A
P042: A
P058: B
P023: A
P054: B
P049: A
P052: B
P056: A
P053: A
P060: A
P055: B
P059: A
P062: A
P057: B
P061: B
P064: A
P043: B
P063: A
P051: A
P068: B
P075: A
P071: A
P069: B
P070: A
P073: A
P072: A
P081: A
P083: A
P066: A
P065: A
P078: B
P079: B
P080: B
P067: B
P074: B
P076: A
P086: A
P088: A
P089: A
P090: B
P084: B
P091: B
P095: A
P096: A
P092: B
P077: A
P085: A
P094: B
P093: B
P097: A
P100: A
P082: A
P087: A
P099: B
P098: B
结果汇总：/root/shared-nvme/nlp26fall/student/runs/reports/results_20261122T021904_303529Z_df5e75.html
已保存：/root/shared-nvme/nlp26fall/student/runs/20261122T021729_382614Z_0c4c49_solution
调用预算 100/500；外部模型请求 100 次
```

</details>

## 步骤2 few-shot（检索相似示例）

- 开始时间：2026-11-22 10:19:04；总耗时 132.4 秒；退出码 0
- 命令：`python run.py`（solution.py 中 STEP = 2）
- 运行目录：`/root/shared-nvme/nlp26fall/student/runs/20261122T021904_459651Z_dd5ad6_solution`
- 逐题详情（含完整提示词、模型回答与思考）：`/root/shared-nvme/nlp26fall/student/runs/20261122T021904_459651Z_dd5ad6_solution/evaluations/evaluation_20261122T022116_659261Z_3bfeeb.html`
- 准确率：**69.00%**（69/100）
- 已提交 100 题，缺失 0，无效/缺失 0
- 调用 100/500；模型请求错误 0；因长度截断 0
- Token：prompt 297697，completion 80301，total 377998
- 运行耗时：132.144 秒
- 已运行题目中答错的题号（31/100）：P002, P004, P006, P012, P014, P016, P017, P021, P027, P030, P035, P039, P044, P049, P051, P052, P055, P056, P062, P063, P072, P073, P074, P075, P081, P083, P085, P091, P093, P097, P098

<details><summary>完整控制台输出</summary>

```text
服务就绪：health = OK
模型名称：Qwen/Qwen3-4B
本次检查未发起模型生成请求。
P016: A
P003: B
P014: B
P015: B
P008: A
P009: A
P012: B
P007: B
P010: A
P001: A
P011: A
P005: B
P006: B
P013: A
P002: A
P004: B
P017: B
P018: A
P019: A
P027: B
P020: B
P025: A
P024: B
P021: B
P029: A
P026: B
P023: B
P031: A
P036: B
P034: A
P022: A
P039: A
P037: B
P038: B
P042: A
P040: B
P033: B
P044: A
P041: B
P030: A
P045: A
P028: B
P046: A
P052: B
P047: A
P032: A
P049: A
P051: A
P053: A
P048: A
P035: B
P043: B
P054: B
P055: A
P058: B
P062: A
P061: B
P065: B
P050: A
P059: A
P063: A
P057: B
P060: A
P066: A
P068: B
P067: B
P071: A
P056: B
P081: A
P079: B
P078: A
P077: A
P064: B
P080: B
P076: B
P073: B
P074: B
P086: A
P083: A
P085: A
P082: B
P087: B
P092: B
P091: B
P075: B
P088: A
P093: A
P069: A
P070: B
P094: B
P089: A
P090: B
P096: A
P084: B
P100: A
P072: B
P097: B
P099: B
P095: A
P098: A
结果汇总：/root/shared-nvme/nlp26fall/student/runs/reports/results_20261122T022116_734629Z_baa55b.html
已保存：/root/shared-nvme/nlp26fall/student/runs/20261122T021904_459651Z_dd5ad6_solution
调用预算 100/500；外部模型请求 100 次
```

</details>

## 步骤3 分步比较（结构化CoT + 日期差）

- 开始时间：2026-11-22 10:21:16；总耗时 166.5 秒；退出码 0
- 命令：`python run.py`（solution.py 中 STEP = 3）
- 运行目录：`/root/shared-nvme/nlp26fall/student/runs/20261122T022116_894168Z_b56d0b_solution`
- 逐题详情（含完整提示词、模型回答与思考）：`/root/shared-nvme/nlp26fall/student/runs/20261122T022116_894168Z_b56d0b_solution/evaluations/evaluation_20261122T022403_146668Z_a4450e.html`
- 准确率：**72.00%**（72/100）
- 已提交 100 题，缺失 0，无效/缺失 0
- 调用 100/500；模型请求错误 0；因长度截断 0
- Token：prompt 343465，completion 101883，total 445348
- 运行耗时：166.195 秒
- 已运行题目中答错的题号（28/100）：P001, P002, P006, P010, P012, P016, P017, P037, P039, P043, P044, P049, P051, P052, P055, P056, P062, P064, P073, P074, P075, P081, P083, P085, P091, P095, P097, P098

<details><summary>完整控制台输出</summary>

```text
服务就绪：health = OK
模型名称：Qwen/Qwen3-4B
本次检查未发起模型生成请求。
P008: A
P010: B
P014: A
P013: A
P009: A
P002: A
P006: B
P005: B
P012: B
P017: B
P011: A
P007: B
P003: B
P020: B
P015: B
P016: A
P018: A
P004: A
P001: B
P019: A
P021: A
P026: B
P031: A
P035: A
P032: A
P025: A
P024: B
P028: B
P036: B
P034: A
P029: A
P038: B
P022: A
P039: A
P030: B
P027: A
P037: A
P033: B
P046: A
P040: B
P041: B
P043: A
P042: A
P044: A
P023: B
P047: A
P045: A
P053: A
P058: B
P048: A
P050: A
P054: B
P062: A
P059: A
P051: A
P060: A
P052: B
P065: B
P066: A
P055: A
P056: B
P068: B
P061: B
P049: A
P057: B
P071: A
P063: B
P074: B
P075: B
P072: A
P067: B
P077: A
P081: A
P069: A
P073: B
P079: B
P076: B
P086: A
P083: A
P088: A
P080: B
P078: A
P064: A
P089: A
P082: B
P070: B
P084: B
P087: B
P092: B
P090: B
P096: A
P091: B
P085: A
P093: B
P097: B
P098: A
P099: B
P094: B
P100: A
P095: B
结果汇总：/root/shared-nvme/nlp26fall/student/runs/reports/results_20261122T022403_238779Z_1043e6.html
已保存：/root/shared-nvme/nlp26fall/student/runs/20261122T022116_894168Z_b56d0b_solution
调用预算 100/500；外部模型请求 100 次
```

</details>

## 步骤4 多次采样投票 + A/B交换去偏

- 开始时间：2026-11-22 10:24:03；总耗时 674.2 秒；退出码 0
- 命令：`python run.py`（solution.py 中 STEP = 4）
- 运行目录：`/root/shared-nvme/nlp26fall/student/runs/20261122T022403_405405Z_26df37_solution`
- 逐题详情（含完整提示词、模型回答与思考）：`/root/shared-nvme/nlp26fall/student/runs/20261122T022403_405405Z_26df37_solution/evaluations/evaluation_20261122T023517_217239Z_e6b7e2.html`
- 准确率：**73.00%**（73/100）
- 已提交 100 题，缺失 0，无效/缺失 0
- 调用 417/500；模型请求错误 0；因长度截断 0
- Token：prompt 1432816，completion 441236，total 1874052
- 运行耗时：673.691 秒
- 已运行题目中答错的题号（27/100）：P001, P002, P005, P006, P010, P012, P013, P014, P017, P021, P037, P039, P043, P044, P052, P062, P069, P070, P073, P074, P075, P081, P083, P091, P093, P095, P098

<details><summary>完整控制台输出</summary>

```text
服务就绪：health = OK
模型名称：Qwen/Qwen3-4B
本次检查未发起模型生成请求。
P003: B
P006: B
P009: A
P002: A
P004: A
P001: B
P012: B
P011: A
P015: B
P007: B
P010: B
P008: A
P014: B
P017: B
P005: A
P018: A
P013: B
P016: B
P020: B
P024: B
P022: A
P027: A
P023: B
P021: B
P019: A
P032: A
P031: A
P029: A
P034: A
P025: A
P030: B
P028: B
P036: B
P033: B
P026: B
P040: B
P038: B
P039: A
P035: A
P043: A
P042: A
P046: A
P047: A
P044: A
P041: B
P048: A
P053: A
P050: A
P054: B
P052: B
P037: A
P058: B
P049: B
P051: B
P057: B
P045: A
P055: B
P059: A
P056: A
P060: A
P062: A
P066: A
P061: B
P067: B
P068: B
P063: B
P071: A
P065: B
P076: B
P074: B
P069: B
P077: A
P072: A
P070: A
P078: A
P075: B
P073: B
P083: A
P086: A
P080: B
P081: A
P089: A
P064: B
P079: B
P084: B
P088: A
P092: B
P085: B
P090: B
P096: A
P091: B
P094: B
P087: B
P097: A
P099: B
P082: B
P095: B
P093: A
P100: A
P098: A
结果汇总：/root/shared-nvme/nlp26fall/student/runs/reports/results_20261122T023517_481358Z_9f6966.html
已保存：/root/shared-nvme/nlp26fall/student/runs/20261122T022403_405405Z_26df37_solution
调用预算 417/500；外部模型请求 417 次
```

</details>

## 本次汇总

| 步骤 | 准确率 | 正确/总数 | 调用/预算 | 无效 | 退出码 |
|---|---:|---:|---:|---:|---:|
| 步骤1 直接指令（zero-shot） | 68.00% | 68/100 | 100/500 | 0 | 0 |
| 步骤2 few-shot（检索相似示例） | 69.00% | 69/100 | 100/500 | 0 | 0 |
| 步骤3 分步比较（结构化CoT + 日期差） | 72.00% | 72/100 | 100/500 | 0 | 0 |
| 步骤4 多次采样投票 + A/B交换去偏 | 73.00% | 73/100 | 417/500 | 0 | 0 |

## 历史结果汇总（evaluate.py）

```text
结果汇总：/root/shared-nvme/nlp26fall/student/runs/reports/results_20261122T023517_645809Z_5fb845.html
```
