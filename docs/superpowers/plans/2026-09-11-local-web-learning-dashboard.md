# Local Web Learning Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the default numeric terminal menu with a localhost browser dashboard that supports mouse navigation, task filtering, link opening, and Markdown-backed completion tracking.

**Architecture:** Extend `learn.py` with group metadata and validated task identifiers, then expose that data through a standard-library HTTP server in `web_app.py`. A dependency-free HTML/CSS/JavaScript client renders the dashboard and calls the local JSON API; the original terminal UI remains available behind `--terminal`.

**Tech Stack:** Python 3.11 standard library, HTML5, CSS, vanilla JavaScript, Windows batch

**Spec:** `docs/superpowers/specs/2026-09-11-local-web-learning-dashboard-design.md`

## Global Constraints

- Add no Python or browser third-party dependencies and use no CDN resources.
- Bind the HTTP server only to `127.0.0.1` and select an available port dynamically.
- Keep Markdown as the sole source of truth and change only a validated checkbox marker.
- Restrict writable task paths to the five configured learning directories.
- Keep `python learn.py --terminal` as the terminal fallback.
- Do not invent video part titles that cannot be verified from a public course page.

---

### Task 1: Web-facing Markdown model

**Files:**
- Modify: `learn.py`
- Modify: `tests/test_learn.py`

**Interfaces:**
- Produces: `Task(path, line_number, title, url, completed, group="未分组")`
- Produces: `task_id(task: Task, root: Path) -> str`
- Produces: `resolve_task(root: Path, identifier: str, expected_completed: bool) -> Task`
- Produces: `stages_payload(root: Path) -> dict[str, object]`

- [ ] **Step 1: Write failing tests for heading groups and payloads**

Add fixtures with two `##` headings and assert each parsed task receives the heading active at its line. Assert `stages_payload()` contains stage progress, file category, group, title, URL, completed state, and an identifier such as `01-python基础/checklist.md:4`.

```python
self.assertEqual([task.group for task in tasks], ["视频", "官方文档"])
self.assertEqual(payload["stages"][0]["tasks"][0]["id"],
                 "01-python基础/checklist.md:4")
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.test_learn.WebModelTests -v`

Expected: FAIL because group metadata and payload helpers do not exist.

- [ ] **Step 3: Implement heading parsing and JSON-ready payloads**

Track the latest `## ` heading while parsing. Convert paths to repository-relative POSIX form and line numbers to one-based display values in identifiers. Derive stage and total progress from the same loaded task objects.

```python
def task_id(task: Task, root: Path) -> str:
    return f"{task.path.relative_to(root).as_posix()}:{task.line_number + 1}"
```

- [ ] **Step 4: Write failing validation tests**

Test `resolve_task()` with a valid identifier, a traversal identifier (`../outside.md:1`), a non-learning path (`README.md:1`), an invalid line, and a stale expected state. Valid input returns the current task; each invalid input raises `ValueError` with a Chinese message.

- [ ] **Step 5: Run validation tests and verify RED**

Run: `python -m unittest tests.test_learn.WebModelTests -v`

Expected: payload tests pass; validation cases fail because `resolve_task()` is missing.

- [ ] **Step 6: Implement validated task resolution**

Split the identifier at the final colon, reject absolute paths and traversal, resolve the candidate, require it to be under one of `STAGE_CONFIG` directories, reload that exact line, and require its current completed state to equal `expected_completed`.

- [ ] **Step 7: Run the complete data-layer suite**

Run: `python -m unittest tests.test_learn -v`

Expected: all old and new data/terminal tests PASS.

- [ ] **Step 8: Commit**

```powershell
git add learn.py tests/test_learn.py
git commit -m "feat: expose validated learning task data"
```

---

### Task 2: Local HTTP API and static assets

**Files:**
- Create: `web_app.py`
- Create: `tests/test_web_app.py`
- Create: `web/index.html`
- Create: `web/styles.css`
- Create: `web/app.js`

**Interfaces:**
- Consumes: `stages_payload`, `resolve_task`, and `toggle_task` from Task 1
- Produces: `create_server(root: Path, port: int = 0) -> ThreadingHTTPServer`
- Produces: HTTP routes `GET /`, `GET /styles.css`, `GET /app.js`, `GET /api/stages`, `POST /api/tasks/toggle`, and `POST /api/shutdown`

- [ ] **Step 1: Write failing real-HTTP GET tests**

