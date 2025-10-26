import cv2
import numpy as np
import os

# 1. 读取原图
image_path = r"D:\C++_OCR\Automatic-Grading\data\241042Y416\test1\1.jpg"
img = cv2.imread(image_path)


# 获取原图文件名（不含扩展名）
image_name = os.path.splitext(os.path.basename(image_path))[0]

# 2. 转为灰度图
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


# 3. 定义仅使用 denoise_only 的预处理方法
def apply_preprocessing_denoise_only(image):
    """
    方法：仅去噪 + Otsu 二值化
    """
    denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


# 4. 应用 denoise_only 预处理
final_result = apply_preprocessing_denoise_only(gray)


# 5. （可选）形态学轻度清理
def post_process(binary_img, apply_morphology=True):
    if apply_morphology:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        cleaned = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, kernel)
        return cleaned
    return binary_img


final_result = post_process(final_result, apply_morphology=True)


# 6. 创建保存结果的目录
output_dir = "preprocessing_results"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 7. 保存 denoise_only 处理结果
output_filename = f"{image_name}_denoise_only.jpg"
cv2.imwrite(os.path.join(output_dir, output_filename), final_result)

print(f"- 已保存去噪预处理结果: {output_filename}")
