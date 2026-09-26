"""Bilan de fin de session et saisie du nom pour le tableau des scores."""

import pygame

from config.levels import LEVELS
from config.settings import COLORS, DEFAULT_PLAYER_NAME, NAME_MAX_LENGTH, RESULT_INPUT_DELAY, SCREEN_WIDTH
from game.highscores import insert_score, qualifies
from game.scene_manager import Scene, SceneManager
from game.scenes.level_result import percent
from game.scoring import Session
from lib.storage import load_entries, save_entries
from lib.ui import Button, draw_text

CURSOR_BLINK = 0.5  # demi-periode du clignotement du curseur de saisie (s)


class SessionResultScene(Scene):
    """Recapitulatif de la session ; saisie du nom si le score entre au tableau."""

    def __init__(self, manager: SceneManager, session: Session) -> None:
        super().__init__(manager)
        self.summary = session.summary()
        self.entries = load_entries()
        self.can_register = qualifies(self.entries, self.summary.points)
        self.name = ""
        self.elapsed = 0.0
        label = "Valider" if self.can_register else "Continuer"
        self.button = Button(label, (SCREEN_WIDTH // 2, 640))
        if self.can_register:
            pygame.key.start_text_input()

    def update(self, dt: float) -> None:
        """Horloge pour le clignotement du curseur et le delai de protection."""
        self.elapsed += dt

    def handle_event(self, event: pygame.event.Event) -> None:
        """Saisie du nom (clavier), validation par Entree ou par le bouton."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._leave(save=False)
            return
        if self.can_register:
            # TEXTINPUT respecte la disposition du clavier (AZERTY, accents...)
            if event.type == pygame.TEXTINPUT:
                self.name = (self.name + event.text)[:NAME_MAX_LENGTH]
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._leave(save=True)
                return
        if self.elapsed >= RESULT_INPUT_DELAY and self.button.is_clicked(event):
            self._leave(save=self.can_register)

    def _leave(self, save: bool) -> None:
        """Enregistre eventuellement le score puis affiche le tableau."""
        from game.scenes.scoreboard import ScoreboardScene  # import local : reference circulaire

        highlight = None
        if save:
            name = self.name.strip() or DEFAULT_PLAYER_NAME
            entries, highlight = insert_score(self.entries, name, self.summary.points, self.summary.levels_passed)
            save_entries(entries)
        if self.can_register:
            pygame.key.stop_text_input()
        self.manager.go_to(ScoreboardScene(self.manager, highlight))

    def draw(self, surface: pygame.Surface) -> None:
        """Scores de la session puis zone de saisie."""
        surface.fill(COLORS["background"])
        cx = SCREEN_WIDTH // 2
        s = self.summary
        draw_text(surface, "Bilan de la session", 64, COLORS["text"], center=(cx, 70))
        lines = [
            f"Niveaux réussis : {s.levels_passed} / {len(LEVELS)}",
            f"Précision : {percent(s.precision)}",
            f"Cibles touchées : {percent(s.completion)}",
            f"Vitesse : {percent(s.speed)}",
        ]
        y = 150
        for line in lines:
            draw_text(surface, line, 36, COLORS["text"], center=(cx, y))
            y += 44
        draw_text(surface, f"Score total : {s.points} points", 60, COLORS["highlight"], center=(cx, y + 35))

        if self.can_register:
            draw_text(surface, "Nouveau record ! Tape ton nom :", 36, COLORS["text"], center=(cx, 470))
            box = pygame.Rect(0, 0, 460, 60)
            box.center = (cx, 540)
            pygame.draw.rect(surface, COLORS["hud"], box, border_radius=8)
            pygame.draw.rect(surface, COLORS["highlight"], box, 2, border_radius=8)
            cursor = "_" if int(self.elapsed / CURSOR_BLINK) % 2 == 0 else " "
            draw_text(surface, self.name + cursor, 42, COLORS["text"], center=box.center)
        else:
            draw_text(surface, "Pas de place au tableau cette fois-ci.", 34, COLORS["text_dim"], center=(cx, 520))
        self.button.draw(surface)
