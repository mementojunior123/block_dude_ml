import os
from typing import Callable
from time import sleep
import sys
from six import itervalues, iteritems
from neat.population import CompleteExtinctionException
sys.path.append(".")
import neat
import neat.config
from neat.config import Config as NeatConfig
import neat.population
from neat.population import Population
import block_dude_core as bd_core
from non_pygame.non_pygame_utils import stall

MAP_USED : bd_core.SavedMap = bd_core.TEST_MAP

class PopulationInterface:
    def __init__(self, population : neat.Population, gens : int|None = 50):
        self.pop = population
        self.current_generation : int = 0
        self.max_generations : int|None = gens


    def start_running(self):
        pop = self.pop
        if pop.config.no_fitness_termination and (self.end_generation is None):
            raise RuntimeError("Cannot have no generational limit with no fitness termination")
    
    def start_generation(self):
        self.pop.reporters.start_generation(self.pop.generation)
    
    def end_generation(self):
        pop = self.pop
        # Gather and report statistics.
        best = None
        for g in itervalues(pop.population):
            if best is None or g.fitness > best.fitness:
                best = g
        pop.reporters.post_evaluate(pop.config, pop.population, pop.species, best)

        # Track the best genome ever seen.
        if pop.best_genome is None or best.fitness > pop.best_genome.fitness:
            pop.best_genome = best

        if not pop.config.no_fitness_termination:
            # End if the fitness threshold is reached.
            fv = pop.fitness_criterion(g.fitness for g in itervalues(pop.population))
            if fv >= pop.config.fitness_threshold:
                pop.reporters.found_solution(pop.config, pop.generation, best)
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
    
def get_fitness(game : bd_core.Game, turn_count : int = 0) -> float:
    door_x, door_y = game.door_coords
    dist : float = float(abs(game.player_x - door_x) + abs(game.player_y - door_y))
    score : float = 80.0 - 5 * dist
    if door_x == game.player_x and door_y == game.player_y:
        game_win_score_bonus : float = 50.0 - turn_count
        if game_win_score_bonus < 20.0: game_win_score_bonus = 20.0
        score += game_win_score_bonus
    return score
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

def eval_genomes(genomes : list[neat.DefaultGenome], config : neat.config.Config):
    nets : list[neat.nn.FeedForwardNetwork] = []
    ges : list[neat.DefaultGenome] = []
    players : list[bd_core.Game] = []
    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        ges.append(genome)
        players.append(bd_core.Game.from_saved_map(MAP_USED, copy_map=True))
    
    #for turn in range(40):
    #finished_players : set[int] = set()
    for index, player in enumerate(players):
        for turn in range(40):
            #if index in finished_players: continue
            player_net = nets[index]
            player_genome = ges[index]
            verifications, actions = player.get_binds()
            output : list[float] = player_net.activate([*flatten_map_gen(player.map), player.player_x, player.player_y, 
                                                        player.player_direction, player.player_holding_block])
            output_dict : dict[int, float] = {i : output[i] for i in range(len(output))}
            sorted_output = sort_dict_by_values(output_dict, reverse=True)
            for action_type in sorted_output:
                if not verifications[action_type](): continue
                actions[action_type]()
                break
            player_genome.fitness = get_fitness(player, turn)
            if player.game_won():
                break
                #finished_players.add(index)
        #if len(finished_players) >= len(players):
            #break
                
        
def modify_config(config_path : str):
    input_count : int = 4 + (len(MAP_USED['map']) * len(MAP_USED['map'][0]))
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
    winner = run_interface(PopulationInterface(pop, 50))

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))
    stall()
    show_genome_playing(winner, config)


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
    local_path : str = os.path.dirname(__file__)
    config_path : str = os.path.join(local_path, "config-feedforward.txt")
    run(config_path)


