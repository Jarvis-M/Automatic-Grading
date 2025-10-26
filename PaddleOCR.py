from paddleocr import PaddleOCR
import json
import cv2
import numpy as np
import os

class OCR:
    def __init__(self,file_path, cpp_output_path="./results/cpp/output.cpp", json_output_path="./results/ocr/res.json"):
        processed_image_path = self.preprocessed_image(file_path)

        ocr = PaddleOCR(
            text_detection_model_name="PP-OCRv5_server_det",
            text_recognition_model_name="PP-OCRv5_server_rec",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            # text_rec_score_thresh=0.7,
        )

        output = ocr.predict(processed_image_path)
        output_dir = os.path.dirname(json_output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for res in output:
            res.save_to_json(json_output_path)

        cpp_output_dir = os.path.dirname(cpp_output_path)
        if not os.path.exists(cpp_output_dir):
            os.makedirs(cpp_output_dir)

        self.generate_cpp_file(json_output_path, cpp_output_path)
    
    def preprocessed_image(self, image_path):
        img = cv2.imread(image_path)
        image_name = os.path.splitext(os.path.basename(image_path))[0]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        def apply_preprocessing_denoise_only(image):
            """
            方法：仅去噪 + Otsu 二值化
            """
            denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
        final_result = apply_preprocessing_denoise_only(gray)

        def post_process(binary_img, apply_morphology=True):
            if apply_morphology:
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
                cleaned = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, kernel)
                return cleaned
            return binary_img

        final_result = post_process(final_result, apply_morphology=True)

        output_dir = "./results/preprocessing_results"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_filename = f"{image_name}.jpg"
        processed_image_path = os.path.join(output_dir, output_filename)
        cv2.imwrite(processed_image_path, final_result)
        
        return processed_image_path

    def generate_cpp_file(self, json_path, cpp_output_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        rec_texts = data.get("rec_texts", [])

        with open(cpp_output_path, 'w', encoding='utf-8') as f:
            for line in rec_texts:
                f.write(line + "\n")

if __name__ == '__main__':
    ocr = OCR(file_path=r"C:\Users\17665\Desktop\1.jpg")