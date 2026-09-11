# Terminal Learning Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dependency-free Chinese terminal interface for browsing the five learning stages, tracking progress, toggling Markdown tasks, and opening course links.

**Architecture:** A single `learn.py` module owns the small data model, Markdown parser, safe checkbox update, progress rendering, and menu loop. Existing Markdown files remain the source of truth; tests create temporary Markdown fixtures so real progress is never changed.

**Tech Stack:** Python 3 standard library (`dataclasses`, `pathlib`, `re`, `webbrowser`, `unittest`), Windows batch launcher

**Spec:** `docs/superpowers/specs/2026-09-11-terminal-learning-entry-design.md`

## Global Constraints

- Do not add third-party dependencies.
- Keep progress in the existing Markdown `- [ ]` and `- [x]` checkboxes.
- Preserve all non-target Markdown content when toggling a task.
- All terminal prompts and recoverable error messages are in Chinese.
- Support normal menu exit and `Ctrl+C`.

---

### Task 1: Markdown task model, discovery, and mutation

**Files:**
- Create: `learn.py`
- Create: `tests/test_learn.py`

**Interfaces:**
- Produces: `Task(path: Path, line_number: int, title: str, url: str | None, completed: bool)`
- Produces: `Stage(name: str, directory: Path, tasks: list[Task])`
- Produces: `parse_tasks(path: Path) -> list[Task]`
- Produces: `load_stages(root: Path) -> tuple[list[Stage], list[str]]`
- Produces: `toggle_task(task: Task) -> None`
- Produces: `progress(tasks: list[Task]) -> tuple[int, int]`

- [ ] **Step 1: Write failing parser and progress tests**

Create `tests/test_learn.py` with a temporary UTF-8 Markdown file containing headings, a linked open task, a linked completed task, and ordinary text. Assert that `parse_tasks()` returns two correctly populated `Task` objects and that `progress()` returns `(1, 2)`.

```python
def test_parse_tasks_and_progress(self):
    path = self.write_markdown(
        "# 清单\n\n- [ ] [课程 A](https://example.com/a)\n"
        "说明文字\n- [x] [课程 B](https://example.com/b)\n"
    )
    tasks = learn.parse_tasks(path)
    self.assertEqual([task.title for task in tasks], ["课程 A", "课程 B"])
    self.assertEqual([task.completed for task in tasks], [False, True])
    self.assertEqual(tasks[0].url, "https://example.com/a")
    self.assertEqual(learn.progress(tasks), (1, 2))
```

- [ ] **Step 2: Run the parser test and verify it fails**

Run: `python -m unittest tests.test_learn.LearnMarkdownTests.test_parse_tasks_and_progress -v`

Expected: FAIL because `learn.py` or `parse_tasks` does not exist.

- [ ] **Step 3: Implement the data model, parser, and progress function**

In `learn.py`, define frozen `Task` and mutable `Stage` dataclasses. Use one anchored regular expression to accept both lowercase and uppercase completed markers, capture the visible link title and URL when present, and fall back to plain task text when a checkbox has no link. Read files with `encoding="utf-8"` and retain zero-based line numbers for exact mutation.

```python
TASK_PATTERN = re.compile(r"^\s*-\s*\[([ xX])\]\s*(.*)$")
LINK_PATTERN = re.compile(r"^\[([^]]+)\]\(([^)]+)\)")

def progress(tasks: list[Task]) -> tuple[int, int]:
    return sum(task.completed for task in tasks), len(tasks)
```

- [ ] **Step 4: Add failing discovery and toggle tests**

Create five stage directories inside a temporary root, put Markdown tasks in one of them, and assert that `load_stages()` returns stages in the configured learning order. Add a test that calls `toggle_task()` twice and verifies the exact file changes from `- [ ]` to `- [x]` and back while surrounding text remains byte-for-byte equivalent after decoding.

```python
def test_toggle_task_only_changes_checkbox(self):
    path = self.write_markdown("前言\n- [ ] [课程](https://example.com)\n结尾\n")
    task = learn.parse_tasks(path)[0]
    learn.toggle_task(task)
    self.assertEqual(path.read_text(encoding="utf-8"),
                     "前言\n- [x] [课程](https://example.com)\n结尾\n")
```

- [ ] **Step 5: Run the new tests and verify they fail**

Run: `python -m unittest tests.test_learn -v`

Expected: parser test passes; discovery/toggle tests fail because the functions are missing.

- [ ] **Step 6: Implement ordered discovery and safe checkbox mutation**

Define the five directory/name pairs as a constant. `load_stages()` scans `*.md` files in each directory in filename order, skips unreadable files while appending a Chinese warning, and always returns all five stages. `toggle_task()` reloads the current file, validates that the stored line is still a task, changes only the character inside its checkbox, then writes UTF-8 with the original newline content preserved.

- [ ] **Step 7: Run Task 1 tests**

Run: `python -m unittest tests.test_learn -v`

Expected: all Task 1 tests PASS.

- [ ] **Step 8: Commit Task 1**

```powershell
git add learn.py tests/test_learn.py
git commit -m "feat: parse and update learning tasks"
```

