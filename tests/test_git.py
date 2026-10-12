import os
import subprocess
import tempfile
import unittest
from io import StringIO
from types import SimpleNamespace

from jour_cli.cmd.git import cmd_git_commit, cmd_git_init
from jour_cli.shared.dependencies import Dependencies


class JourGitTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.storage = os.path.join(self.temporary_directory.name, "journal")
        os.makedirs(self.storage)
        self.stdout = StringIO()
        self.stderr = StringIO()
        dependencies = Dependencies(stdout=self.stdout, stderr=self.stderr)
        self.app_factory = SimpleNamespace(
            get_config=lambda: {
                "storage": {"path": self.storage, "extension": "jmd"}
            },
            dependencies=dependencies,
        )

    def git(self, *arguments):
        return subprocess.run(
            ["git", "-C", self.storage, *arguments],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_init_creates_repo_and_ignores_non_note_files(self):
        with open(os.path.join(self.storage, "jour.db"), "w") as file:
            file.write("metadata")

        cmd_git_init(args=None, app_factory=self.app_factory)

        self.assertEqual(
            os.path.realpath(self.git("rev-parse", "--show-toplevel").stdout.strip()),
            os.path.realpath(self.storage),
        )
        status = self.git("status", "--short", "--untracked-files=all").stdout
        self.assertNotIn("jour.db", status)
        self.assertIn("Initialized note Git repository", self.stdout.getvalue())

    def test_commit_includes_only_note_files_and_preserves_other_staged_changes(self):
        cmd_git_init(args=None, app_factory=self.app_factory)
        self.git("config", "user.name", "Jour Tests")
        self.git("config", "user.email", "jour-tests@example.test")
        for filename in ("first.jmd", "second.jmd", "journal.db", "unrelated.txt"):
            with open(os.path.join(self.storage, filename), "w") as file:
                file.write(filename)
        self.git("add", "--force", "unrelated.txt")

        cmd_git_commit(
            args=SimpleNamespace(message="Save journal notes"),
            app_factory=self.app_factory,
        )

        committed_files = self.git(
            "show", "--pretty=format:", "--name-only", "HEAD"
        ).stdout.splitlines()
        self.assertEqual(committed_files, ["first.jmd", "second.jmd"])
        status = self.git("status", "--short")
        self.assertIn("A  unrelated.txt", status.stdout)
        self.assertIn("Save journal notes", self.git("log", "-1", "--format=%s").stdout)

    def test_commit_rejects_parent_repository_without_local_jour_repo(self):
        subprocess.run(
            ["git", "-C", self.temporary_directory.name, "init"],
            check=True,
            capture_output=True,
            text=True,
        )

        with self.assertRaises(SystemExit) as error:
            cmd_git_commit(
                args=SimpleNamespace(message="Save notes"),
                app_factory=self.app_factory,
            )

        self.assertEqual(error.exception.code, 1)
        self.assertIn("jour git init", self.stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
