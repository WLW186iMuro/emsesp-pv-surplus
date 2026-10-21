"""Replace the GITHUB_USER placeholder before the first push.

    python tools/set_github_user.py <your-github-name> [repo-name]
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "README.md",
    "README.de.md",
    "custom_components/emsesp_pv_surplus/manifest.json",
    "custom_components/emsesp_pv_surplus/frontend/emsesp-pv-surplus-card.js",
]


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    user = sys.argv[1].lstrip("@")
    repo = sys.argv[2] if len(sys.argv) > 2 else "emsesp-pv-surplus"
    for name in FILES:
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        new = text.replace("GITHUB_USER/emsesp-pv-surplus", f"{user}/{repo}").replace(
            "@GITHUB_USER", f"@{user}"
        )
        if new != text:
            path.write_text(new, encoding="utf-8")
            print(f"updated {name}")


if __name__ == "__main__":
    main()
