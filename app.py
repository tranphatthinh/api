from flask import Flask, request, jsonify, render_template
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import jwt
import datetime
import secrets
from functools import wraps
import os
from dotenv import load_dotenv
import google.generativeai as genai
from spellchecker import SpellChecker

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

spell = SpellChecker()
spell.word_frequency.load_words("vietnamese.txt") 


app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost/managers'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    refresh_token = db.Column(db.String(255), nullable=True)
    access_token = db.Column(db.String(500), nullable=True)

def generate_access_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def generate_refresh_token():
    return secrets.token_hex(32)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith("Bearer "):
            return jsonify({"error": "Thiếu hoặc sai định dạng token"}), 401
        token = token.split(" ")[1]
        try:
            # Giải mã và xác thực token
            decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            user_id = decoded_token['user_id']
            user = User.query.filter_by(id=user_id).first()
            
            # Kiểm tra xem người dùng có tồn tại không
            if not user:
                return jsonify({"error": "Token không hợp lệ"}), 403

            # Kiểm tra nếu token đã hết hạn
            if datetime.utcnow() > datetime.utcfromtimestamp(decoded_token['exp']):
                return jsonify({"error": "Token đã hết hạn"}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token đã hết hạn"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token không hợp lệ"}), 403
        
        return f(user, *args, **kwargs)
    
    return decorated

@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'GET':
        return render_template('/home/register.html')

    if request.content_type != 'application/json':
        return jsonify({"error": "Request phải có Content-Type: application/json"}), 415

    data = request.get_json()
    user_email = data.get("email")
    password = data.get("password")
    if not user_email or not password:
        return jsonify({"error": "Thiếu thông tin email hoặc mật khẩu"}), 400
    existing_user = User.query.filter_by(user_email=user_email).first()
    if existing_user:
        return jsonify({"error": "Email đã tồn tại"}), 400
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(user_email=user_email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    access_token = generate_access_token(new_user.id)
    refresh_token = generate_refresh_token()
    new_user.refresh_token = refresh_token
    db.session.commit()
    return jsonify({"access_token": access_token, 
                    "refresh_token": refresh_token
                    }), 201

@app.route('/')
def home():
    return render_template('/home/login.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('/home/login.html') 

    data = request.get_json()
    user_email = data.get("email")
    password = data.get("password")
    user = User.query.filter_by(user_email=user_email).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Sai tài khoản hoặc mật khẩu"}), 401
    access_token = generate_access_token(user.id)
    refresh_token = generate_refresh_token()
    user.refresh_token = refresh_token
    db.session.commit()
    return jsonify({"access_token": access_token,
                    "refresh_token": refresh_token,
                    "email": user.user_email
                    }), 200

@app.route('/refresh-token', methods=['POST'])
def refresh_token():
    data = request.get_json()
    refresh_token = data.get("refresh_token")
    user = User.query.filter_by(refresh_token=refresh_token).first()
    if not user:
        return jsonify({"error": "Refresh Token không hợp lệ"}), 401
    new_access_token = generate_access_token(user.id)
    return jsonify({"access_token": new_access_token, "email": user.user_email}), 200

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        if request.content_type == 'application/json':
            data = request.get_json()
            refresh_token = data.get("refresh_token")
        else:
            refresh_token = request.form.get("refresh_token")

        user = User.query.filter_by(refresh_token=refresh_token).first()
        if user:
            user.refresh_token = None
            db.session.commit()
        return render_template('/home/login.html'), 200

    return render_template('/home/login.html')

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    try:
        if request.method == 'POST':
            email = request.form['email']
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']

            print("Form data:", email, old_password, new_password, confirm_password)

            user = User.query.filter_by(user_email=email).first()
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

@app.route('/check-grammar', methods=['GET', 'POST'])
def grammar_check():
    try:
        if request.method == 'GET':
            return render_template('/home/index.html') 

        data = request.get_json() or {}
        text = data.get("text", "").strip()

        if not text:
            return jsonify({"error": "No text provided"}), 400
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            f"Hãy phát hiện và sửa lỗi chính tả, ngữ pháp trong văn bản sau."
            f" Hãy trình bày kết quả rõ ràng, xuống dòng từng ý:"
            f"\n1. **PHÁT HIỆN LỖI** (liệt kê từng lỗi 1 dòng).\n"
            f"2. **VĂN BẢN ĐÃ SỬA** (viết lại đoạn văn sau khi sửa).\n"
            f"Văn bản cần kiểm tra: {text}"
        )

        return jsonify({
    "VĂN BẢN GỐC": text.replace("\n", "<br>"),
    "VĂN BẢN ĐÃ SỬA": response.text.replace("\n", "<br>")
})

    except Exception as e:
        import traceback
        traceback.print_exc()  # In ra chi tiết lỗi
        return jsonify({"error": f"Lỗi xử lý: {str(e)}"}), 500

@app.route('/suggest-improvement', methods=['GET', 'POST'])
def suggest_improvement():
    if request.method == 'GET':
            return render_template('/home/index.html') 
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(
            f"Hãy cải thiện cách diễn đạt của văn bản sau mà không làm thay đổi ý nghĩa."
            f" Đưa ra phiên bản tốt hơn, sử dụng từ vựng phong phú và ngữ pháp tự nhiên hơn."
            f"\n1. **GỢI Ý CẢI THIỆN** (viết lại đoạn văn bằng cách cải thiện từ ngữ, câu cú).\n"
            f"\n2. **GIẢI THÍCH** (tại sao cách viết này tốt hơn).\n"
            f"\nVăn bản cần cải thiện: {text}"
        )

    return jsonify({
            "VĂN BẢN GỐC": text.replace("\n", "<br>"),
            "GỢI Ý CẢI THIỆN": response.text.replace("\n", "<br>")
        })
if __name__ == '__main__':
    app.run(debug=True)
