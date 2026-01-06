#!/usr/bin/env python3
"""
BamBam Fact-Checking Validation Script

This script validates code changes for:
- Python syntax correctness
- Flake8/PEP8 compliance
- Extension event_map.yaml validity
- Pi 5 Lite compatibility
- Import verification

Usage: python3 scripts/fact_check.py [--fix]
"""

import argparse
import ast
import subprocess
import sys
from pathlib import Path

# Known good apt packages for Pi 5 Lite (Bookworm)
PI5_APT_PACKAGES = {
    'python3': '3.11',
    'python3-pygame': '2.1',
    'python3-yaml': '6.0',
    'cage': '0.1',
    'libsdl2-2.0-0': '2.26',
}

# Required Python imports that must be available
REQUIRED_IMPORTS = ['pygame', 'argparse', 'os', 'sys', 'random', 'time', 'logging']
OPTIONAL_IMPORTS = ['yaml']

# Extension API version
SUPPORTED_API_VERSION = [0, '0']

# Valid policies
VALID_IMAGE_POLICIES = ['font', 'random', 'named_file']
VALID_SOUND_POLICIES = ['random', 'deterministic', 'named_file']

# Valid check types
VALID_CHECK_TYPES = ['KEYDOWN']
VALID_UNICODE_CHECKS = ['isalpha', 'isdigit', 'value']


