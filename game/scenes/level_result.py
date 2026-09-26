"""Bilan d'un niveau."""

import pygame

from config.levels import LEVELS
from config.settings import COLORS, PASS_THRESHOLD, RESULT_INPUT_DELAY, SCREEN_WIDTH
from game.scene_manager import Scene, SceneManager
from game.scoring import LevelScore, Session
from lib.ui import Button, draw_text


def percent(ratio: float) -> str:
    """Formate un ratio 0-1 en pourcentage entier."""
    return f"{round(ratio * 100)} %"


class LevelResultScene(Scene):
    """Affiche les scores du niveau et propose la suite."""

    def __init__(self, manager: SceneManager, session: Session, level_index: int, score: LevelScore) -> None:
        super().__init__(manager)
        self.session = session
        self.level_index = level_index
        self.score = score
        self.input_delay = RESULT_INPUT_DELAY  # evite un clic de jeu pris pour un clic de bouton
        is_last = level_index == len(LEVELS) - 1

        cx = SCREEN_WIDTH // 2
        self.next_button: Button | None = None
        if score.passed:
            label = "Voir le bilan" if is_last else "Niveau suivant"
            self.next_button = Button(label, (cx, 500))
        self.retry_button = Button("Réessayer", (cx - 320, 600))
        self.end_button = Button("Terminer", (cx + 320, 600))
        manager.sounds.play("success" if score.passed else "fail")

    def update(self, dt: float) -> None:
        """Decompte le delai de protection des boutons."""
        self.input_delay = max(0.0, self.input_delay - dt)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Niveau suivant, reessayer ou terminer la session."""
        if self.input_delay > 0:
            return
        # Imports locaux : les ecrans se referencent mutuellement
        from game.scenes.level import LevelScene
        from game.scenes.session_result import SessionResultScene

        if self.next_button is not None and self.next_button.is_clicked(event):
            if self.level_index == len(LEVELS) - 1:
                self.manager.go_to(SessionResultScene(self.manager, self.session))
            else:
                self.manager.go_to(LevelScene(self.manager, self.session, self.level_index + 1))
        elif self.retry_button.is_clicked(event):
            self.manager.go_to(LevelScene(self.manager, self.session, self.level_index))
        elif self.end_button.is_clicked(event):
            self.manager.go_to(SessionResultScene(self.manager, self.session))

    def draw(self, surface: pygame.Surface) -> None:
        """Titre, detail des scores et boutons."""
        surface.fill(COLORS["background"])
        cx = SCREEN_WIDTH // 2
        s = self.score
        level = LEVELS[self.level_index]
        draw_text(surface, f"Niveau {self.level_index + 1} : {level.name}", 50, COLORS["text"], center=(cx, 70))
        if s.passed:
            draw_text(surface, "Niveau réussi !", 60, COLORS["hit"], center=(cx, 140))
        else:
            draw_text(surface, "Pas encore...", 60, COLORS["miss"], center=(cx, 140))

        lines = [
            f"Précision : {percent(s.precision)}  ({s.clicks_on_target} bons clics sur {s.clicks})",
            f"Cibles touchées : {s.hits} / {s.total_targets}  (ratées : {s.missed})",
            f"Vitesse : {percent(s.speed)}",
        ]
        y = 220
        for line in lines:
            draw_text(surface, line, 36, COLORS["text"], center=(cx, y))
            y += 46
        draw_text(surface, f"Score global : {percent(s.global_score)}", 56, COLORS["highlight"], center=(cx, y + 30))
        if not s.passed:
            needed = f"Il faut plus de {percent(PASS_THRESHOLD)} pour passer au niveau suivant."
            draw_text(surface, needed, 30, COLORS["text_dim"], center=(cx, 500))

        for button in (self.next_button, self.retry_button, self.end_button):
            if button is not None:
                button.draw(surface)
