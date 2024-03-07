import cv2
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import math
import csv
from datetime import datetime
import matplotlib.colors as mcolors


class ImageEditor:
    def __init__(self, root, image_path):
        self.color_dict = {'x': 'blue', 'y': 'green', 'z': 'orange', 'r': 'yellow', 'h': 'red', 'm': 'white'}
        self.r_line = 0
        self.m_line = 0
        self.real_len = 0
        self.root = root
        self.root.title("Image Editor")

        self.image_path = image_path
        self.image = cv2.imread(image_path)
        self.image = cv2.resize(self.image, (640, 480))
        self.image_copies = [self.image.copy()]
        self.display_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(self.display_image))

        # Create frame
        self.frame = tk.Frame(root)
        self.frame.pack()

        # Creating and Placing canvas
        self.canvas = tk.Canvas(self.frame, width=self.image.shape[1], height=self.image.shape[0])
        self.canvas.pack(side=tk.LEFT)

        # Add Image
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
                
        # Creat output text box
        self.output_text = scrolledtext.ScrolledText(self.frame, width=40, height=30, bg="lightgrey", font=("Helvetica", 10), wrap=tk.WORD)
        self.output_text.pack(side=tk.BOTTOM, anchor="center", fill="y", padx='100', pady='60')
        
        # Add Button
        self.pick_x_button = tk.Button(self.frame, text="X - axis", command=lambda: self.pick_points('x'), fg="blue")
        self.pick_x_button.pack(side=tk.LEFT, anchor="nw")

        self.pick_y_button = tk.Button(self.frame, text="Y - axis", command=lambda: self.pick_points('y'), fg="green")
        self.pick_y_button.pack(side=tk.LEFT, anchor="nw")

        self.pick_z_button = tk.Button(self.frame, text="Z - axis", command=lambda: self.pick_points('z'), fg="orange")
        self.pick_z_button.pack(side=tk.LEFT, anchor="nw")
        
        self.pick_r_button = tk.Button(self.frame, text="Reference", command=lambda: [self.pick_points('r')], fg="yellow")
        self.pick_r_button.pack(side=tk.LEFT, anchor="nw")
        self.pick_h_button = tk.Button(self.frame, text="Helper", command=lambda: self.pick_points('h'), fg="red")
        self.pick_h_button.pack(side=tk.LEFT, anchor="nw")
        self.pick_m_button = tk.Button(self.frame, text="Measure", command=lambda: self.pick_points('m'), fg="white")
        self.pick_m_button.pack(side=tk.LEFT, anchor="nw")
        
        self.store_button = tk.Button(root, text="Store", command=self.store_data)
        self.store_button.pack(side=tk.RIGHT, anchor="n")
        self.clear_button = tk.Button(root, text="Clear", command=self.clear_lines)
        self.clear_button.pack(side=tk.RIGHT, padx=1)

        # Points for 'x~m' group
        self.x_points = [] 
        self.y_points = [] 
        self.z_points = [] 
        self.r_points = []
        self.h_points = []    
        self.m_points = []

        self.x_lines = [] 
        self.y_lines = [] 
        self.z_lines = []
        self.r_lines = [] 
        self.h_lines = [] 
        self.m_lines = []
        
        self.current_group = None
        self.csv_filename = "lines_data.csv" # CSV file to store (time, image file, line coordinates, etc.)

        self.points = []

    def pick_points(self, group):
        self.current_group = group
        self.points = []  # Reset points when a new group is selected
        self.canvas.bind("<Button-1>", self.get_point)

    def get_point(self, event):
        x, y = event.x, event.y
        self.points.append((x, y))

        # Draw a dot at the picked point with group-specific color
        point_color= self.color_dict.get(self.current_group)
        rgb_color = mcolors.to_rgb(point_color)
        point_color = (int(rgb_color[2] * 255), int(rgb_color[1] * 255), int(rgb_color[0] * 255))

        cv2.circle(self.image, (x, y), 3, point_color, -1)
        getattr(self, f"{self.current_group}_points").append((x, y))
        
        # Display coordinates in the output text box
        if len(self.points) == 1:
            self.output_text.insert(tk.END, f"\n<< {self.current_group}_Line >>\n")
            self.output_text.insert(tk.END, f"Start Point : ({x}, {y})\n")

        if len(self.points) == 2:
            # Draw a line between the two dots with group-specific color
            line_color = self.color_dict.get(self.current_group)
            rgb_color = mcolors.to_rgb(line_color)
            line_color = (int(rgb_color[2] * 255), int(rgb_color[1] * 255), int(rgb_color[0] * 255))
            cv2.line(self.image, self.points[0], self.points[1], line_color, 2)
            # calculate pixel line distance
            distance_pixels = round(math.sqrt((self.points[1][0] - self.points[0][0])**2 + (self.points[1][1] - self.points[0][1])**2), 2)
            
            # Store the line coordinates for the current group
            getattr(self, f"{self.current_group}_lines").append(self.points)
            self.points = []
            self.image_copies.append(self.image.copy())
            
            # Display coordinates in the output text box
            self.output_text.insert(tk.END, f"End Point : ({x}, {y})\n")
            self.output_text.insert(tk.END, f"Line distance : {distance_pixels}\n")
                        
            # Save Data for Length (= Pixel Length on Frame) Measurement > Temporary Version
            if self.current_group=='r':
                self.r_line = distance_pixels
                self.get_()
            if self.current_group=='m':
                self.m_line = distance_pixels
                self.cal_height()

            # Reset points after drawing a line
            self.points = []

        # Update the displayed image
        self.display_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(self.display_image))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
    def get_input(self):
        input_text = self.output_text.get("1.0", tk.END)  # Import text entered with [reference length]
        last_line_words = input_text.split()
        last_word = last_line_words[-1] if last_line_words else ""
        last_word = float(last_word)
        self.real_len = last_word
        self.output_text.insert(tk.END, f"\n")
        
        # Test if the entered [reference length] is successfully imported
        # print("Get", self.real_len)
        
        self.get_input_button.destroy()
        
    def get_(self):
        # button to hand over the reference length entered in the output text box
        self.get_input_button = tk.Button(self.root, text="Get Input", command=lambda: self.get_input(), fg="red")
        self.get_input_button.pack(side=tk.RIGHT)
        self.output_text.insert(tk.END, f"\nInput real length : ")
        
        
    def cal_height(self):
        scale_factor = self.real_len / self.r_line
        est_height = self.m_line * scale_factor
        self.output_text.insert(tk.END, f"\n<< result >>\nEstimate real length : {est_height}")
        
    def store_data(self):
        image_name = self.image_path.split('/')[-1]  # Get the image file name
        
        with open(self.csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            today = datetime.today().strftime("<< %Y/%m/%d %H:%M:%S >>")
            writer.writerow([today])

        # Iterate over all groups ('x', 'y', 'z', 'r', 'h', 'm') and store the corresponding lines
        for group in ['x', 'y', 'z', 'r', 'h', 'm']:
            group_points = getattr(self, f"{group}_points")

            with open(self.csv_filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                for i in range(0, len(group_points), 2):
                    x1, y1 = group_points[i]
                    x2, y2 = group_points[i + 1]
                    writer.writerow([image_name, group, x1, y1, x2, y2])
                    
        self.output_text.insert(tk.END, f"\n<< == Save successfully == >>")
        
    def clear_lines(self):
        if self.current_group is not None:
            # Remove the last line for the currently selected group
            group_lines = getattr(self, f"{self.current_group}_lines")
            if group_lines:
                group_lines.pop()

            # Remove the last two points for the currently selected group
            group_points = getattr(self, f"{self.current_group}_points")
            if len(group_points) >= 2:
                group_points.pop()
                group_points.pop()

            self.image = cv2.imread(self.image_path)
            self.image = cv2.resize(self.image, (640, 480))
            self.update_displayed_image()
            
    def update_displayed_image(self):
            for group in ['x', 'y', 'z', 'r', 'h', 'm']:
                group_points = getattr(self, f"{group}_points")
                group_lines = getattr(self, f"{group}_lines")
                line_color = self.color_dict.get(group)
                rgb_color = mcolors.to_rgb(line_color)
                line_color = (int(rgb_color[2] * 255), int(rgb_color[1] * 255), int(rgb_color[0] * 255))

                # Redraw all points for the current group
                for point in group_points:
                    x, y = point
                    cv2.circle(self.image, (x, y), 3, line_color, -1)

                # Redraw all lines for the current group
                for line in group_lines:
                    x1, y1 = line[0]
                    x2, y2 = line[1]
                    cv2.line(self.image, (x1, y1), (x2, y2), line_color, 2)

            self.display_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(self.display_image))
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)