"""Demonstration animee du geste attendu, jouee en boucle sur l'ecran de consigne.

Chaque image de l'animation est calculee a partir du temps ecoule dans la boucle
(pas d'etat accumule) : un curseur fictif realise le geste sur une cible qui a
les caracteristiques du niveau, et un pictogramme de souris montre le bouton utilise.
"""

import math
from dataclasses import dataclass, field

import pygame

from config.levels import (
    GESTURE_DOUBLE_CLICK,
    GESTURE_DRAG,
    GESTURE_RIGHT_CLICK,
    GESTURE_SCROLL,
    LevelConfig,
)
from config.settings import COLORS
from game.render import draw_drop_zone, draw_grid, draw_lit_cell, draw_shape, draw_target
from game.targets import Target
from lib.ui import draw_text

PRESS_TIME = 0.12  # duree d'affichage d'un bouton enfonce (s)
RING_TIME = 0.4  # duree de l'anneau vert apres une reussite (s)
MOUSE_PANEL_WIDTH = 150  # largeur reservee au pictogramme de souris, a droite

# Duree d'une boucle d'animation selon le geste (s)
LOOP_DURATION = {GESTURE_DRAG: 3.4, GESTURE_SCROLL: 3.4}
DEFAULT_LOOP_DURATION = 2.6

GESTURE_LABELS = {
    GESTURE_DOUBLE_CLICK: "Double-clic gauche",
    GESTURE_RIGHT_CLICK: "Clic droit",
    GESTURE_DRAG: "Garder appuyé",
    GESTURE_SCROLL: "Molette, puis clic",
}
DEFAULT_GESTURE_LABEL = "Clic gauche"

# Contour du curseur fleche, pointe en (0, 0)
CURSOR_SHAPE = ((0, 0), (0, 22), (6, 17), (10, 26), (14, 24), (10, 15), (17, 15))

Point = tuple[float, float]


@dataclass
class DemoFrame:
    """Contenu d'une image de la demonstration (coordonnees ecran)."""

    cursor: Point
    pressed: str | None = None  # "left", "right" ou "wheel"
    target: Target | None = None
    decoys: list[Target] = field(default_factory=list)
    zone: Target | None = None
    ring: Point | None = None  # anneau vert de reussite


def _lerp(a: Point, b: Point, ratio: float) -> Point:
    """Interpolation lineaire entre deux points."""
    return a[0] + (b[0] - a[0]) * ratio, a[1] + (b[1] - a[1]) * ratio


def _ease(ratio: float) -> float:
    """Acceleration puis deceleration (smoothstep), borne a [0, 1]."""
    ratio = min(max(ratio, 0.0), 1.0)
    return ratio * ratio * (3 - 2 * ratio)


