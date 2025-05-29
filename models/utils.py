import numpy as np
import heapq
import os
import glob
from game.baba.rule import extract_ruleset
from PIL import Image, ImageDraw, ImageFont
import itertools

"""
Common util functions between mepomdp and flat agents
"""

def get_low_level_actions(grid, high_level_action):
    """
    Executes actions of the form "move to this loc" or "push block to this loc"
    """
    if len(high_level_action)==4 :
        (go_from_pos, go_to_pos, push_from_pos, push_to_pos) = high_level_action
        path, actions = run_astar(go_from_pos, [push_to_pos], grid, push_from_pos) 
    elif len(high_level_action)==2:
        goal_pos = [high_level_action[1]]
        path, actions = run_astar(high_level_action[0], goal_pos, grid)
    else:
        raise ValueError(f"Unknown action type")
    return path, actions


def estimate_moves_dist(moves):
    """
    Heuristic estimate of distance travelled to carry out list of moves
    """
    def heuristic_dist(pos, goal_pos):
        dists = [abs(pos[0] - gp[0]) + abs(pos[1] - gp[1]) for gp in goal_pos]
        return min(dists)

    def move_dist(move):
        if len(move)==2:
            return heuristic_dist(move[0], [move[1]])
        else:
            return heuristic_dist(move[0], [move[2]]) + heuristic_dist(move[2], [move[3]])
    
    return sum([move_dist(m) for m in moves])


def simulate_move(grid, move):
    """
    Quickly simulate resulting grid state after taking given move, without doing low-level pathfinding
    """
    def get_adj_pos(grid, push_to_pos, dir):
        dirs = [d for d in [(1, 0), (-1, 0), (0, 1), (0, -1)] if not same_pos(d, dir)]
        for d in [dir] + dirs:
            if grid.get(push_to_pos[0]+d[0], push_to_pos[1]+d[1]) is None:
                return (push_to_pos[0]+d[0], push_to_pos[1]+d[1])
        return None

    if len(move)==4:   
        (go_from_pos, go_to_pos, push_from_pos, push_to_pos) = move
        es = [] 
        if go_from_pos is None:
            es.append(None)
        else:
            es.append(grid.get(*go_from_pos))
            if go_to_pos is not None:
                grid.set(*go_from_pos, None)
        es.append(grid.get(*push_from_pos))
        grid.set(*push_from_pos, None)
        if go_to_pos is not None:
            grid.set(*go_to_pos, es[0])
        # push existing block at loc in direction of movement
        e_cur = grid.get(*push_to_pos)
        if e_cur is not None and e_cur.is_push():
            if go_to_pos is not None:
                vec = np.array([push_to_pos[0] - go_to_pos[0], push_to_pos[1] - go_to_pos[1]])
            else:
                vec = np.array([push_to_pos[0] - push_from_pos[0], push_to_pos[1] - push_from_pos[1]])
            # handle ties
            if abs(vec[0])==abs(vec[1]):
                vec[np.random.choice(2)] = 0
            vec *= abs(vec)==max(abs(vec))
            dir = [int(e) for e in vec/sum(vec)]
                
            adj_pos = get_adj_pos(grid, push_to_pos, dir)
            if adj_pos is not None:
                grid.set(*push_to_pos, None)
                grid.set(*adj_pos, e_cur)
        grid.set(*push_to_pos, es[1])
    else:
        (go_from_pos, go_to_pos) = move
        if go_from_pos is None:
            e = None
        else:
            e = grid.get(*go_from_pos)
            grid.set(*go_from_pos, None)
        if go_to_pos is not None:
            grid.set(*go_to_pos, e)
    
    grid = update_rules(grid)
    return grid
   
def get_rules_for_astar(grid, agent_el, block_el, agent_pos, block_pos):
    """
    Helper function for A* algorithm that quickly extracts active rules from current grid
    """
    grid.set(*agent_pos, agent_el)
    if block_pos:
        grid.set(*block_pos, block_el)

    rule_dict = {"float":set(), "stop":set(["border"]), "sink":set(), "you":set()}
    
    def check_possible_rule(pos1, pos2):
        if in_bounds(grid, pos1) and in_bounds(grid, pos2):
            cell2 = grid.get(*pos2)
            if cell2 is not None and cell2.type == "rule_property":
                cell1 = grid.get(*pos1)
                if cell1 is not None and cell1.type=="rule_object":  
                    if cell2.name in rule_dict.keys():
                        rule_dict[cell2.name].add(cell1.name)                              

    for (k,e) in enumerate(grid):
        if e is not None and e.type == 'rule_is':
            i, j = k % grid.width, k // grid.width
            check_possible_rule((i-1, j), (i+1, j))
            check_possible_rule((i, j-1), (i, j+1))

    avatar_exists = np.any([e is not None and e.type in rule_dict["you"] for e in grid])
    is_float = len(rule_dict["float"] & rule_dict["you"]) > 0 
    
    # reset grid
    grid.set(*agent_pos, None)
    if block_pos:
        grid.set(*block_pos, None)
                
    return (avatar_exists, list(rule_dict["stop"]), list(rule_dict["sink"]), is_float)
    
    
