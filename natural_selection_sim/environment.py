from creature import Creature
from tile import Tile
import numpy as np
import random

class Environment:
    # initializes an environment
    def __init__(self,
                 edge_length=50,                    # gurt is a square edge_length by edge_length
                 food_spawn_rate=0.2,   
                 creature_total=None,
                 average_size = 5,
                 average_speed = 5,
                 average_vision = 4,
                 average_trait_variability = 1,
                 ticks_per_day = 20
                 ):

        if creature_total is None:
            creature_total = int(edge_length**2 / 10)  # 1/10 of the total area

        self.edge_length = edge_length
        self.food_spawn_rate = food_spawn_rate
        self.average_size = average_size
        self.average_speed = average_speed
        self.average_vision = average_vision
        self.average_trait_variability = average_trait_variability
        
        self.ticks_per_day = ticks_per_day
        self.day = 1
        self.day_to_averages = {"size": {}, "speed": {}, "vision": {}}
        self.day_to_population = {}

        # gurt is initialized with None as placeholders
        self.gurt = [[Tile(X_coord=x, Y_coord=y) for x in range(edge_length)] for y in range(edge_length)]

        # list of all creature objects
        self.creatures = []

        # loop to create the creature objects and store in the list
        sizes = np.clip(np.random.randn(creature_total) * average_trait_variability + average_size, 1, 8)
        speeds = np.clip(np.random.randn(creature_total) * average_trait_variability + average_speed, 1, 8)
        visions = np.clip(np.random.randn(creature_total) * average_trait_variability + average_vision, 1, 8)
        
        # loops to initialize creatures with the corresponding trait values and then append eacho ne to the list of creatures
        for i in range(creature_total):
            self.creatures.append(Creature(size=sizes[i], speed=speeds[i], vision=visions[i]))

    # resets all tiles and individuals at the end of a day (after reproduction)
    def reset(self):
        for row in self.gurt:
            for tile in row:
                tile.clear_creatures()
                tile.food = False
        for creature in self.creatures:
            creature.reset()

    # spawns food (for beginning of day)
    def spawn_food(self):
        for row in self.gurt:
            for tile in row:
                if random.random() < self.food_spawn_rate:
                    tile.food = True
    
    # moves a creature internally and externally to its new tile
    def move_creature(self, creature: Creature, tile: Tile):
        if tile is None:
            print("cannot move: missing tile argument")
            return
        
        if creature.x is not None and creature.y is not None:
            starting_tile = self.gurt[creature.y][creature.x]
            starting_tile.remove_creature(creature)

        creature.x = tile.X_coord
        creature.y = tile.Y_coord
        tile.add_creature(creature)
        creature.visited_tiles.append(tile)

    # places very creature on a tile (for starting the day)
    def place_creatures_on_tiles(self):
        for creature in self.creatures:
            tile = self.gurt[random.randint(0, self.edge_length-1)][random.randint(0, self.edge_length-1)]
            self.move_creature(creature, tile)

    # distributes food to all contest winners
    def handle_contests(self):
        active_tiles = set()
        for creature in self.creatures:
            if creature.x is not None and creature.y is not None:
                active_tiles.add(self.gurt[creature.y][creature.x])

        for tile in active_tiles:
            if tile.food and tile.is_occupied():
                winner = tile.contest()
                tile.creature_consumed_food(winner)

    # one singluar tick of simulation
    def simulate_tick(self):
        for creature in self.creatures:
            if creature.should_rest():
                creature.resting = True
            else:
                creature.resting = False
                tile = creature.choose_location(self)
                self.move_creature(creature, tile)

        self.handle_contests()

        for creature in self.creatures:
            creature.update_creature()

    # one full day of simulation
    def simulate_day(self):
        # spawns food and puts each creature on a tile
        self.spawn_food()
        self.place_creatures_on_tiles()

        # lets the ticks run
        for tick in range(self.ticks_per_day):
            self.simulate_tick()
        
        # store data from the day
        avg_size, avg_speed, avg_vision = self.average_trait_values()
        self.day_to_averages["size"][self.day] = avg_size
        self.day_to_averages["speed"][self.day] = avg_speed
        self.day_to_averages["vision"][self.day] = avg_vision
        self.day_to_population[self.day] = len(self.creatures)

        # handles death and reproduction fairly by shuffling randomly
        random.shuffle(self.creatures)

        #survival and reproduciton
        survivor_list = []
        offspring_list = []

        for creature in self.creatures:
            creature.survive_and_set_offspring()
            if creature.survives:
                survivor_list.append(creature)
                offspring = creature.reproduce_offspring()
                offspring_list.extend(offspring)

        # update population
        self.creatures = survivor_list + offspring_list
        
        # reset at the end of day
        self.reset()

        # increment day number
        self.day += 1

    # returns a list with the average for each trait currently
    def average_trait_values(self):
        total = len(self.creatures)
        avg_size = np.mean([c.size for c in self.creatures]) if total > 0 else 0
        avg_speed = np.mean([c.speed for c in self.creatures]) if total > 0 else 0
        avg_vision = np.mean([c.vision for c in self.creatures]) if total > 0 else 0
        return (avg_size, avg_speed, avg_vision)