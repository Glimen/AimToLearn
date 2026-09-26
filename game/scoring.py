"""Statistiques et calcul des scores (niveau et session). Module pur, sans pygame."""

import math
from dataclasses import dataclass, field

from config.settings import (
    PASS_THRESHOLD,
    REFERENCE_THROUGHPUT,
    WEIGHT_COMPLETION,
    WEIGHT_PRECISION,
    WEIGHT_SPEED,
)


@dataclass
class LevelStats:
    """Compteurs bruts collectes pendant un niveau.

    Attributes:
        total_targets: Nombre de cibles du niveau.
        clicks: Nombre total de clics.
        clicks_on_target: Clics valides sur la cible (bon bouton, bonne forme).
        hits: Cibles validees.
        missed: Cibles disparues avant d'avoir ete validees.
        samples: Mesures pour la loi de Fitts : (distance, largeur, temps) par cible validee.
    """

    total_targets: int
    clicks: int = 0
    clicks_on_target: int = 0
    hits: int = 0
    missed: int = 0
    samples: list[tuple[float, float, float]] = field(default_factory=list)

    @property
    def resolved(self) -> int:
        """Nombre de cibles terminees (validees ou disparues)."""
        return self.hits + self.missed


@dataclass(frozen=True)
class LevelScore:
    """Scores d'un niveau, tous les ratios entre 0 et 1."""

    precision: float
    completion: float
    speed: float
    throughput: float  # debit moyen en bits/s (information brute, non normalisee)
    global_score: float
    passed: bool
    clicks: int
    clicks_on_target: int
    hits: int
    missed: int
    total_targets: int


@dataclass(frozen=True)
class SessionSummary:
    """Bilan d'une session (dernier essai de chaque niveau joue)."""

    precision: float
    completion: float
    speed: float
    points: int
    levels_played: int
    levels_passed: int


def throughput(distance: float, width: float, movement_time: float) -> float:
    """Debit d'un pointage selon la loi de Fitts (formulation de Shannon).

    ID = log2(D / W + 1) mesure la difficulte en bits ; le debit vaut ID / temps.
    Une cible lointaine et petite est plus dure : l'atteindre vite rapporte plus.

    Args:
        distance: Distance entre le curseur et la cible au moment de l'apparition (px).
        width: Taille de la cible (px).
        movement_time: Temps mis pour valider la cible (s).

    Returns:
        Le debit en bits/s (0 si le temps ou la largeur est nul).
    """
    if movement_time <= 0 or width <= 0:
        return 0.0
    index_of_difficulty = math.log2(distance / width + 1)
    return index_of_difficulty / movement_time


def compute_level_score(stats: LevelStats, reference_throughput: float = REFERENCE_THROUGHPUT) -> LevelScore:
    """Calcule les scores d'un niveau a partir des compteurs bruts.

    Args:
        stats: Compteurs du niveau termine.
        reference_throughput: Debit (bits/s) correspondant a 100 % de vitesse.

    Returns:
        Le score du niveau.
    """
    precision = stats.clicks_on_target / stats.clicks if stats.clicks else 0.0
    completion = stats.hits / stats.total_targets if stats.total_targets else 0.0
    rates = [throughput(d, w, t) for d, w, t in stats.samples]
    mean_rate = sum(rates) / len(rates) if rates else 0.0
    speed = min(1.0, mean_rate / reference_throughput)
    global_score = WEIGHT_PRECISION * precision + WEIGHT_COMPLETION * completion + WEIGHT_SPEED * speed
    return LevelScore(
        precision=precision,
        completion=completion,
        speed=speed,
        throughput=mean_rate,
        global_score=global_score,
        passed=global_score > PASS_THRESHOLD,
        clicks=stats.clicks,
        clicks_on_target=stats.clicks_on_target,
        hits=stats.hits,
        missed=stats.missed,
        total_targets=stats.total_targets,
    )


@dataclass
class Session:
    """Resultats d'une session de jeu : un score par niveau (le dernier essai compte)."""

    results: dict[int, LevelScore] = field(default_factory=dict)

    def record(self, level_index: int, score: LevelScore) -> None:
        """Enregistre le score d'un niveau, en remplacant un essai precedent."""
        self.results[level_index] = score

    def summary(self) -> SessionSummary:
        """Agrege les scores de la session.

        La precision et la completion sont recalculees sur les compteurs cumules
        (un niveau avec beaucoup de clics pese plus), la vitesse est une moyenne.
        Les points (somme des scores globaux x 100) recompensent la progression.

        Returns:
            Le bilan de la session.
        """
        scores = list(self.results.values())
        clicks = sum(s.clicks for s in scores)
        on_target = sum(s.clicks_on_target for s in scores)
        hits = sum(s.hits for s in scores)
        targets = sum(s.total_targets for s in scores)
        return SessionSummary(
            precision=on_target / clicks if clicks else 0.0,
            completion=hits / targets if targets else 0.0,
            speed=sum(s.speed for s in scores) / len(scores) if scores else 0.0,
            points=sum(round(s.global_score * 100) for s in scores),
            levels_played=len(scores),
            levels_passed=sum(1 for s in scores if s.passed),
        )
