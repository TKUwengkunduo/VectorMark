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

    def calculate_angle(self, click_point):
        if self.start_point and self.end_point:
            # Create vectors from robot center to Y axis and to clicked point
            vector_robot_to_y = (0, -1)
            vector_robot_to_click = (click_point[0] - self.start_point[0], self.start_point[1] - click_point[1])

            # Calculate the angle between vectors
            dot_product = vector_robot_to_y[0] * vector_robot_to_click[0] + vector_robot_to_y[1] * vector_robot_to_click[1]
            magnitude = (math.sqrt(vector_robot_to_click[0]**2 + vector_robot_to_click[1]**2))
            angle = math.degrees(math.acos(dot_product / magnitude))

            # Determine if the click is to the left or right of the robot's Y axis
            if vector_robot_to_click[0] < 0:
                angle = -angle

            self.robot_angle = angle

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
        aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_7X7_250)
        aruco_params = cv2.aruco.DetectorParameters_create()
        
        # 偵測標記
        corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)

        # 如果找到标记，绘制标记并估计姿态
        if ids is not None:
            for i, corner in enumerate(corners):
                if ids[i] == 8:  # 如果是编号为8的标记
                    # 计算ArUco标记的中心点
                    center_point = tuple(np.mean(corner[0], axis=0).astype(int))
                    # 保存中心点作为起始点
                    self.current_annotation.set_start_point(center_point[0], center_point[1])
                    # 绘制标记的中心点
                    cv2.circle(image, center_point, 5, (0, 255, 0), -1)
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
