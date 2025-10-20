import cv2
import matplotlib.pyplot as plt
import numpy as np
import os

# 1. 读取原图
image_path = r"D:\C++_OCR\1.jpg"
img = cv2.imread(image_path)

# 获取原图文件名（不含扩展名）
image_name = os.path.splitext(os.path.basename(image_path))[0]

# 2. 转为灰度图
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


# 3. 多种预处理方法对比
def apply_preprocessing(image, method='default'):
    """
    应用不同的预处理方法
    """
    if method == 'default':
        # 方法1：轻度高斯模糊 + 适中CLAHE
        blurred = cv2.GaussianBlur(image, (3, 3), 0)
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        equalized = clahe.apply(blurred)
        _, binary = cv2.threshold(equalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    elif method == 'light':
        # 方法2：轻度处理，保留更多细节
        blurred = cv2.GaussianBlur(image, (3, 3), 0.5)
        clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(8, 8))
        equalized = clahe.apply(blurred)
        _, binary = cv2.threshold(equalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    elif method == 'adaptive':
        # 方法3：自适应阈值（对光照不均更有效）
        blurred = cv2.GaussianBlur(image, (3, 3), 0)
        binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
        return binary

    elif method == 'denoise_only':
        # 方法4：仅去噪 + Otsu
        denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary


# 4. 应用不同的预处理方法
methods = ['default', 'light', 'adaptive', 'denoise_only']
results = []

for method in methods:
    processed = apply_preprocessing(gray, method)
    results.append((method, processed))


# 5. 形态学后处理（根据效果选择应用）
def post_process(binary_img, apply_morphology=True):
    if apply_morphology:
        # 使用更小的核进行形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        cleaned = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, kernel)
        return cleaned
    return binary_img


# 创建保存结果的目录
output_dir = "preprocessing_results"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 6. 显示所有预处理结果对比并保存
plt.figure(figsize=(15, 10))

# 显示原图
plt.subplot(2, 3, 1)
plt.imshow(gray, cmap='gray')
plt.title("Original Grayscale")
plt.axis("off")

# 显示各种预处理结果
for i, (method, result) in enumerate(results):
    plt.subplot(2, 3, i + 2)

    # 对部分方法应用后处理
    if method in ['default', 'light']:
        result = post_process(result, apply_morphology=True)

    plt.imshow(result, cmap='gray')
    plt.title(f"Method: {method}")
    plt.axis("off")







# 7. 选择最佳方法进行进一步优化
def optimized_preprocessing(image):
    """
    优化的预处理流程
    """
    # 步骤1：轻度高斯模糊去噪
    blurred = cv2.GaussianBlur(image, (3, 3), 0.5)

    # 步骤2：适度的CLAHE增强
    clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)

    # 步骤3：Otsu二值化
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 步骤4：轻度形态学操作（可选）
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    return cleaned


# 应用优化后的方法
final_result = optimized_preprocessing(gray)

# 显示最终结果
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.imshow(gray, cmap='gray')
plt.title("Original Image")
plt.axis("off")

plt.subplot(1, 2, 2)
plt.imshow(final_result, cmap='gray')
plt.title("Optimized Preprocessing Result")
plt.axis("off")



# 保存最终处理结果（使用原图名称）
output_filename = f"{image_name}.jpg"
cv2.imwrite(f"{output_dir}/{output_filename}", final_result)




print(f"- 最终优化处理结果 ({output_filename})")