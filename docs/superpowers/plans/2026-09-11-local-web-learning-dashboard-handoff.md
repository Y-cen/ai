# 本地 Web 学习面板交接说明

## 当前状态

仓库已经有一个可用的数字菜单终端版：

- `learn.py`：读取 Markdown 清单、统计进度、切换复选框、打开链接。
- `start.bat`：目前启动终端版，并处理 Windows 中文编码。
- `tests/test_learn.py`：现有 8 项单元与冒烟测试。

终端版已提交，但本地分支尚有提交未推送到 GitHub。接下来的任务不是重写数据层，而是在其上增加可用鼠标操作的本地 Web 面板。

## 改造目标

运行 `start.bat` 后启动只监听 `127.0.0.1` 的本地 HTTP 服务，并自动打开默认浏览器。页面需要支持：

- 鼠标选择五个学习阶段。
- 查看总体和分阶段进度。
- 按清单与二级标题分组浏览任务。
- 搜索任务并筛选全部、未完成、已完成。
- 点击复选框修改完成状态，并准确写回原 Markdown。
- 点击资源按钮在新标签页打开链接。
- 从页面停止本地服务。

保留 `python learn.py --terminal` 作为终端备用入口。不得引入第三方 Python 包、前端框架或 CDN。

## 计划执行顺序

完整逐步计划见：

`docs/superpowers/plans/2026-09-11-local-web-learning-dashboard.md`

建议严格按以下五个任务执行，每个任务采用测试先行并独立提交：

1. 扩展 Markdown 数据模型：解析 `##` 分组，生成任务标识，验证任务路径与旧状态。
2. 新建 `web_app.py`：实现静态资源服务、阶段数据 API、任务切换 API 和关闭 API。
3. 新建 `web/` 页面：使用原生 HTML、CSS、JavaScript 实现鼠标交互、搜索、筛选和进度刷新。
4. 修改启动入口：`start.bat` 默认打开 Web 面板，`--terminal` 保留原界面。
5. 整理视频数据：将可确认的课程拆成分 P，移除整套课程作为单个勾选任务造成的重复进度。

## 关键安全约束

- HTTP 服务只能绑定 `127.0.0.1`，端口传 `0` 让系统动态选择。
- 修改接口只接受 JSON，并限制请求体最大为 16 KiB。
- 任务路径必须位于五个配置的学习目录内，拒绝绝对路径、`..` 穿越和其他仓库文件。
- 写回前重新读取目标行并核对客户端旧状态，过期状态返回冲突，不能改错任务。
- 前端使用 `textContent` 渲染任务标题，不能把 Markdown 内容直接交给 `innerHTML`。
- 视频分 P 标题必须来自可核实的公开课程页面；不能猜测或虚构。

## 接手步骤

```powershell
git clone https://github.com/Y-cen/ai.git
cd ai
git pull
python -m unittest discover -s tests -v
```

确认基线测试通过后，阅读以下两个文件：

1. `docs/superpowers/specs/2026-09-11-local-web-learning-dashboard-design.md`
2. `docs/superpowers/plans/2026-09-11-local-web-learning-dashboard.md`

然后从实现计划 Task 1 开始执行。

## 验证命令

每个任务完成后运行：

```powershell
python -m unittest discover -s tests -v
```

最终再运行：

```powershell
python -m py_compile learn.py web_app.py tests/test_learn.py tests/test_web_app.py
python learn.py --terminal
```

Web 版完成后运行 `start.bat`，在浏览器中人工验证阶段切换、搜索、筛选、勾选、打开链接和关闭服务。

## 完成标准

- 全部自动测试通过。
- `start.bat` 能自动打开本地 Web 面板。
- 鼠标交互无需输入数字菜单。
- 勾选状态准确写回 Markdown。
- 视频任务按可验证的分 P 展示。
- 终端备用入口仍可使用。
