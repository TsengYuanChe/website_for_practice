from flask_wtf.file import FileAllowed, FileField, FileRequired
from flask_wtf.form import FlaskForm
from wtforms.fields.simple import SubmitField

class DetectorForm(FlaskForm):
    submit = SubmitField("檢測")
    
class DeleteForm(FlaskForm):
    submit = SubmitField("刪除")