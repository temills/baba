import numpy as np
import os
from game.baba.rule import extract_ruleset, extract_rule
import itertools
from models.utils import *

class Agent:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.high_level_actions = None
        self.low_level_actions = None
        self.search_depth = None
        self.phase = "centering"
        self.search_n_nodes = 0
        self.n_calls = 0
        self.n_calls = 0
        self.n_err = 0
        self.debug = False

    def is_solvable(self, state):
        ruleset = extract_ruleset(state)
        avatar_pos = get_agent_pos(state, ruleset)
        goal_pos = get_goal_pos(state, ruleset)
        if len(goal_pos)==0 or avatar_pos is None:
            return False
        path, actions = run_astar(avatar_pos, goal_pos, state)
        return path is not None
    
    def get_possible_moves(self, grid):
        reachable_rule_blocks = get_all_rule_blocks(grid)
        possible_rules = self.get_possible_rules(reachable_rule_blocks) # free
        curr_rules = self.get_curr_rules(grid) # free
        changeable_rules = []
        for rule in possible_rules:
            to_form = not(np.any([rules_eq(rule, curr_rule) for curr_rule in curr_rules]))
            changeable_rules.append((to_form, rule))
        # might these be solvable?
        return [(self.maybe_solvable(grid, r), r) for r in changeable_rules]
        
    def attempt_move(self, grid, rule_to_change, reachable_by_state):
        """
        Try to form the given rule using low level path finder
        """
        # move is a set of rule blocks and form/break indication
        achievable_state, achievable_move, nc = self.attempt_rule_change(rule_to_change[1], rule_to_change[0], grid, reachable_by_state)
        return achievable_state, achievable_move, nc, reachable_by_state
        
    def compare_moves(self, moves1, moves2):
        # each of these is a list of lists of moves (one list per rule change)
        # agent pos1, agent pos2, block pos1, block pos2
        if len(moves1) < len(moves2):
            return moves1
        elif len(moves2) < len(moves1):
            return moves2
        else:
            dist1 = sum([estimate_moves_dist(rule_moves) for rule_moves in moves1])
            dist2 = sum([estimate_moves_dist(rule_moves) for rule_moves in moves1])
            if dist1 < dist2:
                return moves1
            elif dist2 < dist1:
                return moves2
            else:
                return [moves1, moves2][np.random.choice(2)]
    
    def is_solution(self, state, is_init=False):
        ruleset = extract_ruleset(state)
        avatar_pos = get_agent_pos(state, ruleset)
        goal_pos = get_goal_pos(state, ruleset)
        if not is_init:
            if len(goal_pos)==0 or avatar_pos is None:
                return False, 0
        path, actions = run_astar(avatar_pos, goal_pos, state)
        return path is not None, 1
            
        
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
            is_sol, nc = self.is_solution(new_state)
            n_calls[depth+1] += nc
            if is_sol:
                solution_states.append(new_state)
            
    
    
    def rulespace_BFS(self, grid):
        add_rule_block_ids(grid)
        
        found_solution = False
        while not(found_solution):
            solution_states, moves_by_state, n_nodes, n_calls = self.BFS(grid.copy())
            self.search_n_nodes += n_nodes
            self.n_calls += n_calls
            if len(solution_states)==0:
                print("NO SOLUTION") if self.debug else None
            else:
                solution_state_moves = [moves_by_state[hash_grid(sol_state)] for sol_state in solution_states]
                i = np.random.choice(len(solution_state_moves))#, p=softmax(scores))
                joined_moves = [tup for move_list in solution_state_moves[i] for tup in move_list]
                found_solution = True
        self.search_depth = min([len(moves) for moves in solution_state_moves])
        
        return joined_moves

    def check_solution(self, grid, moves):
        """
        Are these moves really doable and do they really produce a solvable POMDP?
        """
        sim_state = grid.copy()
        sim_state.assumptions = []
        for move in moves:
            if len(move)==4:
                (go_from_pos, go_to_pos, push_from_pos, push_to_pos) = move
                path, actions = run_astar(go_from_pos, [push_to_pos], sim_state, push_from_pos)
            else:
                (go_from_pos, go_to_pos) = move
                path, actions = run_astar(go_from_pos, [go_to_pos], sim_state, push_from_pos)
            if path is None: 
                return False
            else:
                sim_state = simulate_move(sim_state, move)
        # now can we get to goal
        return self.is_solvable(sim_state)
        
    def form_block_pos(self, rule, rule_loc, grid, verbose=False): 
        """
        Low-level BFS for rule change
        Given rule (list of blocks), desired positions for blocks, and grid,
        Run BFS to check if desired positions are achievable
        """
        def is_solution(state):
            blocks = [get_block_by_id(state, block.id) for block in rule] 
            return np.all([same_pos(blocks[i].cur_pos, rule_loc[i]) for i in range(len(blocks))])
        
        def get_possible_actions(state):
            # actions are block_idx, position pairs
            actions = []
            for block_idx in range(len(rule)):
                block = get_block_by_id(state, rule[block_idx].id)
                if not same_pos(block.cur_pos, rule_loc[block_idx]):
                    actions.append((block_idx, rule_loc[block_idx]))
            return actions
        
        def compare_moves(moves1, moves2):
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
        
        def attempt_move(state, block_idx, goal_loc):
            """
            Can we move the given block to the goal location?
            """
            block_id = rule[block_idx].id
            block = get_block_by_id(state, block_id)
            if same_pos(block.cur_pos, goal_loc):
                return True, state, None, 0
            if get_agent_pos(state) is None:
                return False, state, None, 0
            else:
                path, actions = run_astar(get_agent_pos(state), [goal_loc], state, block.cur_pos)
                if path is None:
                    return False, state, None, 1
                else:
                    block_move = (path[0][0],  path[-1][0], block.cur_pos, goal_loc) #curr pos, resulting pos, push from, push to
                    sim_state = simulate_move(state.copy(), block_move)
                    return True, sim_state, block_move, 1
        
        moves_by_state = {} 
        moves_by_state[hash_grid(grid)] = []
        n_calls = {}
        max_depth =  10000
        frontier = [grid]
        solution_states = []
        if is_solution(grid):
            solution_states.append(grid)
            
        for depth in range(max_depth):
            if verbose: print("depth: ", depth)
            n_calls[depth+1] = 0
            if len(frontier)==0 or len(solution_states)>0:
                break
            next_frontier = []
            possible_actions = []
            for state in frontier:
                for (block_idx, goal_loc) in get_possible_actions(state):
                    possible_actions.append((block_idx, goal_loc, state))
            
            np.random.shuffle(possible_actions)
            
            for (block_idx, goal_loc, state) in possible_actions:
                state_hash = hash_grid(state)
                is_achievable, new_state, move, n_calls_move = attempt_move(state, block_idx, goal_loc)
                n_calls[depth+1] += n_calls_move
                if is_achievable:
                    new_state_hash = hash_grid(new_state) 
                    moves_to_new_state = moves_by_state[state_hash] + [move]
                    if new_state_hash in moves_by_state.keys():
                        moves_by_state[new_state_hash] = compare_moves(moves_to_new_state, moves_by_state[new_state_hash])
                    else:
                        moves_by_state[hash_grid(new_state)] = moves_to_new_state
                        next_frontier.append(new_state)
                        if is_solution(new_state):
                            solution_states.append(new_state)
                            break
                        
            if len(solution_states)>0:
                break

            frontier = next_frontier
            
        if len(solution_states)>0:
            solution_state_moves = [moves_by_state[hash_grid(sol_state)] for sol_state in solution_states]
            assert(len(solution_state_moves))==1
            idx = np.random.choice(len(solution_state_moves))
            return solution_states[idx], solution_state_moves[idx], sum(n_calls.values())
        else:
            return None, None, sum(n_calls.values())

    def get_possible_rules(self, rule_blocks):
        """ linguistically valid rule block combos """ 
        possible_rules = [block_list for block_list in itertools.permutations(rule_blocks, 3) if extract_rule(block_list) is not None]
        return possible_rules   

    def get_curr_rules(self, grid):
        """ currenty active rules """
        rules = []
        for k, e in enumerate(grid):
            if e is not None and e.type == 'rule_is':
                i, j = k % grid.width, k // grid.width
                if in_bounds(grid, (i-1, j)) and in_bounds(grid, (i+1, j)):
                    block_list = [grid.get(i-1, j), e, grid.get(i+1, j)]
                    if extract_rule(block_list) is not None:
                        rules.append(block_list)
                if in_bounds(grid, (i, j-1)) and in_bounds(grid, (i, j+1)):
                    block_list = [grid.get(i, j-1), e, grid.get(i, j+1)]
                    if extract_rule(block_list) is not None:
                        rules.append(block_list) 
        return rules

    def get_rule_diff(self, rules1, rules2):
        """ return rules in rules1 that aren't in rules2 """
        diff = []
        for rule in rules1:
            in_other = False
            for other_rule in rules2:
                if np.all([rule[i].id == other_rule[i].id for i in range(3)]):
                    in_other = True
                    break
            if not in_other:
                diff.append(rule)
        return diff
        
    def BFS(self, init_state, img_path = "models/debug_imgs/"):
        print("Starting BFS!")
        if self.debug:
            img_path = img_path + str(len(os.listdir(img_path)) + 1) + "/"
            os.makedirs(img_path, exist_ok=True)
        
        frontier = [init_state]
        visited = set()
        visited.add(hash_grid(init_state))
        
        n_calls = {}
        tmp = {}
        nodes_visited = 0
        max_depth = 10000
        moves_by_state = {} # for each state, moves required
        moves_by_state[hash_grid(init_state)] = []
        solution_states = []
        is_sol, nc = self.is_solution(init_state, True)
        n_calls[0] = nc
        tmp[0] = nc
        if is_sol:
            solution_states.append(init_state)
            return solution_states, moves_by_state, nodes_visited, n_calls[0]
        
        for depth in range(max_depth):
            n_calls[depth+1] = 0
            tmp[depth+1] = {}
            if len(frontier)==0:
                break
            
            
            next_frontier = []
            print("Depth: ", depth)
            maybe_solvable_poss_moves = []
            unsolvable_poss_moves = []
            for state in frontier:
                for poss_move in self.get_possible_moves(state):
                    if poss_move[0]:
                        maybe_solvable_poss_moves.append((poss_move[1], state))
                    else:
                        unsolvable_poss_moves.append((poss_move[1], state))
            
            # shuffle next moves
            np.random.shuffle(maybe_solvable_poss_moves)
            np.random.shuffle(unsolvable_poss_moves)
            
            reachable_by_state = {}
            tmp[depth+1]["achv"] = []
            tmp[depth+1]["n_achv"] = []
            tmp[depth+1]["rch"] = 0
            for (possible_move, state) in maybe_solvable_poss_moves:
                state_hash = hash_grid(state)
                reachable_by_state[state_hash] = reachable_by_state.get(state_hash, {})
                new_state, move, nc, reachable_by_state = self.attempt_move(state, possible_move, reachable_by_state) # achievable moves/resulting states
                n_calls[depth+1] += nc
                nodes_visited += 1
                # if it's achievable, add to visited and frontier
                if new_state:
                    self.process_node(new_state, visited, next_frontier, solution_states, moves_by_state, state_hash, move, n_calls, img_path, depth)
                if len(solution_states)>0:
                    break
            if len(solution_states)>0:
                break
            # then eval not solvable ones    
            for (possible_move, state) in unsolvable_poss_moves:
                state_hash = hash_grid(state)
                reachable_by_state[state_hash] = reachable_by_state.get(state_hash, {})
                new_state, move, nc, reachable_by_state = self.attempt_move(state, possible_move, reachable_by_state)
                n_calls[depth+1] += nc
                nodes_visited += 1
                # if it's achievable, add to visited and frontier
                if new_state:
                    self.process_node(new_state, visited, next_frontier, solution_states, moves_by_state, state_hash, move, n_calls, img_path, depth)
            frontier = next_frontier

        if len(solution_states)>0:
            mean_n_calls = sum(n_calls.values())
        else:
            mean_n_calls = sum(n_calls.values())
        
        return solution_states, moves_by_state, nodes_visited, mean_n_calls

    def get_action(self, env):
        # get high level action (centering or solving)
        while(True):
            if self.phase == "centering":
                if self.high_level_actions is None:
                    self.high_level_actions = self.rulespace_BFS(env.grid)
                    self.low_level_actions = []
                # if we're out of low and high level actions, it's time to solve
                if len(self.low_level_actions)==0 and len(self.high_level_actions)==0:
                    self.phase = "solving"
                    #print("switching to solving")
                    self.high_level_actions = None
                    continue
                # get low level action for high level action
                if len(self.low_level_actions)==0:
                    grid = env.grid.copy()
                    path, self.low_level_actions = get_low_level_actions(grid, self.high_level_actions[0])
                    self.high_level_actions = self.high_level_actions[1:]
                break
            if self.phase == "solving":
                #if self.high_level_actions is None:
                grid = env.grid.copy()
                path, actions = run_astar(get_agent_pos(grid), get_goal_pos(grid, extract_ruleset(grid)), grid)
                if path is None:
                    self.phase = "centering"
                    # reset env
                    print("RESETTING!")
                    return  {'action':"reset", 'search_n_nodes':self.search_n_nodes, 'search_depth':self.search_depth, 'n_calls':self.n_calls, 'n_err':self.n_err}
                else:
                    self.low_level_actions = actions
                break
        
        # get low level action
        action = self.low_level_actions[0]
        self.low_level_actions = self.low_level_actions[1:]

        return {'action':action, 'search_n_nodes':self.search_n_nodes, 'search_depth':self.search_depth, 'n_calls':self.n_calls,'n_err':self.n_err}



    def maybe_solvable(self, grid, rule):
        """
        If we form this rule in this grid, could the corresponding pomdp be solvable?
        (Is there a you and win object?)
        """
        to_form = rule[0]
        rule_to_change = rule[1]

        # get objs currently in grid
        objs_in_grid = set()
        for e in grid:
            if e is not None:
                objs_in_grid.add(e.type)

        # replace objs if we are forming a replace rule
        if to_form and rule_to_change[0].type=="rule_object" and rule_to_change[0].name in objs_in_grid and rule_to_change[2].type=="rule_object":
            objs_in_grid.add(rule_to_change[2].name)
            objs_in_grid.discard(rule_to_change[0].name)
                
        # then check for win rule and you rule
        if to_form:
            rules = self.get_curr_rules(grid) + [rule_to_change]
        else:
            rules = [rule for rule in self.get_curr_rules(grid) if not rules_eq(rule, rule_to_change)]
        
        is_win = np.any([rule[2].name=="win" and rule[0].name in objs_in_grid for rule in rules])
        is_you = np.any([rule[2].name=="you" and rule[0].name in objs_in_grid for rule in rules])

        return is_win and is_you 
    

    def attempt_rule_change(self, rule, to_form, grid, reachable={}):
        """
        Low-level subroutine to attempt moving rule blocks to form/break this rule using BFS
        Return list of moves, resulting states, and n. A* calls
        """
        n_calls = 0
            
        if get_agent_pos(grid, extract_ruleset(grid)) is None:
            return None, None, n_calls
        
        state_hash = hash_grid(grid)
        
        for r in rule:   
            if r.id not in reachable[state_hash].keys():
                reachable[state_hash][r.id] = is_reachable(grid, r) 
                n_calls += 1
            
        pos0 = rule[0].cur_pos
        pos1 = rule[1].cur_pos
        pos2 = rule[2].cur_pos
        
        if to_form:
            all_rule_locs = [
                            [pos0, right(pos0, 1), right(pos0, 2)],
                            [pos0, down(pos0, 1), down(pos0, 2)],
                            [left(pos1, 1), pos1, right(pos1, 1)],
                            [up(pos1, 1), pos1, down(pos1, 1)],
                            [left(pos2, 2), left(pos2, 1), pos2],
                            [up(pos2, 2), up(pos2, 1), pos2]
                            ]
        else:
            # form vertically
            if pos0[0]==pos1[0]:
                all_rule_locs = [
                    [left(pos0,1), pos1, pos2],
                    [right(pos0,1), pos1, pos2],
                    [pos0, left(pos1,1), pos2],
                    [pos0, right(pos1,1), pos2],
                    [pos0, pos1, left(pos2,1)],
                    [pos0, pos1, right(pos2,1)]
                ]
            # form horizontally 
            else:
                all_rule_locs = [
                    [up(pos0,1), pos1, pos2],
                    [down(pos0,1), pos1, pos2],
                    [pos0, up(pos1,1), pos2],
                    [pos0, down(pos1,1), pos2],
                    [pos0, pos1, up(pos2,1)],
                    [pos0, pos1, down(pos2,1)]
                ]
            
        # Prune locations with block positions are:
        #   out of bounds
        #   require moving a rule block away from a border
        #   require moving a rule block that is in another rule
        all_rule_locs = [[tuple(pos) for pos in l] for l in all_rule_locs] # convert positions to tuples
        all_rule_locs = [list(tup) for tup in set([tuple(l) for l in all_rule_locs])] # remove repeats
        rule_locs = []
        curr_rules = [curr_rule for curr_rule in self.get_curr_rules(grid) if not(rules_eq(curr_rule, rule))]
        immovable = [np.any([block_in_rule(block, curr_rule) for curr_rule in curr_rules]) for block in rule]
        for block_locs in all_rule_locs: 
            prune = False
            for i in range(len(block_locs)):
                if not in_bounds(grid, block_locs[i]) or is_border(grid, block_locs[i]):
                    prune=True
                elif (not same_pos(block_locs[i], rule[i].cur_pos)):
                    if immovable[i] or not reachable[state_hash][rule[i].id]:
                        prune=True
                    elif on_x_border(rule[i], grid):
                        if not(block_locs[i][0]==rule[i].cur_pos[0]):
                            prune = True
                    elif on_y_border(rule[i], grid):
                        if not(block_locs[i][1]==rule[i].cur_pos[1]):
                            prune = True
            if not prune:
                rule_locs.append(block_locs)
            
            
        if len(rule_locs)==0:
            return None, None, n_calls

        # Sort rule locations by desirability
        scores = []
        for rule_loc in rule_locs:
            sim_state = grid.copy()
            for (i, block_loc) in enumerate(rule_loc):
                curr_block = get_block_by_id(sim_state, rule[i].id)
                if curr_block is not None:
                    curr_block_loc = curr_block.cur_pos
                    if not same_pos(curr_block_loc, block_loc):
                        agent_pos = get_agent_pos(sim_state)
                        if isinstance(agent_pos, list):
                            agent_pos = agent_pos[np.random.choice(len(agent_pos))]
                        move = (agent_pos,  None, curr_block_loc, block_loc)
                        sim_state = simulate_move(sim_state.copy(), move)
            score = score_grid(sim_state)
            scores.append(score)
        
        rule_locs = [rl for rl, score in sorted(zip(rule_locs, scores), key=lambda x: x[1], reverse=True)]

        # BFS to attempt to reach rule_locs
        achievable_move = None
        achievable_state = None
        prev_rules = self.get_curr_rules(grid)
        for rule_loc in rule_locs:
            solution_state, moves, n_calls_bfs = self.form_block_pos(rule, rule_loc, grid)
            n_calls += n_calls_bfs
            if solution_state is not None:
                achievable_state = solution_state
                achievable_move = moves
                new_rules = self.get_curr_rules(solution_state)
                n_changes = len(self.get_rule_diff(new_rules, prev_rules) + self.get_rule_diff(prev_rules, new_rules))
                # Only change more than one rule if necessary
                if n_changes == 1:
                    break
        
        return achievable_state, achievable_move, n_calls

    

