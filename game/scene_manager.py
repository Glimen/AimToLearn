"""Gestion des ecrans du jeu (menu, niveau, bilans, scores)."""

import pygame

from lib.sound import SoundBank


class Scene:
    """Ecran de base : les ecrans concrets surchargent les methodes utiles."""

    def __init__(self, manager: "SceneManager") -> None:
        self.manager = manager

    def handle_event(self, event: pygame.event.Event) -> None:
        """Traite un evenement pygame."""

    def update(self, dt: float) -> None:
        """Avance la logique de dt secondes."""

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine l'ecran."""


class SceneManager:
    """Detient l'ecran courant et les ressources partagees.

    Attributes:
        current: Ecran affiche.
        sounds: Banque de sons partagee.
        running: Passe a False pour quitter le jeu.
    """

    def __init__(self, sounds: SoundBank) -> None:
        self.current: Scene = Scene(self)
        self.sounds = sounds
        self.running = True

    def go_to(self, scene: Scene) -> None:
        """Change d'ecran."""
        self.current = scene
