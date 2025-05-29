import math

import numpy as np

from . import utils
add_img_text = utils.add_img_text
from .rendering import fill_coords, point_in_circle, point_in_rect, point_in_triangle, rotate_fn


properties = [
    'is_stop',
    'is_push',
    'is_goal',
    'is_defeat',
    'is_agent',
    'is_pull',
    'is_move',
    'is_open',
    'is_shut',
    'is_sink',
    'is_float'
]

objects = [
    'fball',
    'fdoor',
    "fkey",
    'baba',
    'goop',
    "flag",
    "rock",
    "keke",
    "wall"
]

name_mapping = {
    'wall': 'wall',
    'goop': 'goop',
    'fball': 'ball',
    'fdoor': 'door',
    'fkey': 'key',
    'is_push': 'push',
    'is_stop': 'stop',
    'is_goal': 'win',
    'is_defeat': 'lose',
    'is': 'is',
    'is_agent': 'you',
    'is_pull': 'pull',
    'is_move': 'move',
    'is_open': 'open',
    'is_shut': 'shut',
    'is_sink': 'sink',
    'is_float': 'float'
}
# by default, add the displayed name as the type of the object
name_mapping.update({o: o for o in objects if o not in name_mapping})
name_mapping_inverted = {v: k for k, v in name_mapping.items()}

TILE_PIXELS = 32

# Map of color names to RGB values
COLORS = {
    "red": np.array([255, 0, 0]),
    "green": np.array([0, 255, 0]),
    "blue": np.array([0, 0, 255]),
    "purple": np.array([112, 39, 195]),
    "yellow": np.array([255, 255, 0]),
    "grey": np.array([100, 100, 100]),
}

COLOR_NAMES = sorted(list(COLORS.keys()))


# Map of object type to integers
OBJECT_TO_IDX = {
    "unseen": 0,
    "empty": 1,
    "wall": 2,
    "floor": 3,
    "door": 4,
    "key": 5,
    "ball": 6,
    "box": 7,
    "lava": 9,
    "agent": 10,
    "goop": 11,
    "flag":12,
    "baba":13,
    'is_word':16,
    'ball_word':19,
    'wall_word':20,
    'door_word':21,
    "key_word":22,
    'baba_word':23,
    'goop_word':24,
    "you_word":25,
    "win_word":26,
    "fball":27,
    "fdoor":28,
    "fkey":29,
    "fwall":30,
    "border":31,
    "fgoop":32,
    "rock":33,
    "rock_word":34,
    "flag_word":35,
    "keke_word":36,
    "keke":37,
    "stop_word":38,
    "float_word":39,
    "sink_word":40
}

IDX_TO_OBJECT = dict(zip(OBJECT_TO_IDX.values(), OBJECT_TO_IDX.keys()))


def make_obj(name: str, color: str = None):
    """
    Make an object from a string name
    """
    kwargs = {'color': color} if color is not None else {}

    # TODO: make it more general
    if name == "fwall" or name == "wall":
        obj_cls = Wall
    elif name == "fgoop" or name == "goop":
        obj_cls = Goop
    elif name == "baba":
        obj_cls = Baba
    elif name == "rock":
        obj_cls = Rock
    elif name == "keke":
        obj_cls = Keke
    elif name == "flag":
        obj_cls = Flag
    elif name == "border":
        obj_cls = Border
    else:
        raise ValueError(name)

    return obj_cls(**kwargs)


