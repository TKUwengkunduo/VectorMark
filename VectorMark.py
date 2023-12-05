import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import json
import os
import math

class Annotation:
    def __init__(self, image_path):
        self.image_path = image_path
        self.start_point = None
        self.end_point = None

    def set_start_point(self, x, y):
        self.start_point = (x, (y*-1)+540)

    def set_end_point(self, x, y):
        self.end_point = (x, (y*-1)+540)

    def get_vector_magnitude(self):
        if self.start_point and self.end_point:
            x0 = self.start_point[0]
            y0 = self.start_point[1]
            x1 = self.end_point[0]
            y1 = self.end_point[1]
            if(x0 == x1):
                x0 += 1    # to avoid division by zero
            slope = (y1 - y0)/(x1 - x0)
            # slope = (self.end_point[1] - self.start_point[1]) / (self.end_point[0] - self.start_point[0])
            rad = math.atan(slope)
            deg = math.degrees(rad)
            if((x1 > x0)and(y1 > y0)):      # 1st Quadrant
                deg360 = deg
            elif((x1 < x0)and(y1 > y0)):    # 2nd Quadrant
                deg360 = 180-(deg*-1)
            elif((x1 < x0)and(y1 < y0)):    # 3rd Quadrant
                deg360 = 180+deg
            elif((x1 > x0)and(y1 < y0)):    # 4th Quadrant
                deg360 = 360-(deg*-1)
            else:
                print("Weird Quadrant Problem")
            print("start", self.start_point, ", end", self.end_point, ", slope =", slope, ", radian =", rad, ", degrees =", deg, ", degrees360 =", deg360)
            # return (self.end_point[1] - self.start_point[1]) / (self.end_point[0] - self.start_point[0])
            return(deg360)
        return None

class ImageAnnotationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Annotation Tool")
        self.setup_ui()
        self.annotations = []
        self.current_image_index = 0
        self.current_annotation = None

    def setup_ui(self):
        # self.canvas = tk.Canvas(self.root, width=600, height=400)
        self.canvas = tk.Canvas(self.root, width=960, height=540)
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
            self.image_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
            self.current_image_index = 0
            self.display_image()

    def display_image(self):
        if self.current_image_index < len(self.image_paths):
            img_path = self.image_paths[self.current_image_index]
            self.current_annotation = Annotation(img_path)
            self.annotations.append(self.current_annotation)
            img = Image.open(img_path)
            # img = ImageTk.PhotoImage(img.resize((600, 400)))
            img = ImageTk.PhotoImage(img.resize((960, 540)))
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.canvas.image = img

    def show_previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.display_image()

    def show_next_image(self):
        if self.current_image_index < len(self.image_paths) - 1:
            self.current_image_index += 1
            self.display_image()

    def on_canvas_click(self, event):
        if self.current_annotation:
            if not self.current_annotation.start_point:
                self.current_annotation.set_start_point(event.x, event.y)
                self.canvas.create_oval(event.x - 5, event.y - 5, event.x + 5, event.y + 5, fill="red")
            elif not self.current_annotation.end_point:
                self.current_annotation.set_end_point(event.x, event.y)
                self.canvas.create_line(self.current_annotation.start_point[0], (self.current_annotation.start_point[1]*-1)+540, event.x, event.y, fill="blue")
                # print(self.current_annotation.start_point[0], self.current_annotation.start_point[1], event.x, (event.y*-1)+540)

    def save_annotations(self):
        annotations_data = []
        for annotation in self.annotations:
            vector_magnitude = annotation.get_vector_magnitude()
            if vector_magnitude is not None:
                annotations_data.append({
                    "image": os.path.basename(annotation.image_path),
                    "input_direction": vector_magnitude,
                    "output_direction": vector_magnitude
                })

        if annotations_data:
            folder_name = os.path.basename(os.path.dirname(self.annotations[0].image_path))
            with open(f"{folder_name}.json", "w") as f:
                json.dump(annotations_data, f, indent=4)
            messagebox.showinfo("Info", "Data saved successfully")
        else:
            messagebox.showinfo("Info", "No data to save")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageAnnotationApp(root)
    root.mainloop()
