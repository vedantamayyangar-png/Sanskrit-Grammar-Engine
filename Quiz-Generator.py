import os
import json
import random
from flask import Flask, request, jsonify, render_code_template, redirect, url_for

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'generated_quizzes'

# Ensure required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def core_quiz_generator(source_data):
    """
    Core engine that structures raw Sanskrit corpus JSON data into multiple-choice quizzes
    """
    generated_quizzes = []
    
    # Safely extract words list from corpus format
    words_list = source_data.get('words', []) if isinstance(source_data, dict) else source_data
    
    if not words_list:
        return []

    # Gather all valid samasa types from the dataset to dynamically build incorrect options
    all_samasa_types = list(set(
        item.get('samasa_type', '').split('ः')[0].strip('() ') 
        for item in words_list if item.get('samasa_type')
    ))
    # Fallback default types if dataset pool is narrow
    if len(all_samasa_types) < 4:
        all_samasa_types = list(set(all_samasa_types + ["तत्पुरुषः", "बहुव्रीहिः", "द्वन्द्वः", "कर्मधारयः", "द्विगुः", "अव्ययीभावः"]))

    for index, item in enumerate(words_list):
        word = item.get("word")
        raw_samasa = item.get("samasa_type", "")
        meaning_en = item.get("meaning_en", "")
        notes = item.get("notes", "")
        
        # Skip entries that are not compounds (Samasa)
        if not raw_samasa:
            continue
            
        # Clean the correct samasa string for options matching
        correct_answer = raw_samasa.split('ः')[0].strip('() ')
        
        # Generate wrong options dynamically
        wrong_options = [ans for ans in all_samasa_types if ans != correct_answer]
        sampled_wrong = random.sample(wrong_options, min(3, len(wrong_options)))
        
        options = sampled_wrong + [correct_answer]
        random.shuffle(options)
        
        # Build comprehensive quiz element mapping back to original scholarly details
        quiz_item = {
            "id": index + 1,
            "word": word,
            "question": f"What is the correct Samasa type for the word '{word}' ({meaning_en})?",
            "options": options,
            "correct_answer": correct_answer,
            "hint": f"Split: {item.get('samasa_split')}. Notes: {notes}"
        }
        generated_quizzes.append(quiz_item)
        
    return generated_quizzes

@app.route('/')
def home():
    """
    Built-in independent uploader landing page
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sanskrit Quiz Engine Uploader</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f4f7f6; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
            h2 { color: #2c3e50; margin-top: 0; }
            .drop-zone { border: 2px dashed #3498db; padding: 30px; text-align: center; background: #ecf0f1; border-radius: 4px; cursor: pointer; }
            input[type="file"] { display: none; }
            button { background-color: #2ecc71; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 4px; cursor: pointer; width: 100%; margin-top: 15px; }
            button:hover { background-color: #27ae60; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Independent Mode: Upload Corpus JSON</h2>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <div class="drop-zone" onclick="document.getElementById('fileInput').click()">
                    Drag & Drop or Click to Select 'ramayana-corpus-sanskrit.json'
                    <input type="file" name="file" id="fileInput" required accept=".json">
                </div>
                <button type="submit">Generate Interactive Quiz</button>
            </form>
        </div>
    </body>
    </html>
    """
    return html_content

@app.route('/upload', method_post=['POST'])
@app.route('/api/generate', method_post=['POST', 'GET'])
def process_json_input():
    """
    Dual-purpose endpoint. Handles direct file stream uploads (Independent mode) 
    OR file token query parameters passed from external HTML scripts (Parameter mode).
    """
    raw_data = None
    filename = "dynamic_quiz.json"

    # --- MODE A: Parameter Called from Another HTML/Script ---
    if request.method == 'GET' or request.args.get('file_path'):
        # Check if another UI component specified a localized asset path parameter
        target_path = request.args.get('file_path') or request.form.get('file_path')
        if target_path and os.path.exists(target_path):
            with open(target_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            filename = os.path.basename(target_path)

    # --- MODE B: Independent Standard File Upload Uploader ---
    if not raw_data and 'file' in request.files:
        file = request.files['file']
        if file and file.filename.endswith('.json'):
            file_content = file.read().decode('utf-8')
            raw_data = json.loads(file_content)
            filename = file.filename

    if not raw_data:
        return jsonify({"status": "error", "message": "No valid source JSON data detected via parameters or uploader stream."}), 400

    # Execute transformation pipeline
    quiz_pool = core_quiz_generator(raw_data)
    
    # Save the organized pool file for tracking/persistence layer
    output_filename = f"pool_{filename}"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(quiz_pool, f, indent=4, ensure_ascii=False)

    # Return structured array downstream directly to the quiz player implementation
    return jsonify({
        "status": "success",
        "total_generated": len(quiz_pool),
        "saved_destination": output_path,
        "quiz_pool": quiz_pool
    })

if __name__ == '__main__':
    # Default local development server configurations
    app.run(host='0.0.0.0', port=5000, debug=True)
