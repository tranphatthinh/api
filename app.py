from flask import Flask, request, jsonify, render_template, session
from spellchecker import SpellChecker 
import secrets
from flask_sqlalchemy import SQLAlchemy
import google.generativeai as genai
import os
from dotenv import load_dotenv
from functools import wraps
from flask_bcrypt import Bcrypt
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

spell = SpellChecker()
spell.word_frequency.load_text_file("vietnamese.txt") 

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Danh sách API Key hợp lệ (nếu bạn không lưu trong database)
VALID_API_KEYS = {"test-api-key-123", "your-other-api-key"}

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("Authorization")
        if not api_key or api_key.replace("Bearer ", "") not in VALID_API_KEYS:
            return jsonify({"error": "API Key không hợp lệ"}), 403
        return f(*args, **kwargs)
    return decorated_function

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost/managers'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class apikeys(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    password = db.Column(db.String(255), nullable=False)

@app.route('/')
def home():
    return render_template('/home/login.html')

# Trang đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('/home/register.html')  # Giao diện đăng ký

    if request.content_type != 'application/json':
        return jsonify({"error": "Request phải có Content-Type: application/json"}), 415

    data = request.get_json()
    user_email = data.get("email")
    password = data.get("password")

    if not user_email or not password:
        return jsonify({"error": "Thiếu thông tin email hoặc mật khẩu"}), 400

    # Kiểm tra email đã tồn tại
    existing_user = apikeys.query.filter_by(user_email=user_email).first()
    if existing_user:
        return jsonify({"error": "Email đã tồn tại"}), 400

    # Mã hóa mật khẩu
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Tạo user mới
    new_user = apikeys(user_email=user_email, password=hashed_password)

    # Lưu vào database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Đăng ký thành công"}), 201

# Trang đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('/home/login.html')  # Trả về giao diện đăng nhập
    
    try:
        data = request.get_json()
        user_email = data.get("email")
        password = data.get("password")

        user = apikeys.query.filter_by(user_email=user_email).first()
        if not user or not bcrypt.check_password_hash(user.password, password):
            return jsonify({"error": "Sai tài khoản hoặc mật khẩu"}), 401

        # **Tạo API Key ngẫu nhiên mà không lưu vào database**
        temp_api_key = secrets.token_hex(32)

        return jsonify({
            "message": "Đăng nhập thành công!",
            "redirect_to": "/grammar-check",
            "api_key": temp_api_key  # Trả về API Key để lưu vào localStorage
        }), 200

    except Exception as e:
        return jsonify({"error": f"Lỗi server: {str(e)}"}), 500


@app.route('/logout', methods=['GET','POST'])
def logout():
    session.pop('id', None)
    return render_template('/home/login.html'), 200

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    try:
        if request.method == 'POST':
            email = request.form['email']
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']

            print("Form data:", email, old_password, new_password, confirm_password)

            user = apikeys.query.filter_by(user_email=email).first()
            if not user:
                return render_template('home/change-password.html', message='Tài khoản không tồn tại.')

            if not bcrypt.check_password_hash(user.password, old_password):
                return render_template('home/change-password.html', message='Mật khẩu cũ không đúng.')

            if new_password != confirm_password:
                return render_template('home/change-password.html', message='Mật khẩu xác nhận không khớp.')

            user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
            return render_template('home/login.html')

        return render_template('home/change-password.html')
    except Exception as e:
        print("❌ LỖI TRONG FLASK:", e)
        return f"Lỗi server: {e}", 500

@app.route('/grammar-check', methods=['GET','POST'])
def grammar_check():
    if request.method == 'GET':
        return render_template('/home/index.html') 
    try:
        data = request.get_json()
        text = data.get("text", "")

        if not text:
            return jsonify({"error": "No text provided"}), 400

        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            f"Hãy phát hiện và sửa lỗi chính tả, ngữ pháp trong văn bản sau."
            f" Hãy trình bày kết quả rõ ràng, xuống dòng từng ý:"
            f"\n1. **PHÁT HIỆN LỖI** (liệt kê từng lỗi 1 dòng).\n"
            f"2. **ĐOẠN VĂN ĐÃ SỬA** (viết lại đoạn văn sau khi sửa).\n"
            f"Văn bản cần kiểm tra: {text}"
            )

        return jsonify({
    "VĂN BẢN GỐC": text.replace("\n", "<br>"),
    "VĂN BẢN ĐÃ SỬA": response.text.replace("\n", "<br>")
})
    except Exception as e:
        return jsonify({"error": f"Lỗi server: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
