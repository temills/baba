from __future__ import annotations

import hashlib
import math
from abc import abstractmethod
from enum import IntEnum
from time import perf_counter

import gym
import numpy as np
from gym import spaces

# Size in pixels of a tile in the full-scale human view
from . import world_object
from .world_object import make_obj, WorldObj, RuleColor, RuleObject, RuleIs, RuleProperty, Ruleset, RuleBlock, Wall, OBJECT_TO_IDX, Border
from .rendering import (
    Window,
    downsample,
    fill_coords,
    highlight_img,
    point_in_rect,
)
from .rule import extract_ruleset


TILE_PIXELS = 32

IDX_TO_OBJECT = dict(zip(OBJECT_TO_IDX.values(), OBJECT_TO_IDX.keys()))

# Map of agent direction indices to vectors
DIR_TO_VEC = [
    # Pointing right (positive X)
    np.array((1, 0)),
    # Down (positive Y)
    np.array((0, 1)),
    # Pointing left (negative X)
    np.array((-1, 0)),
    # Up (negative Y)
    np.array((0, -1)),
]

class BabaIsYouGrid:
    """
    Represent a grid and operations on it
    """

    # Static cache of pre-renderer tiles
    tile_cache = {}

    def __init__(self, width, height, debug=False):
        assert width >= 3
        assert height >= 3

        self.width = width
        self.height = height

        self.grid = [[None] for _ in range(width * height)]
        self.debug = debug
        
        self.assumptions = []

    def __eq__(self, other):
        grid1 = self.encode()
        grid2 = other.encode()
        return np.array_equal(grid2, grid1)

    def __ne__(self, other):
        return not self == other

    def copy(self):
        from copy import deepcopy

        return deepcopy(self)

    def _get_idx(self, i, j):
        assert 0 <= i < self.width
        assert 0 <= j < self.height
        return j * self.width + i

    def pop(self, i, j, z=None):
        """
        Remove the zth element in the list of objects at position i, j
        """
        idx = self._get_idx(i, j)
        if z is None:
            self.grid[idx].pop()
        else:
            self.grid[idx].pop(z)

    def set(self, i, j, v):
        idx = self._get_idx(i, j)

        if v is None:
            # either set to none or replace with objects underneath
            if self.grid[idx] == [None]:
                self.grid[idx] = [None]
            else:
                self.grid[idx] = self.grid[idx][0:-1]
        else:
            # if it's water, get rid of this object
            curr_v = self.get(i,j)
            if curr_v is not None and curr_v.is_sink() and not v.is_float():
                pass
            else:
                # stack objects
                self.grid[idx].append(v)
                v.cur_pos = [i,j]
       
    # now we assume we can only have two things stacked, which is not true
    def set_under(self, i, j, v):
        idx = self._get_idx(i, j)

        if v is None:
            # either set to none or replace with objects underneath
            if self.grid[idx] == [None]:
                self.grid[idx] = [None]
            else:
                # we want the thing at the top it!
                self.grid[idx] = [None, self.grid[idx][-1]]
        else:
            # if it's water, get rid of this object
            curr_v = self.get(i,j)
            if curr_v is not None and curr_v.is_sink() and not v.is_float():
                pass
            else:
                # stack objects
                self.grid[idx].append(v)
                v.cur_pos = [i,j]
                
            
    def get(self, i, j, z=-1):
        """
        Args:
            z: return the object at the top if -1
        """
        idx = self._get_idx(i, j)

        if z == 'all':
            return self.grid[idx]

        min_len = z + 1 if z >= 0 else -z
        if len(self.grid[idx]) <= min_len:
            return None

        return self.grid[idx][z]

    def get_under(self, i, j):
        # return the second object in the cell
        assert 0 <= i < self.width
        assert 0 <= j < self.height

        if len(self.grid[j * self.width + i]) <= 1:
            return None
        else:
            return self.grid[j * self.width + i][-2]

    def replace(self, obj_type1: str, obj_type2: str):
        for j in range(0, self.height):
            for i in range(0, self.width):
                cell = self.get(i, j)
                if cell is None:
                    continue

                if cell.type == obj_type1:
                    new_obj = make_obj(obj_type2)
                    new_obj.set_ruleset(self._ruleset)
                    self.set(i, j, None)
                    self.set(i, j, new_obj)

    def __iter__(self):
        for elem in self.grid.__iter__():
            yield elem[-1]

    @classmethod
    def render_tile(
            cls, obj, agent_dir=None, highlight=False, tile_size=TILE_PIXELS, subdivs=3
    ):
        """
        Render a tile and cache the result
        """

        # Hash map lookup key for the cache
        key = agent_dir
        key = obj.encode() if obj else key

        if key in cls.tile_cache:
            return cls.tile_cache[key]

        img = np.zeros(
            shape=(tile_size * subdivs, tile_size * subdivs, 3), dtype=np.uint8
        )

        # Draw the grid lines (top and left edges)
        fill_coords(img, point_in_rect(0, 0.031, 0, 1), (100, 100, 100))
        fill_coords(img, point_in_rect(0, 1, 0, 0.031), (100, 100, 100))

        if obj is not None:
            obj.render(img)

        # Highlight the cell if needed
        if highlight:
            highlight_img(img)

        # Downsample the image to perform supersampling/anti-aliasing
        img = downsample(img, subdivs)

        # Cache the rendered tile
        cls.tile_cache[key] = img

        return img

    def render(self, tile_size=TILE_PIXELS, agent_pos=None, agent_dir=None, highlight_mask=None):
        """
        Render this grid at a given scale
        :param r: target renderer object
        :param tile_size: tile size in pixels
        """

        if highlight_mask is None:
            highlight_mask = np.zeros(shape=(self.width, self.height), dtype=bool)

        # Compute the total grid size
        width_px = self.width * tile_size
        height_px = self.height * tile_size

        img = np.zeros(shape=(height_px, width_px, 3), dtype=np.uint8)

        # Render the grid
        for j in range(0, self.height):
            for i in range(0, self.width):
                cell = self.get(i, j)

                agent_here = np.array_equal(agent_pos, (i, j))
                tile_img = BabaIsYouGrid.render_tile(
                    cell,
                    agent_dir=agent_dir if agent_here else None,
                    highlight=highlight_mask[i, j],
                    tile_size=tile_size,
                )

                ymin = j * tile_size
                ymax = (j + 1) * tile_size
                xmin = i * tile_size
                xmax = (i + 1) * tile_size
                img[ymin:ymax, xmin:xmax, :] = tile_img

        return img

    def encode(self, vis_mask=None):
        """
        Produce a compact numpy encoding of the grid
        """

        if vis_mask is None:
            vis_mask = np.ones((self.width, self.height), dtype=bool)

        array = np.zeros((self.width, self.height, 1 * self.encoding_level), dtype="uint8")

        tic = perf_counter()
        for i in range(self.width):
            for j in range(self.height):

                if not vis_mask[i, j]:
                    continue

                for idx, z in enumerate(range(1, self.encoding_level+1)): # 0, 1
                    v = self.get(i, j, -z)
                    array[i, j, idx * 1:(idx + 1) * 1] = self.encode_cell(v)
        
        element_to_bit = {e: i for i, e in enumerate([('baba', 'you'), ('wall', 'stop'), ('goop', 'sink'), ('flag', 'win')])}
        def subset_id(lst):
            id = 0
            for e in lst:
                id |= 1 << element_to_bit[e]
            return id
        if len(self.assumptions)>0:
            array[0,0,0] += subset_id(self.assumptions)
            
        print("Encoding grid", (perf_counter()-tic)*1000) if self.debug else None
        return array

    def encode_cell(self, v):
        if v is None:
            return OBJECT_TO_IDX["empty"]
        else:
            return v.encode()

    @staticmethod
    def decode(array):
        """
        Decode an array grid encoding back into a grid
        """
        width, height, encoding_levels = array.shape

        vis_mask = np.ones(shape=(width, height), dtype=bool)

        grid = BabaIsYouGrid(width, height)
        for i in range(width):
            for j in range(height):
                for z in range(encoding_levels-1,-1,-1):
                    type_idx = array[i, j][z]
                    v = WorldObj.decode(type_idx)
                    grid.set(i, j, v)
                    vis_mask[i, j] = type_idx != OBJECT_TO_IDX["unseen"]

        return grid, vis_mask

    def process_vis(self, agent_pos):
        mask = np.zeros(shape=(self.width, self.height), dtype=bool)

        mask[agent_pos[0], agent_pos[1]] = True

        for j in reversed(range(0, self.height)):
            for i in range(0, self.width - 1):
                if not mask[i, j]:
                    continue

                cell = self.get(i, j)
                if cell and not cell.see_behind():
                    continue

                mask[i + 1, j] = True
                if j > 0:
                    mask[i + 1, j - 1] = True
                    mask[i, j - 1] = True

            for i in reversed(range(1, self.width)):
                if not mask[i, j]:
                    continue

                cell = self.get(i, j)
                if cell and not cell.see_behind():
                    continue

                mask[i - 1, j] = True
                if j > 0:
                    mask[i - 1, j - 1] = True
                    mask[i, j - 1] = True

        for j in range(0, self.height):
            for i in range(0, self.width):
                if not mask[i, j]:
                    self.set(i, j, None)

        return mask


