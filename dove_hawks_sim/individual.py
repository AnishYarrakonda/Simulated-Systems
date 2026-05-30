import random

class Individual():
    # creates a new individual with a strategy, food, and age variable
    def __init__(self, strategy, sim):
        self.strategy = strategy  # either "Dove" or "Hawk"
        self.food = 0  # tracks how much food the individual has for the day
        self.age = 0  # tracks number of days the individual has survived
        self.survives = False  # whether an individual survives or not on this day
        self.reproduces = False  # whether an individual reproduces or not on this day
        self.isAlive = True
        self.simulation = sim  # whether an individual is alive or not

    # resets food (and maybe other things later if added) for each new day
    def reset(self):
        self.food = 0
        self.survives = False
        self.reproduces = False

    # determines how an individual survives and reproduces
    # the food they have from 0-1 is the chance of them surviving
    # the food they have from 1-2 is the chance of them reproducing
    def survive_and_reproduce(self):

        random1 = random.random()

        if self.food <= 1:
            self.survives = random1 < self.food
        else:
            self.survives = True
            self.reproduces = random1 < self.food - 1

    # adds food
    def add_food(self, amount):
        self.food += amount

    # the individual creates an offspring with the same strategy which is returned
    def reproduce(self):
        return Individual(strategy=self.strategy, sim=self.simulation)

    # the individual dies
    def die(self):
        self.isAlive = False

    # increases age by one
    def increment_age(self):
        self.age += 1

    # String representation of an individual
    def __str__(self):
        return f"{self.strategy.capitalize()} — Age: {self.age}, Food: {self.food}"

    # For printing lists
    def __repr__(self):
        return self.__str__()