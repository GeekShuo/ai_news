"""每日情报 Agent CLI。

用法:
    python run_task.py ai_industry     # ① AI产业日报
    python run_task.py ai_research     # ② AI科研日报
    python run_task.py ai_jobs         # ③ 求职情报日报
    python run_task.py emotion_ups     # ④ 情感UP主更新日报
    python run_task.py all             # 依次跑全部

选项:
    --dry-run   只采集并打印条目，不调 LLM、不推送
    --no-push   生成报告但不推送微信
"""
import argparse
import datetime
import importlib
import sys

TASKS = ["ai_industry", "ai_research", "ai_jobs", "emotion_ups"]


def main():
    ap = argparse.ArgumentParser(description="每日情报 Agent")
    ap.add_argument("task", help="任务名或 all")
    ap.add_argument("--dry-run", action="store_true", help="只采集打印，不调 LLM、不推送")
    ap.add_argument("--no-push", action="store_true", help="生成报告但不推送")
    args = ap.parse_args()

    names = TASKS if args.task == "all" else [args.task]
    for name in names:
        if name not in TASKS:
            sys.exit(f"未知任务: {name}，可选: {TASKS} / all")
        print(f"\n===== [{name}] {datetime.datetime.now():%Y-%m-%d %H:%M:%S} =====")
        mod = importlib.import_module(f"tasks.{name}")
        mod.run(dry_run=args.dry_run, no_push=args.no_push)


if __name__ == "__main__":
    main()
