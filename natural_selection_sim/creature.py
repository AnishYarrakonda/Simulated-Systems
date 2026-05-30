import numpy as np
import random

class Creature:
    distribution_rate = 0.5     # how varied traits are in offspring compared to the parent
    vision_accuracy = 0.1       # how often the creature correctly spots a tile with food when choosing a location

    # creates a new creature object with the given traits
    def __init__(self, size, speed, vision, x=None, y=None):
        self.size = size                        # Size affects contest outcomes and energy usage (bigger = wins more fights but uses more energy)
        self.speed = speed                      # Speed = how many tiles you can move before needing a rest
        self.vision = vision                    # Vision = ability to detect food around your current location
        self.contest_rank = size**3*speed       # rank used in contests
        self.food = 0                           # Food collected today, 0-1 is chance of survival, 1 - X is number of offspring fractions turn into chance
        self.is_alive = True                     # True if the creature is alive this day (dies if not enough food)
        self.survives = False                   # Whether the creature survives on the given day
        self.offspring = 0                      # How many offspring the creature has
        self.traits = np.array([size, speed, vision])     # a list containing the traits for easy array operations
        self.x = x                              # x location
        self.y = y                              # y location
        self.visited_tiles = []                 # tracks tiles already seen to prevent going in circles
        self.ticks_without_rest = 0             # tracks how long its gone without resting
        self.resting = False                    # whether it is currently resting
        self.daily_energy_spent = 0                  # how much energy spent in the entire day

    # resets food for each new day
    def reset(self):   
        self.food = 0
        self.survives = False
        self.offspring = 0
        self.x = None
        self.y = None
        self.visited_tiles.clear()
        self.ticks_without_rest = 0
        self.resting = False
        self.daily_energy_spent = 0

    # creature gets to eat food
    def eat(self):
        self.food += 1

    # creature chooses a location to move to based on whether it thinks the new tile has food or not
    # can miss tiles with food
    # can check up to 4 tiles max
    def choose_location(self, environment):
        surrounding_tiles = []
        moves = (-1, 0, 1)
        max_index = environment.edge_length - 1
        for hrz in moves:
            for vrt in moves:
                tile_x = self.x + hrz
                tile_y = self.y + vrt
                if (                                                    # adds to the list ONLY if:
                    not (tile_x == self.x and tile_y == self.y) and     # NOT the same tile
                    0 <= tile_x <= max_index and                        # x coord is within bounds
                    0 <= tile_y <= max_index                        # y coord is within bounds
                ):
                    surrounding_tiles.append(environment.gurt[tile_y][tile_x])
        
        # a separate list for unvisited tiles
        # cannot be the same as surrounding tiles to prevent edge cases like
        # if the creature is on the corner and has visited all surrounding tiles alr
        best_tiles = []
        visited_set = set(self.visited_tiles)
        for tile in surrounding_tiles:
            if tile not in visited_set:  # tile hasn't alr been visited
                best_tiles.append(tile)

        # number_of_tiles the creature gets to evaluate depending on its vision trait
        total_seen_tiles = self.vision//2
        total_seen_tiles += 1 if (random.random() * 2 < self.vision % 2) else 0

        # randomly select the tiles that the creature will check from all possible options
        tiles_being_checked = []
        if total_seen_tiles > len(best_tiles):
            tiles_being_checked = best_tiles
        else:
            tiles_being_checked = random.sample(best_tiles, k=int(total_seen_tiles))

        for tile in tiles_being_checked:
            if tile.food and random.random() < Creature.vision_accuracy:
                return tile
        
        if not best_tiles:
            return random.choice(surrounding_tiles)
        else:
            return random.choice(best_tiles)
        
    
    # determines if a creature should rest on the given tick or not based on how fatigued it is and its speed
    def should_rest(self):
        if self.resting:
            return False
        elif self.ticks_without_rest < int(self.speed):
            return False
        else:
            return random.random() < self.speed%1


    # determines how an individual survives and reproduces
    # the net_energy units they have from 0-1 is the chance of them surviving
    # the rest of the energy is the number of offspring
    def survive_and_set_offspring(self):
        net_gain = self.food-self.daily_energy_spent
        if net_gain <= 1:
            self.survives = random.random() < net_gain
        else:
            self.survives = True
            net_gain -= 1  # reserve 1 food unit for survival

            # Reproduction: for each remaining energy unit one offspring is reproduced
            while net_gain >= 1:
                self.offspring += 1
                net_gain -= 1

            # Handle fractional leftover food
            if net_gain > 0:
                if random.random() < net_gain:
                    self.offspring += 1

    # returns a list of creature objects (its offspring)
    def reproduce_offspring(self):
        if self.offspring == 0:
            return []

        # Generate noise matrix: shape (offspring_count, 4)
        noise = np.random.randn(self.offspring, 3) * Creature.distribution_rate

        # Add noise to parent's traits
        offspring_traits = self.traits + noise

        # Clip traits to biologically valid ranges
        trait_mins = np.array([1.0, 1.0, 1.0])   # min values for [size, speed, vision]
        trait_maxs = np.array([8.0, 8.0, 8.0])  # max values
        offspring_traits = np.clip(offspring_traits, trait_mins, trait_maxs)

        # Create offspring creatures from traits
        offspring_list = []
        for traits in offspring_traits:
            size, speed, vision = traits
            child = Creature(size=size, speed=speed, vision=vision)
            offspring_list.append(child)

        return offspring_list
    
    # returns how much energy the creature spent on the tick
    def energy_spent(self):
        return 0.02 * (self.vision**3 + self.size**2 + self.speed) ** 0.15

    # updates creature at the end of each tick
    def update_creature(self):
        # add energy to the total counter
        self.daily_energy_spent += self.energy_spent()
        
        # update fatigue
        if self.resting:
            self.resting = False
            self.ticks_without_rest = 0
        else:
            self.ticks_without_rest += 1

    # creature object as a string
    def __str__(self):
        return (
            f"Creature:\n"
            f"Size: {self.size:.2f},\n"
            f"Speed: {self.speed:.2f},\n"
            f"Vision: {self.vision:.2f},\n"
            f"Food: {self.food:.2f},\n"
            f"Survives: {self.survives},\n"
            f"Offspring: {self.offspring}\n"
            f"X coordinate: {self.x}\n"
            f"Y coordinate: {self.y}\n"            
        )

    # same as __str__()
    def __repr__(self):
        return self.__str__()

# Test
if __name__ == '__main__':
    parent = Creature(size=2, speed=3, vision=5)
    parent.food = 5.2

    # Run survival and reproduction logic
    parent.survive_and_set_offspring()
    offspring = parent.reproduce_offspring()

    # Print offspring traits
    for child in offspring:
        print(child)
    print(len(offspring))