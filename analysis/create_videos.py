import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from game.baba import make
from game.baba.my_envs import * 
from game.baba.registration import register
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from moviepy.editor import ImageClip, concatenate_videoclips
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

img_key_to_fname = {"baba": "baba_obj.png", 
                    "wall": "wall_obj.png", 
                    "fwall": "wall_obj.png", 
                    "rock": "rock_obj.png", 
                    "grass": "grass_obj.png", 
                    "flag": "flag_obj.png", 
                    "empty": "empty.png",
                    "border": "border.png", 
                    "flag_word": "flag_word.png", 
                    "floor": "floor_obj.png", 
                    "baba_word": "baba_word.png", 
                    "wall_word": "wall_word.png", 
                    "goop_word": "goop_word.png", 
                    "goop": "goop_obj.png",
                    "lava": "lava_obj.png",
                    "water": "goop_obj.png",
                    "fwater": "goop_obj.png",
                    "stop_word": "stop_word.png", 
                    "win_word": "win_word.png", 
                    "grass_word": "grass_word.png", 
                    "is_word": "is_word.png", 
                    "rock_word": "rock_word.png",
                    "keke_word": "keke_word.png",
                    "keke": "keke_obj.png",
                    "you_word": "you_word.png",
                    "sink_word":"sink_word.jpeg",
                    "float_word":"float_word.jpeg",
                    "water_word":"water_word.jpeg",
                    "stop_word": "stop_word.png"}
        
idx_to_img_key = {-1: 'water', -2: 'lava', 0: 'unseen', 1: 'empty', 2: 'wall', 3: 'floor', 4: 'door', 5: 'key', 6: 'ball', 7: 'box', 9: 'lava', 10: 'agent', 11: 'water', 12: 'flag', 13: 'baba', 16: 'is_word', 19: 'ball_word', 20: 'wall_word', 21: 'door_word', 22: 'key_word', 23: 'baba_word', 24: 'water_word', 25: 'you_word', 26: 'win_word', 27: 'fball', 28: 'fdoor', 29: 'fkey', 30: 'fwall', 31: 'border', 32: 'fwater', 33: 'rock', 34: 'rock_word', 35: 'flag_word', 36: 'keke_word', 37: "keke", 38:"stop_word", 39:"float_word", 40:"sink_word"}

def actions_to_grids(game_type, actions):
    """
    Given list of actions and game_type, generate list of grids
    """
    env = make(f"env/{game_type}")
    init_grid = env.grid.encode()
    reset_grid = np.full(init_grid.shape, -1)
    giveup_grid = np.full(init_grid.shape, -2) 
    grids = []
    grids.append(init_grid)
    for action in actions:
        if action==-1:
            grids.append(reset_grid)
            env = make(f"env/{game_type}")
        elif action==-2:
            grids.append(giveup_grid)
        else:
            _, _, _, _ = env.step(action)
            grids.append(env.grid.encode())
    return grids

def grids_to_frames(grids, sid, game_type, image_dir='../human_experiment/app/static/imgs/keke_img', cell_size=32):
    """
    Convert list of grids to pngs
    """
    out_dir = video_path + 'frames/' + sid + "/" + game_type + "/"

    os.makedirs(out_dir, exist_ok=True)
    frame_paths = []
    images = {}
    for img_key, fname in img_key_to_fname.items():
        images[img_key] = Image.open(os.path.join(image_dir, fname)).resize((cell_size, cell_size))

    for i, grid in enumerate(grids):
        w, h, d = grid.shape
        frame = Image.new('RGB', (w * cell_size, h * cell_size), color=(0,0,0))
        
        for y in range(h):
            for x in range(w):
                img_key = idx_to_img_key[grid[x, y][0]]
                tile = images.get(img_key)
                frame.paste(tile, (x * cell_size, y * cell_size))
        
        frame_path = os.path.join(out_dir, f'frame_{i:04d}.png')
        frame.save(frame_path)
        frame_paths.append(frame_path)

    return frame_paths


def frames_to_video(frame_paths, times, sid, game_type, fps=24):
    """
    Convert pngs at frame_paths to videos 
    """
    out_dir = video_path + game_type + "/"
    os.makedirs(out_dir, exist_ok=True)
    out_path = out_dir + sid + ".mp4"
    
    if os.path.exists(out_path):
        return
    
    clips = []
    for i in range(len(frame_paths)-1):
        duration = times[i+1] - times[i]
        clip = ImageClip(frame_paths[i]).set_duration(duration)
        clips.append(clip)
    clips.append(ImageClip(frame_paths[-1]).set_duration(0.5)) 
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(out_path, fps=24, codec='libx264')



def make_rule_img(words, fname, vert):
    """
    Generate png of a given rule
    """
    image_dir='../human_experiment/app/static/imgs/keke_img'
    images = {}
    cell_size = 32
    for img_key, fname in img_key_to_fname.items():
        images[img_key] = Image.open(os.path.join(image_dir, fname)).resize((cell_size, cell_size))

    if vert:
        w = 1
        h = 3
    else:
        w=3
        h=1
    frame = Image.new('RGB', (w * cell_size, h * cell_size), color=(0,0,0))
    for y in range(h):
        for x in range(w):
            img_key = words[(x+1)*(y+1)-1]
            tile = images.get(img_key)
            frame.paste(tile, (x * cell_size, y * cell_size))
    
    frame_path = os.path.join('../human_experiment/app/static/imgs/', fname + '.png')
    frame.save(frame_path)  


