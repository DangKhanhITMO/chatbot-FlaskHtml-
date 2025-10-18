from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env (khi chạy cục bộ)
load_dotenv()

# Khởi tạo Flask app, trỏ đến thư mục templates (chứa index.html và ảnh)
app = Flask(__name__, template_folder="templates")
CORS(app)  # Cho phép gọi từ frontend

# Lấy API key từ biến môi trường
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ Thiếu biến môi trường OPENAI_API_KEY. Hãy chắc chắn đã khai báo trong .env hoặc Render Environment.")

# Khởi tạo OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Route chính để hiển thị giao diện chatbot
@app.route('/')
def home():
    return render_template("index.html")

# API xử lý chat
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "").strip()

    # Trường hợp tin nhắn bắt đầu hoặc trống
    if user_message.lower() in ["", "start", "begin"]:
        welcome_message = (
            "Xin chào quý khách!\nTôi là nhân viên tư vấn trả lời tự động của hệ thống "
            "phòng khám và chăm sóc thú y GPET!\nTôi có thể hỗ trợ và giúp gì cho quý khách?"
        )
        return jsonify({"reply": welcome_message})

    try:
        # Gửi yêu cầu đến OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Bạn là một trợ lý AI thân thiện."},
                {"role": "user", "content": user_message}
            ]
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({"reply": reply})

    except Exception as e:
        print("LỖI:", e)
        return jsonify({"error": str(e)}), 500
#ngrok config add-authtoken 34Aw6OBPYnUu2twDpvmXxOYYrf4_69GFTDQG24zod9z14idu8
#python -m http.server 5500
# Khởi chạy server cục bộ (Render sẽ dùng start command riêng)
if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')