class FactChecker:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.errors = []
        self.warnings = []
        self.info = []

    def error(self, msg: str):
        self.errors.append(f"❌ ERROR: {msg}")

    def warn(self, msg: str):
        self.warnings.append(f"⚠️  WARNING: {msg}")

    def ok(self, msg: str):
        self.info.append(f"✅ OK: {msg}")

    def check_python_syntax(self, filepath: Path) -> bool:
        """Verify Python file syntax."""
        try:
            with open(filepath) as f:
                source = f.read()
            ast.parse(source)
            self.ok(f"Syntax valid: {filepath.name}")
            return True
        except SyntaxError as e:
            self.error(f"Syntax error in {filepath}: line {e.lineno}: {e.msg}")
            return False

    def check_flake8(self) -> bool:
        """Run flake8 linting."""
        try:
            result = subprocess.run(
                ['flake8', '.', '--max-line-length=120'],
                capture_output=True,
                text=True,
                cwd=self.root_dir
            )
            if result.returncode == 0:
                self.ok("Flake8 linting passed")
                return True
            else:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        self.error(f"Flake8: {line}")
                return False
        except FileNotFoundError:
            self.warn("Flake8 not installed, skipping lint check")
            return True

    def check_imports(self, filepath: Path) -> bool:
        """Verify imports are available."""
        try:
            with open(filepath) as f:
                tree = ast.parse(f.read())
        except SyntaxError:
            return False  # Already reported

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])

        all_ok = True
        for imp in REQUIRED_IMPORTS:
            if imp in imports:
                try:
                    __import__(imp)
                    self.ok(f"Import '{imp}' available")
                except ImportError:
                    self.error(f"Required import '{imp}' not available")
                    all_ok = False

        for imp in OPTIONAL_IMPORTS:
            if imp in imports:
                try:
                    __import__(imp)
                    self.ok(f"Optional import '{imp}' available")
                except ImportError:
                    self.warn(f"Optional import '{imp}' not available")

        return all_ok

    def check_extension(self, ext_dir: Path) -> bool:
        """Validate extension structure and event_map.yaml."""
        event_map_file = ext_dir / 'event_map.yaml'
        if not event_map_file.exists():
            self.error(f"Extension {ext_dir.name} missing event_map.yaml")
            return False

        try:
            import yaml
        except ImportError:
            self.warn("PyYAML not available, skipping extension validation")
            return True

        try:
            with open(event_map_file) as f:
                event_map = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.error(f"YAML parse error in {event_map_file}: {e}")
            return False

        # BUG FIX: yaml.safe_load returns None for empty files
        if event_map is None:
            self.error(f"Extension {ext_dir.name}: event_map.yaml is empty")
            return False

        if not isinstance(event_map, dict):
            self.error(f"Extension {ext_dir.name}: event_map.yaml must contain a YAML mapping")
            return False

        all_ok = True

        # Check API version
        api_version = event_map.get('apiVersion', 'missing')
        if api_version not in SUPPORTED_API_VERSION:
            self.error(f"Extension {ext_dir.name}: unsupported apiVersion '{api_version}'")
            all_ok = False
        else:
            self.ok(f"Extension {ext_dir.name}: apiVersion OK")

        # Check valid keys
        valid_keys = {'apiVersion', 'image', 'sound'}
        for key in event_map.keys():
            if key not in valid_keys:
                self.error(f"Extension {ext_dir.name}: unknown key '{key}'")
                all_ok = False

        # Validate image mappings
        if 'image' in event_map:
            if not self._validate_mappings(ext_dir.name, 'image', event_map['image'], VALID_IMAGE_POLICIES):
                all_ok = False

        # Validate sound mappings
        if 'sound' in event_map:
            if not self._validate_mappings(ext_dir.name, 'sound', event_map['sound'], VALID_SOUND_POLICIES):
                all_ok = False

            # Check that named_file args reference existing files
            sounds_dir = ext_dir / 'sounds'
            for step in event_map['sound']:
                # BUG FIX: Check that step is a dict before calling .get()
                if not isinstance(step, dict):
                    continue  # Already reported in _validate_mappings
                if step.get('policy') == 'named_file':
                    args = step.get('args', [])
                    if not isinstance(args, list):
                        continue  # Malformed args
                    for arg in args:
                        if sounds_dir.exists():
                            sound_file = sounds_dir / arg
                            if not sound_file.exists():
                                self.error(f"Extension {ext_dir.name}: sound file not found: {arg}")
                                all_ok = False

        return all_ok

    def _validate_mappings(self, ext_name: str, mapping_type: str, mappings: list, valid_policies: list) -> bool:
        """Validate a list of mapping steps."""
        all_ok = True
        has_fallback = False

        for i, step in enumerate(mappings):
            if not isinstance(step, dict):
                self.error(f"Extension {ext_name}: {mapping_type}[{i}] is not a dict")
                all_ok = False
                continue

            # Check policy
            policy = step.get('policy')
            if not policy:
                self.error(f"Extension {ext_name}: {mapping_type}[{i}] missing 'policy'")
                all_ok = False
            elif policy not in valid_policies:
                self.error(f"Extension {ext_name}: {mapping_type}[{i}] invalid policy '{policy}'")
                all_ok = False

            # Check for fallback (step without 'check')
            if 'check' not in step:
                has_fallback = True

            # Validate checks
            if 'check' in step:
                # BUG FIX: Verify step['check'] is a list before iterating
                checks = step['check']
                if not isinstance(checks, list):
                    self.error(f"Extension {ext_name}: {mapping_type}[{i}] 'check' must be a list")
                    all_ok = False
                    continue
                for j, check in enumerate(checks):
                    if not isinstance(check, dict):
                        self.error(f"Extension {ext_name}: {mapping_type}[{i}].check[{j}] must be a dict")
                        all_ok = False
                        continue
                    if 'type' in check:
                        if check['type'] not in VALID_CHECK_TYPES:
                            self.error(f"Extension {ext_name}: invalid check type '{check['type']}'")
                            all_ok = False
                    elif 'unicode' in check:
                        u = check['unicode']
                        if not any(k in u for k in VALID_UNICODE_CHECKS):
                            self.error(f"Extension {ext_name}: invalid unicode check keys")
                            all_ok = False
                    else:
                        self.warn(f"Extension {ext_name}: unknown check type in {mapping_type}[{i}]")

        if not has_fallback:
            self.warn(f"Extension {ext_name}: {mapping_type} has no fallback step (may cause errors)")

        return all_ok

    def check_pi5_compatibility(self) -> bool:
        """Verify code patterns are Pi 5 compatible."""
        all_ok = True

        # Check requirements.txt
        req_file = self.root_dir / 'requirements.txt'
        if req_file.exists():
            with open(req_file) as f:
                reqs = f.read()
            if 'pygame' in reqs.lower():
                self.ok("pygame in requirements.txt")
            else:
                self.warn("pygame not in requirements.txt")

            if 'yaml' in reqs.lower() or 'pyyaml' in reqs.lower():
                self.ok("PyYAML in requirements.txt")
            else:
                self.warn("PyYAML not in requirements.txt (extensions won't work)")

        # Check for problematic patterns
        for py_file in self.root_dir.glob('*.py'):
            with open(py_file) as f:
                content = f.read()

            # Check for subprocess calls that might not work
            if 'subprocess' in content and 'shell=True' in content:
                self.warn(f"{py_file.name}: Uses shell=True in subprocess (potential security issue)")

            # Check for hardcoded paths
            if '/usr/lib' in content or '/opt/' in content:
                self.warn(f"{py_file.name}: Contains hardcoded system paths")

        return all_ok

    def run_all_checks(self) -> bool:
        """Run all fact-checking validations."""
        print("=" * 60)
        print("BamBam Fact-Check Validation")
        print("=" * 60)

        all_ok = True

        # Check main Python files
        print("\n📋 Checking Python syntax...")
        for py_file in self.root_dir.glob('*.py'):
            if not self.check_python_syntax(py_file):
                all_ok = False

        # Check imports
        print("\n📋 Checking imports...")
        bambam_py = self.root_dir / 'bambam.py'
        if bambam_py.exists():
            if not self.check_imports(bambam_py):
                all_ok = False

        # Run flake8
        print("\n📋 Running linter...")
        if not self.check_flake8():
            all_ok = False

        # Check extensions
        print("\n📋 Checking extensions...")
        extensions_dir = self.root_dir / 'extensions'
        if extensions_dir.exists():
            for ext_dir in extensions_dir.iterdir():
                if ext_dir.is_dir():
                    if not self.check_extension(ext_dir):
                        all_ok = False
        else:
            self.warn("No extensions directory found")

        # Check Pi 5 compatibility
        print("\n📋 Checking Pi 5 compatibility...")
        if not self.check_pi5_compatibility():
            all_ok = False

        # Print results
        print("\n" + "=" * 60)
        print("Results")
        print("=" * 60)

        for msg in self.info:
            print(msg)
        for msg in self.warnings:
            print(msg)
        for msg in self.errors:
            print(msg)

        print("\n" + "-" * 60)
        if all_ok and not self.errors:
            print("✅ All checks passed!")
            return True
        else:
            print(f"❌ {len(self.errors)} errors, {len(self.warnings)} warnings")
            return False


def main():
    parser = argparse.ArgumentParser(description='BamBam Fact-Checking Script')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues')
    parser.add_argument('--root', default='.', help='Root directory to check')
    args = parser.parse_args()

    checker = FactChecker(args.root)
    success = checker.run_all_checks()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
