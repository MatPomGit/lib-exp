"""Read-only deterministic SHA-256 manifest for explicitly selected files."""
import hashlib
from pathlib import Path

def source_hashes(root, sources):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root must be a directory")
    result = {}
    for relative in sources:
        rel = Path(relative)
        if rel.is_absolute() or not rel.parts or ".." in rel.parts or rel.as_posix() in result:
            raise ValueError("invalid or duplicate relative path")
        path = root
        for part in rel.parts:
            path = path / part
            if path.is_symlink():
                raise ValueError("symlink not permitted")
        if not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError("missing or unsafe source")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(65536), b""):
                digest.update(chunk)
        result[rel.as_posix()] = digest.hexdigest()
    return dict(sorted(result.items()))
