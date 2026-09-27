"""Deroulement d'un niveau, sans affichage : apparition des cibles, gestes, statistiques.

La scene pygame traduit les evenements souris en appels a LevelRound et dessine
son etat. Toutes les positions recues sont en coordonnees ecran ; elles sont
converties dans le repere "monde" du niveau (decale du defilement au niveau molette).
"""

import math
import random
from collections.abc import Callable

from config.levels import (
    GESTURE_DOUBLE_CLICK,
    GESTURE_DRAG,
    GESTURE_RIGHT_CLICK,
    GESTURE_SCROLL,
    LevelConfig,
)
from config.settings import (
    DOUBLE_CLICK_DELAY,
    MIN_DRAG_DISTANCE,
    MIN_SPAWN_DISTANCE,
    SCROLL_STEP,
    SCROLL_WORLD_FACTOR,
    TARGETS_PER_LEVEL,
)
from game.scoring import LevelStats
from game.targets import Target
from lib.geometry import Area

# Resultats d'une action du joueur, utilises par la scene pour le son et les messages
HIT = "hit"  # cible validee
PROGRESS = "progress"  # premier clic d'un double-clic, ou piece saisie
MISS = "miss"  # clic dans le vide
DECOY = "decoy"  # clic sur un leurre
WRONG_BUTTON = "wrong_button"  # clic sur la cible avec le mauvais bouton
DROP_MISS = "drop_miss"  # piece relachee hors de la zone de depot
EXPIRE = "expire"  # cible disparue
NONE = "none"  # rien a signaler

BUTTON_LEFT = 1
BUTTON_RIGHT = 3

_MAX_PLACEMENT_TRIES = 50
_DECOY_SPACING = 1.6  # ecart min entre formes, en multiple de leur taille

Point = tuple[float, float]


