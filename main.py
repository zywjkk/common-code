import os
# 强制屏蔽终端底层的 OpenCV 和 Qt 警告信息
os.environ["QT_LOGGING_RULES"] = "*=false"
os.environ["OPENCV_LOG_LEVEL"] = "FATAL"

import cv2
import numpy as np
import math

class SmartVisionAnalyzer:
    def __init__(self, image_path):
        self.image_path = image_path
        self.img = None
        self.hsv_img = None
        self.edges = None
        self.processed_img = None
        
        # [已改进] 根据终端调参截图，更新为更精准、更具鲁棒性的 HSV 阈值
        self.color_ranges = {
            # 红色包含 0-10 和 150-180 两个跨越带，放宽 S 下限以兼容粉红色圆柱
            'Red': [([0, 70, 70], [10, 255, 255]), ([150, 70, 70], [180, 255, 255])],
            # 绿色覆盖截图中的 H:48-58 区域
            'Green': [([35, 80, 80], [80, 255, 255])],
            # 蓝色覆盖截图中的 H:112-113 区域
            'Blue': [([100, 120, 80], [130, 255, 255])]
        }
        
        self.draw_colors = {
            'Red': (0, 0, 255),
            'Green': (0, 255, 0),
            'Blue': (255, 0, 0)
        }

    def load_image(self):
        self.img = cv2.imread(self.image_path)
        if self.img is None:
            print(f"❌ 错误: 无法读取图像 {self.image_path}，请检查路径。")
            return False
            
        h, w = self.img.shape[:2]
        max_dim = 1000
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            self.img = cv2.resize(self.img, (int(w * scale), int(h * scale)))
            
        self.hsv_img = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
        self.hsv_img = cv2.GaussianBlur(self.hsv_img, (3, 3), 0)
        
        # [已改进] 使用双边滤波替代高斯模糊，更好地保留物理边缘的同时平滑内部纹理
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        blurred_gray = cv2.bilateralFilter(gray, 9, 75, 75)
        edges = cv2.Canny(blurred_gray, 30, 100)
        
        # 稍微膨胀边缘线，使其像刀刃一样宽
        self.edges = cv2.dilate(edges, np.ones((3, 3), np.uint8))
        return True

    def get_color_mask(self, color_name):
        mask = np.zeros(self.img.shape[:2], dtype=np.uint8)
        ranges = self.color_ranges[color_name]
        
        for lower, upper in ranges:
            lower_np = np.array(lower, dtype=np.uint8)
            upper_np = np.array(upper, dtype=np.uint8)
            current_mask = cv2.inRange(self.hsv_img, lower_np, upper_np)
            mask = cv2.bitwise_or(mask, current_mask)
            
        # [已改进] 核心优化 1：先闭运算填补高光阴影造成的内部“破洞”
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
            
        # 物理切割：从颜色掩膜中直接抠去物理边缘线，从根源切断粘连
        mask = cv2.bitwise_and(mask, cv2.bitwise_not(self.edges))
        
        # [已改进] 核心优化 2：开运算清理边缘切割留下的毛刺，断开细微粘连
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        return mask

    def create_ideal_circle(self, center, radius):
        """生成一个完美的正圆轮廓数组"""
        pts = []
        for i in range(0, 360, 5):
            x = center[0] + radius * math.cos(math.radians(i))
            y = center[1] + radius * math.sin(math.radians(i))
            pts.append([int(x), int(y)])
        return np.array(pts).reshape((-1, 1, 2))

    def fit_ideal_geometry(self, contour):
        """
        [已改进] 全新高级特征分类器：综合分析圆度、矩形度、凸实度和多边形逼近
        """
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        area = cv2.contourArea(contour)
        
        # 忽略太小的噪点或无法计算的区域
        if hull_area == 0 or area < 200: 
            return "Unknown", contour, 0
            
        peri = cv2.arcLength(contour, True)
        rect = cv2.minAreaRect(contour)
        (cx, cy), (w, h), angle = rect
        
        if w == 0 or h == 0 or peri == 0: 
            return "Unknown", contour, 0
            
        # 核心几何特征计算
        rect_area = w * h
        extent = area / rect_area                        # 矩形度：占比越接近1越像矩形
        solidity = area / hull_area                      # 凸实度：越接近1代表形状越完整、无凹陷
        circularity = 4 * math.pi * area / (peri * peri) # 圆度：越接近1越像圆
        aspect_ratio = max(w, h) / min(w, h)             # 长宽比
        
        # 多边形逼近特征
        approx = cv2.approxPolyDP(contour, 0.03 * peri, True)
        vertices = len(approx)
        is_large = area > 5000

        # 1. 识别圆盘和小球 (高圆度 或 高凸实度且多边形边缘多)
        if circularity > 0.78 or (solidity > 0.92 and vertices >= 6 and extent > 0.7):
            shape_name = "Disk" if is_large else "Ball"
            (ccx, ccy), radius = cv2.minEnclosingCircle(contour)
            ideal_contour = self.create_ideal_circle((int(ccx), int(ccy)), int(radius))
            
            # 使用完美圆面积作为拟合度
            circle_area = math.pi * radius * radius
            fit_score = area / circle_area if circle_area > 0 else 0
            
            if fit_score > 0.7:
                return shape_name, ideal_contour, fit_score

        # 2. 识别方块和圆柱 (高凸实度且矩形占比高)
        if solidity > 0.85 and extent > 0.65:
            box = cv2.boxPoints(rect)
            ideal_contour = np.int32(box).reshape((-1, 1, 2))
            
            if aspect_ratio < 1.3:
                shape_name = "Cube"  # 长宽比例接近1，判定为正方体
            else:
                # 区分圆柱和长方体：圆柱侧放时两端是圆角，导致多边形拟合的顶点较多(>=5)且长宽比大
                if vertices >= 5 and aspect_ratio > 1.5 and extent < 0.95:
                    shape_name = "Cylinder"
                else:
                    shape_name = "Cuboid"
            
            fit_score = extent
            return shape_name, ideal_contour, fit_score

        # 3. 如果以上都不符合，大概率是被粘连的抽象轮廓
        return "Abstract", hull, max(circularity, extent)

    def split_abstract_contour(self, mask_shape, contour):
        """
        [已改进] 处理粘连轮廓：加强凹陷点识别深度，加粗切断线以彻底分离积木
        """
        local_mask = np.zeros(mask_shape, dtype=np.uint8)
        cv2.drawContours(local_mask, [contour], -1, 255, -1)
        
        hull_indices = cv2.convexHull(contour, returnPoints=False)
        try:
            defects = cv2.convexityDefects(contour, hull_indices)
        except:
            defects = None
            
        if defects is not None:
            deep_defects = []
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                depth = d / 256.0
                if depth > 8:  # 稍微降低阈值，捕捉更敏感的积木交界凹陷
                    deep_defects.append(tuple(contour[f][0]))
                    
            if len(deep_defects) >= 2:
                # 在相近的深坑凹点之间连线，强制切开掩膜
                for i in range(len(deep_defects)):
                    for j in range(i+1, len(deep_defects)):
                        p1 = deep_defects[i]
                        p2 = deep_defects[j]
                        dist = math.hypot(p1[0]-p2[0], p1[1]-p2[1])
                        if dist < 250: 
                            cv2.line(local_mask, p1, p2, 0, thickness=8) # 加粗断痕
                            
        # 腐蚀确保彻底物理断开
        local_mask = cv2.erode(local_mask, np.ones((5, 5), np.uint8))
        sub_cnts, _ = cv2.findContours(local_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return [c for c in sub_cnts if cv2.contourArea(c) > 300]

    def process_contours(self, raw_mask):
        final_shapes_info = []
        cnts, _ = cv2.findContours(raw_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in cnts:
            if cv2.contourArea(cnt) < 300: continue
            
            # 第一轮识别
            shape_name, ideal_contour, fit_score = self.fit_ideal_geometry(cnt)
            
            if fit_score < 0.75 or shape_name == "Abstract":
                # 触发深度粘连切割劈开
                sub_cnts = self.split_abstract_contour(raw_mask.shape, cnt)
                
                for sub_c in sub_cnts:
                    # 第二轮识别（对切割后的碎片）
                    sub_shape, sub_ideal, sub_fit = self.fit_ideal_geometry(sub_c)
                    
                    if sub_shape == "Abstract":
                        # 如果极端情况下仍抽象，根据外接矩形强分
                        rect = cv2.minAreaRect(sub_c)
                        box = cv2.boxPoints(rect)
                        sub_ideal = np.int32(box).reshape((-1, 1, 2))
                        aspect = max(rect[1]) / (min(rect[1]) + 1e-5)
                        sub_shape = "Cuboid" if aspect > 1.3 else "Cube"
                        
                    final_shapes_info.append((sub_shape, sub_ideal))
            else:
                final_shapes_info.append((shape_name, ideal_contour))
                
        return final_shapes_info

    def analyze(self):
        if not self.load_image(): return

        self.processed_img = self.img.copy()
        
        color_counts = {'Red': 0, 'Green': 0, 'Blue': 0}
        shape_counts = {'Cuboid': 0, 'Disk': 0, 'Ball': 0, 'Cube': 0, 'Cylinder': 0}

        for color_name in self.color_ranges.keys():
            raw_mask = self.get_color_mask(color_name)
            shapes_info = self.process_contours(raw_mask)
            
            for shape_name, ideal_contour in shapes_info:
                color_counts[color_name] += 1
                if shape_name in shape_counts:
                    shape_counts[shape_name] += 1
                
                # 绘制完美拟合的图形边框
                cv2.drawContours(self.processed_img, [ideal_contour], -1, self.draw_colors[color_name], 3)
                
                M = cv2.moments(ideal_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    text = f"{color_name}-{shape_name}"
                    cv2.putText(self.processed_img, text, (cx - 50, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
                    cv2.putText(self.processed_img, text, (cx - 50, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        print(f"\n✅ 识别完成！")
        print(f"图片中，红色有{color_counts['Red']}个，蓝色有{color_counts['Blue']}个，绿色有{color_counts['Green']}个；")
        print(f"长方体有{shape_counts['Cuboid']}个，圆盘有{shape_counts['Disk']}个，小球有{shape_counts['Ball']}个，"
              f"正方体有{shape_counts['Cube']}个，圆柱有{shape_counts['Cylinder']}个\n")

        self.show_interactive_result()

    def show_interactive_result(self):
        cv2.namedWindow('Vision Result', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Vision Result', 1000, 800)
        
        ui_img = self.processed_img.copy()
        cv2.putText(ui_img, "Press [T] to Tune Colors, [ESC] to Exit", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        cv2.imshow('Vision Result', ui_img)
        
        while True:
            key = cv2.waitKey(0) & 0xFF
            if key == 27:
                cv2.destroyAllWindows()
                break
            elif key == ord('t') or key == ord('T'):
                cv2.destroyAllWindows()
                self.interactive_tuner()
                self.analyze()
                break

    def interactive_tuner(self):
        print("\n" + "="*45)
        print("🛠️ 智能自修复模式")
        print("1. 鼠标左键点击目标颜色的物块。")
        print("2. 观察小窗口Mask，按【空格键】保存并进行下一颜色，按【ESC】取消。")
        print("="*45)

        for color_name in ['Red', 'Green', 'Blue']:
            print(f"\n👉 请在图像上点击【{color_name}】的物块...")
            
            def on_mouse(event, x, y, flags, param):
                if event == cv2.EVENT_LBUTTONDOWN:
                    h, s, v = map(int, self.hsv_img[y, x])
                    print(f"   [捕获] {color_name} 锚点 HSV: [{h}, {s}, {v}]")
                    lower = [max(0, h - 15), max(70, s - 60), max(70, v - 60)]
                    upper = [min(179, h + 15), min(255, s + 60), min(255, v + 60)]
                    self.color_ranges[color_name] = [(lower, upper)]
                    mask = self.get_color_mask(color_name)
                    cv2.imshow('Mask Preview (Press SPACE to confirm)', mask)

            cv2.namedWindow('Color Tuner', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Color Tuner', 1000, 800)
            cv2.setMouseCallback('Color Tuner', on_mouse)
            
            tune_img = self.img.copy()
            cv2.putText(tune_img, f"Click a {color_name} object, then press SPACE", 
                        (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,255), 3)
            cv2.imshow('Color Tuner', tune_img)
            
            while True:
                k = cv2.waitKey(0) & 0xFF
                if k == 32:
                    print(f"✅ {color_name} 阈值已更新！")
                    try:
                        cv2.destroyWindow('Mask Preview (Press SPACE to confirm)')
                    except:
                        pass
                    break
                elif k == 27:
                    break
            
            if k == 27: break
            
        cv2.destroyAllWindows()
        print("\n🔄 修复完成，正在重新执行智能分析...\n")

if __name__ == "__main__":
    analyzer = SmartVisionAnalyzer("1.jpg")
    analyzer.analyze()
