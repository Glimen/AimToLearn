"""Dessin des formes et des cibles."""

import math

import pygame

from config.settings import COLORS
from game.targets import Target
from lib.geometry import shape_polygon

OUTLINE_WIDTH = 3
TIMER_GAP = 8  # ecart entre la cible et l'arc du compte a rebours (px)
TIMER_WIDTH = 4


def draw_shape(
    surface: pygame.Surface,
    shape: str,
    x: float,
    y: float,
    size: float,
    color: tuple[int, ...],
    outline: tuple[int, ...] | None = None,
) -> None:
    """Dessine une forme pleine, avec un contour optionnel.

    Args:
        surface: Surface cible.
        shape: "circle", "square", "triangle" ou "star".
        x: Abscisse du centre.
        y: Ordonnee du centre.
        size: Taille de la forme.
        color: Couleur de remplissage.
        outline: Couleur du contour (None = pas de contour).
    """
    if shape == "circle":
        pygame.draw.circle(surface, color, (x, y), size / 2)
        if outline:
            pygame.draw.circle(surface, outline, (x, y), size / 2, OUTLINE_WIDTH)
        return
    points = shape_polygon(shape, x, y, size)
    pygame.draw.polygon(surface, color, points)
    if outline:
        pygame.draw.polygon(surface, outline, points, OUTLINE_WIDTH)


def draw_target(surface: pygame.Surface, target: Target, offset_y: float, show_timer: bool = True) -> None:
    """Dessine une cible et, si elle expire, l'arc du temps restant.

    Args:
        surface: Surface cible.
        target: Cible a dessiner.
        offset_y: Defilement vertical a retrancher (niveau molette).
        show_timer: False pour masquer l'arc (niveau avec leurres : il designerait la cible).
    """
    y = target.y - offset_y
    draw_shape(surface, target.shape, target.x, y, target.size, COLORS["target"], COLORS["target_outline"])
    if show_timer and target.lifetime is not None:
        radius = target.size / 2 + TIMER_GAP
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = (round(target.x), round(y))
        # Arc partant du haut, qui se vide dans le sens horaire
        start = math.pi / 2
        pygame.draw.arc(surface, COLORS["timer"], rect, start, start + 2 * math.pi * target.remaining_ratio, TIMER_WIDTH)


def draw_grid(surface: pygame.Surface, area: pygame.Rect, cell: int, origin: tuple[float, float]) -> None:
    """Dessine un quadrillage de cases de cote cell, aligne sur le point origin.

    Args:
        surface: Surface cible.
        area: Zone a quadriller.
        cell: Cote d'une case (px).
        origin: Coin d'une case quelconque ; les lignes passent par ce point.
    """
    color = COLORS["grid"]
    # Premiere ligne visible : origine ramenee juste avant le bord de la zone
    x = area.left + (origin[0] - area.left) % cell
    while x < area.right:
        pygame.draw.line(surface, color, (x, area.top), (x, area.bottom - 1))
        x += cell
    y = area.top + (origin[1] - area.top) % cell
    while y < area.bottom:
        pygame.draw.line(surface, color, (area.left, y), (area.right - 1, y))
        y += cell


def draw_lit_cell(surface: pygame.Surface, target: Target, offset_y: float) -> None:
    """Dessine la case allumee du quadrillage (sans contour : il cacherait une case de 7 px)."""
    rect = pygame.Rect(round(target.x - target.size / 2), round(target.y - offset_y - target.size / 2), target.size, target.size)
    pygame.draw.rect(surface, COLORS["highlight"], rect)


def draw_drop_zone(surface: pygame.Surface, zone: Target, offset_y: float) -> None:
    """Dessine la zone de depot du glisser-deposer (carre vert en contour)."""
    rect = pygame.Rect(0, 0, zone.size, zone.size)
    rect.center = (round(zone.x), round(zone.y - offset_y))
    pygame.draw.rect(surface, COLORS["drop_zone"], rect, 5, border_radius=8)
