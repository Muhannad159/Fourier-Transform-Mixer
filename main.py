from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.uic import loadUiType
import pyqtgraph as pg

import numpy as np
import pandas as pd

from image import Image

import os
import sys
from os import path
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QSlider
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
import sys
from image import Image
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtCore import QRectF
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtGui import QPainter

FORM_CLASS, _ = loadUiType(path.join(path.dirname(__file__), "main.ui"))  # connects the Ui file with the Python file

class MainApp(QMainWindow, FORM_CLASS): # go to the main window in the form_class file

    def __init__(self, parent=None):  # constructor to initiate the main window  in the design
        """
                 Constructor to initiate the main window in the design.

                 Parameters:
                 - parent: The parent widget, which is typically None for the main window.
        """
        super(MainApp, self).__init__(parent)
        self.setupUi(self)
        self.images_dict = {}  # A dictionary to store Image instances
        self.images_counter = 0 # A counter to keep track of the number of images
        self.browsing_pushButton.clicked.connect(self.browse_image)
        # Load the original image
        original_pixmap = QPixmap("contrast.png")

        # Resize the image to 5x5 pixels
        resized_pixmap = original_pixmap.scaled(35, 35, Qt.KeepAspectRatio)


        # Calculate the initial position
        self.calculate_position()

        # Create a QLabel and set its size and position
        self.image_label = QLabel(self)
        self.image_label.setGeometry(self.center_x, self.top_y, resized_pixmap.width(), resized_pixmap.height())
        self.image_label.setPixmap(resized_pixmap)

        # Store the initial window state
        self.prev_window_state = self.windowState()

        # Create a QGraphicsScene for the view
        self.image_1_scene = QGraphicsScene(self.image_1_widget)
        self.image_1_widget.setScene(self.image_1_scene)


    def calculate_position(self):
        # Calculate the position to center at the top
        if self.isMaximized():
            self.center_x = 824
        else:
            self.center_x = 585
        self.top_y = 0  # Set the top y-coordinate as an instance variable

    def changeEvent(self, event):
        if event.type() == event.WindowStateChange:
            # Check if the window state has changed
            if self.prev_window_state != self.windowState():
                # Recalculate the position when the window state changes (e.g., maximized)
                self.calculate_position()
                self.image_label.setGeometry(self.center_x, self.top_y, self.image_label.pixmap().width(),
                                             self.image_label.pixmap().height())

                # Update the previous window state
                self.prev_window_state = self.windowState()

     
    def browse_image(self):
        if self.images_counter == 4:
            return
        self.images_counter += 1
        # browse and get the image path as .jpg or .gif or .png or .jpeg or .svg
        image_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.jpg *.gif *.png *.jpeg *.svg)")
        self.image_instance = Image(str(image_path))
        image_name = f"image_{self.images_counter}"
        # Store the ImageProcessor instance in the dictionary
        self.images_dict[image_name] = self.image_instance
        self.display_image()
        #print(image_path)

    def display_image(self):
            image_data = self.image_instance.get_image_data()
            h, w = image_data.shape
            bytes_per_line = w
            q_image = QImage(image_data.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(q_image)
            # Get the corresponding image widget
            image_widget = getattr(self, f"image_{self.images_counter}_widget")
            # Create the QGraphicsScene and set it for the respective image widget
            image_scene = self.create_image_scene(image_widget)
            # Clear the scene before adding a new item
            image_scene.clear()
            # Create a QGraphicsPixmapItem and add it to the scene
            pixmap_item = QGraphicsPixmapItem(pixmap)
            image_scene.addItem(pixmap_item)
            # Set the initial view to fit the scene content
            initial_view_rect = QRectF(0, 0, w, h)
            image_widget.setSceneRect(initial_view_rect)
            image_widget.fitInView(initial_view_rect, Qt.KeepAspectRatio)

    def create_image_scene(self, image_view):
            image_scene = QGraphicsScene(image_view)
            image_view.setScene(image_scene)
            # Set size policy and other properties as needed
            image_view.setAlignment(Qt.AlignCenter)
            image_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # Set render hints for smoother rendering (optional)
            image_view.setRenderHint(QPainter.Antialiasing, True)
            image_view.setRenderHint(QPainter.SmoothPixmapTransform, True)
            image_view.setRenderHint(QPainter.HighQualityAntialiasing, True)
            return image_scene

            
                

    # def mix_images(self):
    #     # Implement logic to mix images using the slider value
    #     if self.images_list:
    #         mix_ratio = self.slider.value() / 100.0
    #         mixed_image_data = self.image_instnace.apply_mixed_transform(self.images_list, mix_ratio)
    #         h, w = mixed_image_data.shape
    #         bytes_per_line = w
    #         q_image = QImage(mixed_image_data.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
    #         pixmap = QPixmap.fromImage(q_image)
    #         self.image_label.setPixmap(pixmap)

def main():  # method to start app
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()  # infinte Loop


if __name__ == '__main__':
    main()








