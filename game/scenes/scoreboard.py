"""Tableau des meilleurs scores."""

import pygame

from config.levels import LEVELS
from config.settings import COLORS, SCREEN_WIDTH
from game.scene_manager import Scene, SceneManager
from lib.storage import load_entries
from lib.ui import Button, draw_text

ROW_HEIGHT = 40
TABLE_TOP = 160
# Abscisses des colonnes : rang, nom, points, niveaux
COLUMNS = (320, 400, 820, 960)


class ScoreboardScene(Scene):
    """Affiche le top 10, avec la ligne du dernier score en surbrillance."""

    def __init__(self, manager: SceneManager, highlight: int | None = None) -> None:
        super().__init__(manager)
        self.entries = load_entries()
        self.highlight = highlight
        self.menu_button = Button("Menu", (SCREEN_WIDTH // 2, 640))

    def handle_event(self, event: pygame.event.Event) -> None:
        """Retour au menu par le bouton ou Echap."""
        is_escape = event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        if is_escape or self.menu_button.is_clicked(event):
            from game.scenes.menu import MenuScene  # import local : reference circulaire

            self.manager.go_to(MenuScene(self.manager))

    def draw(self, surface: pygame.Surface) -> None:
        """En-tete puis une ligne par score."""
        surface.fill(COLORS["background"])
        cx = SCREEN_WIDTH // 2
        draw_text(surface, "Meilleurs scores", 64, COLORS["highlight"], center=(cx, 70))
        if not self.entries:
            draw_text(surface, "Aucun score pour l'instant. À toi de jouer !", 36, COLORS["text_dim"], center=(cx, 300))
        else:
            headers = ("#", "Nom", "Points", "Niveaux")
            for x, header in zip(COLUMNS, headers):
                draw_text(surface, header, 30, COLORS["text_dim"], midleft=(x, TABLE_TOP - 30))
            for i, entry in enumerate(self.entries):
                color = COLORS["highlight"] if i == self.highlight else COLORS["text"]
                y = TABLE_TOP + 10 + i * ROW_HEIGHT
                cells = (str(i + 1), entry["name"], str(entry["points"]), f"{entry.get('levels', 0)}/{len(LEVELS)}")
                for x, cell in zip(COLUMNS, cells):
                    draw_text(surface, cell, 34, color, midleft=(x, y))
        self.menu_button.draw(surface)
