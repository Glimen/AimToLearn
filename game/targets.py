"""Cible : position, forme, deplacement, duree de vie et changements de forme."""

import random
from dataclasses import dataclass, field

from lib.geometry import Area, contains_point


@dataclass
class Target:
    """Une forme a l'ecran (cible, leurre, piece ou zone de depot).

    Les coordonnees sont exprimees dans le repere "monde" du niveau
    (identique a l'ecran sauf pour le niveau molette, qui defile).
    """

    x: float
    y: float
    size: float
    shape: str
    vx: float = 0.0
    vy: float = 0.0
    lifetime: float | None = None
    shapes: tuple[str, ...] = ()  # formes possibles lors d'un changement de forme
    morph_interval: float | None = None
    age: float = 0.0
    _morph_timer: float = field(default=0.0, repr=False)

    def contains(self, px: float, py: float) -> bool:
        """Indique si le point (px, py) est dans la forme courante."""
        return contains_point(self.shape, self.x, self.y, self.size, px, py)

    @property
    def expired(self) -> bool:
        """Vrai si la duree de vie est ecoulee."""
        return self.lifetime is not None and self.age >= self.lifetime

    @property
    def remaining_ratio(self) -> float:
        """Part de la duree de vie restante, entre 0 et 1 (1 si illimitee)."""
        if self.lifetime is None:
            return 1.0
        return max(0.0, 1.0 - self.age / self.lifetime)

    def update(self, dt: float, bounds: Area, rng: random.Random) -> None:
        """Fait vieillir, deplace (avec rebonds sur les bords) et transforme la cible.

        Args:
            dt: Temps ecoule depuis la derniere image, en secondes.
            bounds: Zone dans laquelle la cible rebondit.
            rng: Generateur aleatoire pour le choix de la forme suivante.
        """
        self.age += dt
        self._move(dt, bounds)
        if self.morph_interval is not None:
            self._morph_timer += dt
            if self._morph_timer >= self.morph_interval:
                self._morph_timer = 0.0
                others = [s for s in self.shapes if s != self.shape]
                if others:
                    self.shape = rng.choice(others)

    def _move(self, dt: float, bounds: Area) -> None:
        """Deplace la cible et la fait rebondir sur les bords de la zone."""
        if self.vx == 0.0 and self.vy == 0.0:
            return
        r = self.size / 2
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Rebond : on replace la cible dans la zone et on inverse la composante
        if self.x - r < bounds.x:
            self.x, self.vx = bounds.x + r, abs(self.vx)
        elif self.x + r > bounds.x + bounds.w:
            self.x, self.vx = bounds.x + bounds.w - r, -abs(self.vx)
        if self.y - r < bounds.y:
            self.y, self.vy = bounds.y + r, abs(self.vy)
        elif self.y + r > bounds.y + bounds.h:
            self.y, self.vy = bounds.y + bounds.h - r, -abs(self.vy)
