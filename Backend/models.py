from flask_sqlalchemy import SQLAlchemy



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




class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    history = db.relationship('History', backref='owner', lazy=True)


    

