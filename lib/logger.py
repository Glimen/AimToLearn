"""Configuration centralisee du logging."""

import logging


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger configure avec le format commun du projet.

    Args:
        name: Nom du logger (en general __name__).

    Returns:
        Le logger demande.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(name)