def get_game_imgs(distr=0):
    """
    Generate pngs of all game types of given distractor variant
    """

    env_types = {}
    for i in range(1,16):
        env_types["Env" + str(i) + "D" + str(distr)] = str(i)

    image_dir = '../human_experiment/app/static/imgs/keke_img'
    cell_size = 32
    images = {}

    for img_key, fname in img_key_to_fname.items():
        images[img_key] = Image.open(os.path.join(image_dir, fname)).resize((cell_size, cell_size))

    out_dir = "figs/game_imgs/"
    os.makedirs(out_dir, exist_ok=True)
    frames = []
    names = []

    for env_name, label in env_types.items():
        env = make(f"env/{env_name}")
        grid = env.grid.encode()
        w, h, d = grid.shape
        frame = Image.new('RGB', (w * cell_size, h * cell_size), color=(0, 0, 0))
        for y in range(h):
            for x in range(w):
                img_key = idx_to_img_key[grid[x, y][0]]
                tile = images.get(img_key)
                frame.paste(tile, (x * cell_size, y * cell_size))
        frames.append(frame)
        names.append(label)

    ncols = 5  # how many images per row
    nrows = (len(frames) + ncols - 1) // ncols  # how many rows needed
    buffer_x=25
    buffer_y=16
    frame_w, frame_h = frames[0].size
    big_img = Image.new('RGB', (ncols * frame_w + buffer_x, nrows * frame_h + buffer_y), color=(0, 0, 0))

    font = ImageFont.truetype("/System/Library/Fonts/ArialHB.ttc", 60)
    for idx, (frame, label) in enumerate(zip(frames, names)):
        x = (idx % ncols) * (frame_w+(buffer_x//(ncols-1)))
        y = (idx // ncols) *(frame_h+(buffer_y//(nrows-1)))
        big_img.paste(frame, (x, y))
        draw = ImageDraw.Draw(big_img)
        if label in ["11", "12", "13", "14", "15"]:
            y-=5
        draw.text((x, y-7), label, fill="white", font=font)
    big_img.save(os.path.join(out_dir, "all_envs_" + str(distr) + ".png"), optimize=True, compress_level=9)


def get_example_game_image(padding=10):
    imgs = [Image.open(path) for path in [video_path + 'frames/2sxnlelk4z/Env5D0/frame_0000' + '.png', video_path + 'frames/2sxnlelk4z/Env5D0/frame_0005.png', video_path + 'frames/2sxnlelk4z/Env5D0/frame_0014.png', video_path + 'frames/2sxnlelk4z/Env5D0/frame_0019.png']]
    widths, heights = zip(*(i.size for i in imgs))
    total_width = sum(widths) + padding * (len(imgs) - 1)
    max_height = max(heights)

    new_img = Image.new('RGB', (total_width, max_height), color=(255,255,255))
    x_offset = 0
    for img in imgs:
        new_img.paste(img, (x_offset, 0))
        x_offset += img.size[0] + padding

    # Save combined image temporarily
    combined_img_path = 'figs/example_game.png'
    new_img.save(combined_img_path, optimize=True, compress_level=9)

    # Plot with matplotlib and draw the arrow + label
    fig, ax = plt.subplots(figsize=(10, 4))
    img = plt.imread(combined_img_path)
    ax.imshow(img)
    ax.axis('off')
    
    # Use axes coordinates: we'll just overlay text + arrow
    ax.annotate(
        '', xy=(0.95, 1.1), xytext=(0.05, 1.1),
        xycoords='axes fraction',
        textcoords='axes fraction',
        arrowprops=dict(arrowstyle='->', color='black', lw=1)
    )
    ax.text(0.5, 1.13, "Time", ha='center', va='bottom', transform=ax.transAxes,
            fontsize=10)

    plt.subplots_adjust(top=1.15)  # Make space for arrow
    plt.savefig('figs/example_game_with_arrow.png', bbox_inches='tight', dpi=1000)
    plt.show()
    

if __name__=="__main__":
    for env in [Tutorial1, Tutorial2, Tutorial3, Tutorial4, Tutorial5, Tutorial6, Tutorial7, Tutorial8, Tutorial9, Tutorial10,
                Env1D0, Env2D0, Env3D0, Env4D0, Env5D0, Env6D0, Env7D0, Env8D0, Env9D0, Env10D0, Env11D0,Env12D0, Env13D0, Env14D0, Env15D0,
                Env1D1, Env2D1, Env3D1, Env4D1, Env5D1, Env6D1, Env7D1, Env8D1, Env9D1, Env10D1, Env11D1, Env12D1, Env13D1, Env14D1, Env15D1]:
        register('env/' +  env.__name__, env)
        
    df = pd.read_csv('data/clean_data.csv')
    
    video_path = "figs/videos/"
    
    #get_example_game_image()
    #get_game_imgs(0)
    #get_game_imgs(1)
    
    # Make videos for all games
    for idx, row in df.iterrows():
        actions = eval(row['actions'])
        action_times = [0] + eval(row['action_times'])
        
        sid = row['sid']
        game_type = row['game_type']
    
        if (max(action_times) < 3600) and not(os.path.exists(video_path + game_type + "/" + sid + ".mp4")):
            grids = actions_to_grids(game_type, actions)
            frame_paths = grids_to_frames(grids, sid, game_type)
            frames_to_video(frame_paths, action_times, sid, game_type)

