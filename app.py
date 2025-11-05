from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from PaddleOCR import OCR
from correct import EnhancedCppOCRCorrector
from batch_compilation import CppBatchCompiler
from scoring.grade_cpp_llm_only import grade_cpp_file_llm_only
import json

app = Flask(__name__)
# CORS(app,resources={r"/*": {"origins": "http://127.0.0.1:5500"}}) #Live Server的默认端口
CORS(app)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/result')
def result():
    return render_template('result.html')

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
async def ai_score():
    data = request.get_json()
    filepath = data.get('filepath')
    # print("filepath: ",filepath)
    
    if not filepath or not os.path.exists(filepath):
        return jsonify({"error":"File not found"}), 400
    # 确保目标文件夹存在
    output_dir = './results/cpp'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    corrected_dir = './results/cpp_ed'
    if not os.path.exists(corrected_dir):
        os.makedirs(corrected_dir)  

    build_dir = './results/build'
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)  
    try:
        ocr = OCR(file_path=filepath)
        cpp_output_path = "./results/cpp/output.cpp"

        corrector = EnhancedCppOCRCorrector()
        corrected_cpp_path = "./results/cpp_ed/corrected_output.cpp"
        corrector.correct_code(cpp_output_path, corrected_cpp_path)

        compiler = CppBatchCompiler(compiler="g++", output_dir="./results/build")
        compile_result = compiler.compile_single_file(corrected_cpp_path)

        stderr = compile_result.get("stderr","")

        problem_desc = "实现栈的pop、push、有多少元素和还剩空余多少空间的操作"
        result = await grade_cpp_file_llm_only(problem_desc, corrected_cpp_path, error_messages=stderr)

        if result.get('score_breakdown'):
            breakdown = result['score_breakdown']

            scores = breakdown.get('scores',{})
            score_data = {
                "compilability": scores.get('compilability', 0),
                "correctness": scores.get('correctness', 0),
                "code_quality": scores.get('code_quality', 0),
                "readability": scores.get('readability', 0),
                "total": breakdown.get('total', 0),
                # "confidence": breakdown.get('confidence', 0)
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
    app.run(debug=True,host='127.0.0.1', port=5000,)