from datetime import datetime
from app import db

class UserImage(db.Model):
    __tablename__ = "user_images"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String)
    image_path = db.Column(db.String)
    is_detected = db.Column(db.Boolean, default = False)
    created_at = db.Column(db.DateTime, default = datetime.now)
    updated_at = db.Column(db.DateTime, default = datetime.now, onupdate =datetime.now)
    
class UserImageTag(db.Model):
    __tablename__='user_image_tags'
    id = db.Column(db.Integer, primary_key = True)
    user_image_id = db.Column(db.Integer, db.ForeignKey("user_images.id"))
    tag_name = db.Column(db.String)
    created_at = db.Column(db.DateTime, default = datetime.now)
    updated_at = db.Column(db.DateTime, default = datetime.now, onupdate =datetime.now)