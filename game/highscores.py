"""Regles du tableau des scores (classement, insertion). Module pur, sans stockage."""

from config.settings import SCOREBOARD_SIZE


def qualifies(entries: list[dict], points: int, size: int = SCOREBOARD_SIZE) -> bool:
    """Indique si un score merite une place au tableau.

    Args:
        entries: Entrees actuelles du tableau.
        points: Score a tester.
        size: Nombre de places du tableau.

    Returns:
        True s'il reste une place ou si le score bat le plus faible.
    """
    return len(entries) < size or points > min(e["points"] for e in entries)


def insert_score(
    entries: list[dict], name: str, points: int, levels: int, size: int = SCOREBOARD_SIZE
) -> tuple[list[dict], int | None]:
    """Insere un score et retourne le nouveau tableau trie et tronque.

    A egalite de points, le score deja present reste devant.

    Args:
        entries: Entrees actuelles du tableau.
        name: Nom du joueur.
        points: Score de la session.
        levels: Nombre de niveaux reussis.
        size: Nombre de places du tableau.

    Returns:
        Le tableau mis a jour et le rang (index) du nouveau score, ou None s'il n'y figure pas.
    """
    ranked = sorted(entries, key=lambda e: e["points"], reverse=True)
    index = next((i for i, e in enumerate(ranked) if e["points"] < points), len(ranked))
    ranked.insert(index, {"name": name, "points": points, "levels": levels})
    return ranked[:size], (index if index < size else None)
