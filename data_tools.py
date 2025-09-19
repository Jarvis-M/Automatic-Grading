# 设计图像预处理的工具类

'''
现存问题
1.拍摄阴影暂时无法规避(考虑光照补偿/去除阴影)
'''
import cv2
import numpy as np

class DataTools:
    def __init__(self, image_path):
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise ValueError("Invalid image path")
        self.original_image = self.image.copy()

    # 去噪
    def Denoise(self, method='gaussian', kernel_size=5):
        if method == 'gaussian':
            self.image = cv2.GaussianBlur(self.image, (kernel_size, kernel_size), 0)
        elif method == 'median':
            self.image = cv2.medianBlur(self.image, kernel_size)
        else:
            raise ValueError("Unsupported denoising method")
        return self.image
    
    # 二值化
    def Binarization(self, method='otsu'):
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        if method == 'otsu':
            _, self.image = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif method == 'adaptive':
            self.image = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        elif method == 'mean':
            _, self.image = cv2.threshold(gray, np.mean(gray), 255, cv2.THRESH_BINARY)
        else:
            raise ValueError("Unsupported binarization method")
        return self.image

    # 形态学操作
    def Morphology(self, operation='dilate', kernel_size=(5, 5)):
        kernel = np.ones(kernel_size, np.uint8)
        if operation == 'dilate':
            self.image = cv2.dilate(self.image, kernel, iterations=1)
        elif operation == 'erode':
            self.image = cv2.erode(self.image, kernel, iterations=1)
        else:
            raise ValueError("Unsupported morphological operation")
        return self.image
    
    # 图像矫正
    def Correction(self):
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        angle = 0
        if lines is not None:
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle_deg = np.rad2deg(theta)-90
                angles.append(angle_deg)
            angle = np.mean(angles)
        if angle != 0:
            rows, cols = self.image.shape[:2]
            M = cv2.getRotationMatrix2D((cols/2, rows/2), angle, 1)
            self.image = cv2.warpAffine(self.image, M, (cols, rows))
        return self.image

    # 光照补偿
    # def Retinex(self, sigma=30):
    #     image_float = np.float32(self.image)+1.0
    #     image_blur = cv2.GaussianBlur(image_float, (0, 0), sigma)
    #     retinex = np.log(image_float)-np.log(image_blur)
    #     self.image = np.uint8(np.clip(retinex*255 / np.max(retinex), 0, 255))
    #     return self.image
    # def Equalization(self):
    #     gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
    #     equalized = cv2.equalizeHist(gray)
    #     self.image = cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)
    #     return self.image
    # def Brightness(self, alpha=1, beta=0):
    #     self.image = cv2.convertScaleAbs(self.image, alpha=alpha, beta=beta)
    #     return self.image

if __name__ == '__main__':
    image_path = r'data\1.jpg'
    data_tools = DataTools(image_path)
    # data_tools.Brightness(alpha=1.5, beta=10)
    # data_tools.Correction()
    # data_tools.Equalization()
    # data_tools.Denoise(method='gussian', kernel_size=1)
    # data_tools.Binarization(method='otsu')
    # data_tools.Morphology(operation='erode', kernel_size=(1, 1))
    # cv2.imshow('image', data_tools.image)
    cv2.imwrite('processed.jpg', data_tools.image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()