Start `create_server()` on port `0` in a daemon thread against a temporary five-stage repository. Use `urllib.request.urlopen` to assert `/api/stages` returns UTF-8 JSON, `/` returns HTML, and static assets have correct content types. Stop and close the server in test cleanup.

```python
with urlopen(f"{self.base_url}/api/stages") as response:
    payload = json.load(response)
self.assertEqual(payload["total"], 1)
```

- [ ] **Step 2: Run GET tests and verify RED**

Run: `python -m unittest tests.test_web_app.WebServerGetTests -v`

Expected: FAIL because `web_app.py` does not exist.

- [ ] **Step 3: Implement the server factory and safe GET routes**

Create a request-handler factory closed over `root` and the fixed `web/` asset directory. Serve only the three named static paths, add `Content-Type` with UTF-8 for text, set `Cache-Control: no-store` for API data, and return JSON 404 errors for unknown paths. Bind with `ThreadingHTTPServer(("127.0.0.1", port), Handler)`.

- [ ] **Step 4: Write failing POST and error tests**

Through real HTTP requests, verify a valid toggle updates a temporary Markdown checkbox and returns refreshed payload data. Verify stale state returns 409, traversal returns 400, invalid JSON returns 400, non-JSON content type returns 415, and a body larger than 16 KiB returns 413.

```python
body = json.dumps({"id": task_id, "completed": False}).encode()
request = Request(url, data=body,
                  headers={"Content-Type": "application/json"}, method="POST")
```

- [ ] **Step 5: Run POST tests and verify RED**

Run: `python -m unittest tests.test_web_app.WebServerPostTests -v`

Expected: GET tests pass and POST tests fail because mutation routes are missing.

- [ ] **Step 6: Implement bounded JSON handling and mutation routes**

Require `application/json`, parse numeric `Content-Length`, reject sizes above `16_384`, decode UTF-8 JSON objects only, validate exact `id: str` and `completed: bool` fields, resolve and toggle the task, then return the refreshed payload. Schedule shutdown on a separate daemon thread so `/api/shutdown` can send its response first.

- [ ] **Step 7: Run all server and regression tests**

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS.

- [ ] **Step 8: Commit**

```powershell
git add web_app.py web tests/test_web_app.py
git commit -m "feat: add localhost learning dashboard API"
```

---

### Task 3: Mouse-first dashboard client

**Files:**
- Modify: `web/index.html`
- Modify: `web/styles.css`
- Modify: `web/app.js`
- Modify: `tests/test_web_app.py`

**Interfaces:**
- Consumes: JSON payload from `GET /api/stages`
- Produces: stage navigation, total/stage progress, task cards, search, status filters, checkbox mutation, external-link buttons, and service shutdown control

- [ ] **Step 1: Add failing page contract tests**

Request the three assets and assert the rendered document exposes semantic controls with IDs `stage-nav`, `search-input`, `status-filter`, `task-groups`, `overall-progress`, `toast`, and `shutdown-button`. Assert the JavaScript references `/api/stages`, `/api/tasks/toggle`, and `/api/shutdown`; assert no `http://` or `https://` dependency appears in asset tags.

- [ ] **Step 2: Run page contract tests and verify RED**

Run: `python -m unittest tests.test_web_app.DashboardAssetTests -v`

Expected: FAIL because the initial assets do not yet contain the full dashboard contract.

- [ ] **Step 3: Implement semantic HTML and responsive CSS**

Build a two-column desktop layout with a sticky sidebar and a single-column narrow layout under `760px`. Use native buttons, labels, search input, select control, progress elements, and checkbox inputs. Include visible keyboard focus styles, disabled/loading states, empty results, and a non-blocking toast region.

- [ ] **Step 4: Implement client state and rendering**

Maintain one state object containing payload, selected stage ID, query, and status filter. Group visible tasks by `file` then `group`, compare search text case-insensitively, and rebuild only the affected dashboard content from the current state. Create DOM nodes with `textContent`; do not inject task titles with `innerHTML`.

- [ ] **Step 5: Implement checkbox, link, and shutdown actions**

Disable a checkbox while POSTing its identifier and old state. Replace local payload with the response only after success; on failure restore the checkbox and show the server's Chinese error. Render links with `target="_blank"` and `rel="noopener noreferrer"`. Require a native confirmation before calling the shutdown endpoint.

