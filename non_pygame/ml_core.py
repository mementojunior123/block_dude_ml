import os
from typing import Callable, TypedDict
from time import sleep
import sys
import pickle
from six import itervalues, iteritems
from neat.population import CompleteExtinctionException
sys.path.append(".")
import neat
import neat.config
from neat.config import Config as NeatConfig
import neat.population
from neat.population import Population
import non_pygame.block_dude_core as bd_core
from non_pygame.non_pygame_utils import stall

MAP_USED : bd_core.SavedMap = bd_core.MAP3

class GenomeReplay(TypedDict):
    genome : neat.DefaultGenome
    config : neat.Config
    map_used : bd_core.SavedMap

class GenomeEvaluator:
    def __init__(self, genomes : list[tuple[int, neat.DefaultGenome]], config : neat.Config, the_map_used : bd_core.SavedMap):
        self.genomes = genomes
        self.config : neat.Config = config
        self.map_used : bd_core.SavedMap = the_map_used
        self.progress : int = 0
        self.genome_count : int = len(genomes)
    
    def isover(self) -> bool:
        return self.progress >= self.genome_count
    
    def do_genome(self):
        if self.isover(): return
        eval_genome(self.genomes[self.progress], self.config, self.map_used)
        self.progress += 1


def save_replay(file_path : str, replay : GenomeReplay):
    with open(file_path, 'wb') as file:
        pickle.dump(replay, file)

def load_replay(file_path : str) -> GenomeReplay|None:
    with open(file_path, 'rb') as file:
        replay = pickle.load(file)
    return replay

class PopulationInterface:
    def __init__(self, population : neat.Population, gens : int|None = 50):
        self.pop = population
        self.current_generation : int = 0
        self.max_generations : int|None = gens
        self.current_best_genome : neat.DefaultGenome|None = None
    
    def get_best_genome(self) -> neat.DefaultGenome:
        sorted_key_list = sorted(self.pop.population, key = lambda k: self.pop.population[k].fitness)
        return self.pop.population[sorted_key_list[-1]]

    def get_genome_list(self) -> list[tuple[int, neat.DefaultGenome]]:
        return list(iteritems(self.pop.population))

    def start_running(self):
        pop = self.pop
        if pop.config.no_fitness_termination and (self.end_generation is None):
            raise RuntimeError("Cannot have no generational limit with no fitness termination")
    
    def start_generation(self):
        self.pop.reporters.start_generation(self.pop.generation)
    
    def end_generation(self):
        pop = self.pop
        # Gather and report statistics.

        for g in itervalues(pop.population):
            if self.current_best_genome is None or g.fitness > self.current_best_genome.fitness:
                self.current_best_genome = g
        pop.reporters.post_evaluate(pop.config, pop.population, pop.species, self.current_best_genome)

        # Track the best genome ever seen.
        if pop.best_genome is None or self.current_best_genome.fitness > pop.best_genome.fitness:
            pop.best_genome = self.current_best_genome

        if not pop.config.no_fitness_termination:
            # End if the fitness threshold is reached.
            fv = pop.fitness_criterion(g.fitness for g in itervalues(pop.population))
            if fv >= pop.config.fitness_threshold:
                pop.reporters.found_solution(pop.config, pop.generation, self.current_best_genome)
                self.current_generation = self.max_generations
                return

        # Create the next generation from the current generation.
        pop.population = pop.reproduction.reproduce(pop.config, pop.species,
                                                        pop.config.pop_size, pop.generation)

        # Check for complete extinction.
        if not pop.species.species:
            pop.reporters.complete_extinction()

            # If requested by the user, create a completely new population,
            # otherwise raise an exception.
            if pop.config.reset_on_extinction:
                pop.population = pop.reproduction.create_new(pop.config.genome_type,
                                                                pop.config.genome_config,
                                                                pop.config.pop_size)
            else:
                raise CompleteExtinctionException()

        # Divide the new population into species.
        pop.species.speciate(pop.config, pop.population, pop.generation)

        pop.reporters.end_generation(pop.config, pop.population, pop.species)

        pop.generation += 1
        self.current_generation += 1
    
    def isover(self):
        return self.current_generation >= self.max_generations
    
    def end_run(self) -> neat.DefaultGenome:
        pop = self.pop
        if pop.config.no_fitness_termination:
            pop.reporters.found_solution(pop.config, pop.generation, pop.best_genome)

        return pop.best_genome
    

def flatten_map(map : list[list[int]]) -> list[int]:
    flat : list[int] = []
    for row in map:
        flat += row
    return flat

def flatten_map_gen(map : list[list[int]]):
    for row in map:
        for val in row:
            yield val


def sort_dict_by_values(input : dict, reverse : bool = True):
    return {k: v for k, v in sorted(input.items(), key=lambda item: item[1], reverse=reverse)}

def get_fitness(game : bd_core.Game, turn_count : int = 0) -> float:
    door_x, door_y = game.door_coords
    dist : float = game.get_adjusted_dist()
    score : float = 80.0 - 5 * dist
    if door_x == game.player_x and door_y == game.player_y:
        game_win_score_bonus : float = 400.0 - turn_count
        if game_win_score_bonus < 350.0: game_win_score_bonus = 350.0
        score += game_win_score_bonus
    if game.player_holding_block:
        score += 15.0
        if game.down_legal():
            score += 20.0
        else:
            score -= 30.0
    return score

