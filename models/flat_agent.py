import numpy as np
import time
import gc
import os
from game.baba.rule import extract_ruleset, extract_rule
from concurrent.futures import ProcessPoolExecutor, as_completed
from models.utils import *

class FlatAgent:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.high_level_actions = None
        self.low_level_actions = None
        self.search_depth = None
        self.search_n_nodes = 0
        self.n_calls = 0
        self.debug = False
        
    def is_solution(self, state, init=False):
        return agent_at_goal(state, extract_ruleset(state))    

    def process_node(self, new_state, visited, next_frontier, solution_states, moves_by_state, state_hash, move, n_calls, img_path, depth, ann=""):
        new_state_hash = hash_grid(new_state)
        moves_to_new_state = moves_by_state[state_hash] + [move]
        # if we've visited this state before, check if this path is better
        if new_state_hash in visited:
            moves_by_state[new_state_hash] = self.compare_moves(moves_to_new_state, moves_by_state[new_state_hash])
        # otherwise, add to frontier/visited and check if solution
        else:  
            if self.debug:
                vis_grid(new_state, img_path + str(depth) + "/", ann=ann)   
            moves_by_state[new_state_hash] = moves_to_new_state
            visited.add(new_state_hash)
            next_frontier.append(new_state)
            is_sol = self.is_solution(new_state)
            if is_sol: 
                solution_states.append(new_state)
        
    def compare_moves(self, moves1, moves2):
        # agent pos1, agent pos2, block pos1, block pos2
        if len(moves1) < len(moves2):
            return moves1
        elif len(moves2) < len(moves1):
            return moves2
        else:
            dist1 = estimate_moves_dist(moves1)
            dist2 = estimate_moves_dist(moves2)
            if dist1 < dist2:
                return moves1
            elif dist2 < dist1:
                return moves2
            else:
                return [moves1, moves2][np.random.choice(2)]

        
    def BFS(self, init_state, img_path = "models/debug_imgs/"):
        add_rule_block_ids(init_state)
        
        n_cpu=os.cpu_count()
        
        if self.debug:
            img_path = img_path + str(len(os.listdir(img_path)) + 1) + "/"
            os.makedirs(img_path, exist_ok=True)
        
        frontier = [init_state]
        visited = set()
        visited.add(hash_grid(init_state))
        
        n_calls = {}
        nodes_visited = 0
        max_depth = 10000
        moves_by_state = {} # for each state, moves required
        moves_by_state[hash_grid(init_state)] = []
        solution_states = []
        is_sol = self.is_solution(init_state, True)
        n_calls[0] = 0
        if is_sol:
            solution_states.append(init_state)
            return solution_states, moves_by_state, nodes_visited, n_calls
        
        for depth in range(max_depth):
            n_calls[depth+1] = 0
            if len(frontier)==0:
                break
            
            n_calls_non_sol = 0
            
            batch_size = 100000
            
            maybe_solution_poss_moves = []
            non_solution_poss_moves = []
            start = time.time()
            args = [(s, hash_grid(s)) for s in frontier]
            with ProcessPoolExecutor(max_workers=n_cpu) as executor:
                for i in range(0, len(args), batch_size):
                    chunk = args[i:i+batch_size]
                    for (maybe_sol, non_sol, nc_maybe_sol, nc_non_sol) in executor.map(get_possible_moves_wrapper, chunk, chunksize=10):
                        n_calls[depth+1] += nc_maybe_sol
                        n_calls_non_sol += nc_non_sol
                        maybe_solution_poss_moves += maybe_sol
                        non_solution_poss_moves += non_sol
                
            print(f"poss moves processes took {time.time() - start:.2f} seconds") if self.debug else None
            
            frontier = []

            # first eval maybe solvable ones
            with ProcessPoolExecutor(max_workers=n_cpu) as executor:
                start = time.time()
                for (new_state, move, nc, state_hash) in executor.map(attempt_move_wrapper, maybe_solution_poss_moves, chunksize=10): # why do we think it's a soluton?
                    n_calls[depth+1] += nc
                    nodes_visited +=1
                    if new_state:  
                        self.process_node(new_state, visited, frontier, solution_states, moves_by_state, state_hash, move, n_calls, img_path, depth)
                print(f"ProcessPoolExecutor took {time.time() - start:.2f} seconds") if self.debug else None
            gc.collect()

            # break if we've found something
            if len(solution_states)>0:
                break
            
            n_calls[depth+1] += n_calls_non_sol
            
            # then eval not solvable ones  
            print(len(non_solution_poss_moves)) if self.debug else None
            n_processed = 0
            start = time.time()
            for i in range(0, len(non_solution_poss_moves), batch_size):
                chunk = non_solution_poss_moves[i:i+batch_size]
    
                with ProcessPoolExecutor(max_workers=n_cpu) as executor:
                    futures = [executor.submit(attempt_move_wrapper, args) for args in chunk]
                    for future in as_completed(futures):
                        new_state, move, nc, state_hash = future.result()
                        n_calls[depth+1] += nc
                        nodes_visited +=1
                        n_processed+=1
                        if self.debug:
                            if n_processed%1000==0:
                                with open("tmp.txt", 'w') as f:
                                    f.write(str(n_processed))
                        if new_state:  
                            self.process_node(new_state, visited, frontier, solution_states, moves_by_state, state_hash, move, n_calls, img_path, depth)
                gc.collect()
            print(f"ProcessPoolExecutor took {time.time() - start:.2f} seconds") if self.debug else None

        return solution_states, moves_by_state, nodes_visited, n_calls
        
        
    def get_high_level_actions(self, grid):
    
        solution_states, moves_by_state, n_actions_considered, n_calls = self.BFS(grid)
        
        if len(solution_states)>0:
            max_depth = max(n_calls.keys())
            self.n_calls = sum(n_calls.values()) - n_calls[max_depth] + n_calls[max_depth]/len(solution_states)
            solution_state_moves = [moves_by_state[hash_grid(sol_state)] for sol_state in solution_states]
            moves = solution_state_moves[np.random.choice(len(solution_state_moves))]  
        else:
            self.n_calls += sum(n_calls.values())
            moves = None
        
        self.n_call_dict = n_calls
        self.n_solutions = len(solution_states)
        self.search_n_nodes += n_actions_considered
        self.search_depth = max([len(moves) for moves in moves_by_state.values()])
        return moves
    
    
    def get_action(self, env):
        # Get high level actions (move to, push to)
        if self.high_level_actions is None:
            self.high_level_actions = self.get_high_level_actions(env.grid)
            self.low_level_actions = []
            
        # Get low level actions (keypresses)
        while len(self.low_level_actions)==0:
            # Recompute high level actions of necessary
            if len(self.high_level_actions)==0:
                self.high_level_actions = self.get_high_level_actions(env.grid)
                print(self.high_level_actions)
                # if no more high level actions, reset
                if self.high_level_actions is None:
                    print("RESETTING") if self.debug else None
                    return  {'action':"reset", 'search_n_nodes':self.search_n_nodes, 'search_depth':self.search_depth, 'n_calls':self.n_calls}
                    
            path, self.low_level_actions = get_low_level_actions(env.grid, self.high_level_actions[0])
            self.high_level_actions = self.high_level_actions[1:]

        action = self.low_level_actions[0]
        self.low_level_actions = self.low_level_actions[1:]
        return {'action':action, 'search_n_nodes':self.search_n_nodes, 'search_depth':self.search_depth, 'n_calls':self.n_calls, "n_call_dict":self.n_call_dict, "n_sol":self.n_solutions}
  
  