def run_astar(agent_pos, goal_pos, grid, block_pos=None, goal_pos_scores=None):
    """
        A* pathfinder
        If block_pos is provided, find a path to push the block to goal_pos
        Otherwise find a path for the agent to reach goal_pos
    """
    
    # Deal with special case of multiple agents
    if isinstance(agent_pos, list):
        paths_and_actions = [run_astar(p, goal_pos, grid, block_pos, goal_pos_scores) for p in agent_pos]
        valid_paths_and_actions = [tup for tup in paths_and_actions if tup[0] is not None]
        if len(valid_paths_and_actions)==0:
            return None, []
        else:
            scores = [1/(len(actions)+1) for (path, actions) in valid_paths_and_actions]
            path, actions = valid_paths_and_actions[np.random.choice(len(valid_paths_and_actions), p=softmax(scores))]
            return path, actions
    # Deal with special case of preferred goal positions
    if goal_pos_scores is not None:
        while(len(goal_pos)>0):
            max_score = max(goal_pos_scores)
            best_positions = [p for (i,p) in enumerate(goal_pos) if goal_pos_scores[i]==max_score]
            path, actions = run_astar(agent_pos, best_positions, grid, block_pos) 
            if path is not None:
                return path, actions
            goal_pos = [p for (i,p) in enumerate(goal_pos) if goal_pos_scores[i]!=max_score]
            goal_pos_scores = [s for s in goal_pos_scores if s != max_score]
        return None, []
    
    # Standard A*
    def ok_pos(pos, curr_block_pos, sink_types, stop_types, is_float, direction=(0,0), pushed=False):
        if not in_bounds(grid, pos) or is_border(grid, pos):
            return False
        e = grid.get(*pos)
        e_under = grid.get_under(*pos)
        if pushed:
            if e is None:
                return True
            if "rule" in e.type:
                return (any(same_pos(pos, gp) and ok_pos((pos[0]+direction[0], pos[1]+direction[1]), curr_block_pos, sink_types, stop_types, is_float, direction) for gp in goal_pos))
            return (e.type not in stop_types and e.type not in sink_types and (e_under is None or e_under.type not in stop_types))
        else:
            if e is None or (curr_block_pos and same_pos(pos, curr_block_pos)):
                return True
            if "rule" in e.type:
                return (np.any([same_pos(pos, gp) and (not curr_block_pos or can_push(pos, gp, direction, sink_types, stop_types)) for gp in goal_pos]))
            return (e.type not in stop_types and (is_float or e.type not in sink_types) and (e_under is None or e_under.type not in stop_types))

    def can_push(agent, block, direction, sink_types, stop_types):
        ax, ay = agent
        bx, by = block
        dx, dy = direction
        return (ax == bx - dx and ay == by - dy) and ok_pos((bx + dx, by + dy), None, sink_types, stop_types, False, direction, pushed=True)

    def heuristic(pos, goals):
        return min(abs(pos[0] - g[0]) + abs(pos[1] - g[1]) for g in goals)

    if not goal_pos or agent_pos is None:
        return None, []
    
    grid = grid.copy()
    agent_pos = tuple(agent_pos)
    block_pos = tuple(block_pos) if block_pos else None
    agent_el = grid.get(*agent_pos)
    block_el = None
    
    grid.set(*agent_pos, None)
    if block_pos:
        block_el = grid.get(*block_pos)
        grid.set(*block_pos, None)

    directions = {(-1, 0): 3, (1, 0): 4, (0, -1): 1, (0, 1): 2}
    
    start_state = (agent_pos, block_pos)
    parents = {start_state: None}
    parent_actions = {start_state: None}

    g_costs = {start_state: 0}
    counter = itertools.count()
    frontier = [[heuristic(block_pos or agent_pos, goal_pos), next(counter), start_state]]
    visited = set()

    rules_by_state = {}

    while frontier:
        _, _, state = heapq.heappop(frontier)
        
        (current_agent, current_block) = state
        if state in visited:
            continue
        visited.add(state)
        target = current_block if block_pos else current_agent
        if any(same_pos(target, gp) for gp in goal_pos):
            path, actions = [], []
            while state is not None:
                path.append(state)
                actions.append(parent_actions[state])
                state = parents[state]
            return path[::-1], actions[::-1][1:]

        if state not in rules_by_state.keys():
            rules_by_state[state] = get_rules_for_astar(grid, agent_el, block_el, current_agent, current_block)        
        
        avatar_exists, stop_types, sink_types, is_float = rules_by_state[state]
        
        if not avatar_exists:
            continue
        
        for (dx, dy), action in directions.items():
            no_rule_change = True
            new_agent = (current_agent[0] + dx, current_agent[1] + dy)

            if not ok_pos(new_agent, current_block, sink_types, stop_types, is_float, (dx, dy), False):
                continue

            if block_pos and same_pos(new_agent, current_block):
                new_block = (current_block[0] + dx, current_block[1] + dy)
                no_rule_change = False
                if not ok_pos(new_block, current_block, sink_types, stop_types, is_float, (dx, dy), True):
                    continue
            else:
                new_block = current_block
                
            new_state = (new_agent, new_block)
            new_g_cost = g_costs[state] + 1
            if new_g_cost < g_costs.get(new_state, 10000):
                if no_rule_change:
                    rules_by_state[new_state] = rules_by_state[state]
                g_costs[new_state] = new_g_cost
                f_cost = new_g_cost + heuristic(new_block or new_agent, goal_pos)
                parents[new_state] = state
                parent_actions[new_state] = action
                heapq.heappush(frontier, [f_cost, next(counter), new_state])
                
    return None, []


