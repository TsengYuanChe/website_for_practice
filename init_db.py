from app import create_app, db
import logging
from sqlalchemy import inspect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app(config_key='production')
with app.app_context():
    try:
        logger.info("開始資料庫建立...")
        db.create_all()
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        if 'user_images' in tables and 'user_image_tags' in tables:
            logger.info("資料表已成功建立。")
        else:
            logger.warning("資料表未建立，請檢查配置。")
        logger.info("資料庫建立完成。")
    except Exception as e:
        logger.error("資料庫建立失敗：%s", e)