class GestureDemo:
    """Animation en boucle du geste d'un niveau."""

    def __init__(self, level: LevelConfig, target_shape: str | None = None) -> None:
        """Prepare l'animation.

        Args:
            level: Niveau dont on montre le geste.
            target_shape: Forme a chercher (niveau avec leurres), la meme que dans le niveau.
        """
        self.level = level
        self.target_shape = target_shape
        self.duration = LOOP_DURATION.get(level.gesture, DEFAULT_LOOP_DURATION)
        self.t = 0.0

    def update(self, dt: float) -> None:
        """Avance l'animation (elle reboucle a la fin)."""
        self.t = (self.t + dt) % self.duration

    def draw(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Dessine le panneau de demonstration.

        Args:
            surface: Surface cible.
            rect: Emplacement du panneau (zone d'animation a gauche, souris a droite).
        """
        pygame.draw.rect(surface, COLORS["background"], rect, border_radius=12)
        pygame.draw.rect(surface, COLORS["scrollbar"], rect, 2, border_radius=12)
        area = pygame.Rect(rect.x, rect.y, rect.w - MOUSE_PANEL_WIDTH, rect.h)
        frame = self._frame(area)

        # Les formes restent dans la zone d'animation (utile pour le defilement)
        surface.set_clip(area)
        if frame.zone is not None:
            draw_drop_zone(surface, frame.zone, 0)
        for decoy in frame.decoys:
            draw_shape(surface, decoy.shape, decoy.x, decoy.y, decoy.size, COLORS["target"], COLORS["target_outline"])
        if self.level.grid and frame.target is not None:
            # Quadrillage aligne sur la case allumee
            half = self.level.size / 2
            draw_grid(surface, area, self.level.size, (frame.target.x - half, frame.target.y - half))
            draw_lit_cell(surface, frame.target, 0)
        elif frame.target is not None:
            draw_target(surface, frame.target, 0, show_timer=not self.level.decoys)
        if frame.ring is not None:
            pygame.draw.circle(surface, COLORS["hit"], frame.ring, 22, 3)
        surface.set_clip(None)

        _draw_cursor(surface, frame.cursor)
        mouse_center = (rect.right - MOUSE_PANEL_WIDTH // 2, rect.centery - 15)
        _draw_mouse(surface, mouse_center, frame.pressed)
        label = GESTURE_LABELS.get(self.level.gesture, DEFAULT_GESTURE_LABEL)
        draw_text(surface, label, 22, COLORS["text_dim"], center=(mouse_center[0], rect.bottom - 25))

    # --- Calcul des images, un scenario par geste ---------------------------------

    def _frame(self, area: pygame.Rect) -> DemoFrame:
        """Aiguille vers le scenario du geste du niveau."""
        if self.level.gesture == GESTURE_DRAG:
            return self._drag_frame(area)
        if self.level.gesture == GESTURE_SCROLL:
            return self._scroll_frame(area)
        return self._click_frame(area)

    def _click_frame(self, area: pygame.Rect) -> DemoFrame:
        """Clic simple, double ou droit ; cible mobile, ephemere, changeante ou avec leurres."""
        lvl, t = self.level, self.t
        button = "right" if lvl.gesture == GESTURE_RIGHT_CLICK else "left"
        presses = (1.2, 1.4) if lvl.gesture == GESTURE_DOUBLE_CLICK else (1.2,)
        hit_time = presses[-1]

        def target_pos(time: float) -> Point:
            # Cible mobile : va-et-vient horizontal, d'autant plus rapide que le niveau l'est
            x = area.x + area.w * 0.65
            if lvl.speed:
                x = area.centerx + math.sin(time * lvl.speed / 60) * area.w * 0.25
            return x, area.centery

        start = (area.x + 40, area.bottom - 30)
        aim = target_pos(min(t, hit_time))
        cursor = _lerp(start, aim, _ease(t / 1.0))
        pressed = button if any(p <= t < p + PRESS_TIME for p in presses) else None

        frame = DemoFrame(cursor=cursor, pressed=pressed)
        if t < hit_time:
            frame.target = Target(
                x=aim[0], y=aim[1], size=lvl.size, shape=self._shape_at(t), lifetime=lvl.lifetime, age=t
            )
        elif t < hit_time + RING_TIME:
            frame.ring = cursor
        if lvl.decoys:
            # Leurres fixes, des autres formes que celle a chercher
            others = [s for s in lvl.shapes if s != self.target_shape]
            spots = ((0.2, 0.3), (0.4, 0.75), (0.85, 0.25))
            size = lvl.size * 0.8  # un peu reduits pour tenir dans le panneau
            for shape, (fx, fy) in zip(others, spots):
                frame.decoys.append(Target(x=area.x + area.w * fx, y=area.y + area.h * fy, size=size, shape=shape))
        return frame

    def _shape_at(self, t: float) -> str:
        """Forme de la cible a l'instant t (forme a chercher si leurres, cycle si changeante)."""
        lvl = self.level
        if lvl.decoys and self.target_shape:
            return self.target_shape
        if lvl.morph_interval:
            return lvl.shapes[int(t / lvl.morph_interval) % len(lvl.shapes)]
        return lvl.shapes[0]

    def _drag_frame(self, area: pygame.Rect) -> DemoFrame:
        """Saisie de la piece, deplacement bouton enfonce, depot dans le carre vert."""
        lvl, t = self.level, self.t
        piece_start = (area.x + area.w * 0.22, area.centery)
        zone_pos = (area.x + area.w * 0.75, area.centery)
        start = (area.x + 30, area.bottom - 20)
        grab, move_start, move_end, release = 0.8, 1.0, 2.2, 2.4

        if t < grab:
            cursor, piece = _lerp(start, piece_start, _ease(t / grab)), piece_start
        elif t < move_start:
            cursor, piece = piece_start, piece_start
        else:
            piece = _lerp(piece_start, zone_pos, _ease((t - move_start) / (move_end - move_start)))
            cursor = piece
        frame = DemoFrame(
            cursor=cursor,
            pressed="left" if grab <= t < release else None,
            target=Target(x=piece[0], y=piece[1], size=lvl.size, shape="circle"),
            zone=Target(x=zone_pos[0], y=zone_pos[1], size=lvl.zone_size, shape="square"),
        )
        if release <= t < release + RING_TIME:
            frame.ring = zone_pos
        return frame

    def _scroll_frame(self, area: pygame.Rect) -> DemoFrame:
        """Defilement a la molette pour faire apparaitre la cible, puis clic."""
        lvl, t = self.level, self.t
        scroll_end, aim_end, click = 1.4, 2.3, 2.5
        # La cible part sous la zone visible et remonte jusqu'au centre
        hidden_y = area.bottom + lvl.size
        target_y = hidden_y + (area.centery - hidden_y) * _ease(t / scroll_end)
        target = (area.x + area.w * 0.65, target_y)
        rest = (area.x + area.w * 0.3, area.y + area.h * 0.4)

        cursor = rest if t < scroll_end else _lerp(rest, target, _ease((t - scroll_end) / (aim_end - scroll_end)))
        pressed = "wheel" if t < scroll_end else ("left" if click <= t < click + PRESS_TIME else None)
        frame = DemoFrame(cursor=cursor, pressed=pressed)
        if t < click:
            frame.target = Target(x=target[0], y=target[1], size=lvl.size, shape="circle")
        elif t < click + RING_TIME:
            frame.ring = target
        return frame


def _draw_cursor(surface: pygame.Surface, pos: Point) -> None:
    """Dessine une fleche de souris blanche cerclee de noir, pointe en pos."""
    points = [(pos[0] + dx, pos[1] + dy) for dx, dy in CURSOR_SHAPE]
    pygame.draw.polygon(surface, (255, 255, 255), points)
    pygame.draw.polygon(surface, (0, 0, 0), points, 2)


def _draw_mouse(surface: pygame.Surface, center: tuple[int, int], pressed: str | None) -> None:
    """Dessine un pictogramme de souris, la partie utilisee en surbrillance.

    Args:
        surface: Surface cible.
        center: Centre du pictogramme.
        pressed: "left", "right", "wheel" ou None.
    """
    width, height = 76, 116
    body = pygame.Rect(0, 0, width, height)
    body.center = center
    button_h = 44
    left = pygame.Rect(body.x, body.y, width // 2, button_h)
    right = pygame.Rect(body.centerx, body.y, width // 2, button_h)
    wheel = pygame.Rect(0, 0, 10, 22)
    wheel.center = (body.centerx, body.y + button_h // 2)

    pygame.draw.rect(surface, COLORS["hud"], body, border_radius=34)
    active = COLORS["highlight"]
    if pressed == "left":
        pygame.draw.rect(surface, active, left, border_top_left_radius=34)
    elif pressed == "right":
        pygame.draw.rect(surface, active, right, border_top_right_radius=34)
    pygame.draw.rect(surface, COLORS["text_dim"], body, 2, border_radius=34)
    # Separations : entre les deux boutons, et sous les boutons
    pygame.draw.line(surface, COLORS["text_dim"], (body.centerx, body.y), (body.centerx, body.y + button_h), 2)
    pygame.draw.line(surface, COLORS["text_dim"], (body.x + 2, body.y + button_h), (body.right - 3, body.y + button_h), 2)
    pygame.draw.rect(surface, active if pressed == "wheel" else COLORS["text_dim"], wheel, border_radius=5)
