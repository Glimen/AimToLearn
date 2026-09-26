"""Menu principal."""

import pygame

from config.settings import COLORS, IS_WEB, SCREEN_WIDTH
from game.scene_manager import Scene, SceneManager
from game.scoring import Session
from lib.ui import Button, draw_text


class MenuScene(Scene):
    """Ecran d'accueil : jouer, voir les scores, quitter (desktop)."""

    def __init__(self, manager: SceneManager) -> None:
        super().__init__(manager)
        cx = SCREEN_WIDTH // 2
        self.play_button = Button("Jouer", (cx, 360))
        self.scores_button = Button("Meilleurs scores", (cx, 440))
        # Dans le navigateur, on ferme l'onglet : pas de bouton Quitter
        self.quit_button = None if IS_WEB else Button("Quitter", (cx, 520))

    def handle_event(self, event: pygame.event.Event) -> None:
        """Clic sur un bouton du menu."""
        # Imports locaux : les ecrans se referencent mutuellement (import circulaire sinon)
        if self.play_button.is_clicked(event):
            from game.scenes.level import LevelScene

            self.manager.go_to(LevelScene(self.manager, Session(), 0))
        elif self.scores_button.is_clicked(event):
            from game.scenes.scoreboard import ScoreboardScene

            self.manager.go_to(ScoreboardScene(self.manager))
        elif self.quit_button is not None and self.quit_button.is_clicked(event):
            self.manager.running = False

    def draw(self, surface: pygame.Surface) -> None:
        """Titre et boutons."""
        surface.fill(COLORS["background"])
        cx = SCREEN_WIDTH // 2
        draw_text(surface, "AimToLearn", 110, COLORS["highlight"], center=(cx, 170))
        draw_text(surface, "Apprends à maîtriser ta souris", 38, COLORS["text_dim"], center=(cx, 250))
        for button in (self.play_button, self.scores_button, self.quit_button):
            if button is not None:
                button.draw(surface)
