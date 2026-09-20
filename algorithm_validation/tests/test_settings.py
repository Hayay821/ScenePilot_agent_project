# tests/test_settings.py
import re
from pathlib import Path
from app.config import settings

def test_all_settings_references_defined():
    defined = set(settings.model_dump().keys())
    missing = set()
    pattern = re.compile(r"settings\.(\w+)")
    for py in Path("app").rglob("*.py"):
        for m in pattern.finditer(py.read_text(encoding="utf-8")):
            name = m.group(1)
            if name not in defined:
                missing.add((str(py), name))
    assert not missing, f"未定义字段: {missing}"