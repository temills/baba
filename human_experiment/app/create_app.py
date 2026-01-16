import eventlet
eventlet.monkey_patch()
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from .dbs import db
from flask_socketio import SocketIO

socketio = SocketIO(
    path="/puzzle_game/socket.io",
    async_mode="eventlet"
)

def create_app():
    app = Flask(__name__, static_url_path="/puzzle_game/static")

    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///local.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    from . import views
    views.register_routes(app)

    socketio.init_app(app, message_queue="redis://localhost:6379")

    return app