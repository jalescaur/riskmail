"""
profiles.py — Perfis de aparência/textos salvos como JSON em profiles/.
Um perfil guarda os tokens visuais e comuns e os textos de todos os idiomas.
"""

from __future__ import annotations
import json
import re
from pathlib import Path

from .tokens import sanitize_profile

PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles"


def _path(name: str) -> Path:
    safe = re.sub(r"[^\w\- ]", "", name, flags=re.UNICODE).strip()
    if not safe:
        raise ValueError("Nome de perfil inválido.")
    return PROFILES_DIR / f"{safe}.json"


def list_profiles() -> list[str]:
    PROFILES_DIR.mkdir(exist_ok=True)
    return sorted(p.stem for p in PROFILES_DIR.glob("*.json"))


def save_profile(name: str, state: dict) -> None:
    PROFILES_DIR.mkdir(exist_ok=True)
    _path(name).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_profile(name: str) -> dict:
    return sanitize_profile(json.loads(_path(name).read_text(encoding="utf-8")))


def delete_profile(name: str) -> None:
    p = _path(name)
    if p.exists():
        p.unlink()
