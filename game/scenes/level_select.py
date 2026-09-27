"""Choix du niveau de depart parmi les niveaux deja atteints."""

import pygame

from config.levels import LEVELS
from config.settings import COLORS, SCREEN_WIDTH
from game.scene_manager import Scene, SceneManager
from game.scoring import Session
from lib.storage import load_progress
from lib.ui import Button, draw_text

COLUMN_OFFSET = 200  # ecart horizontal entre le centre de l'ecran et chaque colonne
BUTTON_WIDTH = 370
ROW_HEIGHT = 62
GRID_TOP = 170


class LevelSelectScene(Scene):
    """Grille des niveaux : ceux deja atteints sont jouables, les autres grises."""

    def __init__(self, manager: SceneManager) -> None:
        super().__init__(manager)
        # Borne au nombre de niveaux : une sauvegarde d'une version plus longue reste utilisable
        unlocked = min(load_progress(), len(LEVELS) - 1)
        rows = (len(LEVELS) + 1) // 2
        cx = SCREEN_WIDTH // 2
        self.level_buttons: list[Button] = []
        for i, level in enumerate(LEVELS):
            # Remplissage par colonne : niveaux 1 a 7 a gauche, 8 a 13 a droite
            column, row = divmod(i, rows)
            center = (cx + (2 * column - 1) * COLUMN_OFFSET, GRID_TOP + row * ROW_HEIGHT)
            self.level_buttons.append(Button(f"{i + 1}. {level.name}", center, BUTTON_WIDTH, enabled=i <= unlocked))
        self.warning_y = GRID_TOP + rows * ROW_HEIGHT + 5
        self.back_button = Button("Retour", (cx, self.warning_y + 60))

    def handle_event(self, event: pygame.event.Event) -> None:
        """Clic sur un niveau debloque, ou retour au menu (bouton ou Echap)."""
        is_escape = event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        if is_escape or self.back_button.is_clicked(event):
            from game.scenes.menu import MenuScene  # import local : reference circulaire

            self.manager.go_to(MenuScene(self.manager))
            return
        for index, button in enumerate(self.level_buttons):
            if button.is_clicked(event):
                from game.scenes.level import LevelScene

                self.manager.go_to(LevelScene(self.manager, Session(start_level=index), index))
                return

    def draw(self, surface: pygame.Surface) -> None:
        """Titre, grille des niveaux et bouton retour."""
        surface.fill(COLORS["background"])
        cx = SCREEN_WIDTH // 2
        draw_text(surface, "Choisis ton niveau de départ", 56, COLORS["highlight"], center=(cx, 70))
        draw_text(
            surface, "Réussis un niveau pour débloquer le suivant", 28, COLORS["text_dim"], center=(cx, 115)
        )
        for button in self.level_buttons:
            button.draw(surface)
        draw_text(
            surface,
            "Attention : seule une partie commencée au niveau 1 peut entrer au tableau des scores.",
            28, COLORS["highlight"], center=(cx, self.warning_y),
        )
        self.back_button.draw(surface)
