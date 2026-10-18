import os
import json
import random
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'player_uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def quiz_player_client():
    """
    Serves the primary Interactive UI dashboard. It dynamically adjusts 
    based on whether a file path parameter is passed or a manual upload is executed.
    """
    # Check if a parameter was passed from another script/HTML (e.g., ?quiz_source=generated_quizzes/pool_ramayana.json)
    passed_source = request.args.get('quiz_source') or ""
    initial_load_js = "false"
    preloaded_questions = []

    # If a valid parameter path is caught, immediately parse it into the frontend state
    if passed_source and os.path.exists(passed_source):
        try:
            with open(passed_source, 'r', encoding='utf-8') as f:
                preloaded_questions = json.load(f)
                # Shuffle the preloaded questions at start for variety
                random.shuffle(preloaded_questions)
                initial_load_js = "true"
        except Exception as e:
            print(f"Error loading parameter source: {e}")

    # Unified Frontend Interface template string
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Sanskrit Samasa Quiz Dashboard</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f0f4f8; margin: 0; padding: 40px; color: #2c3e50; }}
            .container {{ max-width: 750px; margin: 0 auto; background: white; padding: 35px; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); }}
            h1 {{ color: #1a365d; text-align: center; margin-top: 0; font-size: 28px; border-bottom: 3px solid #e2e8f0; padding-bottom: 15px; }}
            .mode-section {{ background: #edf2f7; padding: 20px; border-radius: 8px; margin-bottom: 25px; border-left: 5px solid #3182ce; }}
            .drop-zone {{ border: 2px dashed #4299e1; padding: 25px; text-align: center; background: #ebf8ff; border-radius: 6px; cursor: pointer; font-weight: 500; color: #2b6cb0; }}
            .hidden {{ display: none !important; }}
            .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 25px; margin-top: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }}
            .word-display {{ font-size: 24px; color: #2b6cb0; font-weight: bold; text-align: center; margin-bottom: 15px; }}
            .question-text {{ font-size: 18px; margin-bottom: 20px; font-weight: 500; }}
            .option-btn {{ display: block; width: 100%; text-align: left; padding: 14px 20px; margin-bottom: 12px; background: #f7fafc; border: 2px solid #e2e8f0; border-radius: 6px; font-size: 16px; cursor: pointer; transition: all 0.2s; }}
            .option-btn:hover {{ background: #edf2f7; border-color: #cbd5e0; }}
            .correct {{ background: #c6f6d5 !important; border-color: #48bb78 !important; color: #22543d; font-weight: bold; }}
            .wrong {{ background: #fed7d7 !important; border-color: #f56565 !important; color: #742a2a; }}
            .nav-box {{ display: flex; justify-content: space-between; margin-top: 25px; align-items: center; }}
            .action-btn {{ background: #3182ce; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 6px; cursor: pointer; font-weight: 600; }}
            .action-btn:hover {{ background: #2b6cb0; }}
            .hint-box {{ margin-top: 15px; padding: 15px; background: #fffaf0; border: 1px solid #feebc8; border-left: 4px solid #dd6b20; border-radius: 4px; font-size: 14px; color: #7b341e; }}
            #score-board {{ font-size: 18px; font-weight: bold; color: #4a5568; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🕉️ Samasa Quiz Player Engine</h1>
            
            <!-- SECTION 1: Independent Setup (Hidden automatically if Parameter mode is active) -->
            <div id="setup-area" class="mode-section">
                <p style="margin-top:0; font-weight:600;">Independent Mode: Load Generated Quiz JSON</p>
                <div class="drop-zone" onclick="document.getElementById('file-picker').click()">
                    Plop your 'pool_*.json' file here or click to browse
                    <input type="file" id="file-picker" accept=".json" onchange="handleFileUpload(event)">
                </div>
            </div>

            <!-- SECTION 2: Active Gameplay Screen -->
            <div id="quiz-area" class="hidden">
                <div class="nav-box" style="margin-top: 0; margin-bottom: 15px;">
                    <div id="progress-text">Question 1 of X</div>
                    <div id="score-board">Score: 0</div>
                </div>
                
                <div class="card">
                    <div class="word-display" id="target-word">Sanskrit Word</div>
                    <div class="question-text" id="question-label">Loading question text...</div>
                    <div id="options-box"></div>
                    <div id="hint-panel" class="hint-box hidden"></div>
                </div>

                <div class="nav-box">
                    <button class="action-btn" id="hint-btn" onclick="toggleHint()">💡 View Paninian Hint</button>
                    <button class="action-btn" id="next-btn" onclick="nextQuestion()" disabled>Next Question ➡️</button>
                </div>
            </div>
            
            <!-- SECTION 3: Final Matrix Summary Screen -->
            <div id="result-area" class="hidden" style="text-align: center; padding: 20px;">
                <h2>🎉 Assessment Concluded!</h2>
                <p style="font-size: 22px; margin-bottom: 30px;">You scored <span id="final-score" style="color:#48bb78; font-weight:bold;">0</span> out of <span id="final-total">0</span></p>
                <button class="action-btn" onclick="window.location.reload()">🔄 Restart/Load New Pool</button>
            </div>
        </div>

        <script>
            // State Storage variables
            let questionsPool = {json.dumps(preloaded_questions)};
            let currentQuestionIndex = 0;
            let currentScore = 0;
            let answered = false;

            // Handle script bootstrapping under Parameter configurations
            window.onload = function() {{
                if ({initial_load_js}) {{
                    document.getElementById('setup-area').classList.add('hidden');
                    startQuiz();
                }}
            }};

            // File parsing logic for standalone Independent Upload mode
            function handleFileUpload(event) {{
                const file = event.target.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = function(e) {{
                    try {{
                        questionsPool = JSON.parse(e.target.result);
                        // Shuffle loaded array
                        questionsPool.sort(() => Math.random() - 0.5);
                        document.getElementById('setup-area').classList.add('hidden');
                        startQuiz();
                    }} catch (err) {{
                        alert("Invalid JSON format detected. Ensure this is an output from the Quiz Generator app.");
                    }}
                }};
                reader.readAsText(file);
            }}

            function startQuiz() {{
                if (!questionsPool || questionsPool.length === 0) {{
                    alert("The loaded quiz file is empty.");
                    return;
                }}
                currentQuestionIndex = 0;
                currentScore = 0;
                document.getElementById('quiz-area').classList.remove('hidden');
                renderCurrentQuestion();
            }}

            function renderCurrentQuestion() {{
                answered = false;
                document.getElementById('next-btn').disabled = true;
                document.getElementById('hint-panel').classList.add('hidden');
                
                let qData = questionsPool[currentQuestionIndex];
                
                document.getElementById('progress-text').innerText = `Question ${{currentQuestionIndex + 1}} of ${{questionsPool.length}}`;
                document.getElementById('score-board').innerText = `Score: ${{currentScore}}`;
                document.getElementById('target-word').innerText = qData.word || 'समासः';
                document.getElementById('question-label').innerText = qData.question;
                
                const container = document.getElementById('options-box');
                container.innerHTML = '';
                
                qData.options.forEach((opt) => {{
                    let btn = document.createElement('button');
                    btn.className = 'option-btn';
                    btn.innerText = opt;
                    btn.onclick = () => evaluateChoice(btn, opt, qData.correct_answer);
                    container.appendChild(btn);
                }});
            }}

            function evaluateChoice(selectedBtn, pickedVal, correctVal) {{
                if (answered) return; // Prevent double clicks changing metrics
                answered = true;
                
                const buttons = document.querySelectorAll('.option-btn');
                buttons.forEach(btn => {{
                    if (btn.innerText === correctVal) {{
                        btn.classList.add('correct');
                    }}
                }});

                if (pickedVal === correctVal) {{
                    currentScore++;
                    document.getElementById('score-board').innerText = `Score: ${{currentScore}}`;
                }} else {{
                    selectedBtn.classList.add('wrong');
                }}

