"""Persistance des sauvegardes : tableau des scores et progression.

Chaque sauvegarde est un document JSON identifie par un nom :
- Desktop : fichier <nom>.json a la racine du projet (dans %APPDATA%\\AimToLearn pour l'exe).
- Navigateur (pygbag) : cle localStorage <prefixe><nom>, car le systeme de fichiers
  du navigateur est efface a chaque rechargement de la page.
"""

import json
from pathlib import Path

from config.settings import DATA_DIR, IS_WEB, STORAGE_KEY_PREFIX
from lib.logger import get_logger

logger = get_logger(__name__)

SCORES = "scores"
PROGRESS = "progress"


def load_entries() -> list[dict]:
    """Charge le tableau des scores.

    Returns:
        Les entrees valides ({"name", "points", "levels"}), liste vide en cas de probleme.
    """
    data = _load_json(SCORES)
    if data is None:
        return []
    if not isinstance(data, list):
        logger.error("Tableau des scores mal forme (liste attendue), il repart de zero")
        return []
    # On ignore les entrees abimees plutot que de planter a l'affichage
    return [
        e for e in data
        if isinstance(e, dict) and isinstance(e.get("name"), str) and isinstance(e.get("points"), int)
    ]


def save_entries(entries: list[dict]) -> None:
    """Enregistre le tableau des scores.

    Args:
        entries: Entrees a sauvegarder.
    """
    _save_json(SCORES, entries)


def load_progress() -> int:
    """Charge l'index du niveau le plus avance debloque.

    Returns:
        L'index (0 = seul le niveau 1 est accessible), 0 en cas de probleme.
    """
    data = _load_json(PROGRESS)
    if data is None:
        return 0
    unlocked = data.get("unlocked") if isinstance(data, dict) else None
    if not isinstance(unlocked, int) or unlocked < 0:
        logger.error("Progression mal formee, elle repart du niveau 1")
        return 0
    return unlocked


def save_progress(unlocked: int) -> None:
    """Enregistre l'index du niveau le plus avance debloque.

    Args:
        unlocked: Index du niveau.
    """
    _save_json(PROGRESS, {"unlocked": unlocked})


# --- Lecture / ecriture generiques ------------------------------------------------


def _load_json(name: str) -> object | None:
    """Lit et decode une sauvegarde, None si elle est absente ou illisible."""
    raw = _read_raw(name)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Sauvegarde '%s' illisible, elle repart de zero : %s", name, e)
        return None


def _save_json(name: str, data: object) -> None:
    """Encode et ecrit une sauvegarde (les erreurs sont journalisees, pas propagees)."""
    raw = json.dumps(data, ensure_ascii=False, indent=2)
    if IS_WEB:
        try:
            _web_storage().setItem(STORAGE_KEY_PREFIX + name, raw)
        except Exception as e:  # noqa: BLE001 - les erreurs du pont JS n'ont pas de type Python precis
            logger.error("Impossible d'ecrire '%s' dans le localStorage : %s", name, e)
        return
    path = _file(name)
    try:
        # Le dossier %APPDATA%\AimToLearn n'existe pas au premier lancement de l'exe
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(raw, encoding="utf-8")
    except OSError as e:
        logger.error("Impossible d'ecrire %s : %s", path, e)


def _read_raw(name: str) -> str | None:
    """Lit le contenu brut d'une sauvegarde, None si elle est vide ou inaccessible."""
    if IS_WEB:
        try:
            return _web_storage().getItem(STORAGE_KEY_PREFIX + name)
        except Exception as e:  # noqa: BLE001 - voir _save_json
            logger.error("Impossible de lire '%s' dans le localStorage : %s", name, e)
            return None
    path = _file(name)
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error("Impossible de lire %s : %s", path, e)
        return None


def _file(name: str) -> Path:
    """Chemin du fichier d'une sauvegarde en desktop."""
    return DATA_DIR / f"{name}.json"


def _web_storage():  # type: ignore[no-untyped-def] - objet JavaScript, pas de type Python
    """Retourne le localStorage du navigateur.

    Sous pygbag, le module `platform` est remplace par une version qui expose
    l'objet JavaScript `window` ; l'import est donc fait ici, jamais en desktop.
    """
    import platform

    return platform.window.localStorage
