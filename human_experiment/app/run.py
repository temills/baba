import eventlet
eventlet.monkey_patch()

from .create_app import create_app, socketio, db

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=8005)