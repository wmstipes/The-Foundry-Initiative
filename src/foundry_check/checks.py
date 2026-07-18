"""The five repository readiness checks performed by foundry-check."""

from __future__ import annotations

from pathlib import Path
import subprocess

from .models import CheckResult

_IGNORED_FILE_NAMES = {".gitkeep", ".DS_Store"}
_IGNORED_DIRECTORY_NAMES = {"__pycache__", ".pytest_cache"}
_COMPILED_PYTHON_SUFFIXES = {".pyc", ".pyo"}
_ENV_EXAMPLES = {".env.example", ".env.sample", ".env.template"}
_PRIVATE_KEY_NAMES = {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
_SENSITIVE_JSON_NAMES = {
    "credentials.json",
    "service-account.json",
    "service_account.json",
}
_SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


def check_required_baseline_files(repository: Path) -> CheckResult:
    """Require the two baseline files expected at the repository root."""
    required = ("README.md", ".gitignore")
    missing = tuple(name for name in required if not (repository / name).is_file())
    if missing:
        return CheckResult(
            "baseline_files", "Required baseline files", "fail",
            "Required baseline files are missing.", missing,
        )
    return CheckResult(
        "baseline_files", "Required baseline files", "pass",
        "README.md and .gitignore are present.",
    )


def check_expected_directories(repository: Path) -> CheckResult:
    """Require source and test directories at the repository root."""
    required = ("src", "tests")
    missing = tuple(name for name in required if not (repository / name).is_dir())
    if missing:
        return CheckResult(
            "expected_directories", "Expected directories", "fail",
            "Expected directories are missing.", missing,
        )
    return CheckResult(
        "expected_directories", "Expected directories", "pass",
        "src and tests directories are present.",
    )


def _contains_substantive_file(directory: Path) -> bool:
    if not directory.is_dir():
        return False
    for path in directory.rglob("*"):
        relative_parts = path.relative_to(directory).parts
        if any(part in _IGNORED_DIRECTORY_NAMES for part in relative_parts[:-1]):
            continue
        if not path.is_file():
            continue
        if path.name in _IGNORED_FILE_NAMES:
            continue
        if path.suffix.lower() in _COMPILED_PYTHON_SUFFIXES:
            continue
        return True
    return False


def check_implementation_and_test_content(repository: Path) -> CheckResult:
    """Require substantive files below both src and tests."""
    empty = tuple(
        name for name in ("src", "tests")
        if not _contains_substantive_file(repository / name)
    )
    if empty:
        return CheckResult(
            "implementation_and_tests_nonempty", "Implementation and test content",
            "fail", "Implementation or test directories lack substantive files.", empty,
        )
    return CheckResult(
        "implementation_and_tests_nonempty", "Implementation and test content", "pass",
        "src and tests contain substantive files.",
    )


def check_baseline_documentation(repository: Path) -> CheckResult:
    """Require the three baseline documents under docs."""
    required = (
        "docs/vision.md", "docs/architecture.md", "docs/learning-journal.md",
    )
    missing = tuple(name for name in required if not (repository / name).is_file())
    if missing:
        return CheckResult(
            "baseline_documentation", "Baseline documentation", "fail",
            "Baseline documentation is incomplete.", missing,
        )
    return CheckResult(
        "baseline_documentation", "Baseline documentation", "pass",
        "Vision, architecture, and learning journal documents are present.",
    )


def _is_suspicious_filename(path_text: str) -> bool:
    name = Path(path_text).name.lower()
    if name == ".env":
        return True
    if name.startswith(".env.") and name not in _ENV_EXAMPLES:
        return True
    if name in _PRIVATE_KEY_NAMES or name in _SENSITIVE_JSON_NAMES:
        return True
    if Path(name).suffix in _SENSITIVE_SUFFIXES:
        return True
    return "secret" in name


def _git_warning(message: str) -> CheckResult:
    return CheckResult(
        "tracked_secret_filenames", "Suspicious tracked secret filenames",
        "warning", message,
    )


def check_suspicious_tracked_secret_filenames(repository: Path) -> CheckResult:
    """Inspect tracked filenames through Git without opening their contents."""
    try:
        root_process = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "--show-toplevel"],
            check=False, capture_output=True, text=True,
        )
    except FileNotFoundError:
        return _git_warning("Git is unavailable; tracked filenames were not checked.")
    except OSError:
        return _git_warning("Git could not be executed; tracked filenames were not checked.")

    if root_process.returncode != 0:
        return _git_warning(
            "The target is not a Git repository; tracked filenames were not checked."
        )
    try:
        git_root = Path(root_process.stdout.strip()).resolve()
    except (OSError, RuntimeError):
        return _git_warning("The Git repository root could not be resolved.")
    if git_root != repository.resolve():
        return _git_warning(
            "The target is not the Git repository root; tracked filenames were not checked."
        )

    try:
        files_process = subprocess.run(
            ["git", "-C", str(repository), "ls-files", "--cached", "-z"],
            check=False, capture_output=True,
        )
    except (FileNotFoundError, OSError):
        return _git_warning("Git could not list tracked filenames.")
    if files_process.returncode != 0:
        return _git_warning("Git could not list tracked filenames.")

    tracked = files_process.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    suspicious = tuple(
        sorted(path for path in tracked if path and _is_suspicious_filename(path))
    )
    if suspicious:
        return CheckResult(
            "tracked_secret_filenames", "Suspicious tracked secret filenames", "fail",
            "Suspicious filenames are tracked; file contents were not inspected.",
            suspicious,
        )
    return CheckResult(
        "tracked_secret_filenames", "Suspicious tracked secret filenames", "pass",
        "No suspicious tracked secret filenames were found.",
    )


def run_checks(repository: Path) -> tuple[CheckResult, ...]:
    """Run the complete, ordered set of five readiness checks."""
    return (
        check_required_baseline_files(repository),
        check_expected_directories(repository),
        check_implementation_and_test_content(repository),
        check_baseline_documentation(repository),
        check_suspicious_tracked_secret_filenames(repository),
    )
