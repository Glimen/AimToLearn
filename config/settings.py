"""Constantes globales du jeu : affichage, regles, scores, couleurs."""

import os
import sys
from pathlib import Path

# Vrai quand le jeu tourne dans le navigateur via pygbag (Python compile en WebAssembly)
IS_WEB: bool = sys.platform == "emscripten"
# Vrai quand le jeu tourne depuis l'exe construit par PyInstaller
IS_FROZEN: bool = getattr(sys, "frozen", False)


def _data_dir() -> Path:
    """Dossier des fichiers de sauvegarde (scores, progression) en desktop.

    Dans l'exe PyInstaller, le code est extrait dans un dossier temporaire efface
    a la fermeture : les sauvegardes vont alors dans le dossier de donnees de
    l'utilisateur (%APPDATA% sous Windows, ~/.local/share ailleurs).
    """
    if IS_FROZEN:
        base = Path(os.environ.get("APPDATA") or Path.home() / ".local" / "share")
        return base / "AimToLearn"
    return Path(__file__).resolve().parent.parent

# --- Affichage ---
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
FPS: int = 60
MAX_FRAME_TIME: float = 0.1  # plafond du dt (s) : evite les sauts si la fenetre gele
WINDOW_TITLE: str = "AimToLearn"
HUD_HEIGHT: int = 70  # bandeau d'infos en haut, exclu de la zone de jeu

# --- Regles ---
TARGETS_PER_LEVEL: int = 15
PASS_THRESHOLD: float = 0.7  # score global a depasser pour debloquer le niveau suivant
DOUBLE_CLICK_DELAY: float = 0.4  # secondes max entre les deux clics d'un double-clic
MIN_SPAWN_DISTANCE: float = 200.0  # distance min curseur -> nouvelle cible (px)
MIN_DRAG_DISTANCE: float = 350.0  # distance min piece -> zone de depot (px)
SCROLL_STEP: float = 60.0  # pixels defiles par cran de molette
SCROLL_WORLD_FACTOR: int = 4  # la bande a faire defiler mesure N hauteurs d'ecran
END_OF_LEVEL_DELAY: float = 0.6  # pause apres la derniere cible avant le bilan
RESULT_INPUT_DELAY: float = 0.5  # ignore les clics a l'arrivee sur un ecran de bilan

# --- Scores ---
WEIGHT_PRECISION: float = 0.4
WEIGHT_COMPLETION: float = 0.3
WEIGHT_SPEED: float = 0.3
# Debit selon la loi de Fitts (bits/s) considere comme 100 % de vitesse.
# Un utilisateur a l'aise se situe vers 3-5 bits/s, un debutant plutot vers 1-2.
REFERENCE_THROUGHPUT: float = 3.0

# --- Tableau des scores ---
SCOREBOARD_SIZE: int = 10
NAME_MAX_LENGTH: int = 15
DEFAULT_PLAYER_NAME: str = "Joueur"

# --- Sauvegardes : <nom>.json dans DATA_DIR (desktop), cle <prefixe><nom> (web) ---
DATA_DIR: Path = _data_dir()
STORAGE_KEY_PREFIX: str = "aimtolearn_"

# --- Couleurs : point unique a modifier pour de futurs skins ---
COLORS: dict[str, tuple[int, ...]] = {
    "background": (24, 28, 38),
    "hud": (36, 42, 56),
    "text": (235, 235, 240),
    "text_dim": (150, 155, 170),
    "target": (240, 90, 70),
    "target_outline": (255, 255, 255),
    "timer": (255, 210, 80),
    "drop_zone": (90, 200, 120),
    "hit": (90, 220, 120),
    "miss": (230, 70, 70),
    "button": (60, 110, 200),
    "button_hover": (80, 135, 230),
    "button_disabled": (50, 56, 70),
    "overlay": (0, 0, 0, 180),
    "scrollbar": (70, 80, 100),
    "highlight": (255, 210, 80),
    "grid": (55, 62, 80),
}
