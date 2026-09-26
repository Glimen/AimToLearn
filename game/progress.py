"""Regle de deblocage des niveaux. Module pur, sans stockage."""


def unlock_after(unlocked: int, level_index: int, passed: bool, level_count: int) -> int:
    """Calcule le niveau le plus avance debloque apres avoir joue un niveau.

    Reussir un niveau debloque le suivant ; on ne perd jamais un niveau deja atteint.

    Args:
        unlocked: Index du niveau le plus avance deja debloque.
        level_index: Index du niveau qui vient d'etre joue.
        passed: Vrai si le niveau est reussi.
        level_count: Nombre total de niveaux.

    Returns:
        Le nouvel index du niveau le plus avance debloque.
    """
    if not passed:
        return unlocked
    return max(unlocked, min(level_index + 1, level_count - 1))
