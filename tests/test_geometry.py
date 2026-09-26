"""Tests des formes et du test d'appartenance d'un point."""

import unittest

from lib.geometry import Area, contains_point


class ContainsPointTest(unittest.TestCase):
    """Verifie la zone cliquable de chaque forme (taille 100, centre en 0, 0)."""

    def test_circle(self) -> None:
        self.assertTrue(contains_point("circle", 0, 0, 100, 0, 0))
        self.assertTrue(contains_point("circle", 0, 0, 100, 49, 0))
        # Coin du carre englobant : hors du cercle
        self.assertFalse(contains_point("circle", 0, 0, 100, 45, 45))

    def test_square(self) -> None:
        self.assertTrue(contains_point("square", 0, 0, 100, 45, 45))
        self.assertFalse(contains_point("square", 0, 0, 100, 55, 0))

    def test_triangle(self) -> None:
        self.assertTrue(contains_point("triangle", 0, 0, 100, 0, 0))
        self.assertTrue(contains_point("triangle", 0, 0, 100, 0, -45))  # pres de la pointe
        # Coins hauts du carre englobant : a cote de la pointe
        self.assertFalse(contains_point("triangle", 0, 0, 100, -40, -40))
        self.assertFalse(contains_point("triangle", 0, 0, 100, 40, -40))

    def test_star(self) -> None:
        self.assertTrue(contains_point("star", 0, 0, 100, 0, 0))
        self.assertTrue(contains_point("star", 0, 0, 100, 0, -45))  # dans la pointe du haut
        # Entre deux pointes (creux a 36 deg de la verticale), au-dela du rayon interieur
        self.assertFalse(contains_point("star", 0, 0, 100, 20, -40))

    def test_unknown_shape_raises(self) -> None:
        with self.assertRaises(ValueError):
            contains_point("hexagon", 0, 0, 100, 0, 0)


class AreaTest(unittest.TestCase):
    """Verifie le rectangle."""

    def test_contains(self) -> None:
        area = Area(10, 20, 100, 50)
        self.assertTrue(area.contains(10, 20))
        self.assertFalse(area.contains(110, 20))  # bord droit exclu
        self.assertFalse(area.contains(50, 10))


if __name__ == "__main__":
    unittest.main()
