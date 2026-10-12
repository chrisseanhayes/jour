import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

from jour_cli.config import (
    StoragePrompt,
    StorageScope,
    detect_storage_location,
    initialize_local_context,
    initialize_local_storage,
    resolve_storage_context,
    resolve_storage_scope,
)
from jour_cli.shared.dependencies import Dependencies


class StorageScopeTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.home = os.path.join(self.temporary_directory.name, "home")
        self.repo = os.path.join(self.temporary_directory.name, "repo")
        os.makedirs(os.path.join(self.repo, ".git"))
        os.makedirs(self.home)
        self.stderr = StringIO()
        self.dependencies = Dependencies(
            working_directory=self.repo,
            path_expander=lambda path: path.replace("~", self.home, 1),
            stderr=self.stderr,
        )
        self.config = {
            "storage": {"path": "~/.jour", "extension": "jmd"},
            "database": {"path": "~/.jour/jour.db"},
        }

    def test_interactive_yes_selects_repo_local_data(self):
        with patch.object(self.dependencies, "stdin_is_interactive", return_value=True):
            with patch.object(self.dependencies, "confirm", return_value=True):
                config = resolve_storage_scope(self.config, self.dependencies)

        local_storage = os.path.join(self.repo, ".jour")
        self.assertEqual(config["storage"]["path"], local_storage)
        self.assertEqual(
            config["database"]["path"], os.path.join(local_storage, "jour.db")
        )
        self.assertTrue(os.path.isdir(local_storage))
        self.assertIn(".gitignore", self.stderr.getvalue())

    def test_interactive_no_remembers_repo_as_global(self):
        with patch.object(self.dependencies, "stdin_is_interactive", return_value=True):
            with patch.object(self.dependencies, "confirm", return_value=False):
                config = resolve_storage_scope(self.config, self.dependencies)

        ignore_file = os.path.join(self.home, ".jour", ".jourignore")
        self.assertEqual(config["storage"]["path"], "~/.jour")
        with open(ignore_file) as ignore_file_handle:
            self.assertEqual(
                ignore_file_handle.read(), f"{os.path.abspath(self.repo)}\n"
            )
        with patch.object(self.dependencies, "confirm") as confirm:
            ignored_config = resolve_storage_scope(self.config, self.dependencies)
        confirm.assert_not_called()
        self.assertEqual(ignored_config["storage"]["path"], "~/.jour")

    def test_ignored_repo_is_separated_when_ignore_file_has_no_trailing_newline(self):
        jour_home = os.path.join(self.home, ".jour")
        os.makedirs(jour_home)
        ignore_file = os.path.join(jour_home, ".jourignore")
        with open(ignore_file, "w") as ignore_file_handle:
            ignore_file_handle.write("# ignored repositories")

        with patch.object(self.dependencies, "stdin_is_interactive", return_value=True):
            with patch.object(self.dependencies, "confirm", return_value=False):
                resolve_storage_scope(self.config, self.dependencies)

        with open(ignore_file) as ignore_file_handle:
            self.assertEqual(
                ignore_file_handle.read(),
                f"# ignored repositories\n{os.path.abspath(self.repo)}\n",
            )

    def test_non_interactive_repo_uses_global_data_without_prompt(self):
        with patch.object(self.dependencies, "stdin_is_interactive", return_value=False):
            with patch.object(self.dependencies, "confirm") as confirm:
                config = resolve_storage_scope(self.config, self.dependencies)

        confirm.assert_not_called()
        self.assertEqual(config["storage"]["path"], "~/.jour")

    def test_global_override_skips_repository_detection(self):
        with patch.object(self.dependencies, "get_git_root") as get_git_root:
            context = resolve_storage_context(
                self.config, self.dependencies, global_mode=True
            )

        get_git_root.assert_not_called()
        self.assertEqual(context.scope, StorageScope.GLOBAL)
        self.assertEqual(context.config, self.config)
        self.assertEqual(context.storage_path, os.path.join(self.home, ".jour"))
        self.assertEqual(
            context.database_path,
            os.path.join(self.home, ".jour", "jour.db"),
        )

    def test_existing_local_directory_resolves_to_local_context(self):
        local_storage = os.path.join(self.repo, ".jour")
        os.makedirs(local_storage)

        context = resolve_storage_context(self.config, self.dependencies)

        self.assertEqual(context.scope, StorageScope.REPO_LOCAL)
        self.assertEqual(context.storage_path, local_storage)
        self.assertEqual(context.database_path, os.path.join(local_storage, "jour.db"))

    def test_detection_requests_choice_without_prompting_or_creating_storage(self):
        with patch.object(self.dependencies, "confirm") as confirm:
            location = detect_storage_location(self.config, self.dependencies)

        self.assertIsInstance(location, StoragePrompt)
        self.assertEqual(location.repo_root, os.path.abspath(self.repo))
        self.assertFalse(os.path.exists(os.path.join(self.repo, ".jour")))
        self.assertFalse(os.path.exists(os.path.join(self.home, ".jour")))
        confirm.assert_not_called()
        self.assertEqual(self.stderr.getvalue(), "")

    def test_existing_local_directory_selects_local_data_without_prompt(self):
        local_storage = os.path.join(self.repo, ".jour")
        os.makedirs(local_storage)
        with patch.object(self.dependencies, "stdin_is_interactive") as is_interactive:
            config = resolve_storage_scope(self.config, self.dependencies)

        is_interactive.assert_not_called()
        self.assertEqual(config["storage"]["path"], local_storage)

    def test_init_creates_local_storage_and_removes_repo_from_ignore_file(self):
        jour_home = os.path.join(self.home, ".jour")
        os.makedirs(jour_home)
        ignore_file = os.path.join(jour_home, ".jourignore")
        other_repo = os.path.join(self.temporary_directory.name, "other-repo")
        with open(ignore_file, "w") as ignore_file_handle:
            ignore_file_handle.write(
                f"# global-only repositories\n{os.path.abspath(self.repo)}\n"
                f"{other_repo}\n"
            )

        config = initialize_local_storage(self.config, self.dependencies)

        local_storage = os.path.join(self.repo, ".jour")
        self.assertTrue(os.path.isdir(local_storage))
        self.assertEqual(config["storage"]["path"], local_storage)
        self.assertEqual(
            config["database"]["path"], os.path.join(local_storage, "jour.db")
        )
        with open(ignore_file) as ignore_file_handle:
            self.assertEqual(
                ignore_file_handle.read(),
                f"# global-only repositories\n{other_repo}\n",
            )

    def test_init_returns_explicit_repo_local_context(self):
        context = initialize_local_context(self.config, self.dependencies)

        self.assertEqual(context.scope, StorageScope.REPO_LOCAL)
        self.assertEqual(context.storage_path, os.path.join(self.repo, ".jour"))
        self.assertEqual(
            context.database_path,
            os.path.join(self.repo, ".jour", "jour.db"),
        )

    def test_init_requires_a_git_repository(self):
        self.dependencies.get_git_root = lambda: None
        with self.assertRaisesRegex(ValueError, "inside a Git repository"):
            initialize_local_storage(self.config, self.dependencies)


if __name__ == "__main__":
    unittest.main()
