from flask import Flask
from pathlib import Path
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from config import config
from flask_login import LoginManager
import os


db = SQLAlchemy()
migrate = Migrate()

def create_app(config_key=None):
    if config_key is None:
        config_key = os.getenv("FLASK_CONFIG", "local")
    app = Flask(__name__)
    app.config.from_object(config[config_key])
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    from detector.models import UserImage, UserImageTag
    print(UserImage.__table__)  # 測試模型是否已加載
    
    from detector.views import dt
    app.register_blueprint(dt)
    
    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)