- [ ] **Step 6: Run asset, API, and regression tests**

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add web tests/test_web_app.py
git commit -m "feat: build mouse-first learning dashboard"
```

---

### Task 4: Default Web startup and terminal fallback

**Files:**
- Modify: `web_app.py`
- Modify: `learn.py`
- Modify: `start.bat`
- Modify: `README.md`
- Modify: `tests/test_web_app.py`

**Interfaces:**
- Produces: `serve(root: Path, open_browser: bool = True) -> int`
- Produces: `python learn.py` Web launch and `python learn.py --terminal` fallback

- [ ] **Step 1: Write failing launch tests**

Inject a fake browser opener into a one-shot server startup helper and assert the URL uses `http://127.0.0.1:<dynamic-port>/`. Patch terminal `run()` and assert `learn.main(["--terminal"])` selects it, while `learn.main([])` imports and selects Web serving.

- [ ] **Step 2: Run launch tests and verify RED**

Run: `python -m unittest tests.test_web_app.LaunchTests -v`

Expected: FAIL because command dispatch and `serve()` do not exist.

- [ ] **Step 3: Implement launch lifecycle and command dispatch**

Print the local URL, open it after the server is bound, run `serve_forever()`, handle `KeyboardInterrupt`, and always call `server_close()`. Add `main(argv: list[str] | None = None) -> int` in `learn.py`; accept only optional `--terminal` and use `argparse` for errors.

- [ ] **Step 4: Update the batch launcher and README**

Keep UTF-8 setup and Python launcher fallback in `start.bat`, but let its default `learn.py` invocation start Web mode. Document Web startup, browser behavior, local-only service, shutdown, and `python learn.py --terminal` fallback.

- [ ] **Step 5: Run launch and full tests**

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS.

Run: `python learn.py --terminal` and enter `0`.

Expected: the Chinese terminal menu renders and exits with status 0.

- [ ] **Step 6: Commit**

```powershell
git add learn.py web_app.py start.bat README.md tests/test_web_app.py
git commit -m "feat: launch learning dashboard from terminal"
```

---

### Task 5: Verified per-part course data and final QA

**Files:**
- Modify: `01-python基础/checklist.md`
- Modify: `05-综合项目/课程清单.md`
- Modify: `tests/test_learn.py`

**Interfaces:**
- Consumes: publicly visible Bilibili course-part metadata
- Produces: one checkbox per verified video part and non-duplicated project pointers

- [ ] **Step 1: Inventory course-level video tasks**

Search all learning Markdown files for Bilibili checkbox links without a `?p=` query. Classify Python video courses as needing verified per-part expansion and comprehensive-project entries as pointers to existing RAG/Agent project sections.

- [ ] **Step 2: Verify public part metadata**

Open each Python course page or its public metadata endpoint. Record the BV identifier, part number, and exact public title. If metadata is unavailable, keep a non-checkbox `课程入口：[...]` line and do not create guessed parts.

- [ ] **Step 3: Write a failing repository granularity test**

Add a test that scans files categorized as video lists and asserts every checkbox Bilibili URL contains a positive `p` query parameter. The test intentionally excludes non-checkbox `课程入口` lines and non-video project pointers.

```python
self.assertEqual(course_level_video_tasks, [],
                 "视频复选框必须指向具体分 P")
```

- [ ] **Step 4: Run the granularity test and verify RED**

Run: `python -m unittest tests.test_learn.RepositorySmokeTests -v`

Expected: FAIL listing the two current Python course-level checkbox URLs.

- [ ] **Step 5: Replace course-level tasks with verified entries**

In `01-python基础/checklist.md`, preserve each course URL as a non-checkbox course entry and add one checkbox line per verified part using `?p=N`. In `05-综合项目/课程清单.md`, replace duplicate whole-course checkboxes with plain pointers to the existing RAG and Agent project-section Markdown files; keep genuinely standalone documentation projects as checkboxes.

- [ ] **Step 6: Run complete automated verification**

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS and no test changes a repository Markdown checkbox.

Run: `python -m py_compile learn.py web_app.py tests/test_learn.py tests/test_web_app.py`

Expected: exit status 0 with no output.

- [ ] **Step 7: Perform browser smoke QA**

Start `python learn.py`, open the printed localhost URL, and verify stage switching, search, all three status filters, one temporary checkbox round-trip (toggle and toggle back), one external resource link, responsive layout, and shutdown. Confirm `git diff` shows no unintended progress change after the round-trip.

- [ ] **Step 8: Commit**

```powershell
git add 01-python基础/checklist.md 05-综合项目/课程清单.md tests/test_learn.py
git commit -m "content: split video courses into verified parts"
```