def eval_genome(genome_arg : tuple[int, neat.DefaultGenome], config : neat.Config, used_map : bd_core.SavedMap|None = None):
    genome = genome_arg[1]
    genome.fitness = 0
    if used_map is None: used_map = MAP_USED
    player = bd_core.Game.from_saved_map(MAP_USED, copy_map=True)
    player_net = neat.nn.FeedForwardNetwork.create(genome, config)
    box_carry_start_dist : float|None = None
    box_carry_bonus : float = 0.0
    verifications, actions = player.get_binds()
    for turn in range(40):
        start_dist : float = player.get_dist()        
        output : list[float] = player_net.activate([*flatten_map_gen(player.map), player.player_x, player.player_y, 
                                                    player.player_direction, player.player_holding_block])
        output_dict : dict[int, float] = {i : output[i] for i in range(len(output))}
        sorted_output : dict[int, float] = sort_dict_by_values(output_dict, reverse=True)
        chosen_action : int
        for action_type in sorted_output:
            if not verifications[action_type](): continue
            actions[action_type]()
            chosen_action = action_type
            break
        end_dist : float = player.get_dist()
        if (end_dist + 0.5) < start_dist:
            genome.fitness += 1
        if chosen_action == bd_core.ActionType.DOWN.value:
            if not player.player_holding_block:
                box_carry_end_dist = player.get_facing_dist()
                progress : float = box_carry_start_dist - box_carry_end_dist
                box_carry_bonus += 6 * progress
                box_carry_start_dist = None
            else:
                box_carry_start_dist = player.get_facing_dist()
        genome.fitness = get_fitness(player, turn) + box_carry_bonus
        if player.game_won():
            genome.fitness += 20
            return

def eval_genomes(genomes : list[int, tuple[int, neat.DefaultGenome]], config : neat.config.Config, used_map : bd_core.SavedMap|None = None):
    if used_map is None: used_map = MAP_USED
    for genome in genomes:
        eval_genome(genome, config, used_map)
                
        
def modify_config(config_path : str, used_map : bd_core.SavedMap|None = None):
    if used_map is None: used_map = MAP_USED
    input_count : int = 4 + (len(used_map['map']) * len(used_map['map'][0]))
    with open(config_path, 'r') as file:
        og_lines : list[str] = file.readlines()
    
    with open(config_path, 'w') as file:
        for og_line in og_lines:
            if "num_inputs" in og_line:
                file.write(f"num_inputs              = {input_count}\n")
            else:
                file.write(og_line)

def run(config_path : str):
    modify_config(config_path)
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    pop : neat.Population = neat.Population(config)
    
    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    #pop.add_reporter(neat.Checkpointer(5))

    # Run for up to 50 generations.
    winner = run_interface(PopulationInterface(pop, 199))

    # show final stats
    print('\nBest genome:')
    print(f'Key: {winner.key}')
    print(f'Fitness: {winner.fitness}')
    stall()
    show_genome_playing(winner, config)
    with open('non_pygame/winners/winner1', 'wb') as file:
        pass
        #pickle.dump((winner, config), file)
    

def get_pop_runner(config_path : str, map_used : bd_core.SavedMap, generations : int) -> PopulationInterface:
    modify_config(config_path, map_used)
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    pop : neat.Population = neat.Population(config)
    
    return PopulationInterface(pop, generations)


def run_interface(ipop : 'PopulationInterface') -> neat.DefaultGenome:
    ipop.start_running()
    while True:
        ipop.start_generation()
        eval_genomes(list(iteritems(ipop.pop.population)), ipop.pop.config)
        ipop.end_generation()
        if ipop.isover(): break
    winner = ipop.end_run()
    return winner


def show_genome_playing(genome : neat.DefaultGenome, config : neat.config.Config, playback_speed : float = 5, max_turn : int = 100, 
                        intro_text : str = 'The best genome is now playing!'):
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    player = bd_core.Game.from_saved_map(MAP_USED, copy_map=True)
    bd_core.clear_console()
    print(intro_text)
    stall()
    bd_core.clear_console()
    player.render_terminal()
    won : bool = False
    for turn in range(max_turn):
        verifications, actions = player.get_binds()
        output : list[float] = net.activate([*flatten_map(player.map), player.player_x, player.player_y, 
                                                    player.player_direction, player.player_holding_block])
        output_dict : dict[int, float] = {i : output[i] for i in range(len(output))}
        sorted_output = sort_dict_by_values(output_dict, reverse=True)
        for action_type in sorted_output:
            if not verifications[action_type](): continue
            actions[action_type]()
            break
        bd_core.clear_console()
        player.render_terminal()
        if player.game_won():
            won = True
            print(f'This genome has beaten the level in {turn + 1} turns!')
            stall()
            break
        sleep(1/playback_speed)
    if not won:
        print("This genome ran out of time...")
        stall()
        

    

if __name__ == '__main__':
    with open('non_pygame/winners/winner1', 'rb') as file:
        pass
        #previous_winner, previous_config = pickle.load(file)
    #show_genome_playing(previous_winner, previous_config, intro_text='The previous best genome is now playing!')
    local_path : str = os.path.dirname(__file__)
    config_path : str = os.path.join(local_path, "config-feedforward.txt")
    run(config_path)


