import json
import pandas as pd

if __name__=="__main__":
    data_path = "data/"
    with open(data_path + 'raw_data.json') as f:
        trials = json.load(f)
        
    d = {'sid':[], 'actions':[], 'action_times':[], 'game_time':[], 'n_actions':[], 'game_time_to_first_action':[], 'game_type':[], 'env_type':[], 'distr_type':[], 'centering_type':[], 'game_idx':[], 'gave_up':[], 'is_tutorial':[]}
    
    env_to_centering_type = {
        'Env1':'none',
        'Env2':'you',
        'Env3':'float',
        'Env4':'win',
        'Env5':'stop',
        'Env6':'replace',
        'Env7':'you',
        'Env8':'you',
        'Env9':'float,win', 
        'Env10':'you,stop',
        'Env11':'replace,win',
        'Env12':'sink,replace',
        'Env13':'you,win',
        'Env14':'you,replace',
        'Env15':'stop,replace',
    }
    
    for trial in trials:
        d['sid'].append(trial['internal_id'])
        d['game_time'].append(eval(trial['game_end_time'])/1000)
        actions = trial['actions']
        action_times = [a/1000 for a in trial['action_times']]
        d['actions'].append(actions)
        d['action_times'].append(action_times)
        d['n_actions'].append(len(actions))
        d['is_tutorial'].append('Tutorial' in trial['game_type'])
        d['gave_up'].append(int(actions[-1]==-2))
        d['game_time_to_first_action'].append(action_times[0])
        d['game_idx'].append(trial['game_idx'])
        d['game_type'].append(trial['game_type'])
        d['env_type'].append(trial['game_type'].split("D")[0])
        try:
            d['distr_type'].append(trial['game_type'].split("D")[1])
        except:
            d['distr_type'].append(0)
        if 'Tutorial' in trial['game_type']:
            d['centering_type'].append("tutorial")
        else:
            d['centering_type'].append(env_to_centering_type[trial['game_type'].split("D")[0]])
        
    df = pd.DataFrame(d)
    df.to_csv(data_path + 'clean_data.csv')