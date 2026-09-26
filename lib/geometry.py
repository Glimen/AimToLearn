"""Geometrie des formes de cible : contours et test d'appartenance d'un point."""

import math
from typing import NamedTuple

STAR_INNER_RATIO = 0.45  # rayon des creux de l'etoile / rayon des pointes


class Area(NamedTuple):
    """Rectangle en coordonnees flottantes (x, y = coin haut-gauche)."""

    x: float
    y: float
    w: float
    h: float

    def contains(self, px: float, py: float) -> bool:
        """Indique si le point (px, py) est dans le rectangle."""
        return self.x <= px < self.x + self.w and self.y <= py < self.y + self.h


def shape_polygon(shape: str, cx: float, cy: float, size: float) -> list[tuple[float, float]]:
    """Calcule les sommets d'une forme polygonale centree en (cx, cy).

    Args:
        shape: "square", "triangle" ou "star" (le cercle n'est pas un polygone).
        cx: Abscisse du centre.
        cy: Ordonnee du centre.
        size: Taille de la forme (cote du carre, diametre du cercle circonscrit sinon).

    Returns:
        La liste des sommets dans l'ordre du contour.

    Raises:
        ValueError: Si la forme n'est pas polygonale ou inconnue.
    """
    r = size / 2
    if shape == "square":
        return [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)]
    if shape == "triangle":
        # Triangle equilateral pointe en haut (y descend a l'ecran, donc -90 deg = haut)
        angles = (-90, 30, 150)
        return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in angles]
    if shape == "star":
        # 10 sommets alternant pointes (rayon r) et creux (rayon r * ratio)
        points = []
        for i in range(10):
            radius = r if i % 2 == 0 else r * STAR_INNER_RATIO
            angle = math.radians(-90 + i * 36)
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        return points
    raise ValueError(f"Forme non polygonale ou inconnue : {shape}")


def point_in_polygon(px: float, py: float, polygon: list[tuple[float, float]]) -> bool:
    """Test d'appartenance par lancer de rayon (fonctionne aussi pour l'etoile, non convexe).

    Args:
        px: Abscisse du point.
        py: Ordonnee du point.
        polygon: Sommets du polygone.

    Returns:
        True si le point est a l'interieur.
    """
    inside = False
    j = len(polygon) - 1
    for i, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[j]
        # Le rayon horizontal partant du point croise-t-il l'arete (i, j) ?
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def contains_point(shape: str, cx: float, cy: float, size: float, px: float, py: float) -> bool:
    """Indique si le point (px, py) est dans la forme centree en (cx, cy).

    Args:
        shape: "circle", "square", "triangle" ou "star".
        cx: Abscisse du centre de la forme.
        cy: Ordonnee du centre de la forme.
        size: Taille de la forme.
        px: Abscisse du point teste.
        py: Ordonnee du point teste.

    Returns:
        True si le point est dans la forme.
    """
    if shape == "circle":
        return math.hypot(px - cx, py - cy) <= size / 2
    return point_in_polygon(px, py, shape_polygon(shape, cx, cy, size))
