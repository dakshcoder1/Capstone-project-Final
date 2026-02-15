from flask_sqlalchemy import SQLAlchemy
from datetime import datetime



db = SQLAlchemy()



# =============================================================================
# MODEL
# =============================================================================
class History(db.Model):
    __tablename__ = "history"

    id=db.Column(db.Integer,primary_key=True)
    tool_name=db.Column(db.String(200),nullable=False)
   
    input_text= db.Column(db.Text)
    input_img= db.Column(db.String(400))
    
    output_text=db.Column(db.Text)
    output_img=db.Column(db.String(400))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



    def to_dict(self):
        return {
            'id': self.id,
            'tool_name': self.tool_name,
            'input_text': self.input_text,
            'input_img': self.input_img,
            'output_text': self.output_text,
            'output_img': self.output_img,
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id,
            
        }


 # NEW: For admin panel - include user statistics
    def to_dict_with_stats(self):
        total_history = len(self.history)
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
            'total_history': total_history,
        }


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    history = db.relationship('History', backref='owner', lazy=True)


    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat()
        }


    