class LevelRound:
    """Etat et regles d'un niveau en cours.

    Attributes:
        level: Configuration du niveau.
        viewport: Zone de jeu visible a l'ecran.
        world: Zone ou vivent les cibles (plus haute que viewport au niveau molette).
        stats: Compteurs pour le calcul du score.
        target: Cible courante (None avant le debut ou apres la fin).
        fixed_shape: Forme a chercher pendant tout le niveau (niveau avec leurres), None sinon.
        decoys: Leurres affiches avec la cible courante.
        drop_zone: Zone de depot (niveau glisser-deposer).
        scroll_offset: Decalage vertical du defilement, en pixels.
        grabbing: Vrai pendant qu'une piece est tenue.
        finished: Vrai quand toutes les cibles sont terminees.
    """

    def __init__(
        self,
        level: LevelConfig,
        viewport: Area,
        rng: random.Random,
        total_targets: int = TARGETS_PER_LEVEL,
    ) -> None:
        self.level = level
        self.viewport = viewport
        self.rng = rng
        self.stats = LevelStats(total_targets=total_targets)
        world_height = viewport.h * (SCROLL_WORLD_FACTOR if level.gesture == GESTURE_SCROLL else 1)
        self.world = Area(viewport.x, viewport.y, viewport.w, world_height)
        self.scroll_offset = 0.0
        self.now = 0.0  # horloge du niveau (s), avancee par update()
        self.target: Target | None = None
        self.decoys: list[Target] = []
        self.drop_zone: Target | None = None
        self.grabbing = False
        self.finished = False
        # Niveau avec leurres : une seule forme a chercher pour tout le niveau,
        # tiree des maintenant pour pouvoir l'annoncer sur l'ecran de consigne
        self.fixed_shape: str | None = rng.choice(level.shapes) if level.decoys else None
        self._grab_offset: Point = (0.0, 0.0)
        self._piece_origin: Point = (0.0, 0.0)
        self._last_target_click: float | None = None
        self._spawn_time = 0.0
        self._fitts_distance = 0.0
        self._fitts_width = 0.0

    # --- API appelee par la scene -------------------------------------------------

    def start(self, cursor: Point) -> None:
        """Fait apparaitre la premiere cible.

        Args:
            cursor: Position ecran du curseur.
        """
        self._spawn(cursor)

    def press(self, button: int, pos: Point) -> str:
        """Traite un appui sur un bouton de la souris.

        Args:
            button: Bouton pygame (1 gauche, 2 milieu, 3 droit).
            pos: Position ecran du clic.

        Returns:
            Le resultat de l'action (constantes du module).
        """
        if self.target is None:
            return NONE
        self.stats.clicks += 1
        wx, wy = self._to_world(pos)
        # Un clic dans le bandeau ne doit pas toucher une cible cachee au-dessus
        if not self.viewport.contains(*pos) or not self.target.contains(wx, wy):
            self._last_target_click = None
            if self.viewport.contains(*pos) and any(d.contains(wx, wy) for d in self.decoys):
                return DECOY
            return MISS

        expected = BUTTON_RIGHT if self.level.gesture == GESTURE_RIGHT_CLICK else BUTTON_LEFT
        if button != expected:
            return WRONG_BUTTON
        self.stats.clicks_on_target += 1

        if self.level.gesture == GESTURE_DOUBLE_CLICK:
            if self._last_target_click is not None and self.now - self._last_target_click <= DOUBLE_CLICK_DELAY:
                return self._hit(pos)
            self._last_target_click = self.now
            return PROGRESS
        if self.level.gesture == GESTURE_DRAG:
            self.grabbing = True
            self._grab_offset = (self.target.x - wx, self.target.y - wy)
            return PROGRESS
        return self._hit(pos)

    def release(self, button: int, pos: Point) -> str:
        """Traite un relachement de bouton (utile seulement au glisser-deposer).

        Args:
            button: Bouton pygame relache.
            pos: Position ecran du relachement.

        Returns:
            HIT si la piece est deposee dans la zone, DROP_MISS sinon, NONE si rien n'etait tenu.
        """
        if not self.grabbing or button != BUTTON_LEFT or self.target is None or self.drop_zone is None:
            return NONE
        self.grabbing = False
        if self.drop_zone.contains(self.target.x, self.target.y):
            return self._hit(pos)
        # Rate : la piece revient a sa place de depart
        self.target.x, self.target.y = self._piece_origin
        return DROP_MISS

    def motion(self, pos: Point) -> None:
        """Deplace la piece tenue avec le curseur.

        Args:
            pos: Position ecran du curseur.
        """
        if not self.grabbing or self.target is None:
            return
        wx, wy = self._to_world(pos)
        r = self.target.size / 2
        # La piece reste dans la zone de jeu
        self.target.x = min(max(wx + self._grab_offset[0], self.world.x + r), self.world.x + self.world.w - r)
        self.target.y = min(max(wy + self._grab_offset[1], self.world.y + r), self.world.y + self.world.h - r)

    def wheel(self, notches: float) -> None:
        """Fait defiler la zone de jeu (niveau molette uniquement).

        Args:
            notches: Crans de molette (positif = vers le haut).
        """
        if self.level.gesture != GESTURE_SCROLL:
            return
        max_offset = self.world.h - self.viewport.h
        self.scroll_offset = min(max(self.scroll_offset - notches * SCROLL_STEP, 0.0), max_offset)

    def update(self, dt: float, cursor: Point) -> str:
        """Avance le temps : deplacement des cibles et gestion des disparitions.

        Args:
            dt: Temps ecoule depuis la derniere image (s).
            cursor: Position ecran du curseur (sert a placer la cible suivante).

        Returns:
            EXPIRE si la cible vient de disparaitre, NONE sinon.
        """
        self.now += dt
        if self.target is None:
            return NONE
        if not self.grabbing:
            self.target.update(dt, self.world, self.rng)
        if self.target.expired:
            self.stats.missed += 1
            self._spawn(cursor)
            return EXPIRE
        return NONE

    @property
    def target_direction(self) -> int:
        """Position de la cible par rapport a la zone visible : -1 au-dessus, 1 en dessous, 0 visible."""
        if self.target is None:
            return 0
        top = self.viewport.y + self.scroll_offset
        if self.target.y < top:
            return -1
        if self.target.y > top + self.viewport.h:
            return 1
        return 0

    # --- Interne -----------------------------------------------------------------

    def _to_world(self, pos: Point) -> Point:
        """Convertit une position ecran en position monde."""
        return pos[0], pos[1] + self.scroll_offset

    def _is_visible(self, y: float, size: float) -> bool:
        """Indique si une forme centree en y (monde) est au moins en partie visible."""
        top = self.viewport.y + self.scroll_offset
        return top - size / 2 < y < top + self.viewport.h + size / 2

    def _random_position(self, size: float, is_valid: Callable[[Point], bool]) -> Point:
        """Tire une position aleatoire dans le monde qui respecte une contrainte.

        Si aucune position valide n'est trouvee apres plusieurs essais, la derniere
        tiree est gardee : mieux vaut une cible un peu mal placee qu'un blocage.
        """
        margin = size / 2 + 5
        pos = (0.0, 0.0)
        for _ in range(_MAX_PLACEMENT_TRIES):
            pos = (
                self.rng.uniform(self.world.x + margin, self.world.x + self.world.w - margin),
                self.rng.uniform(self.world.y + margin, self.world.y + self.world.h - margin),
            )
            if is_valid(pos):
                break
        return pos

    def _spawn(self, cursor: Point) -> None:
        """Remplace la cible courante par la suivante, ou termine le niveau."""
        self.decoys = []
        self.drop_zone = None
        self.grabbing = False
        self._last_target_click = None
        if self.stats.resolved >= self.stats.total_targets:
            self.target = None
            self.finished = True
            return

        lvl = self.level
        cursor_world = self._to_world(cursor)

        def is_valid(p: Point) -> bool:
            # Assez loin du curseur pour qu'il y ait un vrai geste a faire ;
            # au niveau molette, hors de la zone visible pour obliger a defiler
            far_enough = math.dist(p, cursor_world) >= MIN_SPAWN_DISTANCE
            if lvl.gesture == GESTURE_SCROLL:
                return far_enough and not self._is_visible(p[1], lvl.size)
            return far_enough

        x, y = self._random_position(lvl.size, is_valid)
        if lvl.grid:
            x, y = self._snap_to_grid(x, y)
        angle = self.rng.uniform(0, 2 * math.pi)
        self.target = Target(
            x=x,
            y=y,
            size=lvl.size,
            shape=self.fixed_shape or self.rng.choice(lvl.shapes),
            vx=math.cos(angle) * lvl.speed,
            vy=math.sin(angle) * lvl.speed,
            lifetime=lvl.lifetime,
            shapes=lvl.shapes,
            morph_interval=lvl.morph_interval,
        )
        self._spawn_decoys()

        # Mesures pour la loi de Fitts
        self._spawn_time = self.now
        self._fitts_distance = math.dist(cursor_world, (x, y))
        self._fitts_width = lvl.size
        if lvl.gesture == GESTURE_DRAG:
            self._spawn_drop_zone()
            # Approximation : trajet curseur -> piece -> zone, precision imposee par la zone
            self._fitts_distance += math.dist((x, y), (self.drop_zone.x, self.drop_zone.y))
            self._fitts_width = lvl.zone_size

    def _snap_to_grid(self, x: float, y: float) -> Point:
        """Centre la position sur la case du quadrillage qui la contient.

        Le quadrillage part du coin haut-gauche du monde ; la case est bornee aux
        cases entieres, pour ne jamais tomber sur une case coupee par le bord.
        """
        size = self.level.size
        col = min(int((x - self.world.x) // size), int(self.world.w // size) - 1)
        row = min(int((y - self.world.y) // size), int(self.world.h // size) - 1)
        return self.world.x + (col + 0.5) * size, self.world.y + (row + 0.5) * size

    def _spawn_decoys(self) -> None:
        """Place les leurres, d'une autre forme que la cible, sans chevauchement."""
        other_shapes = [s for s in self.level.shapes if s != self.target.shape]
        occupied = [(self.target.x, self.target.y)]
        size = self.level.size

        def is_free(p: Point) -> bool:
            return all(math.dist(p, o) >= size * _DECOY_SPACING for o in occupied)

        for _ in range(self.level.decoys):
            x, y = self._random_position(size, is_free)
            occupied.append((x, y))
            self.decoys.append(Target(x=x, y=y, size=size, shape=self.rng.choice(other_shapes)))

    def _spawn_drop_zone(self) -> None:
        """Place la zone de depot loin de la piece."""
        piece = (self.target.x, self.target.y)
        self._piece_origin = piece
        x, y = self._random_position(
            self.level.zone_size, lambda p: math.dist(p, piece) >= MIN_DRAG_DISTANCE
        )
        self.drop_zone = Target(x=x, y=y, size=self.level.zone_size, shape="square")

    def _hit(self, pos: Point) -> str:
        """Valide la cible courante et passe a la suivante."""
        self.stats.hits += 1
        self.stats.samples.append((self._fitts_distance, self._fitts_width, self.now - self._spawn_time))
        self._spawn(pos)
        return HIT
