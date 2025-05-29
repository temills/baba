from flask import Blueprint, request, render_template, make_response
from flask_socketio import emit, join_room
from .dbs import db, Subject, Trial, Stimuli
import numpy as np
from game.play import init_env, step_env, step_tutorial_env
from .create_app import socketio
from collections import defaultdict
import random
import redis
import pickle

def get_redis_conn():
    return redis.Redis(host='localhost', port=6379, db=0)

bp = Blueprint('main', __name__)

@socketio.on('connect')
def handle_connect():
    print(f"New WebSocket connection: {request.sid}")
    
@socketio.on('disconnect')
def handle_disconnect(d):
    print(f"Client disconnected: {request.sid}")
    
@socketio.on_error()
def handle_error(e):
    print(f"Socket.IO error: {e}")    

@socketio.on("init_game")
def init_game(data):
    print("In init game!")
    print(data)
    game_type = data.get("game_type")
    env = init_env(game_type)
    r = get_redis_conn()
    r.set(f"grid:{request.sid}", pickle.dumps({"env": env, "game_type": game_type}))
    emit("game_update", {'grid':env.grid.encode().tolist()})
    
@socketio.on("player_action")
def handle_player_action(data):
    action = data.get('action')
    game_type = data.get('game_type')
    r = get_redis_conn()
    raw = r.get(f"grid:{request.sid}")
    if raw is None:
       emit("error", {"message": "Game not initialized."})
       return
    game_data = pickle.loads(raw)
    env = game_data["env"]
    if data.get("is_tutorial"):
        _, won, agent_pos = step_tutorial_env(game_type, env, action)
    else:
        _, won, agent_pos = step_env(game_type, env, action)
    game_data["env"] = env
    r.set(f"grid:{request.sid}", pickle.dumps(game_data))
    emit('game_update', {'grid': env.grid.encode().tolist(), 'won': won, 'agent_pos':agent_pos})


@bp.route('/puzzle_game/get_stim', methods=['GET', 'POST'])
def get_stim():
    result = {}
    all_stims = Stimuli.query.all()
    if not all_stims:
        return {"error": "No stimuli in DB"}, 404
    stim_by_type = defaultdict(list)
    for stim in all_stims:
        stim_by_type[stim.type].append(stim)
    for stim_type, stim_list in stim_by_type.items():
        min_count = min(s.use_count for s in stim_list)
        candidates = [s for s in stim_list if s.use_count == min_count]
        chosen_stim = random.choice(candidates)
        chosen_stim.use_count += 1
        result[stim_type] = chosen_stim.subtype
    db.session.commit()
    stim = []
    for (et, dt) in result.items():
        stim.append(et + dt)
    random.shuffle(stim)
    return stim

@bp.route('/puzzle_game/', methods=['GET', 'POST'])
def experiment():
    if request.method == 'GET':
        return render_template('experiment.html')
    if request.method == 'POST':
        dd = request.get_json(force=True)['data']
        # subject information
        if dd['exp_phase'] == 'subject_info':
            print('recording subject data')
            ret = Subject(**{k: str(v) for k, v in dd.items()})
        # trial response
        else:
            print('recording trial data')
            ret = Trial(**{k: str(v) for k, v in dd.items()})
        db.session.add(ret)
        db.session.commit()
        return make_response("", 200)

def register_routes(app):
    app.register_blueprint(bp)
    
  