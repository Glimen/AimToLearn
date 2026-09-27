"""Ecran de jeu d'un niveau : traduit la souris en actions et dessine l'etat du niveau."""

import random
from dataclasses import dataclass

import pygame

from config.levels import GESTURE_DRAG, GESTURE_RIGHT_CLICK, GESTURE_SCROLL, LEVELS
from config.settings import COLORS, END_OF_LEVEL_DELAY, HUD_HEIGHT, SCREEN_HEIGHT, SCREEN_WIDTH
from game import round as rnd
from game.demo import GestureDemo
from game.render import draw_drop_zone, draw_grid, draw_lit_cell, draw_shape, draw_target
from game.scene_manager import Scene, SceneManager
from game.scoring import Session, compute_level_score
from lib.geometry import Area
from lib.ui import draw_text, wrap_text

MARKER_DURATION = 0.35  # duree de l'anneau affiche a chaque clic (s)
MESSAGE_DURATION = 1.5  # duree d'affichage d'un message d'aide (s)
SCROLLBAR_WIDTH = 14
DEMO_PANEL_SIZE = (720, 250)  # panneau de demonstration de l'ecran de consigne

SHAPE_LABELS = {"circle": "le cercle", "square": "le carré", "triangle": "le triangle", "star": "l'étoile"}

OUTCOME_SOUNDS = {
    rnd.HIT: "hit",
    rnd.PROGRESS: "progress",
    rnd.MISS: "miss",
    rnd.DECOY: "miss",
    rnd.WRONG_BUTTON: "miss",
    rnd.DROP_MISS: "miss",
    rnd.EXPIRE: "expire",
}


@dataclass
class _Marker:
    """Anneau de retour visuel a l'endroit d'un clic."""

    x: float
    y: float
    color: tuple[int, ...]
    age: float = 0.0


