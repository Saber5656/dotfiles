"""COMMON contract regressions and executable examples, not Saihai runtime tests."""

import os
import json
import hashlib
import copy
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
POLICY = (ROOT / "COMMON-AGENTS.md").read_text(encoding="utf-8")


class UsageFirstContractTests(unittest.TestCase):
    """Document-contract checks; executable historical Git examples remain below."""

    def test_real_delivery_not_issue_exhaustion_is_the_objective(self):
        for clause in (
            "実タスクをハーネスで受け付け",
            "全 Issue の完遂やハーネス全体の完成を通常作業の前提・目的にしない",
            "Issue と PR の一対一対応は必須にしない",
            "関連する複数 Issue を一つの機能 PR にまとめてよい",
        ):
            self.assertIn(clause, POLICY)

    def test_review_is_limited_and_never_duplicated(self):
        for clause in (
            "review を必要とするのは権限拡大・認証/secret・データ消失に関わる変更だけ",
            "その範囲に適した担当で一回",
            "内部 review と PR review を重複させない",
            "初回→妥当な指摘の修正→元指摘の解消確認→merge",
            "修正後の全面再 review・review-of-review・再帰 review を行わない",
            "軽微な改善は後続 Issue に移してよい",
            "未解決の権限・認証/secret・データ消失リスクを軽微として除外しない",
        ):
            self.assertIn(clause, POLICY)

    def test_bot_switch_requires_quota(self):
        self.assertIn("quota に到達したときだけ ChatGPT review へ切り替える", POLICY)
        self.assertIn("通常併用・二重 trigger はしない", POLICY)
        self.assertIn("quota 以外の障害を切替理由にせず", POLICY)

    def test_full_validation_is_per_integrated_change(self):
        for clause in (
            "修正中は影響範囲の focused validation",
            "full validation は統合変更一式に対して一回",
            "個別 commit ごとの full validation は要求しない",
            "影響を受けない検証結果は再利用",
            "影響した範囲だけを再検証",
        ):
            self.assertIn(clause, POLICY)

    def test_ci_drives_autonomous_pr_merge_without_bypass(self):
        for clause in (
            "必要 CI が成功したら、通常 review・CodeRabbit・追加承認を待たず自律的に PR を merge",
            "指定 head を条件に通常の GitHub PR merge",
            "現在のサーバー側保護を bypass せず",
            "必要 CI の failed・missing・pending・unknown を成功と扱わない",
            "default branch（main）への直 push は禁止",
            "force push は禁止",
        ):
            self.assertIn(clause, POLICY)

    def test_conflicts_preserve_intent_and_only_requirements_need_questions(self):
        for clause in (
            "競合は双方の意図を保持して自動解消",
            "解消箇所と影響範囲を検証",
            "ours/theirs で一方を無条件に捨てない",
            "質問は両立できない要件選択が必要な場合だけ",
        ):
            self.assertIn(clause, POLICY)

    def test_task_owned_cleanliness_and_excluded_changes_are_preserved(self):
        for clause in (
            "task-owned な未コミット差分がないこと",
            "task-owned な未コミット差分を残さない",
            "着手前に task-owned の範囲",
            "path・hunk", "staged・unstaged・untracked",
            "開始時と終了時", "内容・mode・diff identity",
            "task-owned の変更を無関係として除外してはならない",
            "無関係な変更を commit・stash・reset・削除しない",
            "確認できない他者差分は取り込まず保持",
        ):
            self.assertIn(clause, POLICY)

    def test_records_are_lightweight_and_checkpoint_is_finite(self):
        for clause in (
            "目的・主要判断・検証結果・制限・成果物リンクだけ",
            "記録 commit に review や source の full validation を要求しない",
            "checkpoint 自身の SHA は同じ hashed content へ追記しない",
            "自身の SHA 記録だけを目的とする追加 commit を作らない",
            "source commit を Vault checkpoint の親とみなしてはならない",
            "既存の checkpoint ID・bounded evidence envelope・過去の review 証跡は保持",
            "過去の厳密形式の作成や review を新規記録の必須条件にはしない",
        ):
            self.assertIn(clause, POLICY)

    def test_retry_budget_is_consecutive_same_cause_only(self):
        self.assertIn("同じ未解決原因への連続 retry だけを数え", POLICY)
        self.assertIn("過去の文書修正・環境復旧・累積 review 回数を合算して停止しない", POLICY)
        self.assertIn("連続 retry の回数を偽ってリセットしない", POLICY)

    def test_bootstrap_does_not_gate_normal_work_on_review_facade(self):
        self.assertIn("environ={}", POLICY)
        self.assertIn("require_catalog=True", POLICY)
        self.assertIn("scripts/saihai.py startup", POLICY)
        self.assertIn("通常作業は role 定義や正式 review facade の復旧を待たない", POLICY)
        self.assertIn("別 Vault の作成や catalog の付け替えで迂回しない", POLICY)

    def test_completion_and_safety_are_not_false_success(self):
        for stage in ("artifact", "validation", "review", "evidence", "commit", "publication", "merge", "release"):
            self.assertEqual(1, sum(line.startswith("| `" + stage + "` |") for line in POLICY.splitlines()))
        self.assertIn("通常は not_required", POLICY)
        self.assertIn("merge ≠ release", POLICY)
        self.assertIn("既存の成果物・設計ドキュメント・ファイルは、ユーザーの明示的な依頼なしに削除しない", POLICY)
        self.assertIn("鍵・シークレット・認証情報の生成・設定・登録はユーザーが手動で行う", POLICY)

    def test_obsolete_global_gates_are_not_active(self):
        for old in (
            "1 task を 1 process、かつ 1 Issue",
            "指摘が解消されレビューを通過した場合に限り",
            "完了前の role review、evidence 記録を省略しない",
            "one-time gate-state digest を mutation の atomic precondition",
            "必要な再 review を要求",
            "検証・独立レビューを省略する例外ではない",
        ):
            self.assertNotIn(old, POLICY)


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

    def checkpoint_fixture(self, change=None, omit=False):
        """Synthetic review receipts exercise storage, never certify a real review."""
        self.source_temp = tempfile.TemporaryDirectory(prefix="dotfiles-source-")
        self.addCleanup(self.source_temp.cleanup)
        self.source_repo = Path(self.source_temp.name)
        self.source_git("init", "-q")
        (self.source_repo / "source.md").write_text("accepted artifact\n")
        self.source_git("add", "source.md")
        self.source_git("commit", "-qm", "Source result")
        source_sha = self.source_git("rev-parse", "HEAD").decode().strip()
        self.write("vault.md", "Canonical fixture vault\n")
        self.git("add", "vault.md")
        self.git("commit", "-qm", "Vault baseline")
        vault_base = self.git("rev-parse", "HEAD").decode().strip()
        self.assertNotEqual(source_sha, vault_base)
        checkpoint_id = "fixture-task-12-receipt-1"
        receipt = {
            "task_id": "fixture-task-12",
            "repository": "fixture-source",
            "source_commit": source_sha,
            "checkpoint_id": checkpoint_id,
            "source_tree": self.source_git("rev-parse", "HEAD^{tree}").decode().strip(),
            "checkpoint_evidence": "Read the exact Evidence-Envelope JSON from the commit message; verify against the trusted handoff.",
        }
        self.write("task-record.json", json.dumps(receipt, sort_keys=True) + "\n")
        self.write("raw-evidence.txt", "Synthetic canonical fixture log and review provenance\n")
        self.git("add", "task-record.json", "raw-evidence.txt")
        intended_tree = self.git("write-tree").decode().strip()
        diff_digest = hashlib.sha256(self.git("diff", "--cached", "--binary", "--full-index")).hexdigest()
        # This trusted expected receipt stands for the caller's fixed handoff;
        # read-back must not use message-supplied identities as its own authority.
        expected = {
            "checkpoint_id": checkpoint_id, "task_id": receipt["task_id"],
            "repository": "fixture-vault", "base": vault_base,
            "source_repository": receipt["repository"],
            "source_commit": source_sha, "source_tree": receipt["source_tree"],
            "tree": intended_tree, "diff_sha256": diff_digest,
            "owned_paths": ["raw-evidence.txt", "task-record.json"],
            "validation": [{"command": "fixture focused/full", "start": "2026-09-05T00:00:00Z", "end": "2026-09-05T00:00:01Z", "exit": 0, "tests": 1, "skipped": 0, "result": "success"}],
            "reviews": [{"role": "fixture-independent-reviewer", "version": "fixture-v1", "result": "accepting_terminal_success", "provenance": "raw-evidence.txt"}],
            "references": [{"path": "raw-evidence.txt", "sha256": hashlib.sha256((self.repo / "raw-evidence.txt").read_bytes()).hexdigest()}],
        }
        actual = copy.deepcopy(expected)
        if change:
            change(actual)
        message = "Evidence checkpoint\n\nCheckpoint-ID: " + checkpoint_id
        if not omit:
            message += "\nEvidence-Envelope: " + json.dumps(actual, sort_keys=True)
        self.git("commit", "-qm", message)
        return expected, receipt

    def source_git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=self.source_repo, env=self.env, stderr=subprocess.STDOUT
        )

    def read_checkpoint(self, expected):
        """Test-only conformance procedure, not a production completion gate."""
        candidates = []
        for sha in self.git("rev-list", "--all").decode().splitlines():
            message = self.git("show", "-s", "--format=%B", sha).decode()
            ids = [line.removeprefix("Checkpoint-ID: ") for line in message.splitlines() if line.startswith("Checkpoint-ID: ")]
            if expected["checkpoint_id"] not in ids:
                continue
            self.assertEqual([expected["checkpoint_id"]], ids)
            envelopes = [line.removeprefix("Evidence-Envelope: ") for line in message.splitlines() if line.startswith("Evidence-Envelope: ")]
            self.assertEqual(1, len(envelopes))
            self.assertLessEqual(len(envelopes[0].encode()), 16 * 1024)

            def unique_keys(pairs):
                result = {}
                for key, value in pairs:
                    self.assertNotIn(key, result)
                    result[key] = value
                return result

            envelope = json.loads(envelopes[0], object_pairs_hook=unique_keys)
            self.assertEqual(expected, envelope)
            self.assertTrue(envelope["validation"])
            self.assertTrue(envelope["reviews"])
            for validation in envelope["validation"]:
                self.assertEqual("success", validation["result"])
                self.assertEqual(0, validation["exit"])
                self.assertGreater(validation["tests"], 0)
                self.assertEqual(0, validation["skipped"])
            for review in envelope["reviews"]:
                self.assertEqual("accepting_terminal_success", review["result"])
            self.assertEqual(expected["base"], self.git("rev-parse", sha + "^").decode().strip())
            source_receipt = json.loads(self.git("show", sha + ":task-record.json"))
            self.assertEqual(expected["source_repository"], source_receipt["repository"])
            self.assertEqual(expected["source_commit"], source_receipt["source_commit"])
            self.assertEqual(expected["source_tree"], source_receipt["source_tree"])
            self.assertEqual(expected["source_tree"], self.source_git("rev-parse", expected["source_commit"] + "^{tree}").decode().strip())
            self.assertEqual(expected["tree"], self.git("rev-parse", sha + "^{tree}").decode().strip())
            self.assertEqual(expected["diff_sha256"], hashlib.sha256(self.git("diff", "--binary", "--full-index", expected["base"], sha)).hexdigest())
            self.assertEqual(expected["owned_paths"], self.git("diff", "--name-only", expected["base"], sha).decode().splitlines())
            for ref in envelope["references"]:
                self.assertEqual(ref["sha256"], hashlib.sha256(self.git("show", sha + ":" + ref["path"])).hexdigest())
            candidates.append(sha)
        self.assertEqual(1, len(candidates))
        return candidates[0]

    def test_evidence_checkpoint_readback_and_resume_need_no_self_sha_commit(self):
        expected, receipt = self.checkpoint_fixture()
        count = self.git("rev-list", "--count", "HEAD")

        for _ in range(2):
            checkpoint_sha = self.read_checkpoint(expected)
            data = self.git("show", checkpoint_sha + ":task-record.json")
            self.assertEqual(receipt, json.loads(data))
            self.assertNotIn(checkpoint_sha.encode(), data)
            self.assertEqual(count, self.git("rev-list", "--count", "HEAD"))
            self.assertEqual(b"", self.git("status", "--porcelain"))
        self.assertEqual(b"2\n", count)

    def test_checkpoint_rejects_tampered_review_receipt(self):
        expected, _ = self.checkpoint_fixture(lambda e: e["reviews"][0].update(version="tampered"))
        with self.assertRaises(AssertionError):
            self.read_checkpoint(expected)

    def test_checkpoint_rejects_missing_envelope(self):
        expected, _ = self.checkpoint_fixture(omit=True)
        with self.assertRaises(AssertionError):
            self.read_checkpoint(expected)

    def test_checkpoint_rejects_duplicate_exact_id(self):
        expected, _ = self.checkpoint_fixture()
        message = self.git("show", "-s", "--format=%B", "HEAD").decode()
        # A second valid candidate with the same parent and tree but different
        # message is reachable; uniqueness must not depend on latest-first grep.
        other = self.git("commit-tree", expected["tree"], "-p", expected["base"], "-m", "Duplicate\n" + message).decode().strip()
        self.git("update-ref", "refs/heads/duplicate-fixture", other)
        with self.assertRaises(AssertionError):
            self.read_checkpoint(expected)

    def test_checkpoint_rejects_pending_review(self):
        expected, _ = self.checkpoint_fixture(lambda e: e["reviews"][0].update(result="pending"))
        with self.assertRaises(AssertionError):
            self.read_checkpoint(expected)

    def test_checkpoint_rejects_failed_validation_even_if_handoff_agrees(self):
        expected, _ = self.checkpoint_fixture(lambda e: e["validation"][0].update(result="failed", exit=1))
        expected["validation"][0].update(result="failed", exit=1)
        with self.assertRaises(AssertionError):
            self.read_checkpoint(expected)

    def test_checkpoint_rejects_unknown_review_even_if_handoff_agrees(self):
        expected, _ = self.checkpoint_fixture(lambda e: e["reviews"][0].update(result="unknown"))
        expected["reviews"][0].update(result="unknown")
        with self.assertRaises(AssertionError):
            self.read_checkpoint(expected)

    def test_checkpoint_rejects_missing_review_even_if_handoff_agrees(self):
        expected, _ = self.checkpoint_fixture(lambda e: e.update(reviews=[]))
        expected["reviews"] = []
        with self.assertRaises(AssertionError):
            self.read_checkpoint(expected)


if __name__ == "__main__":
    unittest.main()
