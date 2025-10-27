from flask import Flask, render_template, request, jsonify
import json
from openai import OpenAI
from dotenv import load_dotenv
from flask_cors import CORS
import os
import pandas as pd
from scipy.spatial.distance import cosine
import pickle

load_dotenv()

app = Flask(__name__, template_folder="templates")
CORS(app)

# Lấy API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ Thiếu OPENAI_API_KEY trong .env")

# Khởi tạo client OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def get_path_pkl(language):
    if language == "vi":
        return "data/vi_qa_with_embeddings.pkl"
    if language == "en":
        return "data/en_question_embeddings.pkl"
    if language == "ja":
        return "data/ja_question_embeddings.pkl"
    return None

path_pickle = get_path_pkl("vi")
with open(path_pickle, "rb") as f:
    data = pickle.load(f)
df = pd.DataFrame(data) if isinstance(data, list) else data

def get_embedding(text, model="text-embedding-3-small"):
    try:
        response = client.embeddings.create(input=text, model=model)
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Lỗi khi tạo embedding: {e}")
        return None

def find_best_match(user_question, threshold=0.85):
    user_embedding = get_embedding(user_question)
    if user_embedding is None:
        return None, 0.0

    best_score = -1
    best_row = None

    for idx, row in df.iterrows():
        emb = row.get("embedding")
        if emb is None:
            continue
        try:
            score = 1 - cosine(user_embedding, emb)
        except Exception as e:
            print(f"❌ Lỗi khi tính cosine: {e}")
            continue
        if score > best_score:
            best_score = score
            best_row = row

    if best_row is not None:
        return best_row["id_question"], best_score
    return None, 0.0

def load_data_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_answer_by_id_and_language(data_json, id_question, language):
    for item in data_json:
        if str(item.get("id_question", "")).strip() == str(id_question).strip():
            lang_data = item.get(language)
            if lang_data and "answer" in lang_data:
                return lang_data["answer"]
            else:
                return f"Không tìm thấy câu trả lời cho ngôn ngữ '{language}'."
    return f"Không tìm thấy câu hỏi với ID '{id_question}'."

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/init', methods=['POST'])
def init_language():
    data = request.get_json()
    lang = data.get('flag_language', 'en')

    if lang == 'vi':
        response = (
            "Quý khách đã chọn ngôn ngữ Tiếng Việt để được tư vấn.\n"
            " Xin kính chào quý khách! Tôi là trợ lý tư vấn tự động của Phòng khám và Chăm sóc Thú cưng GAIA PET."
            " Rất hân hạnh được đồng hành cùng quý khách và thú cưng yêu quý."
            " Quý khách cần hỗ trợ điều gì ạ?"
        )
    elif lang == 'ja':
        response = (
            "ご希望の言語として「日本語」が選択されました。\n"
            " こんにちは。私はGAIA PET動物クリニック・ケアセンターの自動応答アシスタントです。"
            " 大切なペットとの暮らしをサポートできることを光栄に思います。"
            " 本日はどのようなご相談でしょうか？"
        )
    else:
        response = (
            "You have selected English as your preferred consultation language. \n"
            " Hello and welcome! I’m the virtual assistant of GAIA PET Animal Clinic and Care Center."
            " It’s a pleasure to support you and your beloved pet."
            " How can I assist you today?"
        )

    return jsonify({"response": response})

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get("question", "").strip()
    lang = data.get("flag_language", "en")

    if not question:
        return jsonify({"error": "Missing question"}), 400

    # ✅ Nếu tiếng Việt, dùng fine-tuned model
    if lang == "vi":
        try:
            completion = client.chat.completions.create(
                model="ft:gpt-3.5-turbo-0125:personal::CV70liZF",
                messages=[
                    {"role": "system", "content": "Bạn là trợ lý tư vấn chăm sóc thú cưng của GAIA PET. Diễn đạt câu trả lời đảm bảo tính lịch sử và thu hút khách hàng."},
                    {"role": "user", "content": question}
                ]
            )
            answer = completion.choices[0].message.content.strip()
            return jsonify({
                "matched": False,
                "answer": answer
            })
        except Exception as e:
            return jsonify({"error": f"OpenAI error (fine-tuned): {e}"}), 500

    # ✅ Các ngôn ngữ khác xử lý như cũ
    path_pickle = get_path_pkl(lang)
    if not path_pickle or not os.path.exists(path_pickle):
        return jsonify({"error": f"No embedding data for language '{lang}'."}), 500

    try:
        with open(path_pickle, "rb") as f:
            loaded_data = pickle.load(f)
        df_local = pd.DataFrame(loaded_data) if isinstance(loaded_data, list) else loaded_data
    except Exception as e:
        return jsonify({"error": f"Failed to load embedding data: {e}"}), 500

    global df
    df = df_local

    id_match, score = find_best_match(question)
    THRESHOLD = 0.8
    if id_match and score >= THRESHOLD:
        json_path = f"data/qa_translations.json"
        if not os.path.exists(json_path):
            return jsonify({"error": f"Missing QA JSON file for language '{lang}'"}), 500

        data_json = load_data_from_json(json_path)
        answer = get_answer_by_id_and_language(data_json, id_match, lang)
        return jsonify({
            "matched": True,
            "id_question": id_match,
            "score": round(score, 4),
            "answer": answer
        })

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a customer care and consultation expert in the veterinary field. Please answer the following question in language {lang} in a clear and in-context manner related to GAIA pet clinic and care."},
                {"role": "user", "content": question}
            ]
        )
        answer = completion.choices[0].message.content.strip()
    except Exception as e:
        return jsonify({"error": f"OpenAI error: {e}"}), 500

    return jsonify({
        "matched": False,
        "answer": answer
    })
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)