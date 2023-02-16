"""
Update the history file.
"""
from pathlib import Path
import re

START_MARKER = "<!-- latest-start -->"
STOP_MARKER = "<!-- latest-stop -->"

history = Path("HISTORY.md").read_text()
latest = Path("changelog.md").read_text()
print(re.findall(f"{START_MARKER}.*", history, flags=re.DOTALL))
updated = re.sub(
    f"{START_MARKER}.*{STOP_MARKER}",
    f"{START_MARKER}\n{latest}\n{STOP_MARKER}",
    history,
    flags=re.DOTALL,
)

Path("HISTORY.md").write_text(updated)
