"""Resolve pack files while enforcing an optional trusted pack root."""

from pathlib import Path


def ensure_pack_path(path: str | Path, root: Path | None, filenames: tuple[str, ...]) -> None:
    if root is None:
        return
    pack_path = Path(path).resolve()
    allowed_root = root.resolve()
    if pack_path != allowed_root and allowed_root not in pack_path.parents:
        raise ValueError("pack path is outside configured pack root")
    for filename in filenames:
        candidate = pack_path / filename
        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError:
            continue
        if resolved != allowed_root and allowed_root not in resolved.parents:
            raise ValueError(f"pack file {filename} is outside configured pack root")
