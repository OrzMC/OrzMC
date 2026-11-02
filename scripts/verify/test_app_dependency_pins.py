"""Offline tests for the staged App/umbrella dependency consistency guard."""
import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
import check  # noqa: E402


class AppDependencyPinTests(unittest.TestCase):
    def run_check(self, *, mismatch=False, missing=False):
        expected = {name: str(index + 1) * 40 for index, name in enumerate(check.APP_DEPENDENCIES)}
        pins = [{"identity": name, "state": {"revision": sha}} for name, sha in expected.items()]
        if mismatch:
            pins[0]["state"]["revision"] = "f" * 40
        if missing:
            pins.pop()
        reverse = {path: expected[name] for name, path in check.APP_DEPENDENCIES.items()}

        def run(args, **_kwargs):
            if args[1:3] == ["ls-files", "-s"]:
                path = args[-1]
                sha = "a" * 40 if path == "swift/app" else reverse[path]
                return SimpleNamespace(returncode=0, stdout=f"160000 {sha} 0\t{path}\n")
            return SimpleNamespace(returncode=0, stdout=json.dumps({"pins": pins}))

        with patch.object(check.subprocess, "run", side_effect=run), patch("builtins.print"):
            return check.check_app_dependency_pins()

    def test_matching_pins_pass(self):
        self.assertTrue(self.run_check())

    def test_mismatch_fails(self):
        self.assertFalse(self.run_check(mismatch=True))

    def test_missing_pin_fails(self):
        self.assertFalse(self.run_check(missing=True))


if __name__ == "__main__":
    unittest.main()
