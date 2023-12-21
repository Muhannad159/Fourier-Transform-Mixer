from PyQt5.QtCore import *
import functools
import sys
from os import path

import cv2
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
)
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QRubberBand, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.uic import loadUiType

from image import Image
from imageMixer import ImageMixer
from overlay import overlay

FORM_CLASS, _ = loadUiType(
    path.join(path.dirname(__file__), "main.ui")
)  # connects the Ui file with the Python file


class MainApp(QMainWindow, FORM_CLASS):  # go to the main window in the form_class file
    def __init__(self, parent=None):  # constructor to initiate the main window  in the design
        """
        Constructor to initiate the main window in the design.

        Parameters:
        - parent: The parent widget, which is typically None for the main window.
        """

        super(MainApp, self).__init__(parent)
        self.setupUi(self)
        self.images_dict = {  # A dictionary to store Image instances and their associated widgets
            self.image_1_widget: [self.graphicsView_1,  # FT plot widget
                                  self.image_1_widget.objectName(),  # widget name
                                  None,  # image instance
                                  self.FT_combo_box_1,  # FT combo box
                                  None  # overlay instance
                                  ],
            self.image_2_widget: [self.graphicsView_2,  # FT plot widget
                                  self.image_2_widget.objectName(),  # widget name
                                  None,  # image instance
                                  self.FT_combo_box_2,  # FT combo box
                                  None  # overlay instance
                                  ],
            self.image_3_widget: [self.graphicsView_3,  # FT plot widget
                                  self.image_3_widget.objectName(),  # widget name
                                  None,  # image instance
                                  self.FT_combo_box_3,  # FT combo box
                                  None  # overlay instance
                                  ],
            self.image_4_widget: [self.graphicsView_4,  # FT plot widget
                                  self.image_4_widget.objectName(),  # widget name
                                  None,  # image instance
                                  self.FT_combo_box_4,  # FT combo box
                                  None  # overlay instance
                                  ],
        }
        self.images_counter = 0  # A counter to keep track of the number of images
        self.mixing_ratios = []
        self.active_widget = None  # A variable to store the active widget
        self.active_widget_name = None  # A variable to store the active widget name
        self.mode_combobox_list = [self.mode_comboBox_1, self.mode_comboBox_2, self.mode_comboBox_3,
                                   self.mode_comboBox_4]
        self.output_dictionary = {
            "Viewport 1": self.output_image_1,
            "Viewport 2": self.output_image_2,
        }
        self.sliders_list = [self.slider_1, self.slider_2, self.slider_3, self.slider_4]
        self.selection_modes_dict = {"Magnitude": ["Magnitude", "Phase"],
                                     "Phase": ["Magnitude", "Phase"],
                                     "Real": ["Real", "Imaginary"],
                                     "Imaginary": ["Real", "Imaginary"]
                                     }
        self.brightness = 0
        self.contrast = 0
        self.mouse_dragging = False  # Flag to track if the mouse is dragging

        self.initial_mouse_pos = QPoint(0, 0)
        self.progressBar.setValue(0)
        # Set up the QGraphicsScene for the view
        scene = QGraphicsScene()
        self.setScene(scene)

        self.setupImagesView()
        # Connect the mouse press event to the handle_buttons method
        self.handle_button()

    def mouse_press_event(self, event, w):
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, w)
        self.origin = event.pos()
        self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())
        self.rubber_band.show()

    def mouse_move_event(self, event, w):
        if self.rubber_band.isVisible():
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouse_press_event0(self, event, w):
        if event.button() == Qt.LeftButton:
            self.mouse_dragging = True
            self.initial_mouse_pos = event.pos()
            self.active_widget = w
            self.active_widget_name = w.objectName()

    def mouse_move_event0(self, event, w):
        if self.images_dict[w][2] is None:
            return

        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self.mouse_dragging = True
            self.initial_mouse_pos = event.pos()

        elif event.type() == QEvent.MouseMove and self.mouse_dragging:
            diff = event.pos() - self.initial_mouse_pos
            self.brightness = diff.x()  # Use positive values for right movement
            self.contrast = -diff.y()  # Invert for up movement
            self.apply_brightness_contrast(w)
            # self.initial_mouse_pos = event.pos()

        elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            self.mouse_dragging = False

    def mouse_release_event0(self, event, w):
        if event.button() == Qt.LeftButton:
            self.mouse_dragging = False

    def mouse_release_event(self, event, w):
        if self.rubber_band.isVisible():
            selected_region = self.rubber_band.geometry()
            # Do something with the selected region
            self.rubber_band.hide()
            # Get the dictionary key associated with the widget
            desired_key = next((key for key, value in self.images_dict.items() if value[0] == w and value[2]), None)
            region_selected = self.images_dict[desired_key][2].get_selected_region(selected_region,
                                                                                   self.images_dict[desired_key][
                                                                                       2].get_magnitude_spectrum())

    def connect_comboboxes(self, is_connected=True):
        if is_connected:
            for i in range(1, 5):
                combobox = getattr(self, f"mode_comboBox_{i}")
                combobox.currentIndexChanged.connect(functools.partial(self.handle_mode_combobox_change, i))
        else:
            for i in range(1, 5):
                combobox = getattr(self, f"mode_comboBox_{i}")
                combobox.currentIndexChanged.disconnect()

    def handle_button(self):
        # Connect the clicked signal to the browse_image method
        for slider in self.sliders_list:
            slider.valueChanged.connect(self.mix_images)
        self.pushButton_reset.clicked.connect(self.reset_brightness_contrast)

        # Connect mouseDoubleClickEvent for each widget
        for widget, value in self.images_dict.items():
            widget.mouseDoubleClickEvent = lambda event, w=widget: self.on_mouse_click(event, w)

            # value[0].mousePressEvent = lambda event, w=value[0]: self.mouse_press_event(event, w)
            # value[0].mouseMoveEvent = lambda event, w=value[0]: self.mouse_move_event(event, w)
            # value[0].mouseReleaseEvent = lambda event, w=value[0]: self.mouse_release_event(event, w)
            widget.mousePressEvent = lambda event, w=widget: self.mouse_press_event0(event, w)
            widget.mouseMoveEvent = lambda event, w=widget: self.mouse_move_event0(event, w)
            widget.mouseReleaseEvent = lambda event, w=widget: self.mouse_release_event0(event, w)

            # Connect currentIndexChanged for each QComboBox using a loop
        for key, values in self.images_dict.items():
            values[3].currentIndexChanged.connect(functools.partial(self.plot_FT, values[0], values[3]))
        self.connect_comboboxes()
        # Connect the currentIndexChanged signal to the change_area_region method
        self.area_taken_region.currentIndexChanged.connect(lambda : self.overlay_instance.change_area_region)
    def reset_brightness_contrast(self, widget):
        self.brightness = 0
        self.contrast = 0
        self.apply_brightness_contrast(self.active_widget)

    def apply_brightness_contrast(self, widget, alpha=1.0, beta=0):
        if self.images_dict[widget][2] is None:
            return

        image = np.float32(self.images_dict[widget][2].get_image_data())
        alpha = 1.0 + self.contrast / 100.0
        beta = self.brightness
        image = alpha * (image - 128) + 128 + beta
        image = np.clip(image, 0, 255).astype("uint8")

        hight, width = image.shape
        self.plot_images(width, hight, widget, image)

    def setScene(self, scene):
        # Set the scene for each widget
        for key, value in self.images_dict.items():
            key.setScene(scene)
            # value[0].setScene(scene)

    def setupImagesView(self):

        for widget_name, value in self.images_dict.items():
            break
            value[0].ui.histogram.hide()
            value[0].ui.roiBtn.hide()
            value[0].ui.menuBtn.hide()
            value[0].ui.roiPlot.hide()
            value[0].getView().setAspectLocked(False)
            value[0].view.setAspectLocked(False)

    def on_mouse_click(self, event, widget):
        self.active_widget = widget
        self.active_widget_name = widget.objectName()
        if event.button() == pg.QtCore.Qt.LeftButton:
            self.update_active_widget(widget)
            self.browse_image(widget)
        if event.button() == pg.QtCore.Qt.RightButton:
            self.delete_image(widget)

    def update_active_widget(self, active_widget):
        # Define a list containing all the widgets you want to manage
        widgets = [
            self.image_1_widget,
            self.image_2_widget,
            self.image_3_widget,
            self.image_4_widget
        ]

        # Iterate through each widget
        for widget in widgets:
            # Check if the current widget is the active_widget
            widget_active = widget == active_widget

            # Set the stylesheet based on whether the widget is active or not
            widget.setStyleSheet(
                "border: 1px solid  rgb(0, 133, 255);" if widget_active else "border: 1px solid rgba(0, 0, 0, 0.20);"
            )

        # Update the active state variables based on the active_widget
        self.image_1_widget_active, self.image_2_widget_active, self.image_3_widget_active, self.image_4_widget_active = [
            widget == active_widget for widget in widgets
        ]

    def browse_image(self, widget):
        if self.images_counter == 4:
            return
        self.images_counter += 1
        # browse and get the image path as .jpg or .gif or .png or .jpeg or .svg
        image_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.jpg *.gif *.png *.jpeg *.svg)"
        )
        image_instance = Image(str(image_path))
        if self.images_counter != 1:
            min_width, min_height = self.get_min_size()
            image_instance.set_image_size(min_width, min_height)
        # Update the third element of the list associated with self.active_widget
        self.images_dict[self.active_widget][2] = image_instance
        self.display_image()
        # Call Plot FT
        self.plot_FT(self.images_dict[self.active_widget][0], self.images_dict[self.active_widget][3])

    def display_image(self):
        min_width, min_height = self.get_min_size()

        for widget_name, value in self.images_dict.items():
            if value[2] is None:
                continue
            value[2].set_image_size(min_width, min_height)
            image_data = value[2].get_image_data()
            resized_image = cv2.resize(image_data, (min_width, min_height))
            height, width = resized_image.shape
            image_data = bytes(resized_image.data)
            self.plot_images(width, height, widget_name, image_data, True)

    def plot_images(self, width, height, widget_name, image_data, is_input_image=False):
        bytes_per_line = width

        q_image = QImage(
            image_data,
            width,
            height,
            bytes_per_line,
            QImage.Format_Grayscale8,
        )
        pixmap = QPixmap.fromImage(q_image)

        image_scene = self.create_image_scene(widget_name)
        image_scene.clear()

        pixmap_item = QGraphicsPixmapItem(pixmap)
        image_scene.addItem(pixmap_item)

        if is_input_image:
            # Set the size of the view to match the size of the image
            widget_name.setFixedSize(width, height)

            # Disable scroll bars
            widget_name.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            widget_name.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            # Set the size policy to ignore the size hint
            widget_name.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        else:
            # Fit the view to the pixmap item's bounding rectangle without keeping the aspect ratio
            widget_name.fitInView(pixmap_item.boundingRect(), Qt.IgnoreAspectRatio)

        # Set the margins to zero
        widget_name.setContentsMargins(0, 0, 0, 0)

    def create_image_scene(self, image_view):
        # Create the QGraphicsScene and set it for the respective image widget
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

    def plot_FT(self, widget, combobox):
        # Get the current text of the combobox
        current_text = combobox.currentText()

        area_region = self.area_taken_region.currentText()
        # Get the dictionary key associated with the widget
        desired_key = next((key for key, value in self.images_dict.items() if value[0] == widget and value[2]), None)

        # If desired_key is None, then there was no matching widget in the dictionary
        if desired_key is None:
            return

        # Create an instance of the overlay class
        self.overlay_instance = overlay(self.images_dict[desired_key][0],
                                        self.images_dict[desired_key][2],
                                        current_text,
                                        area_region,
                                        )
        # Connect the sig_ROI_changed signal to the mix_images method
        self.overlay_instance.sig_emitter.sig_ROI_changed.connect(self.mix_images)
        # Connect the currentIndexChanged signal to the change_area_region method
        self.area_taken_region.currentIndexChanged.connect(self.overlay_instance.change_area_region)
        # Update the dictionary
        self.images_dict[desired_key][4] = self.overlay_instance
        self.mix_images()

    def plot_image_view(self, image_data, widget):

        widget.ui.roiPlot.hide()
        # Set the image data
        widget.setImage(image_data)

    def delete_image(self, widget):
        # Check if the key is in the dictionary
        if widget in self.images_dict:
            # Set the third element of the list associated with the key to None
            self.images_dict[widget][2] = None

            # Clear the QGraphicsScene of the widget
            widget.scene().clear()

            # Decrement the images_counter
            self.images_counter -= 1

    def get_min_size(self):
        # Get the minimum width and height of all images in the dictionary
        min_width = min_height = sys.maxsize
        for widget_name, value in self.images_dict.items():
            if value[2] is None:
                continue
            image_data = value[2].get_image_data()
            h, w = image_data.shape
            min_width = min(min_width, w)
            min_height = min(min_height, h)
        return min_width, min_height

    def mix_images(self):
        """Mix images using the slider value"""
        # Implement logic to mix images using the slider value

        self.progressBar.setValue(0)
        if self.images_dict:
            min_width, min_height = self.get_min_size()
            images_lists = []

            for image_list in self.images_dict.values():

                if image_list[2] is None:
                    continue
                else:
                    image_list[2].set_image_size(min_width, min_height)
                    images_lists.append(image_list[2])

                image_list[4].update_mask_size()

            mix = ImageMixer(images_lists)
            slider_values, mode = self.get_slider_mode_values()
            self.progressBar.setValue(25)

            output_image = mix.mix_images(slider_values, min_width, min_height, mode)
            self.progressBar.setValue(50)
            # Create a QImage from the output_image
            bytes_per_line = min_width
            image_data = bytes(output_image.data)
            current_view = self.comboBox_2.currentText()
            self.progressBar.setValue(75)
            self.plot_images(min_width, min_height, self.output_dictionary[current_view], image_data)
            self.progressBar.setValue(100)

    def get_slider_mode_values(self):

        """Get the slider values and normalize them"""
        # Get the slider values
        slider_values = [
            self.slider_1.value(),
            self.slider_2.value(),
            self.slider_3.value(),
            self.slider_4.value(),
        ]
        # Normalize the slider values
        normalized_slider_values = [value / 100 for value in slider_values]
        mode = []
        for combox_mode in self.mode_combobox_list:
            mode.append(combox_mode.currentText())
        return normalized_slider_values, mode

    def handle_mode_combobox_change(self, index):
        # Get the current combobox that triggered the signal
        current_combobox = self.sender()
        print(current_combobox.objectName())

        # Get the current text of the combobox
        current_text = current_combobox.currentText()

        # Disconnect the signal temporarily
        self.connect_comboboxes(False)

        # Update the items of the remaining combo-boxes
        for i in range(1, 5):
            if i != index:
                combobox = getattr(self, f"mode_comboBox_{i}")
                combobox.clear()
                combobox.addItems(self.selection_modes_dict[current_text])

        # Reconnect the signal
        self.connect_comboboxes(True)


def main():  # method to start app
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()  # infinte Loop


if __name__ == "__main__":
    main()
