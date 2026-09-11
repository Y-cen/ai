from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


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
