from creature import Creature
import random

class Tile:
    def __init__(self, X_coord, Y_coord, food=False):
        self.X_coord = X_coord        # Tile's x-position on the gurt
        self.Y_coord = Y_coord        # Tile's y-position on the gurt
        self.food = food              # Units of food available (default 0)
        self.creatures = []           # List of Creature objects on this tile

    def add_creature(self, creature: Creature):
        self.creatures.append(creature)

    def clear_creatures(self):
        self.creatures.clear()

    def remove_creature(self, creature: Creature):
        try:
            self.creatures.remove(creature)
        except ValueError:
            print("creature argument does not exist on tile")
        
    def creature_consumed_food(self, creature):
        if self.food:
            creature.eat()
            self.food = False

    def contest(self):
        if not self.creatures:
            return None
        contest_ranks = []
        for creature in self.creatures:
            contest_ranks.append(creature.contest_rank)
        
        winning_creature = random.choices(self.creatures, contest_ranks, k=1)
        return winning_creature[0]

    def is_occupied(self):
        return len(self.creatures) > 0

    def __str__(self):
        return f"Tile({self.X_coord}, {self.Y_coord}) | Food: {self.food} | Creatures: {len(self.creatures)}"
    
    def __repr__(self):
        return self.__str__()
    
if __name__ == '__main__':
    tile = Tile(0, 0, food=True)

    # Create test creatures
    c1 = Creature(size=4, speed=4, vision=4)
    c2 = Creature(size=6, speed=5, vision=3)

    # Add creatures to tile
    tile.add_creature(c1)
    tile.add_creature(c2)

    print("Before contest:")
    print(tile)

    # Run contest
    winner = tile.contest()
    print(f"Winner: {winner}")

    # Food consumption
    tile.creature_consumed_food(winner)

    print("After contest and food consumption:")
    print(tile)
    print(f"{winner} ate? {winner.food}")