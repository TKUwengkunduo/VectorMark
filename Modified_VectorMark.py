import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import json
import os
import math
from cv2 import aruco
import cv2
import numpy as np

class Annotation:
    def __init__(self, image_path, color_image_path):
        self.image_path = image_path
        self.color_image_path = color_image_path
        self.start_point = None
        self.end_point = None
        self.vector_line_id = None
        self.robot_angle = 0

    def set_start_point(self, x, y):
        self.start_point = (x, y)

    def set_end_point(self, x, y):
        self.end_point = (x, y)

    def set_aruco_direction(self, top_right, top_left):
        # 計算ArUco標記的Y軸方向（從底部到頂部）
        # self.aruco_y_direction = (top_left[0] - bottom_left[0], top_left[1] - bottom_left[1])
        # 计算ArUco标记的X轴方向（从左到右）
        self.aruco_x_direction = (top_right[0] - top_left[0], top_right[1] - top_left[1])

    def calculate_angle(self, click_point):
        if self.start_point and self.end_point and self.aruco_x_direction:
            vector_click = (click_point[0] - self.start_point[0], click_point[1] - self.start_point[1])
            # Normalize ArUco X direction
            aruco_x_direction_norm = self.aruco_x_direction / np.linalg.norm(self.aruco_x_direction)

            # Calculate the angle
            dot_product = np.dot(vector_click, aruco_x_direction_norm)
            angle_radians = np.arccos(dot_product / np.linalg.norm(vector_click))
            angle_degrees = np.degrees(angle_radians)

            # Determine if the click is above or below the ArUco's X axis
            if np.cross(aruco_x_direction_norm, vector_click) < 0:
                angle_degrees = -angle_degrees

            self.robot_angle = angle_degrees

    def draw_annotation(self, canvas):
        if self.start_point and self.end_point:
            if self.vector_line_id:
                canvas.delete(self.vector_line_id)
            self.vector_line_id = canvas.create_line(self.start_point[0], self.start_point[1],
                                                     self.end_point[0], self.end_point[1], fill="blue", width=2)

class ImageAnnotationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Annotation Tool")
        self.setup_ui()
        self.annotations = []
        self.current_image_index = 0
        self.current_annotation = None

    def setup_ui(self):
        self.canvas = tk.Canvas(self.root, width=1280, height=720)
        self.canvas.pack(side=tk.LEFT)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.folder_btn = tk.Button(btn_frame, text="Open Folder", command=self.load_folder)
        self.folder_btn.pack(fill=tk.X)

        self.prev_btn = tk.Button(btn_frame, text="<< Prev", command=self.show_previous_image)
        self.prev_btn.pack(fill=tk.X)

        self.next_btn = tk.Button(btn_frame, text="Next >>", command=self.show_next_image)
        self.next_btn.pack(fill=tk.X)

        self.save_btn = tk.Button(btn_frame, text="Save Data", command=self.save_annotations)
        self.save_btn.pack(fill=tk.X)

        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def load_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.annotations = []  # Reset annotations for new folder
            self.image_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.startswith('zenith_') and f.endswith(('.png', '.jpg', '.jpeg'))]
            self.current_image_index = 0
            self.display_image()

    def display_image(self):
        if self.current_image_index < len(self.image_paths):
            color_img_path = self.image_paths[self.current_image_index]
            original_img_path = color_img_path.replace("zenith_", "")
            self.current_annotation = Annotation(original_img_path, color_img_path)
            self.annotations.append(self.current_annotation)

            # 从文件读取图像并转换为 OpenCV 格式
            image = Image.open(color_img_path)
            # image = image.resize((600, 400))
            open_cv_image = np.array(image)
            open_cv_image = open_cv_image[:, :, ::-1].copy()  # RGB to BGR

            # 调用 ArUco 检测方法
            img_with_aruco = self.detect_and_draw_aruco(open_cv_image)
            img_with_aruco = Image.fromarray(cv2.cvtColor(img_with_aruco, cv2.COLOR_BGR2RGB))
            img_with_aruco = ImageTk.PhotoImage(img_with_aruco)

            self.canvas.create_image(0, 0, anchor=tk.NW, image=img_with_aruco)
            self.canvas.image = img_with_aruco
            self.current_annotation.draw_annotation(self.canvas)
    
    def detect_and_draw_aruco(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 定义 ArUco 字典
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_7X7_1000)
        aruco_params = cv2.aruco.DetectorParameters()
        
        # 偵測標記
        corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)

        # 如果找到标记，绘制标记并估计姿态
        if ids is not None:
            for i, marker_id in enumerate(ids.flatten()):
                if marker_id == 8:
                    # 计算ArUco标记的中心点
                    center_point = tuple(np.mean(corners[i][0], axis=0).astype(int))
                    # 保存中心点作为起始点
                    self.current_annotation.set_start_point(center_point[0], center_point[1])
                    # 绘制标记的中心点
                    cv2.circle(image, center_point, 5, (0, 255, 0), -1)
                    # 计算并保存ArUco标记的Y軸方向
                    # self.current_annotation.set_aruco_direction(corners[i][0][0], corners[i][0][3])  # Top left and bottom left corners
                    self.current_annotation.set_aruco_direction(corners[i][0][1], corners[i][0][0])  # Top left and top right corners
                    # 绘制检测到的ArUco标记
                    cv2.aruco.drawDetectedMarkers(image, [corners[i]], ids[i].reshape(-1, 1))

                    # # 假设的相机矩阵和失真系数
                    camera_matrix = np.array([[914.233, 0, 640.8177],  # 假设焦距为600，图像中心为(640, 360)
                                            [0, 912, 376],
                                            [0, 0, 1]], dtype=np.float32)
                    dist_coeffs = np.array([0.0, 0.0, 0.0, 0.0, 0.0])  # 假设无失真
                    rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, 0.05, camera_matrix, dist_coeffs)
                    cv2.drawFrameAxes(image, camera_matrix, dist_coeffs, rvecs[i], tvecs[i], 0.1)
        return image


    def show_previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.display_image()

    def show_next_image(self):
        if self.current_image_index < len(self.image_paths) - 1:
            self.current_image_index += 1
            self.display_image()

    def on_canvas_click(self, event):
        if self.current_annotation.start_point:
            # 用户点击定义新的结束点，并创建向量
            click_point = (event.x, event.y)
            self.current_annotation.set_end_point(event.x, event.y)
            self.current_annotation.calculate_angle(click_point)
            self.current_annotation.draw_annotation(self.canvas)
            messagebox.showinfo("Angle", f"Angle to clicked point: {self.current_annotation.robot_angle} degrees")
        else:
            messagebox.showinfo("Info", "Please wait for the ArUco marker to be detected as the starting point.")

    def save_annotations(self):
        folder_path = os.path.dirname(self.annotations[0].color_image_path)
        json_file_path = os.path.join(folder_path, "data.json")
        if not os.path.exists(json_file_path):
            messagebox.showinfo("Error", "data.json not found in the selected folder.")
            return

        with open(json_file_path, "r") as f:
            data = json.load(f)

        updated = False
        for annotation in self.annotations:
            vector_magnitude = annotation.get_vector_magnitude()
            if vector_magnitude is not None:
                for item in data:
                    if item["image"] == os.path.basename(annotation.image_path):
                        item["output_direction"] = vector_magnitude
                        updated = True

        if updated:
            with open(json_file_path, "w") as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Info", "Data updated successfully in data.json")
        else:
            messagebox.showinfo("Info", "No updates made to data.json")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageAnnotationApp(root)
    root.mainloop()
