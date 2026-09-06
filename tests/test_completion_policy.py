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


class CompletionStateContractTests(unittest.TestCase):
    def test_every_completion_stage_has_its_own_evidence_condition(self):
        rows = {
            "artifact": "承認済み scope の全成果物と受け入れ条件",
            "validation": "対象 identity に一致する focused/full validation",
            "review": "対象 identity に一致する必須の独立 review",
            "evidence": "canonical Vault への耐久保存と read-back",
            "commit": "task-owned 差分と immutable commit の一致",
            "publication": "remote head の一致と必要な PR の実作成",
            "merge": "有効な merge gate と実 merge SHA の統合後検証",
            "release": "別途許可された release gate と配布先の実結果",
        }
        for stage, evidence in rows.items():
            with self.subTest(stage=stage):
                matches = [line for line in POLICY.splitlines() if line.startswith("| `" + stage + "` |")]
                self.assertEqual(1, len(matches))
                self.assertIn(evidence, matches[0])

    def test_pending_review_or_evidence_blocks_parent_completion(self):
        for clause in (
            "必須段階の一つでも pending・failed・unknown なら task complete にしない",
            "review 待ち・evidence 保存待ちを artifact 完成で代替しない",
            "PR 作成済みを merge 済み、merge 済みを release 済みと扱わない",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, POLICY)

    def test_not_required_needs_scope_and_no_waiver_inference(self):
        self.assertIn("not_required は承認済み scope と適用 policy の根拠", POLICY)
        self.assertIn("必須 gate を not_required に変更してはならない", POLICY)
        self.assertIn("後工程を省略する許可や未達要件の除外を暗黙に導かない", POLICY)

    def test_review_only_transport_terminal_is_not_review_or_parent_success(self):
        for clause in (
            "review-only の返却処理の終端と、review 判定の成功と、依頼元 task の完了は別",
            "非成功 verdict・failed・unknown・未解決の blocking/必須 finding を review 成功へ変換しない",
            "返却証跡の保存・必須指摘の対応・残りの完了条件は依頼元が担う",
            "その review-only handoff 自体に追加の role review を要求せず",
            "reviewer が実装・修正まで行った場合はこの例外の対象外",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, POLICY)

    def test_review_success_allows_only_explicitly_nonblocking_notes(self):
        for clause in (
            "policy 定義の accepting terminal",
            "明示的な nonblocking notes だけであれば review 成功を維持する",
            "必須 finding を自己判断で nonblocking に格下げしてはならない",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, POLICY)

    def test_review_examples_distinguish_notes_and_required_failures(self):
        cases = {
            "accepting + nonblocking notes": "success",
            "accepting + unresolved mandatory finding": "不通過",
            "accepting + unresolved blocking finding": "不通過",
            "failed": "不通過",
            "unknown": "不通過",
            "non_accepting verdict": "不通過",
        }
        for case, outcome in cases.items():
            with self.subTest(case=case):
                self.assertIn("| `" + case + "` | " + outcome + " |", POLICY)


class ReceiptContractTests(unittest.TestCase):
    def test_checkpoint_review_receipt_does_not_change_the_reviewed_tree(self):
        for clause in (
            "canonical Vault の Git commit message",
            "bounded evidence envelope",
            "task record evidence の一部",
            "本文へ追記せず",
            "exact parsing",
            "最大 16 KiB",
            "新しい authorization",
            "private temporary file だけを参照してはならない",
            "review-of-review を要求しない",
            "source repository と checkpoint を保存する Vault repository",
            "source commit を Vault checkpoint の親とみなしてはならない",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, POLICY)

    def test_checkpoint_is_a_finite_exception_to_own_sha_recording(self):
        self.assertIn("checkpoint 自身の SHA は同じ hashed content へ追記しない", POLICY)
        self.assertIn("自身の SHA 記録だけを目的とする追加 commit を作らない", POLICY)
        self.assertIn("各コミット（後述の evidence checkpoint 自身の SHA を除く）", POLICY)

    def test_checkpoint_binds_receipts_to_task_and_immutable_git_objects(self):
        for clause in (
            "一意な checkpoint ID",
            "task ID・repository・source commit SHA",
            "base/tree/diff identity",
            "commit message にも checkpoint ID",
            "immutable Git object",
            "read-back",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, POLICY)

    def test_resume_is_verified_and_does_not_generate_recursive_evidence(self):
        for clause in (
            "再開時は同じ checkpoint ID",
            "欠落・複数候補・identity 不一致・保存失敗",
            "evidence 保存済みと報告しない",
            "検証・独立レビューを省略する例外ではない",
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
