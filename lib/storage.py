"""Persistance du tableau des scores.

- Desktop : fichier JSON a la racine du projet (dans %APPDATA%\\AimToLearn pour l'exe).
- Navigateur (pygbag) : localStorage, car le systeme de fichiers du navigateur
  est efface a chaque rechargement de la page.
"""

import json

from config.settings import IS_WEB, SCORES_FILE, SCORES_STORAGE_KEY
from lib.logger import get_logger

logger = get_logger(__name__)


def load_entries() -> list[dict]:
    """Charge le tableau des scores.

    Returns:
        Les entrees valides ({"name", "points", "levels"}), liste vide en cas de probleme.
    """
    raw = _read_raw()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Tableau des scores illisible, il repart de zero : %s", e)
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
    raw = json.dumps(entries, ensure_ascii=False, indent=2)
    if IS_WEB:
        try:
            _web_storage().setItem(SCORES_STORAGE_KEY, raw)
        except Exception as e:  # noqa: BLE001 - les erreurs du pont JS n'ont pas de type Python precis
            logger.error("Impossible d'ecrire dans le localStorage : %s", e)
        return
    try:
        # Le dossier %APPDATA%\AimToLearn n'existe pas au premier lancement de l'exe
        SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
        SCORES_FILE.write_text(raw, encoding="utf-8")
    except OSError as e:
        logger.error("Impossible d'ecrire %s : %s", SCORES_FILE, e)


def _read_raw() -> str | None:
    """Lit le contenu brut du stockage, None s'il est vide ou inaccessible."""
    if IS_WEB:
        try:
            return _web_storage().getItem(SCORES_STORAGE_KEY)
        except Exception as e:  # noqa: BLE001 - voir save_entries
            logger.error("Impossible de lire le localStorage : %s", e)
            return None
    if not SCORES_FILE.exists():
        return None
    try:
        return SCORES_FILE.read_text(encoding="utf-8")
    except OSError as e:
        logger.error("Impossible de lire %s : %s", SCORES_FILE, e)
        return None


def _web_storage():  # type: ignore[no-untyped-def] - objet JavaScript, pas de type Python
    """Retourne le localStorage du navigateur.

    Sous pygbag, le module `platform` est remplace par une version qui expose
    l'objet JavaScript `window` ; l'import est donc fait ici, jamais en desktop.
    """
    import platform

    return platform.window.localStorage