def get_block_push_moves(state):
    """
    Get all possible moves that involve pushing a rule block to a new locations
    Valid new locations include all locations adjacent to other rule blocks
    And, if the rule block is already adjacent to another rule block, any of the locations not adjacent to other rule blocks
    Prune moves for blocks previously determined to be unreachable
    """
    
    def check_maybe_solvable_after_move(sim_move):
        if isinstance(sim_move[3], list):
            sim_move = (sim_move[0], sim_move[1], sim_move[2], sim_move[3][0])
        if isinstance(sim_move[0], list):
            sim_move = (sim_move[0][0], sim_move[1], sim_move[2], sim_move[3])
        sim_state = simulate_move(state.copy(), sim_move)
        return agent_is_goal(sim_state)
    
    nc_maybe_sol = 0
    nc_non_sol = 0
    
    moves = []
    agent_pos = get_agent_pos(state)
    # Iterate thru rule blocks
    for k, e in enumerate(state):
        if e is not None and "rule" in e.type:
            # check if it's reachable
            found_maybe_solvable = False
            reachable = is_reachable(state, e)
            
            edge_x = on_x_border(e, state)
            edge_y = on_y_border(e, state)
            adj_rule_locs = []
            non_adj_rule_locs = []
            
            # Iterate thru other locations in grid
            for k2, e2 in enumerate(state):
                i, j = k2 % state.width, k2 // state.width
                if not(same_pos((i,j), e.cur_pos)) and (e2 is None or e2.type != 'border'):
                    if (edge_x and i != e.cur_pos[0]) or (edge_y and j != e.cur_pos[1]):
                        continue
                    if n_adjacent_rule_block(state, (i,j), exclude_ids=[e.id])==0 and e2 is None:
                        non_adj_rule_locs.append((i,j))
                    else:
                        adj_rule_locs.append((i,j)) 
            
            for loc in adj_rule_locs:
                m = (agent_pos, None, tuple(e.cur_pos), loc)
                sol = check_maybe_solvable_after_move(m)
                if sol:
                    found_maybe_solvable = True
                if reachable:
                    moves.append((sol, m)) 
                  
            if n_adjacent_rule_block(state, e.cur_pos)>0 and len(non_adj_rule_locs)>0:
                m = (agent_pos, None, tuple(e.cur_pos), non_adj_rule_locs)
                sol = check_maybe_solvable_after_move(m)
                if sol:
                    found_maybe_solvable = True
                if reachable:
                    moves.append((sol, m))
             
            if found_maybe_solvable:
                nc_maybe_sol += 1
            else:
                nc_non_sol += 1   
                    
    return moves, nc_maybe_sol, nc_non_sol

