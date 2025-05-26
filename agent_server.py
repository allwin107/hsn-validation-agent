# Flask API server for managing agents

# Import necessary libraries
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename

import logging
import os
import re
import spacy
from spacy.lang.en.stop_words import STOP_WORDS

from hsn_agent import validate_hsn, validate_hsn_list, extract_hsn_from_text, load_dataset, invalid_attempts, get_invalid_hsn_summary, log_invalid_hsn

nlp = spacy.load("en_core_web_sm")
COMMON_ENGLISH_WORDS = {
    'check', 'tell', 'about', 'show', 'list', 'find', 'give',
    'valid', 'invalid', 'code', 'codes', 'describe', 'me', 'is', 'are'
}

# Create Flask app and configure logging
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) 
ALLOWED_EXTENSIONS = {'xlsx'} 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure logging to output to console
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)


# Define home route
@app.route('/')
def home():
    invalid_attempts.clear()
    return render_template('chat.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Define a route to upload an Excel file containing HSN codes
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('upload.html', message="❌ No file part.")
        file = request.files['file']
        if file.filename == '':
            return render_template('upload.html', message="❌ No selected file.")
        if file and allowed_file(file.filename):
            filename = secure_filename("HSN_SAC.xlsx")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            try:
                load_dataset()
                return redirect(url_for('home'))
            except Exception as e:
                return render_template('upload.html', message=f"⚠️ Upload succeeded, but reload failed: {e}")
        else:
            return render_template('upload.html', message="❌ Invalid file type. Only .xlsx is allowed.")
    return render_template('upload.html')

# Define routes for single HSN code validation
@app.route('/validate', methods=['POST'])
def validate():
    data = request.json
    if not data or 'hsn_code' not in data:
        return jsonify({"error": "Missing 'hsn_code' in request"}), 400
    hsn_code = data['hsn_code']
    result = validate_hsn(hsn_code)
    logging.info(f"Validated HSN: {hsn_code} → {result}")
    return jsonify(result)

# The /validate_list route accepts a list of HSN codes and returns their validation results
@app.route('/validate_list', methods=['POST'])
def validate_list():
    data = request.json
    if not data or 'hsn_list' not in data:
        return jsonify({"error": "Missing 'hsn_list' in request"}), 400
    hsn_list = data['hsn_list']
    results = validate_hsn_list(hsn_list)
    logging.info(f"Batch validation: {results}")
    return jsonify(results)

# The /chat route accepts a user message and extracts the HSN code from it
# It then validates the extracted HSN code and returns a response
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    user_message = re.sub(r'[,\uFF0C;/+|\-]', ' ', user_message)
    doc = nlp(user_message)

    codes = set()
    invalid_tokens = set()

    #import re
    #text = re.sub(r'\W+', '', token.text)

    for token in doc:
        text = token.text.strip()
        if not text or token.is_punct:
            continue
        
        if text.isdigit():
            # Numeric token
            if len(text) in [2,4,6,8]:
                codes.add(text)
            else:
                invalid_tokens.add(f"{text} (invalid format - must be 2,4,6, or 8 digits)")
        else:
            # Non-numeric token
            # Only add to invalid_tokens if NOT a stop word (filter normal English)
            word = text.lower()
            if word not in STOP_WORDS and word not in COMMON_ENGLISH_WORDS and any(c.isalpha() for c in word):
                invalid_tokens.add(text)


    replies = []

    # Validate detected codes
    for code in sorted(codes):
        result = validate_hsn(code)
        if result["valid"]:
            reply = f"✅ {code} is valid: {result['description']}"
            if "hierarchy" in result:
                reply += "\n🔗 Hierarchy:"
                for level, desc in result["hierarchy"].items():
                    reply += f"\n- {level}: {desc}"
            replies.append(reply)

        else:
            reason = result.get("reason", "No reason provided.")
            replies.append(f"❌ {code} is invalid: {reason}")


    # Show error messages for invalid tokens
    for token in sorted(invalid_tokens):
        replies.append(f"❌ `{token}` is not a valid HSN code.")

    if not replies:
        return jsonify({
            "reply": (
                "❌ I couldn’t detect a valid HSN code.\n\n"
                "👉 Try: `01012100`, `Check 99999999`, or `Tell me about 1101`"
            )
        })

    return jsonify({"reply": "\n".join(replies)})



@app.route('/reload_dataset', methods=['POST'])
def reload_dataset():
    try:
        load_dataset()
        return jsonify({"status": "Dataset reloaded successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/invalids')
def show_invalid_summary():
    summary = get_invalid_hsn_summary(invalid_attempts)
    html = "<h2>Invalid HSN Attempts</h2><ul>"
    for entry, count in summary:
        html += f"<li>{entry} — <strong>{count}</strong></li>"
    html += "</ul><a href='/'>← Back to Chat</a>"
    return html

@app.route('/admin/invalids_json')
def invalids_json():
    return jsonify(get_invalid_hsn_summary(invalid_attempts))


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
    
# To run the server, use the command:
# python agent_server.py