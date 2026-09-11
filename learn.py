from __future__ import annotations

import re
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


TASK_PATTERN = re.compile(r"^\s*-\s*\[([ xX])\]\s*(.*)$")
LINK_PATTERN = re.compile(r"^\[([^]]+)\]\(([^)]+)\)")

STAGE_CONFIG = (
    ("Python 基础", "01-python基础"),
    ("大模型基础", "02-大模型基础"),
    ("RAG", "03-rag"),
    ("Agent", "04-agent"),
    ("综合项目", "05-综合项目"),
)


@dataclass(frozen=True)
class Task:
    path: Path
    line_number: int
    title: str
    url: str | None
    completed: bool


@dataclass
class Stage:
    name: str
    directory: Path
    tasks: list[Task]


def parse_tasks(path: Path) -> list[Task]:
    tasks: list[Task] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        task_match = TASK_PATTERN.match(line)
        if not task_match:
            continue

        marker, text = task_match.groups()
        link_match = LINK_PATTERN.match(text)
        title = link_match.group(1) if link_match else text.strip()
        url = link_match.group(2) if link_match else None
        tasks.append(
            Task(
                path=path,
                line_number=line_number,
                title=title,
                url=url,
                completed=marker.lower() == "x",
            )
        )
    return tasks


def progress(tasks: list[Task]) -> tuple[int, int]:
    return sum(task.completed for task in tasks), len(tasks)


def load_stages(root: Path) -> tuple[list[Stage], list[str]]:
    stages: list[Stage] = []
    warnings: list[str] = []
    for name, directory_name in STAGE_CONFIG:
        directory = root / directory_name
        tasks: list[Task] = []
        if not directory.is_dir():
            warnings.append(f"未找到学习目录：{directory_name}")
        else:
            for path in sorted(directory.glob("*.md")):
                try:
                    tasks.extend(parse_tasks(path))
                except (OSError, UnicodeError) as error:
                    warnings.append(f"无法读取 {path.name}：{error}")
        stages.append(Stage(name=name, directory=directory, tasks=tasks))
    return stages, warnings


def toggle_task(task: Task) -> None:
    with task.path.open("r", encoding="utf-8", newline="") as file:
        lines = file.readlines()

    if task.line_number >= len(lines) or not TASK_PATTERN.match(lines[task.line_number]):
        raise ValueError("任务所在行已发生变化，请刷新后重试。")

    replacement = " " if task.completed else "x"
    lines[task.line_number] = re.sub(
        r"^(\s*-\s*\[)[ xX](\])",
        rf"\g<1>{replacement}\2",
        lines[task.line_number],
        count=1,
    )
    with task.path.open("w", encoding="utf-8", newline="") as file:
        file.writelines(lines)


def progress_bar(done: int, total: int, width: int = 20) -> str:
    percentage = round(done / total * 100) if total else 0
    filled = int(done / total * width) if total else 0
    return f"[{'#' * filled}{'-' * (width - filled)}] {percentage}%"


def read_choice(
    prompt: str,
    minimum: int,
    maximum: int,
    input_fn: Callable[[str], str] = input,
) -> int:
    while True:
        try:
            choice = int(input_fn(prompt).strip())
        except ValueError:
            print("请输入数字。")
            continue
        if minimum <= choice <= maximum:
            return choice
        print(f"请输入 {minimum} 到 {maximum} 之间的数字。")


def _print_main_menu(stages: list[Stage]) -> None:
    all_tasks = [task for stage in stages for task in stage.tasks]
    done, total = progress(all_tasks)
    print("\n=== AI 学习路线 ===")
    print(f"总进度：{done}/{total} {progress_bar(done, total)}\n")
    for number, stage in enumerate(stages, start=1):
        stage_done, stage_total = progress(stage.tasks)
        print(f"{number}. {stage.name:<10} {stage_done}/{stage_total}")
    print("0. 退出")


def _task_action(
    task: Task,
    input_fn: Callable[[str], str],
    open_fn: Callable[[str], bool],
) -> None:
    print(f"\n任务：{task.title}")
    print("1. 标记未完成" if task.completed else "1. 标记完成")
    if task.url:
        print("2. 打开链接")
    print("0. 返回")
    maximum = 2 if task.url else 1
    choice = read_choice("请选择操作：", 0, maximum, input_fn)
    if choice == 1:
        toggle_task(task)
        print("状态已更新。")
    elif choice == 2 and task.url:
        if open_fn(task.url):
            print("已交给默认浏览器打开。")
        else:
            print("浏览器未能打开该链接。")


def _stage_menu(
    root: Path,
    stage_index: int,
    input_fn: Callable[[str], str],
    open_fn: Callable[[str], bool],
) -> None:
    page = 0
    page_size = 15
    while True:
        stages, _ = load_stages(root)
        stage = stages[stage_index]
        total_pages = max(1, (len(stage.tasks) + page_size - 1) // page_size)
        page = min(page, total_pages - 1)
        start = page * page_size
        visible_tasks = stage.tasks[start : start + page_size]

        done, total = progress(stage.tasks)
        print(f"\n=== {stage.name} ===")
        print(f"进度：{done}/{total} {progress_bar(done, total)}")
        print(f"第 {page + 1}/{total_pages} 页\n")
        if not visible_tasks:
            print("这个阶段还没有可识别的任务。")
        for number, task in enumerate(visible_tasks, start=1):
            marker = "x" if task.completed else " "
            print(f"{number:>2}. [{marker}] {task.title}")
        print("\n0. 返回")
        if page > 0:
            print("P. 上一页")
        if page + 1 < total_pages:
            print("N. 下一页")

        raw_choice = input_fn("请选择任务：").strip().lower()
        if raw_choice == "0":
            return
        if raw_choice == "p" and page > 0:
            page -= 1
            continue
        if raw_choice == "n" and page + 1 < total_pages:
            page += 1
            continue
        try:
            task_number = int(raw_choice)
        except ValueError:
            print("请输入任务编号或菜单选项。")
            continue
        if not 1 <= task_number <= len(visible_tasks):
            print("没有这个任务编号。")
            continue
        _task_action(visible_tasks[task_number - 1], input_fn, open_fn)


def run(
    root: Path,
    input_fn: Callable[[str], str] = input,
    open_fn: Callable[[str], bool] = webbrowser.open,
) -> int:
    try:
        while True:
            stages, warnings = load_stages(root)
            _print_main_menu(stages)
            for warning in warnings:
                print(f"提示：{warning}")
            choice = read_choice("\n请选择学习阶段：", 0, len(stages), input_fn)
            if choice == 0:
                print("已退出。")
                return 0
            _stage_menu(root, choice - 1, input_fn, open_fn)
    except KeyboardInterrupt:
        print("\n已退出。")
        return 0


if __name__ == "__main__":
    raise SystemExit(run(Path(__file__).resolve().parent))