class BabaIsYouEnv(gym.Env):
    metadata = {
        # Deprecated: use 'render_modes' instead
        "render.modes": ["human", "rgb_array", "dict"],
        "video.frames_per_second": 10,  # Deprecated: use 'render_fps' instead
        "render_modes": ["human", "rgb_array", "single_rgb_array", "dict", "matrix"],
        "render_fps": 10,
    }

    # Enumeration of possible actions
    class Actions(IntEnum):
        idle = 0
        up = 1
        right = 2
        down = 3
        left = 4

    def __init__(
            self,
            grid_size: int = None,
            width: int = None,
            height: int = None,
            max_steps: int = 500,
            **kwargs,
    ):
        # Can't set both grid_size and width/height
        if grid_size:
            assert width is None and height is None
            width = grid_size
            height = grid_size

        # Number of objects to encode for each cell
        self.encoding_level = 2#kwargs.get('encoding_level', 1)

        # Action enumeration for this environment
        self.actions = BabaIsYouEnv.Actions

        # Actions are discrete integer values
        self.action_space = spaces.Discrete(len(self.actions))

        self.observation_space = spaces.Box(
            low=0,
            high=255,
            shape=(width, height, 1 * self.encoding_level),
            dtype="uint8",
        )

        # Range of possible rewards
        self.reward_range = (0, 1)

        self.window: Window = None

        # Environment configuration
        self.width = width
        self.height = height
        self.max_steps = max_steps

        # Current position and direction of the agent
        self.agent_pos: np.ndarray = None
        self.agent_dir: int = None
        self.agent_object = 'baba'

        # Initialize the env
        self.grid = None
        self._ruleset = {}
        self.default_ruleset = kwargs.get('default_ruleset', {})

        self.reset()
        

    def get_ruleset(self):
        return self._ruleset

    def reset(self, *, seed=None, return_info=False, options=None):
        try:
            super().reset(seed=seed)
        except TypeError:
            # gym==0.21 reset not implemented in gym.Env
            pass

        # Current position and direction of the agent
        self.agent_pos = None
        self.agent_dir = None

        # Generate a new random grid at the start of each episode
        self._gen_grid(self.width, self.height)

        # Set the encoding level for the grid
        self.grid.encoding_level = self.encoding_level

        # Compute the ruleset for the generated grid
        self._ruleset = extract_ruleset(self.grid, default_ruleset=self.default_ruleset)

        self._ruleset = Ruleset(self._ruleset)
        self.grid._ruleset = self._ruleset
        for e_list in self.grid.grid:
            for e in e_list:
                if hasattr(e, "set_ruleset"):
                    e.set_ruleset(self._ruleset)

        self.agent_pos = self.set_agent()

        assert self.agent_pos is not None
        assert self.agent_dir is not None

        # Step count since episode start
        self.step_count = 0
        # Return first observation
        obs = self.gen_obs()

        self.is_win = False
        self.is_lose = False

        if not return_info:
            return obs
        else:
            return obs, {}

    def set_grid(self, grid):
        # Set the encoding level for the grid
        self.grid = grid
        self.grid.encoding_level = self.encoding_level
        self._ruleset = extract_ruleset(self.grid, default_ruleset=self.default_ruleset)
        self._ruleset = Ruleset(self._ruleset)
        self.grid._ruleset = self._ruleset
        for e_list in self.grid.grid:
            for e in e_list:
                if hasattr(e, "set_ruleset"):
                    e.set_ruleset(self._ruleset)
        self._ruleset.set(extract_ruleset(self.grid))
        self.agent_pos = self.set_agent()

    def hash(self, size=16):
        """
        Compute a hash that uniquely identifies the current state of the environment.
        :param size: Size of the hashing
        """
        sample_hash = hashlib.sha256()
        # TODO: make the agent part of the grid encoding
        to_encode = [self.grid.encode().tolist(), self.agent_pos, self.agent_dir]
        for item in to_encode:
            sample_hash.update(str(item).encode("utf8"))

        return sample_hash.hexdigest()[:size]

    @property
    def steps_remaining(self):
        return self.max_steps - self.step_count

    def __str__(self):
        """
        Produce a pretty string of the environment's grid along with the agent.
        A grid cell is represented by 2-character string, the first one for
        the object and the second one for the color.
        """
        grid = []
        for j in range(self.grid.height):
            row = []
            for i in range(self.grid.width):
                c = self.grid.get(i, j)
                if c is None:
                    name = 'empty'
                elif isinstance(c, RuleBlock):
                    name = c.name.upper()
                else:
                    name = c.type
                # TODO
                if name[0] == 'f' and name != 'flag':
                    name = name[1:]
                row.append(name)
            grid.append(row)

        res = ""
        for row in grid:
            res += "["
            res += ", ".join(row)
            res += "], \n"
        res = res[:-3]  # remove last ", \n"
        return res

    @abstractmethod
    def _gen_grid(self, width, height):
        pass

    def get_reward(self):
        """
        Compute the reward to be given upon success
        """

        return 1 - 0.9 * (self.step_count / self.max_steps)

    def put_obj(self, obj, i, j):
        """
        Put an object at a specific position in the grid
        """

        self.grid.set(i, j, obj)
        obj.init_pos = (i, j)
        obj.cur_pos = (i, j)


    def set_agent(self, top=None, size=None, rand_dir=True, max_tries=math.inf):
        """
        Set the agent's starting point at an empty position in the grid
        """
        pos = None
        for k, e in enumerate(self.grid):
            if e is not None and e.is_agent():
                pos = (k % self.grid.width, k // self.grid.width)
                self.agent_pos = pos
                self.agent_dir = e.dir
                break
        return pos


    @property
    def dir_vec(self):
        """
        Get the direction vector for the agent, pointing in the direction
        of forward movement.
        """

        assert self.agent_dir >= 0 and self.agent_dir < 4
        return DIR_TO_VEC[self.agent_dir]

    @property
    def right_vec(self):
        """
        Get the vector pointing to the right of the agent.
        """

        dx, dy = self.dir_vec
        return np.array((-dy, dx))

    @property
    def front_pos(self):
        """
        Get the position of the cell that is right in front of the agent
        """

        return self.agent_pos + self.dir_vec

    def change_obj_pos(self, pos, new_pos, mvt_dir=None, under=False):
        """
        Change the position and the direction of an object in the grid
        """
        if np.any(pos != new_pos):
            # move the object
            if under:
                e = self.grid.get_under(*pos)
            else:
                e = self.grid.get(*pos)

            if e is None:
                return

            self.grid.set(*new_pos, e)
            if under:
                self.grid.set_under(*pos, None) #set_under
            else:
                self.grid.set(*pos, None)
            # change the dir of the object
            if mvt_dir is not None:
                e.dir = np.argwhere(np.all(DIR_TO_VEC == mvt_dir, axis=1))[0][0]

    def is_win_pos(self, pos):
        new_cell = self.grid.get(*pos)
        new_cell_under = self.grid.get_under(*pos)
        return (new_cell is not None and (new_cell.is_goal() or new_cell.type in self._ruleset.get('is_goal', []))) or (new_cell_under is not None and (new_cell_under.is_goal() or new_cell.type in self._ruleset.get('is_goal', [])))

    def is_lose_pos(self, pos):
        new_cell = self.grid.get(*pos)
        # agent is float?
        drown = False
        if new_cell is not None and new_cell.is_sink():
            if self._ruleset.get('is_agent') is not None:
                if list(self._ruleset.get('is_agent').keys())[0] not in self._ruleset.get('is_float', []):
                    drown = True
        return new_cell is not None and (new_cell.is_defeat() or drown)

    def move(self, pos, dir_vec, under=False):
        """
        Return fwd_pos if can move, otherwise return pos
        """
        
        fwd_pos = pos + dir_vec
        fwd_cell = self.grid.get(*fwd_pos)

        # try to move the forward obj if it can be pushed
        if fwd_cell is not None and fwd_cell.is_push():
            new_fwd_pos, _, _ = self.move(fwd_pos, dir_vec)

        # move if the fwd cell is empty or can overlap
        fwd_cell = self.grid.get(*fwd_pos)
        if fwd_cell is None or fwd_cell.can_overlap():
            new_pos = tuple(fwd_pos)
        else:
            new_pos = pos

        # check if win or lose before moving the agent
        is_win = self.is_win_pos(new_pos)
        is_lose = self.is_lose_pos(new_pos)
        self.change_obj_pos(pos, new_pos, dir_vec, under)

        return new_pos, is_win, is_lose

    def step(self, action):
        self.step_count += 1

        is_win, is_lose = False, False
        reward = 0
        done = False

        if action == self.actions.up:
            self.agent_dir = 3
        elif action == self.actions.right:
            self.agent_dir = 0
        elif action == self.actions.down:
            self.agent_dir = 1
        elif action == self.actions.left:
            self.agent_dir = 2
            
        dir = self.agent_dir
        move_dir = DIR_TO_VEC[self.agent_dir]

        if action != self.actions.idle and not(self.is_lose):
            # move the agent if the forward cell is empty or can overlap or can be pushed
            for i in range(self.grid.width):
                for j in range(self.grid.height):
                    pos = (i, j)
                    e_list = self.grid.get(*pos, 'all')
                    for e in e_list:
                        if e is not None and (e.is_agent() or e.is_move()):
                            e.has_moved = False            

            # Move avatar, dealing with multiple avatars by ordering movements based on direction moved
            i_list = list(range(self.grid.width))
            j_list = list(range(self.grid.height))
            if self.agent_dir == 0:
                i_list.reverse()
            elif self.agent_dir == 1:
                j_list.reverse() 
            for i in i_list:
                for j in j_list:
                    pos = (i, j)
                    e_list = self.grid.get(*pos, 'all')
                    for (e_idx, e) in enumerate(e_list):
                        if e is not None and e.is_agent() and not e.has_moved:
                            e.dir = dir
                            new_pos, is_win, is_lose = self.move(pos, move_dir, e_idx<len(e_list)-1)
                            e.has_moved = True
                            self.agent_pos = new_pos 
                 
            # move other objects
            for k, e in enumerate(self.grid):
                if e is not None and e.is_move() and not e.has_moved:
                    pos = (k % self.grid.width, k // self.grid.width)
                    new_pos, _, _ = self.move(pos, DIR_TO_VEC[e.dir])
                    e.has_moved = True

            # win/lose based on the rules active in the env
            self.is_win = is_win
            self.is_lose = is_lose

            self._ruleset.set(extract_ruleset(self.grid, default_ruleset=self.default_ruleset))
            
            # check if some bocks need to be replaced (obj1 is obj2 rules)
            for (obj1, obj2) in self._ruleset.get('replace', []):
                self.grid.replace(obj1, obj2)
            # are we at a winning pos after all blocks have moved?
            for k, e in enumerate(self.grid):
                if e is not None and e.is_agent():
                    if self.is_win_pos(e.cur_pos):
                        self.is_win = True
            
            reward, done = self.reward()

        if self.step_count >= self.max_steps:
            done = True

        obs = self.gen_obs()
        return obs, reward, done, {}

    def reward(self):
        if self.is_win:
            done = True
            reward = self.get_reward()
        elif self.is_lose:
            done = True
            reward = 0#-1
        else:
            done = False
            reward = 0
        return reward, done

    def gen_obs(self):
        return self.grid.encode()

    def get_obs_render(self, obs, tile_size=TILE_PIXELS // 2):
        """
        Render an agent observation for visualization
        """

        grid, vis_mask = BabaIsYouGrid.decode(obs)

        # Render the whole grid
        img = grid.render(
            tile_size,
            agent_pos=(self.agent_view_size // 2, self.agent_view_size - 1),
            agent_dir=3,
            highlight_mask=vis_mask,
        )

        return img

    def render(self, mode="human", highlight=True, tile_size=TILE_PIXELS):
        assert mode in self.metadata["render_modes"], mode
        """
        Render the whole-grid human view
        """
        if mode == "dict":
            grid = {}
            # don't output the outer walls
            for j in range(1, self.height-1):
                for i in range(1, self.width-1):
                    cell = self.grid.get(i, j)
                    if cell is None:
                        continue

                    if isinstance(cell, RuleBlock):
                        grid[(i, j)] = ('rule', cell.name)
                    else:
                        grid[(i, j)] = (cell.name, cell.color)
            return grid

        if mode == "matrix":
            # don't output the outer walls
            grid = np.zeros((self.width-2, self.height-2), dtype=object)
            for j in range(self.height-2):
                for i in range(self.width-2):
                    cell = self.grid.get(i+1, j+1)
                    if cell is None:
                        grid[i, j] = "Empty"
                        continue

                    if isinstance(cell, RuleBlock):
                        grid[(i, j)] = f"Rule[{cell.name}]"
                    elif isinstance(cell, Wall):
                        # grid[(i, j)] = "Wall"  # TODO: different than wall object
                        grid[(i, j)] = "Block"  # TODO: better way to call this?
                    else:
                        grid[(i, j)] = f"Obj[{cell.name}, {cell.color}]"
            grid = grid.T
            return grid

        if mode == "human" and not self.window:
            self.window = Window("baba_minigrid")
            self.window.show(block=False)

        # Render the whole grid
        img = self.grid.render(
            tile_size,
            self.agent_pos,
            self.agent_dir
        )

        if mode == "human":
            # self.window.set_caption(self.mission)
            self.window.show_img(img)
        else:
            return img

    def close(self):
        if self.window:
            self.window.close()
