from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv
import traceback

# Load biến môi trường từ file .env khi chạy local
load_dotenv()

# Khởi tạo Flask app
app = Flask(__name__, template_folder="templates")
CORS(app)

# Đọc API Key từ biến môi trường
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ Thiếu biến môi trường OPENAI_API_KEY. Hãy khai báo trong .env hoặc Render Environment.")

# Khởi tạo OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Trang chính giao diện chatbot
@app.route('/')
def home():
    return render_template("index.html")

# API chat chính
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    # Lời chào ban đầu
    if user_message.lower() in ["", "start", "begin"]:
        welcome_message = (
            "Xin chào quý khách!\nTôi là nhân viên tư vấn trả lời tự động của hệ thống "
            "phòng khám và chăm sóc thú y GPET!\nTôi có thể hỗ trợ và giúp gì cho quý khách?"
        )
        return jsonify({"reply": welcome_message})

    try:
        print("📨 Gửi yêu cầu đến OpenAI với nội dung:", user_message)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Bạn là một trợ lý AI thân thiện."},
                {"role": "user", "content": user_message}
            ]
        )
        reply = response.choices[0].message.content.strip()
        print("✅ Nhận phản hồi từ OpenAI:", reply)
        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ Lỗi khi gọi OpenAI:", e)
        traceback.print_exc()
        return jsonify({"reply": "❌ Lỗi server khi xử lý yêu cầu. Vui lòng thử lại sau!"}), 500

# Route kiểm tra hoạt động của server
@app.route('/health')
def health_check():
    return "✅ Server đang hoạt động", 200

# Route test OpenAI kết nối
@app.route('/test-openai')
def test_openai():
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Xin chào"}]
        )
        return jsonify({"reply": response.choices[0].message.content})
    except Exception as e:
        print("❌ Lỗi khi test OpenAI:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Chạy server local (Render sẽ dùng start command riêng)
if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')