def get_goto_goal_moves(state):
    """
    Get all possible moves that involve moving the avatar to a goal object
    """
    goal_pos_list = get_goal_pos(state, extract_ruleset(state))
    ruleset = extract_ruleset(state)
    agent_pos = get_agent_pos(state, ruleset)
    move_list = []
    for gp in goal_pos_list:
        move = (agent_pos, tuple(gp))
        move_list.append(move)
    return move_list

def get_possible_moves_wrapper(args):
    state, state_hash = args
    m1, nc_maybe_sol, nc_non_sol = get_block_push_moves(state)
    m2 = get_goto_goal_moves(state)
    possible_moves = m1
    for m in m2:
        possible_moves.append((True, m))
    
    maybe_solution_poss_moves = []
    non_solution_poss_moves = []
    for (maybe_solution, poss_move) in possible_moves:
        if maybe_solution:
            maybe_solution_poss_moves.append((poss_move, state, state_hash))
        else:
            non_solution_poss_moves.append((poss_move, state, state_hash))
 
    return maybe_solution_poss_moves, non_solution_poss_moves, nc_maybe_sol, nc_non_sol
 
 
def attempt_goto_goal(state):
    goal_pos_list = get_goal_pos(state, extract_ruleset(state))
    ruleset = extract_ruleset(state)
    agent_pos = get_agent_pos(state, ruleset)
    if agent_pos is None or len(goal_pos_list)==0:
        return None, 0
    path, _ = run_astar(agent_pos, goal_pos_list, state)
    if path is None:
        return None, 1
    else:
        return (path[0][0], path[-1][0]), 1

def move_generator(poss_moves, n_cpu):
    with ProcessPoolExecutor(max_workers=n_cpu) as executor:
        for (new_state, move, nc, state_hash) in executor.map(attempt_move_wrapper, poss_moves, chunksize=10):
            yield new_state, move, nc, state_hash

def attempt_move_wrapper(args):
    move, state, state_hash = args
    if get_agent_pos(state, extract_ruleset(state)) is None:
        return None, None, 0, state_hash

    if len(move) == 4:
        (_, _, push_from_pos, push_to_pos) = move
        r = state.get(*push_from_pos)
        if isinstance(push_to_pos, list): # pushing block to one of any positions away from other rule blocks
            scores = [1 / (n_adjacent_stop(state, p) + 1) for p in push_to_pos]
            path, _ = run_astar(get_agent_pos(state), push_to_pos, state, push_from_pos, scores)
        else:
            path, _ = run_astar(get_agent_pos(state), [push_to_pos], state, push_from_pos)
    else:
        path, _ = run_astar(get_agent_pos(state), [move[1]], state)
    
    if path is None:
        return None, None, 1, state_hash
    else:
        if len(move) == 4:
            move = (path[0][0], path[-1][0], move[2], path[-1][1])
        else:
            move = (path[0][0], path[-1][0])
        new_state = simulate_move(state.copy(), move)
        return new_state, move, 1, state_hash