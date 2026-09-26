"""Briques d'interface : polices, texte, boutons."""

from functools import lru_cache

import pygame

from config.settings import COLORS


@lru_cache(maxsize=None)
def get_font(size: int) -> pygame.font.Font:
    """Retourne la police par defaut a la taille demandee (mise en cache)."""
    return pygame.font.Font(None, size)


def draw_text(surface: pygame.Surface, text: str, size: int, color: tuple[int, ...], **anchor: object) -> pygame.Rect:
    """Dessine une ligne de texte.

    Args:
        surface: Surface cible.
        text: Texte a afficher.
        size: Taille de police.
        color: Couleur RGB.
        **anchor: Ancrage passe a Rect (ex. center=(x, y), topleft=(x, y)).

    Returns:
        Le rectangle occupe par le texte.
    """
    rendered = get_font(size).render(text, True, color)
    rect = rendered.get_rect(**anchor)
    surface.blit(rendered, rect)
    return rect


def wrap_text(text: str, size: int, max_width: int) -> list[str]:
    """Decoupe un texte en lignes qui tiennent dans une largeur donnee.

    Args:
        text: Texte a decouper.
        size: Taille de police.
        max_width: Largeur maximale d'une ligne en pixels.

    Returns:
        Les lignes.
    """
    font = get_font(size)
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if not current or font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class Button:
    """Bouton rectangulaire cliquable au clic gauche."""

    def __init__(self, label: str, center: tuple[int, int], width: int = 300, height: int = 56) -> None:
        self.label = label
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = center

    def is_clicked(self, event: pygame.event.Event) -> bool:
        """Indique si l'evenement est un clic gauche sur le bouton."""
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == pygame.BUTTON_LEFT
            and self.rect.collidepoint(event.pos)
        )

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine le bouton, plus clair au survol."""
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        color = COLORS["button_hover"] if hovered else COLORS["button"]
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        draw_text(surface, self.label, 34, COLORS["text"], center=self.rect.center)
