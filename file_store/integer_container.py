import unittest


class IntegerContainer:

    def __init__(self):
        pass  # TODO: set up your data structure

    def insert(self, val: int) -> None:
        """Insert val into the container."""
        pass  # TODO

    def delete(self, val: int) -> bool:
        """Remove one occurrence of val. Return True if found, False otherwise."""
        pass  # TODO

    def get_rank(self, val: int) -> int:
        """Return how many elements are strictly less than val."""
        pass  # TODO

    def get_median(self) -> float:
        """Return the median of all elements (lower median if even count)."""
        pass  # TODO


# ── tests (run with: python integer_container.py) ────────────────────────────

class TestIntegerContainer(unittest.TestCase):

    def test_insert_and_rank(self):
        c = IntegerContainer()
        c.insert(3)
        c.insert(1)
        c.insert(4)
        c.insert(1)
        self.assertEqual(c.get_rank(1), 0)  # nothing < 1
        self.assertEqual(c.get_rank(2), 2)  # 1, 1 < 2
        self.assertEqual(c.get_rank(4), 3)  # 1, 1, 3 < 4
        self.assertEqual(c.get_rank(5), 4)  # all four < 5

    def test_delete(self):
        c = IntegerContainer()
        c.insert(5)
        c.insert(5)
        self.assertTrue(c.delete(5))   # removes one 5
        self.assertTrue(c.delete(5))   # removes the other
        self.assertFalse(c.delete(5))  # none left
        self.assertEqual(c.get_rank(6), 0)  # container empty

    def test_median_odd(self):
        c = IntegerContainer()
        for v in [1, 3, 5]:
            c.insert(v)
        self.assertEqual(c.get_median(), 3.0)

    def test_median_even(self):
        c = IntegerContainer()
        for v in [1, 2, 3, 4]:
            c.insert(v)
        # lower median of [1,2,3,4] = 2
        self.assertEqual(c.get_median(), 2.0)

    def test_combined(self):
        c = IntegerContainer()
        for v in [10, 20, 30, 20]:
            c.insert(v)
        self.assertEqual(c.get_rank(20), 1)   # only 10 < 20
        self.assertEqual(c.get_median(), 20.0) # sorted: [10,20,20,30], lower mid = 20
        c.delete(20)
        self.assertEqual(c.get_rank(20), 1)   # still one 20 left
        self.assertEqual(c.get_median(), 20.0) # sorted: [10,20,30], mid = 20


if __name__ == "__main__":
    unittest.main(verbosity=2)
