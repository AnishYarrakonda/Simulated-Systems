from individual import Individual

class Patch():
    # Creates a new patch
    def __init__(self):
        self.food_supply = 0        # stores the food at the location
        self.individual1 = None     # stores the first individual (if any)
        self.individual2 = None     # stores the second individual (if any)
        
    #resets food supply each round.
    def reset(self):
        self.food_supply = 2

    # decides how to split food between 0, 1, or 2 individuals
    def encounter(self, individuals):
        # raise error for more than 2 individuals
        if len(individuals) > 2:
            raise ValueError("encounter() expects a list of 0 to 2 individuals")

        # 0 individuals
        if len(individuals) == 0:
            self.individual1 = None
            self.individual2 = None
            return

        # 1 individual
        if len(individuals) == 1:
            self.individual1 = individuals[0]
            self.individual2 = None

            strategy = "alone"
            ratio = Patch.ratios[strategy]

            self.individual1.add_food(ratio)
            return

        # 2 individuals
        self.individual1 = individuals[0]
        self.individual2 = individuals[1]

        move1 = self.individual1.playMove()
        move2 = self.individual2.playMove()

        encounterKey = move1 + move2
        ratio = Patch.ratios[encounterKey]

        self.individual1.add_food(ratio[0])
        self.individual2.add_food(ratio[1])

    # Function to clear the patch of individuals
    def clear_individuals(self):
        self.individual1 = None
        self.individual2 = None
    
    # Returns whether or not the patch has two individuals in it
    def is_full(self):
        return self.individual1 != None and self.individual2 != None
    
    # Patch object as a string
    def __str__(self):
        ind1 = str(self.individual1) if self.individual1 else "N/A"
        ind2 = str(self.individual2) if self.individual2 else "N/A"
        return f"Patch: Food = {self.food_supply}, Individual 1 = {ind1}, Individual 2 = {ind2}"
    
    def __repr__(self):
        return self.__str__()