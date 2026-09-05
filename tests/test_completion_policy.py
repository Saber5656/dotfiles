"""COMMON contract regressions and executable examples, not Saihai runtime tests."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY = (ROOT / "COMMON-AGENTS.md").read_text(encoding="utf-8")


class OwnershipContractTests(unittest.TestCase):
    def test_cleanliness_is_scoped_at_both_existing_entrypoints(self):
        self.assertNotIn("完了を宣言する前に、未コミット差分がないこと", POLICY)
        self.assertNotIn("作業終了時に未コミット差分を残さない", POLICY)
        self.assertIn("task-owned な未コミット差分がないこと", POLICY)
        self.assertIn("task-owned な未コミット差分を残さない", POLICY)

    def test_ownership_must_be_fixed_before_changes_and_rechecked(self):
        for clause in (
            "着手前に task-owned の範囲",
            "path・hunk",
            "staged・unstaged・untracked",
            "開始時と終了時",
            "内容・mode・diff identity",
            "所有者が不明",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, POLICY)

    def test_exclusion_cannot_hide_task_changes_or_discard_others_work(self):
        for clause in (
            "task-owned の変更を無関係として除外してはならない",
            "無関係な変更を commit・stash・reset・削除しない",
            "無関係な dirty が残っていても",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, POLICY)

    def test_unsafe_ownership_conditions_require_stopping_commit_and_completion(self):
        self.assertIn(
            "所有者が不明、同じ hunk を安全に分離できない、"
            "または除外した変更に drift がある場合は、"
            "影響する commit・完了判定を停止して所有者との調整へ戻す。",
            POLICY,
        )

    def test_existing_validation_and_authority_gates_remain(self):
        for clause in (
            "focused validation と repository 所定の full validation",
            "作業を担当していない別のエージェント",
            "force push は禁止",
            "default branch（main）への直 push は禁止",
            "merge ≠ release",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, POLICY)


class IsolatedGitExample(unittest.TestCase):
    """Exercise the documented Git procedure only in disposable repositories."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dotfiles-policy-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.env = {
            "PATH": os.environ["PATH"],
            "HOME": self.temp.name,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": "Policy Test",
            "GIT_AUTHOR_EMAIL": "policy@example.invalid",
            "GIT_COMMITTER_NAME": "Policy Test",
            "GIT_COMMITTER_EMAIL": "policy@example.invalid",
        }
        self.git("init", "-q")

    def git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=self.repo, env=self.env, stderr=subprocess.STDOUT
        )

    def write(self, name, text):
        (self.repo / name).write_text(text, encoding="utf-8")

    def test_task_commit_preserves_unrelated_staged_unstaged_and_untracked(self):
        self.write("task.md", "before\n")
        self.write("unrelated.md", "original\n")
        self.git("add", "task.md", "unrelated.md")
        self.git("commit", "-qm", "Fixture baseline")
        self.write("unrelated.md", "staged edit\n")
        self.git("add", "unrelated.md")
        self.write("unrelated.md", "staged edit\nunstaged edit\n")
        self.write("untracked.md", "other owner's draft\n")

        def excluded_snapshot():
            return (
                self.git("diff", "--binary", "--", "unrelated.md"),
                self.git("diff", "--cached", "--binary", "--", "unrelated.md"),
                self.git("ls-files", "--stage", "--", "unrelated.md"),
                (self.repo / "unrelated.md").read_bytes(),
                (self.repo / "untracked.md").read_bytes(),
                (self.repo / "unrelated.md").stat().st_mode,
                (self.repo / "untracked.md").stat().st_mode,
            )

        before = excluded_snapshot()
        self.write("task.md", "accepted task result\n")
        self.git("commit", "--only", "-qm", "Task-owned change", "--", "task.md")
        self.assertEqual(before, excluded_snapshot())
        self.assertEqual(b"", self.git("status", "--porcelain", "--", "task.md"))
        self.assertEqual(
            b"MM unrelated.md\n?? untracked.md\n", self.git("status", "--porcelain")
        )
        self.assertEqual(
            b"task.md\n", self.git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD")
        )


if __name__ == "__main__":
    unittest.main()
