"""A bush. Holds FOOD_VALUE (2) units -- enough for two blobs to share."""


class Patch:
    """Resolves one contest. Capacity is exactly 2.

    The payoff table here already matched Primer's before this rewrite; it is
    kept, just sourced from Config so every value stays tunable.
    """

    def __init__(self, config, index=0):
        self.config = config
        self.index = index
        self.individual1 = None
        self.individual2 = None

    def clear(self):
        self.individual1 = None
        self.individual2 = None

    def is_full(self):
        return self.individual1 is not None and self.individual2 is not None

    def is_empty(self):
        return self.individual1 is None

    def add(self, individual):
        if self.individual1 is None:
            self.individual1 = individual
        elif self.individual2 is None:
            self.individual2 = individual
        else:
            raise ValueError("Too many blobs on the dance floor")

    def resolve(self):
        """Award food. Returns (kind, score1, score2); score2 is None if alone."""
        payoffs = self.config.payoffs()

        if self.individual1 is None:
            return (None, None, None)

        if self.individual2 is None:
            score = payoffs["alone"][0]
            self.individual1.add_food(score)
            return ("alone", score, None)

        fight1 = self.individual1.plays_fight()
        fight2 = self.individual2.plays_fight()

        if fight1 and fight2:
            kind = "fight_fight"
            s1, s2 = payoffs["fight_fight"]
        elif fight1:
            kind = "fight_share"
            s1, s2 = payoffs["fight_share"]
        elif fight2:
            kind = "fight_share"
            s2, s1 = payoffs["fight_share"]
        else:
            kind = "share_share"
            s1, s2 = payoffs["share_share"]

        self.individual1.add_food(s1)
        self.individual2.add_food(s2)
        return (kind, s1, s2)

    def __str__(self):
        return f"Patch {self.index}: {self.individual1}, {self.individual2}"

    __repr__ = __str__
