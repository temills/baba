import pygame
from gym.utils.play import display_arr
from pygame import VIDEORESIZE
import pandas as pd
import numpy as np
import argparse
from game.baba import make
from game.baba.my_envs import *
from game.baba.grid import BabaIsYouGrid
from game.baba.registration import register

def play(env, transpose=True, fps=30, zoom=None, callback=None, keys_to_action=None):
    if keys_to_action is None:
        keys_to_action = {
            (pygame.K_UP,): env.actions.up,
            (pygame.K_DOWN,): env.actions.down,
            (pygame.K_LEFT,): env.actions.left,
            (pygame.K_RIGHT,): env.actions.right,
        }
    env.reset()
    rendered = env.render(mode="rgb_array")
    if keys_to_action is None:
        if hasattr(env, "get_keys_to_action"):
            keys_to_action = env.get_keys_to_action()
        elif hasattr(env.unwrapped, "get_keys_to_action"):
            keys_to_action = env.unwrapped.get_keys_to_action()
        else:
            assert False, (
                env.spec.id
                + " does not have explicit key to action mapping, "
                + "please specify one manually"
            )
    relevant_keys = set(sum(map(list, keys_to_action.keys()), []))

    video_size = [rendered.shape[1], rendered.shape[0]]
    if zoom is not None:
        video_size = int(video_size[0] * zoom), int(video_size[1] * zoom)

    pressed_keys = []
    running = True
    env_done = True


    while running:
        if env_done:
            env_done = False
            obs = env.reset()
        else:
            action = keys_to_action.get(tuple(sorted(pressed_keys)), None)  # TODO: was 0
            pressed_keys = []
            prev_obs = obs
            if action is not None:
                # obs, rew, env_done, _, info = env.step(action)
                obs, rew, env_done, info = env.step(action)
                print("Reward:", rew) if rew != 0 else None
            if callback is not None:
                callback(prev_obs, obs, action, rew, env_done, info)
        if obs is not None:
            rendered = env.render(mode="rgb_array")
        break
    
def play_and_render(env, transpose=True, fps=30, zoom=None, callback=None, keys_to_action=None):
    if keys_to_action is None:
        keys_to_action = {
            (pygame.K_UP,): env.actions.up,
            (pygame.K_DOWN,): env.actions.down,
            (pygame.K_LEFT,): env.actions.left,
            (pygame.K_RIGHT,): env.actions.right,
        }

    env.reset()
    rendered = env.render(mode="rgb_array")

    if keys_to_action is None:
        if hasattr(env, "get_keys_to_action"):
            keys_to_action = env.get_keys_to_action()
        elif hasattr(env.unwrapped, "get_keys_to_action"):
            keys_to_action = env.unwrapped.get_keys_to_action()
        else:
            assert False, (
                env.spec.id
                + " does not have explicit key to action mapping, "
                + "please specify one manually"
            )
    relevant_keys = set(sum(map(list, keys_to_action.keys()), []))

    video_size = [rendered.shape[1], rendered.shape[0]]
    if zoom is not None:
        video_size = int(video_size[0] * zoom), int(video_size[1] * zoom)

    pressed_keys = []
    running = True
    env_done = True

    screen = pygame.display.set_mode(video_size)
    clock = pygame.time.Clock()

    while running:
        if env_done:
            env_done = False
            obs = env.reset()
        else:
            action = keys_to_action.get(tuple(sorted(pressed_keys)), None)  # TODO: was 0
            pressed_keys = []
            prev_obs = obs
            if action is not None:
                # obs, rew, env_done, _, info = env.step(action)
                obs, rew, env_done, info = env.step(action)
                print("Reward:", rew) if rew != 0 else None
            if callback is not None:
                callback(prev_obs, obs, action, rew, env_done, info)
        if obs is not None:
            # rendered = env.render()
            rendered = env.render(mode="rgb_array")
            display_arr(screen, rendered, transpose=transpose, video_size=video_size)

        # process pygame events
        for event in pygame.event.get():
            # test events, set key states
            if event.type == pygame.KEYDOWN:
                if event.key in relevant_keys:
                    pressed_keys.append(event.key)
                elif event.key == 27:
                    # running = False
                    env_done = True
            elif event.type == pygame.QUIT:
                running = False
            elif event.type == VIDEORESIZE:
                video_size = event.size
                screen = pygame.display.set_mode(video_size)
                print(video_size)

        pygame.display.flip()
        clock.tick(fps)
    pygame.quit()


def register_envs():
    for env in [Tutorial1, Tutorial2, Tutorial3, Tutorial4, Tutorial5, Tutorial6, Tutorial7, Tutorial8, Tutorial9, Tutorial10, Env1D0, Env1D1, Env2D0, Env2D1, Env3D0, Env3D1, Env4D0, Env4D1, Env5D0, Env5D1, Env6D0, Env6D1, Env7D0, Env7D1, Env8D0, Env8D1, Env9D0, Env9D1, Env10D0, Env10D1, Env11D0, Env11D1, Env12D0, Env12D1, Env13D0, Env13D1, Env14D0, Env14D1, Env15D0, Env15D1]:
        register('env/' +  env.__name__, env)


def step_env(game_type, env, action):
    obs, rew, env_done, info = env.step(action)
    if rew > 0:
        rew = 1
    try:
        agent_pos = int(env.agent_pos[0])*env.grid.width + int(env.agent_pos[1])
    except:
        agent_pos = None
    return env.grid.encode(), rew, agent_pos # +1, -1, 0
    
    
def step_tutorial_env(game_type, env, action):
    obs, rew, env_done, info = env.step(action)
    if rew > 0:
        rew = 1
    try:
        agent_pos = int(env.agent_pos[0])*env.grid.width + int(env.agent_pos[1])
    except:
        agent_pos = None 
    return env.grid.encode(), rew, agent_pos # +1, -1, 0
    

def init_env(game_type):
    register_envs()
    env = make(f"env/{game_type}")
    return env

if __name__ == "__main__":
    register_envs()
