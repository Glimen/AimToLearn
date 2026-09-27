#!/usr/bin/env python3
"""
AimToLearn - jeu educatif pour apprendre a utiliser la souris avec precision.

Usage:
    python3 main.py        (version desktop)
    pygbag .               (version navigateur, lancee depuis le dossier du projet)

La boucle de jeu est asynchrone : c'est obligatoire pour pygbag, qui doit rendre
la main au navigateur a chaque image, et sans effet sur la version desktop.
"""

import asyncio
import os
import sys

# Splash du studio, en sous-module git (voir .gitmodules) : on rend son paquet
# importable avant l'import. Chemin relatif a ce fichier, pas au dossier courant
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "vendor", "copper_tortoise_identity"))

import pygame  # noqa: E402
from copper_tortoise_splash import play_splash_async  # noqa: E402

from config.settings import FPS, MAX_FRAME_TIME, SCREEN_HEIGHT, SCREEN_WIDTH, WINDOW_TITLE
from game.scene_manager import SceneManager
from game.scenes.menu import MenuScene
from lib.logger import get_logger
from lib.sound import SoundBank

logger = get_logger(__name__)


async def main() -> None:
    """Initialise pygame et fait tourner la boucle de jeu jusqu'a la fermeture."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    # False : fenetre fermee pendant le splash, on quitte sans ouvrir le menu
    if not await play_splash_async(clock):
        pygame.quit()
        return
    manager = SceneManager(SoundBank())
    manager.go_to(MenuScene(manager))

    while manager.running:
        # dt plafonne : si la fenetre gele (deplacement...), les cibles ne sautent pas
        dt = min(clock.tick(FPS) / 1000.0, MAX_FRAME_TIME)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                manager.running = False
            else:
                manager.current.handle_event(event)
        manager.current.update(dt)
        manager.current.draw(screen)
        pygame.display.flip()
        await asyncio.sleep(0)  # rend la main au navigateur (pygbag)

    pygame.quit()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:  # noqa: BLE001 - dernier filet : on journalise avant de quitter
        logger.exception("Erreur inattendue : %s", e)
        sys.exit(1)
