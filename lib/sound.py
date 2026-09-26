"""Effets sonores synthetises par code : aucun fichier audio a fournir."""

import math
from array import array

import pygame

from lib.logger import get_logger

logger = get_logger(__name__)

VOLUME = 0.3  # amplitude relative (0-1) ; au-dela, les bips deviennent agressifs

# Chaque son est une suite de notes (frequence en Hz, duree en s)
SOUND_NOTES: dict[str, list[tuple[float, float]]] = {
    "hit": [(880, 0.08)],
    "progress": [(660, 0.05)],
    "miss": [(200, 0.12)],
    "expire": [(440, 0.08), (330, 0.12)],
    "success": [(523, 0.1), (659, 0.1), (784, 0.2)],
    "fail": [(392, 0.15), (311, 0.25)],
}


def _synthesize(notes: list[tuple[float, float]], rate: int, channels: int) -> bytes:
    """Genere des echantillons 16 bits signes pour une suite de notes.

    Args:
        notes: Suite de (frequence, duree).
        rate: Frequence d'echantillonnage du mixer.
        channels: Nombre de canaux du mixer (chaque echantillon est duplique).

    Returns:
        Le tampon audio brut, au format attendu par pygame.mixer.Sound(buffer=...).
    """
    samples = array("h")
    for freq, duration in notes:
        count = int(rate * duration)
        for i in range(count):
            # Enveloppe decroissante : evite le "clac" en fin de note
            envelope = 1.0 - i / count
            value = int(VOLUME * 32767 * envelope * math.sin(2 * math.pi * freq * i / rate))
            samples.extend([value] * channels)
    return samples.tobytes()


class SoundBank:
    """Charge les sons au demarrage ; reste silencieux si l'audio est indisponible."""

    def __init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            rate, sample_format, channels = pygame.mixer.get_init()
            if sample_format != -16:
                logger.warning("Format audio %s non gere (16 bits signes attendu), son desactive", sample_format)
                return
            for name, notes in SOUND_NOTES.items():
                self._sounds[name] = pygame.mixer.Sound(buffer=_synthesize(notes, rate, channels))
        except pygame.error as e:
            logger.warning("Son desactive (audio indisponible) : %s", e)

    def play(self, name: str) -> None:
        """Joue un son s'il existe.

        Args:
            name: Cle de SOUND_NOTES.
        """
        sound = self._sounds.get(name)
        if sound is not None:
            sound.play()