class LevelScene(Scene):
    """Un niveau : ecran de consigne, puis 15 cibles, puis passage au bilan."""

    def __init__(self, manager: SceneManager, session: Session, level_index: int) -> None:
        super().__init__(manager)
        self.session = session
        self.level_index = level_index
        self.level = LEVELS[level_index]
        self.viewport = Area(0, HUD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - HUD_HEIGHT)
        self.round = rnd.LevelRound(self.level, self.viewport, random.Random())
        self.started = False  # False tant que la consigne est affichee
        self.demo = GestureDemo(self.level, self.round.fixed_shape)
        self.end_timer = 0.0
        self.markers: list[_Marker] = []
        self.message = ""
        self.message_timer = 0.0

    # --- Evenements ----------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Echap abandonne ; sinon transmet la souris au niveau."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._end_session()
            return
        # Les boutons 4 et 5 sont les anciens evenements de molette : ce ne sont pas des clics
        is_click = event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 2, 3)
        if not self.started:
            if is_click:  # ce clic lance le niveau, il n'est pas compte
                self.started = True
                self.round.start(event.pos)
            return
        if is_click:
            self._feedback(self.round.press(event.button, event.pos), event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._feedback(self.round.release(event.button, event.pos), event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self.round.motion(event.pos)
        elif event.type == pygame.MOUSEWHEEL:
            self.round.wheel(event.y)

    def _feedback(self, outcome: str, pos: tuple[int, int] | None) -> None:
        """Son, anneau et message d'aide correspondant au resultat d'une action."""
        sound = OUTCOME_SOUNDS.get(outcome)
        if sound:
            self.manager.sounds.play(sound)
        if pos is not None and outcome in (rnd.HIT, rnd.MISS, rnd.DECOY, rnd.WRONG_BUTTON):
            color = COLORS["hit"] if outcome == rnd.HIT else COLORS["miss"]
            self.markers.append(_Marker(pos[0], pos[1], color))
        message = self._message_for(outcome)
        if message:
            self.message, self.message_timer = message, MESSAGE_DURATION

    def _message_for(self, outcome: str) -> str:
        """Message d'aide pedagogique a afficher apres une erreur."""
        if outcome == rnd.WRONG_BUTTON:
            side = "droit" if self.level.gesture == GESTURE_RIGHT_CLICK else "gauche"
            return f"Utilise le bouton {side} de la souris"
        if outcome == rnd.DECOY:
            return "Ce n'est pas la bonne forme"
        if outcome == rnd.DROP_MISS:
            return "Relâche le rond dans le carré vert"
        if outcome == rnd.EXPIRE:
            return "Trop tard !"
        return ""

    # --- Logique -------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Avance le niveau et passe au bilan une fois termine."""
        for marker in self.markers:
            marker.age += dt
        self.markers = [m for m in self.markers if m.age < MARKER_DURATION]
        self.message_timer = max(0.0, self.message_timer - dt)
        if not self.started:
            self.demo.update(dt)
            return
        self._feedback(self.round.update(dt, pygame.mouse.get_pos()), None)
        if self.round.finished:
            # Courte pause pour voir le dernier retour avant le bilan
            self.end_timer += dt
            if self.end_timer >= END_OF_LEVEL_DELAY:
                score = compute_level_score(self.round.stats)
                self.session.record(self.level_index, score)
                from game.scenes.level_result import LevelResultScene  # import local : reference circulaire

                self.manager.go_to(LevelResultScene(self.manager, self.session, self.level_index, score))

    def _end_session(self) -> None:
        """Abandon : bilan de session si au moins un niveau est termine, menu sinon."""
        if self.session.results:
            from game.scenes.session_result import SessionResultScene

            self.manager.go_to(SessionResultScene(self.manager, self.session))
        else:
            from game.scenes.menu import MenuScene

            self.manager.go_to(MenuScene(self.manager))

    # --- Dessin --------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        """Zone de jeu, bandeau, puis consigne par-dessus si le niveau n'a pas commence."""
        surface.fill(COLORS["background"])
        offset = self.round.scroll_offset
        # Tout ce qui est dans le monde du niveau est coupe au bord de la zone de jeu
        surface.set_clip(pygame.Rect(self.viewport))
        if self.level.grid:
            # Quadrillage aligne sur le coin de la zone de jeu, comme le placement des cibles
            draw_grid(surface, pygame.Rect(self.viewport), self.level.size, (self.viewport.x, self.viewport.y))
        if self.round.drop_zone is not None:
            draw_drop_zone(surface, self.round.drop_zone, offset)
        for decoy in self.round.decoys:
            draw_shape(surface, decoy.shape, decoy.x, decoy.y - offset, decoy.size, COLORS["target"], COLORS["target_outline"])
        if self.round.target is not None and self.level.grid:
            draw_lit_cell(surface, self.round.target, offset)
        elif self.round.target is not None:
            # Avec des leurres, l'arc du temps restant designerait la cible : on le masque
            draw_target(surface, self.round.target, offset, show_timer=not self.round.decoys)
        surface.set_clip(None)

        for marker in self.markers:
            radius = 6 + marker.age / MARKER_DURATION * 24
            pygame.draw.circle(surface, marker.color, (marker.x, marker.y), radius, 3)
        if self.level.gesture == GESTURE_SCROLL:
            self._draw_scrollbar(surface)
        self._draw_hud(surface)
        if not self.started:
            self._draw_instructions(surface)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        """Bandeau : niveau, progression, cibles ratees, aide contextuelle."""
        pygame.draw.rect(surface, COLORS["hud"], (0, 0, SCREEN_WIDTH, HUD_HEIGHT))
        stats = self.round.stats
        current = min(stats.resolved + 1, stats.total_targets)
        title = f"Niveau {self.level_index + 1}/{len(LEVELS)} : {self.level.name}"
        draw_text(surface, title, 30, COLORS["text"], midleft=(20, 22))
        draw_text(surface, f"Cible {current}/{stats.total_targets}", 30, COLORS["text"], center=(SCREEN_WIDTH // 2, 22))
        draw_text(surface, f"Ratées : {stats.missed}", 30, COLORS["text"], midright=(SCREEN_WIDTH - 20, 22))

        hint, color = self._hud_hint()
        if hint:
            draw_text(surface, hint, 28, color, center=(SCREEN_WIDTH // 2, 52))

    def _hud_hint(self) -> tuple[str, tuple[int, ...]]:
        """Deuxieme ligne du bandeau : message d'erreur en priorite, sinon aide du niveau."""
        if self.message_timer > 0:
            return self.message, COLORS["miss"]
        target = self.round.target
        if target is None:
            return "", COLORS["text"]
        if self.round.decoys:
            return f"Clique sur {SHAPE_LABELS[target.shape]}", COLORS["highlight"]
        if self.level.gesture == GESTURE_SCROLL and self.round.target_direction != 0:
            where = "plus haut" if self.round.target_direction < 0 else "plus bas"
            return f"La cible est {where} : fais tourner la molette", COLORS["highlight"]
        if self.level.gesture == GESTURE_DRAG and self.round.grabbing:
            return "Garde le bouton enfoncé jusqu'au carré vert", COLORS["highlight"]
        return "", COLORS["text"]

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        """Ascenseur a droite, avec un repere jaune a la hauteur de la cible."""
        vp, world = self.viewport, self.round.world
        ratio = vp.h / world.h
        x = vp.x + vp.w - SCROLLBAR_WIDTH
        pygame.draw.rect(surface, COLORS["hud"], (x, vp.y, SCROLLBAR_WIDTH, vp.h))
        thumb_y = vp.y + self.round.scroll_offset * ratio
        pygame.draw.rect(surface, COLORS["scrollbar"], (x, thumb_y, SCROLLBAR_WIDTH, vp.h * ratio), border_radius=6)
        if self.round.target is not None:
            marker_y = vp.y + (self.round.target.y - world.y) * ratio
            pygame.draw.rect(surface, COLORS["highlight"], (x, marker_y - 3, SCROLLBAR_WIDTH, 6))

    def _draw_instructions(self, surface: pygame.Surface) -> None:
        """Voile sombre avec le nom du niveau, sa consigne et la demonstration du geste."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(COLORS["overlay"])
        surface.blit(overlay, (0, 0))
        cx = SCREEN_WIDTH // 2
        draw_text(surface, f"Niveau {self.level_index + 1} : {self.level.name}", 64, COLORS["highlight"], center=(cx, 110))
        y = 175
        for line in wrap_text(self.level.instruction, 36, SCREEN_WIDTH - 300):
            draw_text(surface, line, 36, COLORS["text"], center=(cx, y))
            y += 42
        if self.round.fixed_shape:
            label = f"Ta forme pour tout le niveau : {SHAPE_LABELS[self.round.fixed_shape]}"
            draw_text(surface, label, 36, COLORS["highlight"], center=(cx, y))
        # Position fixe du panneau : consigne (et forme a chercher) sur deux lignes au plus
        panel = pygame.Rect((0, 0), DEMO_PANEL_SIZE)
        panel.midtop = (cx, 270)
        self.demo.draw(surface, panel)
        draw_text(surface, "Clique n'importe où pour commencer", 34, COLORS["text_dim"], center=(cx, 580))
        draw_text(surface, "Échap : terminer la session", 26, COLORS["text_dim"], center=(cx, SCREEN_HEIGHT - 40))
