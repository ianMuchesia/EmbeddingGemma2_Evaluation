"""Measurements of the machine: disk sizes, memory and environment info."""
import os
import platform
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
TYPESENSE_DATA = ROOT / "typesense-data"


def to_mb(n_bytes):
    return None if n_bytes is None else round(n_bytes / 1e6, 1)


def dir_size(path):
    """Bytes used by all files under `path`, or None if it is missing or unreadable."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        return sum(f.stat().st_size for f in path.rglob("*") if f.is_file() and not f.is_symlink())
    except PermissionError:
        return None


def huggingface_model_size(model_name):
    """Size of a downloaded Hugging Face model in the local cache.

    The cache stores files as links into a shared blob store, so follow the
    links (and count each real file once).
    """
    from huggingface_hub.constants import HF_HUB_CACHE
    snapshots = Path(HF_HUB_CACHE) / f"models--{model_name.replace('/', '--')}" / "snapshots"
    if not snapshots.exists():
        return None
    real_files = {f.resolve() for f in snapshots.rglob("*") if f.is_file()}
    return sum(f.stat().st_size for f in real_files)


def typesense_model_size(model_name):
    """Size of a Typesense built-in model inside the mounted data folder."""
    models_dir = TYPESENSE_DATA / "models"
    if not models_dir.exists():
        return None
    short_name = model_name.removeprefix("ts/")
    sizes = [dir_size(d) for d in models_dir.iterdir() if d.is_dir() and short_name in d.name]
    return max((s for s in sizes if s), default=None)


def typesense_disk_usage():
    return {"total_mb": to_mb(dir_size(TYPESENSE_DATA)),
            "models_mb": to_mb(dir_size(TYPESENSE_DATA / "models")),
            "db_mb": to_mb(dir_size(TYPESENSE_DATA / "db"))}


def process_memory():
    """Resident memory of this Python process, in bytes."""
    return psutil.Process().memory_info().rss


def environment(typesense=None):
    import torch

    cpuinfo = Path("/proc/cpuinfo")
    cpu = platform.processor()
    if cpuinfo.exists():
        cpu = next((line.split(":", 1)[1].strip() for line in cpuinfo.read_text().splitlines()
                    if line.startswith("model name")), cpu)
    return {
        "cpu": cpu,
        "cores": os.cpu_count(),
        "ram_gb": round(psutil.virtual_memory().total / 1e9, 1),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "typesense": typesense.version() if typesense else None,
    }
