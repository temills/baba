from .create_app import create_app, db
from .dbs import Stimuli

# Init db:
#from .run import app
#with app.app_context():
#   db.create_all()

# Init stim:
app = create_app()
app.app_context().push()

types = [f'Env{i+1}' for i in range(15)]
subtypes = ['D0', 'D1']
Stimuli.query.delete()
for t in types:
    for s in subtypes:
        stim = Stimuli(type=t, subtype=s)
        db.session.add(stim)

db.session.commit()