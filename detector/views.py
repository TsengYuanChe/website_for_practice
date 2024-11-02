from app import db
from .models import UserImage, UserImageTag
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import os, random, cv2, torchvision, torch, uuid
from werkzeug.utils import secure_filename
from PIL import Image
from pathlib import Path
import numpy as np
from .forms import DetectorForm, DeleteForm
from sqlalchemy.exc import SQLAlchemyError


dt = Blueprint("detector", __name__, template_folder="templates")

UPLOAD_FOLDER = 'static/Images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@dt.route('/', methods=['GET', 'POST'])
def index():
    return render_template("detector/index.html")

@dt.route('/upload', methods=['GET', 'POST'])
def upload():
    
    if request.method == 'POST':
        # 取得 ID 和文件
        user_id = request.form.get('user_id')
        file = request.files['file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            new_image = UserImage(user_id=user_id, image_path=f"{filename}")
            db.session.add(new_image)
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash("上傳失敗")
                return redirect(url_for('detector.upload'))

            flash('File successfully uploaded')
            return redirect(url_for('detector.index'))

    return render_template("detector/upload.html")

@dt.route('/view_user', methods=["POST"])
def view_user():
    user_id = request.form.get('user_id')  # 從表單中獲取 user_id
    if not user_id:
        flash("請輸入有效的用戶 ID")
        return redirect(url_for('detector.index'))  # 如果 user_id 無效，重定向到首頁或其他頁面
    
    # 重定向到 view_images 路徑，將 user_id 作為路徑參數
    return redirect(url_for('detector.view_images', user_id=user_id))

@dt.route('/view/<string:user_id>', methods=["GET",'POST'])
def view_images(user_id):
    detector_form = DetectorForm()
    delete_form = DeleteForm()
    
    images = UserImage.query.filter_by(user_id=user_id).all()
    
    user_image_tag_dict = {}
    for image in images:
        tags = UserImageTag.query.filter_by(user_image_id=image.id).all()
        user_image_tag_dict[image.id] = tags 

    return render_template(
        "detector/view.html",
        images=images,
        user_id=user_id,
        detector_form=detector_form,
        user_image_tag_dict=user_image_tag_dict,
        delete_form=delete_form
    )

def make_color(labels):
    colors = [[random.randint(0,255) for _ in range(3)] for _ in labels]
    color = random.choice(colors)
    return color

def make_line(result_image):
    line = round(0.002 * max(result_image.shape[0:2])) + 1
    return line

def draw_lines(c1, c2, result_image, line, color):
    cv2.rectangle(result_image, c1, c2, color, thickness=line)
    return result_image

def draw_texts(result_image, line, c1, c2, color, labels, label):
    display_txt = f"{labels[label]}"
    font = max(line - 1, 1)
    t_size = cv2.getTextSize(display_txt, 0, fontScale=line / 3, thickness=font)[0]
    c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
    cv2.rectangle(result_image, c1, c2, color, -1)
    cv2.putText(result_image, display_txt, (c1[0], c1[1] - 2), 0, line / 3, [255, 255, 255], thickness=font, lineType=cv2.LINE_AA,)
    return result_image

def exec_detect(target_image_path):
    labels = current_app.config["LABELS"]
    image = Image.open(target_image_path).convert('RGB')
    image_tensor = torchvision.transforms.functional.to_tensor(image)
    print(f"Image tensor shape: {image_tensor.shape}")
    
    model = torch.load(Path(current_app.root_path, "detector", "model.pt"))
    model = model.eval()
    output = model([image_tensor])[0]
    tags = []
    result_image = np.array(image.copy())
    print(f"Initial result_image type: {type(result_image)}")
    print(f"Initial result_image shape: {result_image.shape}")
    for box, label, score in zip(
        output["boxes"], output["labels"], output["scores"]
    ):
        if score > 0.5 and labels[label] not in tags:
            color = make_color(labels)
            line = make_line(result_image)
            c1 = (int(box[0]), int(box[1]))
            c2 = (int(box[2]), int(box[3]))
            result_image = draw_lines(c1, c2, result_image, line, color)
            print(f"After draw_lines: result_image type: {type(result_image)}")
            result_image = draw_texts(result_image, line, c1, c2, color, labels, label)
            tags.append(labels[label])
    detected_image_file_name = str(uuid.uuid4()) + ".jpg"
    detected_image_file_path = str(Path(UPLOAD_FOLDER, detected_image_file_name))
    cv2.imwrite(detected_image_file_path, cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR))
    return tags, detected_image_file_name

def save_detected_image_tags(user_image, tags, detected_image_file_name):
    user_image.image_path = detected_image_file_name
    user_image.is_detected = True
    db.session.add(user_image)
    
    for tag in tags:
        user_image_tag = UserImageTag(user_image_id = user_image.id, tag_name=tag)
        db.session.add(user_image_tag)
    
    db.session.commit()

@dt.route('/images/delete/<string:filename>', methods=["POST"])
def delete_image(filename):
    image = db.session.query(UserImage).filter(UserImage.image_path == filename).first()
    user_id = image.user_id
    image_id = image.id
    try:
        db.session.query(UserImageTag).filter(UserImageTag.user_image_id == image_id).delete()
        db.session.query(UserImage).filter(UserImage.id == image_id).delete()
        db.session.commit()
    except SQLAlchemyError as e:
        flash("圖片刪除處理發生錯誤")
        db.session.rollback()
    
    return redirect(url_for("detector.view_images", user_id=user_id))

@dt.route("/detect/<string:filename>", methods=["POST"])
def detect(filename):
    user_image = db.session.query(UserImage).filter(UserImage.image_path == filename).first()
    if user_image is None:
        flash("沒有物件")
        return redirect(url_for("detector.view_images", user_id=user_image.user_id))
    target_image_path = Path(UPLOAD_FOLDER).joinpath(user_image.image_path)
    tags, detected_image_file_name = exec_detect(target_image_path)
    try:
        save_detected_image_tags(user_image, tags, detected_image_file_name)
    except SQLAlchemyError as e:
        flash("物件偵測時發生錯誤")
        db.session.rollback()
        current_app.logger.error(e)
        return redirect(url_for("detector.view_images", user_id=user_image.user_id))
    return redirect(url_for("detector.view_images", user_id=user_image.user_id))