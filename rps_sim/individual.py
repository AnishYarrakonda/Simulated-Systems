import random

class Individual():
    mutation_chance = 0
    moves = ("r", "p", "s")
    strategy_types = (
        (1, 0, 0),           # Always Rock
        (0, 1, 0),           # Always Paper
        (0, 0, 1),           # Always Scissors
        (1/3, 1/3, 1/3),     # Random
        (2/3, 1/3, 0),       # Mostly Rock
        (2/3, 0, 1/3),
        (1/3, 2/3, 0),       # Mostly Paper
        (0, 2/3, 1/3),
        (1/3, 0, 2/3),       # Mostly Scissors
        (0, 1/3, 2/3)    
    )

    # creates a new individual with a strategy
    def __init__(self, strategy, sim):
        self.strategy = strategy    # how often they play rock, paper, or scissors
        self.food = 0               # tracks how much food the individual has for the day
        self.survives = False       # whether an individual survives or not on this day
        self.reproduces = False     # whether an individual reproduces or not on this day
        self.isAlive = True         # whether an individual is alive or not         
        self.simulation = sim       # has access the sim resources
    
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
        if random.random() < Individual.mutation_chance:
            return Individual(strategy=random.choice(Individual.strategy_types), sim=self.simulation)
        else:
            return Individual(strategy=self.strategy, sim = self.simulation)
    
    # the individual dies
    def die(self):
        self.isAlive = False
    
    # the individual plays a move based on its strategy
    def playMove(self):
        move = random.choices(Individual.moves, self.strategy, k=1)
        return move[0]

    # String representation of an individual
    def __str__(self):
        return f"Chance of playing Rock: {self.strategy[0]}\nChance of playing Paper: {self.strategy[1]}\nChance of playing Scissors: {self.strategy[2]}\nFood: {self.food}"
    
    # For printing lists
    def __repr__(self):
        return self.__str__()