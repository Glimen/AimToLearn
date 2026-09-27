"""Definition des niveaux du mode debutant (donnees pures, sans logique)."""

from dataclasses import dataclass

# Gestes attendus du joueur
GESTURE_CLICK = "click"
GESTURE_DOUBLE_CLICK = "double_click"
GESTURE_RIGHT_CLICK = "right_click"
GESTURE_DRAG = "drag"
GESTURE_SCROLL = "scroll"

ALL_SHAPES = ("circle", "square", "triangle", "star")


@dataclass(frozen=True)
class LevelConfig:
    """Parametres d'un niveau.

    Attributes:
        name: Nom affiche.
        instruction: Consigne affichee avant le debut du niveau.
        gesture: Geste attendu (constantes GESTURE_*).
        size: Taille de la cible en pixels (diametre / cote).
        speed: Vitesse de deplacement en px/s (0 = cible fixe).
        lifetime: Duree de vie d'une cible en secondes (None = illimitee).
        shapes: Formes possibles pour la cible.
        decoys: Nombre de leurres affiches en meme temps que la cible.
        morph_interval: Intervalle de changement de forme en secondes (None = jamais).
        zone_size: Taille de la zone de depot (niveau glisser-deposer uniquement).
        grid: Vrai pour afficher un quadrillage dont la cible est une case.
    """

    name: str
    instruction: str
    gesture: str = GESTURE_CLICK
    size: int = 100
    speed: float = 0.0
    lifetime: float | None = None
    shapes: tuple[str, ...] = ("circle",)
    decoys: int = 0
    morph_interval: float | None = None
    zone_size: int = 0
    grid: bool = False


LEVELS: tuple[LevelConfig, ...] = (
    LevelConfig(
        name="Grosse cible",
        instruction="Place la flèche sur le rond et fais un clic gauche.",
        size=160,
    ),
    LevelConfig(
        name="Cible moyenne",
        instruction="Même exercice, mais la cible est plus petite.",
        size=100,
    ),
    LevelConfig(
        name="Petite cible",
        instruction="Vise bien : la cible est petite.",
        size=60,
    ),
    LevelConfig(
        name="Contre la montre",
        instruction="Clique sur la cible avant qu'elle disparaisse. "
        "Le cercle jaune montre le temps restant.",
        size=90,
        lifetime=3.0,
    ),
    LevelConfig(
        name="Cible mobile",
        instruction="La cible se déplace lentement. Suis-la et clique dessus.",
        size=90,
        speed=80.0,
        lifetime=4.0,
    ),
    LevelConfig(
        name="Double-clic",
        instruction="Fais deux clics gauches rapides sur la cible.",
        gesture=GESTURE_DOUBLE_CLICK,
        size=100,
    ),
    LevelConfig(
        name="Clic droit",
        instruction="Clique sur la cible avec le bouton DROIT de la souris.",
        gesture=GESTURE_RIGHT_CLICK,
        size=100,
    ),
    LevelConfig(
        name="La bonne forme",
        instruction="Plusieurs formes apparaissent. Clique seulement sur ta forme.",
        size=90,
        lifetime=5.0,
        shapes=ALL_SHAPES,
        decoys=3,
    ),
    LevelConfig(
        name="Glisser-déposer",
        instruction="Garde le clic gauche enfoncé sur le rond, amène-le dans le "
        "carré vert, puis relâche.",
        gesture=GESTURE_DRAG,
        size=70,
        zone_size=140,
    ),
    LevelConfig(
        name="Molette",
        instruction="La cible est cachée plus haut ou plus bas. Fais tourner la "
        "molette pour la trouver, puis clique dessus.",
        gesture=GESTURE_SCROLL,
        size=80,
    ),
    LevelConfig(
        name="Le grand défi",
        instruction="Petite, rapide, et elle change de forme. Bonne chance !",
        size=55,
        speed=220.0,
        lifetime=4.0,
        shapes=ALL_SHAPES,
        morph_interval=1.0,
    ),
    # Niveaux de precision : la case fait 1/4 du plus petit rond des niveaux
    # precedents (55 px, grand defi), puis encore moitie moins
    LevelConfig(
        name="Précision",
        instruction="Une case du quadrillage s'allume : clique dessus. "
        "Elle est toute petite : vise bien.",
        size=14,
        shapes=("square",),
        grid=True,
    ),
    LevelConfig(
        name="Précision extrême",
        instruction="Même exercice, avec des cases deux fois plus petites. "
        "Prends ton temps pour bien viser.",
        size=7,
        shapes=("square",),
        grid=True,
    ),
)
