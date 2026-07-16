"""A mango tree. Feeds one blob alone, or hosts a game between two."""

from config import NAMES


class Patch:
    def __init__(self, config, index=0):
        self.config = config
        self.index = index
        self.individual1 = None
        self.individual2 = None

    def clear(self):
        self.individual1 = None
        self.individual2 = None

    def add(self, individual):
        if self.individual1 is None:
            self.individual1 = individual
        elif self.individual2 is None:
            self.individual2 = individual
        else:
            raise ValueError("A tree holds at most two blobs")

    def resolve(self):
        """Award rewards. Returns (kind, moves, r1, r2)."""
        if self.individual1 is None:
            return (None, None, None, None)

        if self.individual2 is None:
            # Eating alone always pays 2 -> exactly two offspring.
            reward = 1 + self.config.win_magnitude
            self.individual1.reward = reward
            return ("alone", None, reward, None)

        m1 = self.individual1.play()
        m2 = self.individual2.play()
        matrix = self.config.reward_matrix()
        r1, r2 = matrix[m1][m2], matrix[m2][m1]

        self.individual1.reward = r1
        self.individual2.reward = r2
        return ("game", (NAMES[m1], NAMES[m2]), r1, r2)

    def __str__(self):
        return f"Tree {self.index}: {self.individual1}, {self.individual2}"

    __repr__ = __str__
