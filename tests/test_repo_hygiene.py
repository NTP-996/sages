"""Guards on what the public tree may contain."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Consumer mailbox providers. A project address on its own domain or GitHub's no-reply
# address is fine; a personal mailbox must never be published in this repository.
PERSONAL_EMAIL = re.compile(
    r"[\w.+-]+@(?:gmail|googlemail|yahoo|outlook|hotmail|live|icloud|me|proton|protonmail)\.[a-z.]+",
    re.IGNORECASE,
)


def tracked_files() -> list[Path]:
    listing = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True
    ).stdout
    return [ROOT / name for name in listing.decode("utf-8").split("\0") if name]


def find_personal_emails(text: str) -> list[str]:
    return [match.group(0) for match in PERSONAL_EMAIL.finditer(text)]


def test_personal_email_pattern_catches_a_webmail_address() -> None:
    sample = "someone.name+tag@" + "gmail.com"
    assert find_personal_emails(f"contact: {sample}") == [sample]


def test_personal_email_pattern_ignores_the_noreply_address() -> None:
    assert find_personal_emails("31298991+NTP-996@users.noreply.github.com") == []


def test_no_personal_email_in_tree() -> None:
    hits: list[str] = []
    for path in tracked_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        hits.extend(f"{path.relative_to(ROOT)}: {email}" for email in find_personal_emails(text))
    assert hits == []


def test_gitignore_keeps_working_docs_private() -> None:
    result = subprocess.run(
        ["git", "check-ignore", "-q", "docs-private/anything.md"], cwd=ROOT, check=False
    )
    assert result.returncode == 0
