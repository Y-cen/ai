import tempfile
import unittest
from pathlib import Path

import learn


class LearnMarkdownTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_markdown(self, content: str, name: str = "清单.md") -> Path:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

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

    def test_load_stages_uses_learning_order_and_reports_missing_directories(self):
        stage_directories = [
            "01-python基础",
            "02-大模型基础",
            "03-rag",
            "04-agent",
        ]
        for directory in stage_directories:
            stage_path = self.root / directory
            stage_path.mkdir()
            (stage_path / "清单.md").write_text(
                f"- [ ] [{directory}](https://example.com)\n", encoding="utf-8"
            )

        stages, warnings = learn.load_stages(self.root)

        self.assertEqual(
            [stage.name for stage in stages],
            ["Python 基础", "大模型基础", "RAG", "Agent", "综合项目"],
        )
        self.assertEqual([len(stage.tasks) for stage in stages], [1, 1, 1, 1, 0])
        self.assertEqual(warnings, ["未找到学习目录：05-综合项目"])

    def test_toggle_task_only_changes_checkbox(self):
        path = self.write_markdown(
            "前言\n- [ ] [课程](https://example.com)\n结尾\n"
        )
        task = learn.parse_tasks(path)[0]

        learn.toggle_task(task)
        self.assertEqual(
            path.read_text(encoding="utf-8"),
            "前言\n- [x] [课程](https://example.com)\n结尾\n",
        )

        learn.toggle_task(learn.parse_tasks(path)[0])
        self.assertEqual(
            path.read_text(encoding="utf-8"),
            "前言\n- [ ] [课程](https://example.com)\n结尾\n",
        )


if __name__ == "__main__":
    unittest.main()
