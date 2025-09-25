"""
图像预处理模块
用于对手写代码图片进行预处理，提高OCR识别准确率
"""

import cv2
import numpy as np
from skimage import filters, morphology, measure
from skimage.filters import threshold_otsu
from skimage.morphology import disk
import matplotlib.pyplot as plt


class ImagePreprocessor:
    def __init__(self):
        self.processed_image = None
        
    def load_image(self, image_path):
        """加载图像"""
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise ValueError(f"无法加载图像: {image_path}")
        return self.image
    
    def resize_image(self, image, max_width=1200):
        """调整图像大小，保持宽高比"""
        height, width = image.shape[:2]
        if width > max_width:
            ratio = max_width / width
            new_width = max_width
            new_height = int(height * ratio)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return image
    
    def remove_noise(self, image):
        """去除噪声"""
        # 使用高斯滤波去除噪声
        denoised = cv2.GaussianBlur(image, (3, 3), 0)
        return denoised
    
    def correct_skew(self, image):
        """校正图像倾斜"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 使用霍夫变换检测直线
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None:
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = theta - np.pi/2
                angles.append(angle)
            
            # 计算平均角度
            median_angle = np.median(angles)
            
            # 如果角度大于阈值，进行旋转校正
            if abs(median_angle) > 0.1:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle * 180 / np.pi, 1.0)
                image = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return image
    
    def enhance_contrast(self, image):
        """增强对比度"""
        # 转换到LAB色彩空间
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # 对L通道应用CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # 合并通道并转换回BGR
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def binarize(self, image):
        """二值化处理"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 使用自适应阈值处理，效果更好
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        
        # 反转图像（让文字为白色，背景为黑色）
        binary = cv2.bitwise_not(binary)
        
        # 形态学操作去除噪点
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # 进一步去噪
        binary = cv2.medianBlur(binary, 3)
        
        return binary
    
    def remove_lines(self, image):
        """去除横线（如笔记本的横线）"""
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 检测水平线
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        detected_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        
        # 创建掩码
        cnts = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        
        # 填充检测到的线条
        for c in cnts:
            cv2.drawContours(detected_lines, [c], -1, 0, 2)
        
        # 从原图中移除线条
        result = cv2.inpaint(image, detected_lines, 3, cv2.INPAINT_TELEA)
        
        return result
    
    def remove_white_noise(self, binary_image, min_area=30):
        """去除白色噪点"""
        # 找到连通域
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_image, connectivity=8)
        
        # 创建掩码，只保留面积大于阈值的区域
        mask = np.zeros_like(binary_image)
        for i in range(1, num_labels):  # 跳过背景（标签0）
            area = stats[i, cv2.CC_STAT_AREA]
            # 保留面积大于阈值的区域
            if area >= min_area:
                mask[labels == i] = 255
        
        return mask
    
    def auto_crop(self, image):
        """自动裁剪图像，去除空白边缘"""
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 找到非零像素的边界
        coords = cv2.findNonZero(binary)
        if coords is not None:
            # 获取边界框
            x, y, w, h = cv2.boundingRect(coords)
            
            # 添加一些边距
            margin = 20
            x = max(0, x - margin)
            y = max(0, y - margin)
            w = min(image.shape[1] - x, w + 2 * margin)
            h = min(image.shape[0] - y, h + 2 * margin)
            
            # 裁剪图像
            cropped = image[y:y+h, x:x+w]
            return cropped
        else:
            return image
    
    def smart_crop(self, image):
        """智能裁剪，基于文字密度"""
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 计算每行的非零像素密度
        row_density = np.sum(binary > 0, axis=1)
        col_density = np.sum(binary > 0, axis=0)
        
        # 找到密度大于阈值的区域
        density_threshold = 0.1  # 10%的密度阈值
        
        # 找到上下边界
        rows_with_content = np.where(row_density > density_threshold * binary.shape[1])[0]
        if len(rows_with_content) > 0:
            top = max(0, rows_with_content[0] - 20)
            bottom = min(binary.shape[0], rows_with_content[-1] + 20)
        else:
            top, bottom = 0, binary.shape[0]
        
        # 找到左右边界
        cols_with_content = np.where(col_density > density_threshold * binary.shape[0])[0]
        if len(cols_with_content) > 0:
            left = max(0, cols_with_content[0] - 20)
            right = min(binary.shape[1], cols_with_content[-1] + 20)
        else:
            left, right = 0, binary.shape[1]
        
        # 裁剪图像
        cropped = image[top:bottom, left:right]
        return cropped
    
    def advanced_preprocess(self, image_path, save_intermediate=False):
        """针对手写代码的高级预处理流程"""
        print("开始高级图像预处理...")
        
        # 1. 加载图像
        image = self.load_image(image_path)
        print("✓ 图像加载完成")
        
        # 2. 智能裁剪，去除空白区域
        image = self.smart_crop(image)
        print("✓ 智能裁剪完成")
        
        # 3. 调整大小
        image = self.resize_image(image, max_width=1600)  # 提高分辨率
        print("✓ 图像大小调整完成")
        
        # 4. 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 5. 高斯模糊去噪
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        print("✓ 噪声去除完成")
        
        # 6. 增强对比度
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)
        print("✓ 对比度增强完成")
        
        # 7. 去除横线（针对笔记本）
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        detected_lines = cv2.morphologyEx(enhanced, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        enhanced = cv2.inpaint(enhanced, detected_lines, 3, cv2.INPAINT_TELEA)
        print("✓ 横线去除完成")
        
        # 8. 自适应二值化
        binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 15, 10)
        
        # 9. 反转图像（文字为白色）
        binary = cv2.bitwise_not(binary)
        
        # 10. 去除白色噪点
        binary = self.remove_white_noise(binary, min_area=30)
        
        # 11. 形态学操作清理
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)  # 去除小噪点
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)  # 连接断开的字符
        
        # 12. 再次去除噪点
        binary = self.remove_white_noise(binary, min_area=20)
        
        # 13. 最终滤波
        binary = cv2.medianBlur(binary, 3)
        print("✓ 二值化处理完成")
        
        self.processed_image = binary
        
        if save_intermediate:
            # 保存处理后的图像
            output_path = image_path.replace('.jpg', '_processed.jpg')
            cv2.imwrite(output_path, binary)
            print(f"✓ 处理后的图像已保存到: {output_path}")
        
        return binary

    def preprocess(self, image_path, save_intermediate=False):
        """完整的预处理流程"""
        return self.advanced_preprocess(image_path, save_intermediate)
    
    def show_comparison(self, original_path, processed_image):
        """显示原图和处理后图像的对比"""
        original = cv2.imread(original_path)
        original = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        processed = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
        
        plt.figure(figsize=(15, 8))
        
        plt.subplot(1, 2, 1)
        plt.imshow(original)
        plt.title('原始图像')
        plt.axis('off')
        
        plt.subplot(1, 2, 2)
        plt.imshow(processed, cmap='gray')
        plt.title('预处理后图像')
        plt.axis('off')
        
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    # 测试预处理功能
    preprocessor = ImagePreprocessor()
    
    # 处理示例图像
    image_path = r"D:\C++_OCR\Automatic-Grading\1.jpg"  # 假设图像文件名为1.jpg
    try:
        processed = preprocessor.preprocess(image_path, save_intermediate=False)
        print("图像预处理完成！")
        
        # 显示对比图
        preprocessor.show_comparison(image_path, processed)
        
    except Exception as e:
        print(f"预处理过程中出现错误: {e}")