def score_grid(grid):
    """
    Return a score for the desirability of this grid
    Based on average number of immovable blocks adjacent to rule blocks
    """
    n_adj_stop = 0
    n = 0
    for k, e in enumerate(grid):
        if e is not None and "rule" in e.type:
            i, j = k % grid.width, k // grid.width
            n_adj_stop += n_adjacent_stop(grid, (i, j))
            n+=1
    if n==0:
        return 1
    else:
        m = n_adj_stop/n
        if m==0:
            return 10
        return 1/(n_adj_stop/n)

def n_adjacent_stop(grid, pos):
    (i, j) = pos
    n = 0
    for adj in [(i+1, j), (i-1, j), (i, j+1), (i, j-1)]:
        if in_bounds(grid, adj) and cell_in_type(adj, get_stop_types(extract_ruleset(grid)) + ["rule_object", "rule_property", "rule_is"], grid):
            n+=1
    return n

def n_adjacent_rule_block(grid, pos, exclude_ids=[]):
    (i, j) = pos
    n = 0
    for adj in [(i+1, j), (i-1, j), (i, j+1), (i, j-1)]:
        if cell_in_type(adj, ["rule_object", "rule_property", "rule_is"], grid):
            if grid.get(*adj).id not in exclude_ids:
                n+=1
    return n  
 
def update_rules(grid):
    ruleset = extract_ruleset(grid)
    for (obj1, obj2) in ruleset.get('replace', []):
        grid.replace(obj1, obj2)
    for e_list in grid.grid:
        for e in e_list:
            if hasattr(e, "set_ruleset"):
                e.set_ruleset(ruleset)
    return grid

def get_agent_pos(grid, ruleset=None):
    if ruleset is None:
        ruleset = extract_ruleset(grid)
    
    avatar_pos = []
    agent_tps = []
    if ruleset.get('is_agent') is not None:
        agent_tps = list(ruleset['is_agent'].keys())
    if len(agent_tps)>0:
        for (k,e) in enumerate(grid):
            if e!=None:
                if e.type in agent_tps:
                    avatar_pos.append(e.cur_pos)

    if len(avatar_pos)==0:
        return None
    else:
        if len(avatar_pos)==1:
            return tuple(avatar_pos[0])
        else:
            return [tuple(p) for p in avatar_pos]