class WorldObj:
    """
    Base class for grid world objects
    """

    def __init__(self, type, color):
        #assert type in OBJECT_TO_IDX, type
        self.type = type
        self.color = color
        self.contains = None

        # Initial position of the object
        self.init_pos = None

        # Current position of the object
        self.cur_pos = None

    def is_agent(self):
        return False

    def is_move(self):
        return False

    def is_goal(self):
        return False

    def is_defeat(self):
        return False

    def can_overlap(self):
        """Can the agent overlap with this?"""
        return False

    def is_push(self):
        """Can the agent push this?"""
        return False

    def is_pull(self):
        return False
    
    def is_float(self):
        return False
    
    def is_sink(self):
        return False

    def toggle(self, env, pos):
        """Method to trigger/toggle an action this object performs"""
        return False

    def encode(self):
        """Encode the a description of this object as a 3-tuple of integers"""
        return OBJECT_TO_IDX[self.type]

    @staticmethod
    def decode(type_idx):
        """Create an object from a 3-tuple state description"""

        try:
            obj_type = IDX_TO_OBJECT[type_idx]
        except:
            obj_type = "empty"

        if obj_type == "empty" or obj_type == "unseen":
            return None 

        if "word" in obj_type:
            name = obj_type.split("_")[0]
            if name == "is":
                v = RuleIs()
            elif name in ["stop", "win", "sink", "float", "you"]:
                v = RuleProperty(name)
            elif name in objects:
                v = RuleObject(name)
        else:
            # State, 0: open, 1: closed, 2: locked
            if obj_type in ["wall", "fwall"]:
                v = Wall()
            elif obj_type == "border":
                v = Border()
            elif obj_type == "flag":
                v = Flag()
            elif obj_type == "rock":
                v = Rock()
            elif obj_type == "goop":
                v = Goop()
            elif obj_type == "baba":
                v = Baba()
            elif obj_type == "keke":
                v = Keke()
            else:
                assert False, "unknown object type in decode '%s'" % obj_type
        return v

    def render(self, r):
        """Draw this object with the given renderer"""
        raise NotImplementedError


class Wall(WorldObj):
    def __init__(self, color="grey"):
        super().__init__("wall", color)

    def see_behind(self):
        return False

    def render(self, img):
        fill_coords(img, point_in_rect(0, 1, 0, 1), COLORS[self.color])

class Border(WorldObj):
    def __init__(self, color="red"):
        super().__init__("border", color)

    def see_behind(self):
        return False

    def render(self, img):
        fill_coords(img, point_in_rect(0, 1, 0, 1), COLORS["red"])


class RuleBlock(WorldObj):
    """
    By default, rule blocks can be pushed by the agent.
    """
    def __init__(self, name, type, color, is_push=True):
        #type = name_mapping[name] + "_word"
        
        super().__init__(type, color)
        self._is_push = is_push
        self.name = name = name_mapping.get(name, name)
        self.margin = 10
        img = np.zeros((96-2*self.margin, 96-2*self.margin, 3), np.uint8)
        add_img_text(img, name)
        self.img = img
        self.id = None

    def can_overlap(self):
        return False

    def is_push(self):
        return self._is_push

    def render(self, img):
        fill_coords(img, point_in_rect(0.06, 0.94, 0.06, 0.94), [235, 235, 235])
        img[self.margin:-self.margin, self.margin:-self.margin] = self.img

    # TODO: different encodings of the rule blocks for the agent observation
    def encode(self):
        """Encode the a description of this object as a 3-tuple of integers"""
        # RuleBlock characterized by their name instead of color
        return OBJECT_TO_IDX[self.name + "_word"]


class RuleObject(RuleBlock):
    def __init__(self, obj, is_push=True):
        obj = name_mapping_inverted[obj] if obj not in objects else obj
        # TODO: red push is win (push is a rule_obj but not in objects)
        # assert obj in objects, "{} not in {}".format(obj, objects)
        
        super().__init__(obj, 'rule_object', 'purple', is_push=is_push)
        self.object = obj


class RuleProperty(RuleBlock):
    def __init__(self, property, is_push=True):
        property = name_mapping_inverted[property] if property not in properties else property
        assert property in properties, "{} not in {}".format(property, properties)

        super().__init__(property, 'rule_property', 'purple', is_push=is_push)
        self.property = property


class RuleIs(RuleBlock):
    def __init__(self, is_push=True):
        super().__init__('is', 'rule_is', 'purple', is_push=is_push)


class RuleColor(RuleBlock):
    def __init__(self, obj_color, is_push=True):

        super().__init__(obj_color, 'rule_color', 'purple', is_push=is_push)
        self.obj_color = obj_color


class Ruleset:
    """
    Each object in the env has a reference to the ruleset object, which is automatically updated (would have to manually
    update it if were using a dict instead).
    """
    def __init__(self, ruleset_dict):
        self.ruleset_dict = ruleset_dict

    def set(self, ruleset_dict):
        self.ruleset_dict = ruleset_dict

    def __getitem__(self, item):
        return self.ruleset_dict[item]

    def __setitem__(self, key, value):
        self.ruleset_dict[key] = value

    def __str__(self):
        return f'Ruleset dict: {self.ruleset_dict}'

    # TODO: cause infinite loop when using vec env
    # def __getattr__(self, item):
    #     return getattr(self.ruleset_dict, item)

    def get(self, *args, **kwargs):
        return self.ruleset_dict.get(*args, **kwargs)