---

### Task 2: Terminal menus and browser actions

**Files:**
- Modify: `learn.py`
- Modify: `tests/test_learn.py`

**Interfaces:**
- Consumes: `Stage`, `Task`, `load_stages`, `toggle_task`, and `progress` from Task 1
- Produces: `progress_bar(done: int, total: int, width: int = 20) -> str`
- Produces: `read_choice(prompt: str, minimum: int, maximum: int) -> int`
- Produces: `run(root: Path, input_fn: Callable[[str], str] = input, open_fn: Callable[[str], bool] = webbrowser.open) -> int`

- [ ] **Step 1: Write failing rendering and input-validation tests**

Test zero-total and partial progress bars. Inject an iterator-backed input function that first returns text, then an out-of-range number, then a valid number; capture stdout with `redirect_stdout` and assert `read_choice()` returns the valid value and prints Chinese retry messages.

```python
def test_progress_bar(self):
    self.assertEqual(learn.progress_bar(0, 0, 10), "[----------] 0%")
    self.assertEqual(learn.progress_bar(1, 4, 10), "[##--------] 25%")
```

- [ ] **Step 2: Run rendering tests and verify they fail**

Run: `python -m unittest tests.test_learn.TerminalUiTests -v`

Expected: FAIL because the terminal UI helpers are missing.

- [ ] **Step 3: Implement progress rendering and reusable choice input**

Render an ASCII progress bar so it remains readable in common Windows terminals. Make `read_choice()` accept an injected input callable, catch non-integer values, enforce the inclusive range, and continue prompting without recursion.

- [ ] **Step 4: Write failing menu-flow tests**

Build a temporary repository with one linked task. Feed choices that enter stage 1, select task 1, toggle it, return, and exit; assert the file becomes completed and `run()` returns `0`. In a second test inject a fake browser function, choose the open-link action, and assert it receives the task URL exactly once.

- [ ] **Step 5: Run menu-flow tests and verify they fail**

Run: `python -m unittest tests.test_learn.TerminalFlowTests -v`

Expected: FAIL because `run()` and the menus do not exist.

- [ ] **Step 6: Implement the main and stage menu loops**

The main menu reloads stages each time, prints global progress and one numbered row per stage, and accepts `0` to exit. The stage menu paginates long task lists in fixed pages of 15; selecting a task opens a compact action menu with toggle, open link when available, and return. After a mutation, reload from disk before repainting. Catch `KeyboardInterrupt` at the public entry point, print `\n已退出。`, and return `0`.

- [ ] **Step 7: Run all unit tests**

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS with no real Markdown learning file modified.

- [ ] **Step 8: Commit Task 2**

```powershell
git add learn.py tests/test_learn.py
git commit -m "feat: add interactive terminal learning menus"
```

---

### Task 3: Windows launcher, documentation, and repository smoke test

**Files:**
- Create: `start.bat`
- Modify: `README.md`
- Modify: `tests/test_learn.py`

**Interfaces:**
- Consumes: `learn.py` command-line entry point from Task 2
- Produces: `start.bat` launcher that works regardless of the caller's current directory

- [ ] **Step 1: Add a repository discovery smoke test**

Resolve the repository root relative to the test file, call `load_stages(root)`, and assert the five expected stage names are present and the total task count is greater than zero. This test reads but never writes repository Markdown files.

```python
def test_repository_has_five_populated_stages(self):
    root = Path(__file__).resolve().parents[1]
    stages, warnings = learn.load_stages(root)
    self.assertEqual(len(stages), 5)
    self.assertGreater(sum(len(stage.tasks) for stage in stages), 0)
    self.assertEqual(warnings, [])
```

- [ ] **Step 2: Run the smoke test**

Run: `python -m unittest tests.test_learn.RepositorySmokeTests -v`

Expected: PASS if discovery matches the real repository; otherwise fix only the discovery configuration and rerun.

- [ ] **Step 3: Add the Windows launcher**

Create `start.bat` using `%~dp0` so it starts the root script even when launched from another directory. Prefer the Python launcher when present and fall back to `python`.

```bat
@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (py -3 learn.py) else (python learn.py)
```

- [ ] **Step 4: Document both launch methods**

Add a `## 终端学习入口` section to `README.md` showing `python learn.py` and `start.bat`, followed by four concise bullets covering progress display, task browsing, checkbox updates, and browser opening.

- [ ] **Step 5: Run full verification**

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS.

Run: `cmd /c "echo 0|start.bat"`

Expected: the main menu renders all five stages and exits with status 0.

Run: `git diff --check` and then `git status --short`.

Expected: no whitespace errors; only `start.bat`, `README.md`, and the planned test change remain uncommitted.

- [ ] **Step 6: Commit Task 3**

```powershell
git add start.bat README.md tests/test_learn.py
git commit -m "docs: add terminal launcher instructions"
```

- [ ] **Step 7: Verify final repository state**

Run: `python -m unittest discover -s tests -v; git status --short --branch`

Expected: all tests PASS and the working tree is clean on `main`.
