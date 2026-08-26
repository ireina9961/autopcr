import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from .logger import instance as logger


def update_json_config(path: str, values: Mapping[str, Any]) -> bool:
    """Atomically merge values into an optional external JSON config.

    Returns ``False`` when the integration is disabled or the file already has
    the requested values. Integration failures are logged without breaking the
    game request that produced the values.
    """
    if not path:
        return False

    target = Path(path)
    try:
        data = {}
        if target.exists():
            with target.open("r", encoding="utf-8") as stream:
                loaded = json.load(stream)
                if isinstance(loaded, dict):
                    data = loaded

        if all(data.get(key) == value for key, value in values.items()):
            return False

        data.update(values)
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            temp_path = stream.name
        os.replace(temp_path, target)
        return True
    except Exception:
        logger.exception(f"failed to update integration config: {target}")
        return False