def make_prop_fn(prop: str):
    """
    Make a method that retrieves the property of an instance of FlexibleWorldObj in the ruleset
    """
    def _get_color_set(ruleset, typ, prop):
        return ruleset[prop].get(typ + "_color", [])

    def get_prop(self: FlexibleWorldObj):
        # retrieve the type and color specific to the instance 'self' (the function is the same for all instances)
        typ = self.type
        ruleset = self.get_ruleset()

        if prop == 'is_stop':
            if ruleset['is_agent'].get(typ, False):
                ruleset['is_stop'][typ] = True

        if ruleset[prop].get(typ, False):  # object type set to True
            return True
        return False

    return get_prop


class FlexibleWorldObj(WorldObj):
    def __init__(self, type, color):
        assert type in objects, "{} not in {}".format(type, objects)
        super().__init__(type, color)
        self.name = name_mapping[type]  # pretty name
        # direction in which the object is facing
        self.dir = 0  # order: right, down, left, up
        self.default_type = self.type
        for prop in properties:
            # create a method for each property and bind it to the class (same for all the instances of that class)
            setattr(self.__class__, prop, make_prop_fn(prop))

    def set_ruleset(self, ruleset):
        self._ruleset = ruleset

    def get_ruleset(self):
        return self._ruleset


    # compatibility with WorldObj
    def can_overlap(self):
        return not (self.is_stop() or self.is_agent())


class Wall(FlexibleWorldObj):
    def __init__(self, color="grey"):
        super().__init__("wall", color)

    def render(self, img):
        fill_coords(img, point_in_rect(0.2, 0.8, 0.2, 0.8), COLORS[self.color])


class Rock(FlexibleWorldObj):
    def __init__(self, color="green"):
        super().__init__("rock", color)

    def render(self, img):
        fill_coords(img, point_in_circle(0.5, 0.5, 0.31), COLORS[self.color])

class Flag(FlexibleWorldObj):
    def __init__(self, color="blue"):
        super().__init__("flag", color)

    def render(self, img):
        fill_coords(img, point_in_circle(0.5, 0.5, 0.31), COLORS[self.color])
        
class Keke(FlexibleWorldObj):
    def __init__(self, color="yellow"):
        super().__init__("keke", color)

    def render(self, img):
        fill_coords(img, point_in_circle(0.5, 0.5, 0.31), COLORS[self.color])
        
class Goop(FlexibleWorldObj):
    def __init__(self, color="blue"):
        super().__init__("goop", color)

    def render(self, img):
        fill_coords(img, point_in_rect(0.0, 1.0, 0.0, 1.0), np.array([3, 194, 252]))
        fill_coords(img, point_in_rect(0.05, 0.95, 0.1, 0.12), np.array([7, 3, 252]))
        fill_coords(img, point_in_rect(0.05, 0.95, 0.25, 0.27), np.array([7, 3, 252]))
        fill_coords(img, point_in_rect(0.05, 0.95, 0.4, 0.42), np.array([7, 3, 252]))
        fill_coords(img, point_in_rect(0.05, 0.95, 0.55, 0.57), np.array([7, 3, 252]))
        fill_coords(img, point_in_rect(0.05, 0.95, 0.7, 0.72), np.array([7, 3, 252]))
        fill_coords(img, point_in_rect(0.05, 0.95, 0.85, 0.87), np.array([7, 3, 252]))

class Baba(FlexibleWorldObj):
    def __init__(self, color="white"):
        super().__init__("baba", color)

    def render(self, img):
        tri_fn = point_in_triangle(
            (0.12, 0.19),
            (0.87, 0.50),
            (0.12, 0.81),
        )

        # Rotate the agent based on its direction
        tri_fn = rotate_fn(tri_fn, cx=0.5, cy=0.5, theta=0.5 * math.pi * self.dir)
        fill_coords(img, tri_fn, (255, 255, 255))

class Keke(FlexibleWorldObj):
    def __init__(self, color="red"):
        super().__init__("keke", color)

    def render(self, img):
        tri_fn = point_in_triangle(
            (0.12, 0.19),
            (0.87, 0.50),
            (0.12, 0.81),
        )

        # Rotate the agent based on its direction
        tri_fn = rotate_fn(tri_fn, cx=0.5, cy=0.5, theta=0.5 * math.pi * self.dir)
        fill_coords(img, tri_fn, (255, 255, 255))
