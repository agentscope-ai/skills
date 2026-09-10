# -*- coding: utf-8 -*-
"""Exercise discovery without depending on an installed AgentScope version."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills/agentscope-skill/scripts/view_module_signature.py"
)
SPEC = importlib.util.spec_from_file_location("signature_inspector", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
INSPECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSPECTOR)


class InspectorTests(unittest.TestCase):
    """Test package discovery, optional dependencies, and inherited APIs."""

    def setUp(self) -> None:
        # enterContext registers cleanup even when setUp or a test fails.
        # pylint: disable-next=consider-using-with
        self.temp_path = self.enterContext(tempfile.TemporaryDirectory())
        package = Path(self.temp_path) / "agentscope"
        package.mkdir()
        (package / "__init__.py").write_text(
            '__version__ = "2.test"\n__all__ = ["__version__"]\n',
            encoding="utf-8",
        )
        (package / "agent.py").write_text(
            "class Parent:\n"
            "    async def reply(self, inputs=None):\n"
            '        """Return a response."""\n'
            "        return inputs\n"
            "    async def stream(self):\n"
            "        yield 'chunk'\n"
            "    @classmethod\n"
            "    def create(cls, name):\n"
            "        return cls(name)\n"
            "    @staticmethod\n"
            "    def label():\n"
            "        return 'agent'\n"
            "class Agent(Parent):\n"
            "    def __init__(self, name):\n"
            "        self.name = name\n"
            '__all__ = ["Agent"]\n',
            encoding="utf-8",
        )
        (package / "optional.py").write_text(
            "import missing_agentscope_test_dependency\n",
            encoding="utf-8",
        )
        (package / "lazy.py").write_text(
            '__all__ = ["OptionalBackend"]\n'
            "def __getattr__(name):\n"
            "    if name == 'OptionalBackend':\n"
            "        import missing_agentscope_test_dependency\n"
            "    raise AttributeError(name)\n",
            encoding="utf-8",
        )
        self.module_patch = patch.dict(sys.modules)
        self.module_patch.start()
        self.addCleanup(self.module_patch.stop)
        for name in list(sys.modules):
            if name == "agentscope" or name.startswith("agentscope."):
                del sys.modules[name]
        self.path_patch = patch.object(
            sys,
            "path",
            [self.temp_path, *sys.path],
        )
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)

    def test_discovers_modules_without_top_level_exports(self) -> None:
        """Discover child modules without loading their dependencies."""
        output = INSPECTOR.view_agentscope_library("agentscope")
        self.assertIn("agentscope.agent", output)
        self.assertIn("agentscope.optional", output)
        self.assertIn("2.test", output)
        self.assertIn(self.temp_path, output)
        self.assertNotIn("agentscope.optional", sys.modules)

    def test_inherited_async_method_is_visible_and_resolvable(self) -> None:
        """Include a parent's API when inspecting a concrete class."""
        output = INSPECTOR.view_agentscope_library("agentscope.agent.Agent")
        self.assertIn("async def reply", output)
        self.assertIn("defined on Parent", output)
        method = INSPECTOR.resolve_target("agentscope.agent.Agent.reply")
        self.assertEqual(method.__name__, "reply")

    def test_missing_dependency_is_not_reported_as_missing_api(self) -> None:
        """Preserve the missing optional dependency's identity."""
        with self.assertRaises(ModuleNotFoundError) as caught:
            INSPECTOR.resolve_target("agentscope.optional")
        self.assertEqual(
            caught.exception.name,
            "missing_agentscope_test_dependency",
        )

    def test_lazy_exports_are_not_loaded_during_listing(self) -> None:
        """Listing a module should not load a lazy optional backend."""
        output = INSPECTOR.view_agentscope_library("agentscope.lazy")
        self.assertIn("OptionalBackend (lazy export", output)
        with self.assertRaises(ModuleNotFoundError):
            INSPECTOR.resolve_target("agentscope.lazy.OptionalBackend")

    def test_invalid_namespace_and_unknown_attribute(self) -> None:
        """Reject sibling packages and distinguish absent class members."""
        for name in ("agentscope_fake", "agentscope..agent", "os.path"):
            with self.assertRaises(ValueError):
                INSPECTOR.resolve_target(name)
        with self.assertRaises(AttributeError):
            INSPECTOR.resolve_target("agentscope.agent.Agent.missing")

    def run_cli(
        self,
        *args: str,
        without_site: bool = False,
    ) -> subprocess.CompletedProcess:
        """Execute the actual script against the isolated fixture package."""
        env = dict(os.environ, PYTHONPATH=self.temp_path)
        command = [sys.executable]
        if without_site:
            command.append("-S")
        return subprocess.run(
            [*command, str(SCRIPT), *args],
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

    def test_cli_success_cases(self) -> None:
        """Run module, class, method, and value queries as commands."""
        cases = [
            ((), "agentscope.agent"),
            (("--help",), "--module"),
            (("--module", "agentscope.agent"), "agentscope.agent.Agent"),
            (("--module", "agentscope.agent.Agent"), "defined on Parent"),
            (("--module", "agentscope.agent.Agent.reply"), "async def reply"),
            (
                ("--module", "agentscope.agent.Agent.stream"),
                "async def stream",
            ),
            (
                ("--module", "agentscope.agent.Agent.create"),
                "def create(name)",
            ),
            (("--module", "agentscope.agent.Agent.label"), "def label()"),
            (("--module", "agentscope.__version__"), "'2.test'"),
            (("--module", "agentscope.lazy"), "lazy export"),
        ]
        for args, expected in cases:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(expected, result.stdout)
                self.assertEqual(result.stderr, "")

    def test_cli_import_and_path_errors(self) -> None:
        """Return a nonzero status and useful errors, without tracebacks."""
        cases = [
            ("agentscope_fake", "dotted path"),
            ("agentscope..agent", "dotted path"),
            ("agentscope.missing", "missing"),
            ("agentscope.agent.Agent.missing", "missing"),
            ("agentscope.optional", "missing_agentscope_test_dependency"),
            (
                "agentscope.lazy.OptionalBackend",
                "missing_agentscope_test_dependency",
            ),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                result = self.run_cli("--module", name)
                self.assertEqual(result.returncode, 1)
                self.assertIn(expected, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_cli_argument_errors(self) -> None:
        """Let argparse report missing values and unsupported flags."""
        for args in [("--module",), ("--unknown",)]:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_cli_without_agentscope(self) -> None:
        """Help works without the SDK and queries explain a missing install."""
        # Remove the fixture and disable site-packages for this subprocess.
        package = Path(self.temp_path) / "agentscope"
        package.rename(package.with_name("hidden_package"))
        result = self.run_cli(without_site=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("No module named 'agentscope'", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        help_result = self.run_cli("--help", without_site=True)
        self.assertEqual(help_result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
