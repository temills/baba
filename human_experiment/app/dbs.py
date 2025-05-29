from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
 
class Subject(db.Model):
    __tablename__ = 'subjects'
    
    internal_id = db.Column(db.String, primary_key=True)
    subject_id = db.Column(db.String)
    comments = db.Column(db.String)
    age = db.Column(db.String)
    language = db.Column(db.String)
    nationality = db.Column(db.String)
    country = db.Column(db.String)
    gender = db.Column(db.String)
    student = db.Column(db.String)
    education = db.Column(db.String)
    bonus = db.Column(db.String)
    n_instruction_loops = db.Column(db.String)
    exp_phase = db.Column(db.String)
    
    def __repr__(self):
        return '<Subject %r>' % self.internal_id


class Trial(db.Model):
    __tablename__ = 'trials'
    row_id = db.Column(db.String, primary_key=True)
    internal_id = db.Column(db.String)
    subject_id = db.Column(db.String)
    actions = db.Column(db.String)
    action_times = db.Column(db.String)
    agent_pos = db.Column(db.String)
    game_end_time = db.Column(db.String)
    trial_start_time = db.Column(db.String)
    game_type = db.Column(db.String)
    game_idx = db.Column(db.String)
    exp_phase = db.Column(db.String)

    def __repr__(self):
        return '<Subject %r>' % self.row_id
    
    
class Stimuli(db.Model):
    __tablename__ = 'stimuli'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)        # e.g. 'stim_type_1'
    subtype = db.Column(db.String)     # e.g. 'A'
    use_count = db.Column(db.Integer, default=0)