def agent_at_goal(grid, ruleset):
    if ruleset.get('is_goal') is not None:
        goal_tps = list(ruleset['is_goal'].keys())
        if ruleset.get('is_agent') is not None:
            agent_tps = list(ruleset['is_agent'].keys())
            for (k,e) in enumerate(grid):
                if e!=None:
                    e_under = grid.get_under(*e.cur_pos) 
                    if e.type in goal_tps or (e_under is not None and e_under.type in goal_tps):
                        # check if agent 
                        if e.type in agent_tps or (e_under is not None and e_under.type in agent_tps):
                            return True
    return False
   
def agent_is_goal(grid):
    ruleset=extract_ruleset(grid)
    goal_tps = list(ruleset['is_goal'].keys())
    agent_tps = list(ruleset['is_agent'].keys())
    return np.any([a in goal_tps for a in agent_tps])

def get_stop_types(ruleset):
    stop_tps = ['border']
    if ruleset.get('is_stop') is not None:
        stop_tps = stop_tps + [tp for tp in ruleset['is_stop']]
    return stop_tps

def get_goal_pos(grid, ruleset):
    goal_pos = []
    goal_tps = []
    if ruleset.get('is_goal') is not None:
        goal_tps = list(ruleset['is_goal'].keys())
    if len(goal_tps)>0:
        for (k,e) in enumerate(grid):
            if e!=None:
                if e.type in goal_tps:
                    goal_pos.append(e.cur_pos)
                else:
                    e_under = grid.get_under(*e.cur_pos) 
                    if e_under is not None and e_under.type in goal_tps:
                        goal_pos.append(e.cur_pos)
    return goal_pos

def get_block_by_id(grid, block_id):
    for k, e in enumerate(grid):
        if e is not None and "rule" in e.type and e.id==block_id:
            return e
    return None

def is_reachable(grid, block):
    path, actions = run_astar(get_agent_pos(grid), [block.cur_pos], grid)
    return path is not None

def get_reachable_rule_blocks(grid):
    rule_blocks = [e for e in grid if  e is not None and "rule" in e.type] 
    reachable_rule_blocks = []
    n_calls = 0
    ruleset = extract_ruleset(grid)
    for (i, rule_block) in enumerate(rule_blocks):
        n_calls +=1
        path, actions = run_astar(get_agent_pos(grid, ruleset), [rule_block.cur_pos], grid)
        if path is not None:
            reachable_rule_blocks.append(rule_block)
    return reachable_rule_blocks, n_calls

def get_all_rule_blocks(grid):
    rule_blocks = [e for e in grid if  e is not None and "rule" in e.type] 
    return rule_blocks

def same_pos(pos1, pos2):
    if pos1 is None or pos2 is None:
        return False
    return (pos1[0]==pos2[0] and pos1[1]==pos2[1])

def in_bounds(grid, pos):
    return (0 <= pos[0] < grid.width) and (0 <= pos[1] < grid.height)

def cell_in_type(pos, types, grid):
    cell = grid.get(*pos)
    return (not(cell is None) and cell.type in types)

def add_rule_block_ids(grid):
    rule_blocks = [e for e in grid if e is not None and "rule" in e.type] 
    for (i, rule_block) in enumerate(rule_blocks):
        rule_block.id = i

def softmax(x):
    x = np.array(x)
    exp_x = np.exp(x - np.max(x))  # Subtract max for numerical stability
    return exp_x / exp_x.sum()

def is_border(grid, pos):
    return not(grid.get(*pos) is None) and grid.get(*pos).type=="border"

def hash_grid(state):
    return hash(state.encode().tobytes())

def rules_eq(rule1, rule2):
    return np.all([rule1[i].id == rule2[i].id for i in range(3)])

def block_in_rule(block, rule):
    return block.id in [rule_block.id for rule_block in rule]

def right(pos, n=1):
    return (pos[0]+n, pos[1])

def left(pos, n=1):
    return (pos[0]-n, pos[1])

def up(pos, n=1):
    return (pos[0], pos[1]-n)

def down(pos, n=1):
    return (pos[0], pos[1]+n)

def on_x_border(block, grid):
    return (block.cur_pos[0] in [1, grid.width-2])

def on_y_border(block, grid):
    return (block.cur_pos[1] in [1, grid.height-2])

def vis_grid(grid, path, ann=""):
    os.makedirs(path, exist_ok=True)
    existing_files = glob.glob(os.path.join(path, "*.png"))
    next_number = len(existing_files) + 1
    fname = path + str(next_number) + ".png"
    img = grid.render()
    image = Image.fromarray(img)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((5, 5), str(ann), fill=(255, 255, 255), font=font)
    image.save(fname)
            
        