from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
from PaddleOCR import OCR
from correct import EnhancedCppOCRCorrector
from batch_compilation import CppBatchCompiler
from scoring.grade_cpp_llm_only import grade_cpp_file_llm_only
import json

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload',methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error":"No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error":"No selected part"}), 400
    if file :
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({"message": "File uploaded successfully", "filepath": filepath}), 200
    else:
        return jsonify({"error": "Invalid file type"}), 400 
    
@app.route('/ai_score', methods=['POST'])
def ai_score():
    data = request.get_json()
    filepath = data.get('filepath')
    
    if not filepath or not os.path.exists(filepath):
        return jsonify({"error":"File not found"}), 400
    
    try:
        ocr = OCR(file_path=filepath)
        cpp_output_path = "./results/cpp/output.cpp"

        corrector = EnhancedCppOCRCorrector()
        corrected_cpp_path = "./results/cpp_ed/corrected_output.cpp"
        corrector.correct_code(cpp_output_path, corrected_cpp_path)

        compiler = CppBatchCompiler(compiler="g++", output_dir="./results/build")
        compile_result = compiler.compile_single_file(corrected_cpp_path)

        stderr = compile_result.get("stderr","")
        ##ai评分还没有完善
        problem_desc = ""
        result = grade_cpp_file_llm_only(problem_desc, corrected_cpp_path, error_messages=stderr)

        if result.get('score_breakdown'):
            breakdown = result['score_breakdown']

            scores = breakdown.get('scores',{})
            score_data = {
                "compilability": scores.get('compilability', 0),
                "correctness": scores.get('correctness', 0),
                "code_quality": scores.get('code_quality', 0),
                "readability": scores.get('readability', 0),
                "total": breakdown.get('total', 0),
                "confidence": breakdown.get('confidence', 0)
            }

            # 获取评分理由
            rationale = breakdown.get('rationale', '')
            
            # 获取改进建议
            suggestions = breakdown.get('suggestions', [])
            
            response = {
                "score_breakdown": score_data,
                "rationale": rationale,
                "suggestions": suggestions
            }
            return jsonify(response), 200
        else:
            return jsonify({"error": "评分数据缺失"}), 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ =='__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)