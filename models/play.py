import pygame
from models.flat_agent import FlatAgent
from models.mepomdp_agent import Agent
from gym.utils.play import display_arr
from pygame import VIDEORESIZE
import pandas as pd
import numpy as np
from game.baba.registration import make
import warnings
import time
from game.baba.my_envs import * 
from game.baba.registration import register


def make_agent(model_tp):
    if model_tp=="flat":
        agent = FlatAgent()
    elif model_tp == "mepomdp":
        agent = Agent()
    elif model_tp == "mepomdp_rr":
        agent = Agent(rr=True)
    else:
        print("no agent type ", model_tp)
        assert False
    return agent


def model_play(env, model_tp="mepomdp", transpose=True, fps=30, zoom=None, callback=None, keys_to_action=None):
    if keys_to_action is None:
        keys_to_action = {
            1: env.actions.up,
            2: env.actions.down,
            3: env.actions.left,
            4: env.actions.right,
        }

    env.reset()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        rendered = env.render(mode="rgb_array")
             
    video_size = [rendered.shape[1], rendered.shape[0]]
    if zoom is not None:
        video_size = int(video_size[0] * zoom), int(video_size[1] * zoom)

    running = True

    screen = pygame.display.set_mode(video_size)
    clock = pygame.time.Clock()
    data = []
    env_done = False
    obs = env.reset()
    
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        rendered = env.render(mode="rgb_array")
    display_arr(screen, rendered, transpose=transpose, video_size=video_size)
    pygame.display.flip()
    clock.tick(fps)
        
    agent = make_agent(model_tp)
    
    while running:
        step_info = agent.get_action(env)
        action = step_info['action']
        data.append(step_info)
        
        if action == -1:
            rew = 0
            env_done = True
        elif action == "reset":
            prev_obs = obs
            obs = env.reset()
        else:
            action = keys_to_action[action]
            prev_obs = obs
            if action is not None:
                obs, rew, env_done, info = env.step(action)
                print("Reward:", rew) if rew != 0 else None
                if rew != 0:
                    running = False
        if callback is not None:
            callback(prev_obs, obs, action, rew, env_done, info)
        if obs is not None:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning)
                rendered = env.render(mode="rgb_array")
            display_arr(screen, rendered, transpose=transpose, video_size=video_size)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == VIDEORESIZE:
                video_size = event.size
                screen = pygame.display.set_mode(video_size)

        pygame.display.flip()
        clock.tick(fps)
            
    pygame.quit()
    return data, data[-1]



def run_single():
    n_runs_per_env = 1
    for model_tp in ["flat"]:#, "flat"]:
        for run in range(n_runs_per_env):
            for env_tp in [Env7D0]:
                np.random.seed(run)
                print(env_tp.__name__)
                print("---------")
                env = make("env/"+ env_tp.__name__)
                #start=time.time()
                data, summ_data = model_play(env, model_tp, 1)
                print(summ_data)
                #print(time.time()-start)

def run_experiment():
    out_dir = "models/output/"
    
    model_n_seeds = {"mepomdp": 50, "flat": 1}
    
    for model_tp in ["mepomdp", "flat"]:
        n_seeds = model_n_seeds[model_tp]
            
        all_data = []
        all_summ_data = []
        
        for seed in range(n_seeds):
            print(seed)
            print("\n\n")
            for env_tp in [Env1D0, Env1D1, Env2D0, Env2D1, Env3D0, Env3D1, Env4D0, Env4D1, Env5D0, Env5D1, Env6D0, Env6D1, Env7D0, Env7D1, Env8D0, Env8D1, Env9D0, Env9D1, Env10D0, Env10D1, Env11D0, Env11D1, Env12D0, Env12D1, Env13D0, Env13D1, Env14D0, Env14D1, Env15D0, Env15D1]:
                np.random.seed(seed)
                print(env_tp.__name__)
                print("---------")
                start=time.time()
                env = make("env/"+ env_tp.__name__)
                data, summ_data = model_play(env, model_tp, 1)
                df = pd.DataFrame.from_records(data)
                summ_df = pd.DataFrame.from_records([summ_data])
                df["env_name"] = env_tp.__name__
                df["seed"] = seed
                summ_df["env_name"] = env_tp.__name__
                summ_df["seed"] = seed
                all_data.append(df)
                all_summ_data.append(summ_df)
                final_df = pd.concat(all_data, ignore_index=True)
                final_df.to_csv(out_dir + model_tp + ".csv", index=False)
                final_summ_df = pd.concat(all_summ_data, ignore_index=True)
                final_summ_df.to_csv(out_dir + model_tp + "_summ.csv", index=False)
                print(time.time()-start)
                
def register_envs():
    for env in [Tutorial1, Tutorial2, Tutorial3, Tutorial4, Tutorial5, Tutorial6, Tutorial7, Tutorial8, Tutorial9, Env1D0, Env1D1, Env2D0, Env2D1, Env3D0, Env3D1, Env4D0, Env4D1, Env5D0, Env5D1, Env6D0, Env6D1, Env7D0, Env7D1, Env8D0, Env8D1, Env9D0, Env9D1, Env10D0, Env10D1, Env11D0, Env11D1, Env12D0, Env12D1, Env13D0, Env13D1, Env14D0, Env14D1, Env15D0, Env15D1]:
        register('env/' +  env.__name__, env)

if __name__ == "__main__":
    
    register_envs()
    
    run_single()
    #run_experiment()
