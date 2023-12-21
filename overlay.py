from PyQt5.QtWidgets import QWidget, QFileDialog
import pyqtgraph as pg
import numpy as np
import cv2
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QSlider
from PyQt5.QtCore import Qt, QRectF, QObject, pyqtSignal
from PyQt5.QtCore import QPointF


class SignalEmitter(QObject):
    sig_ROI_changed = pyqtSignal()


class overlay:
    def __init__(self, plot_widget, img_data, new_img_data, mode, area_region):
        self.data = img_data
        self.new_img_data = new_img_data
        self.plot_ft = plot_widget
        self.mode = mode
        self.area_region = area_region


        # Signal emitter class to emit custom signals
        self.sig_emitter = SignalEmitter()
        shifted_data = self.data.get_shifted()
        self.ROI_Maxbounds = QRectF(0, 0, shifted_data[self.mode].shape[1], shifted_data[self.mode].shape[0])

        self.plot_ft.clear()  # This will clear all items from the PlotWidget
        self.ft_view = self.plot_ft.addViewBox()
        self.ft_view.setAspectLocked(True)
        self.ft_view.setMouseEnabled(x=False, y=False)

        self.img_item_ft = pg.ImageItem()
        self.ft_view.addItem(self.img_item_ft)

        self.calc_imag_ft()

        self.ft_roi = pg.ROI(pos=self.ft_view.viewRect().center(), size=(50, 50), hoverPen='b', resizable=True,
                             invertible=True, rotatable=False, maxBounds=self.ROI_Maxbounds)
        self.ft_view.addItem(self.ft_roi)
        self.add_scale_handles_ROI(self.ft_roi)
        self.ft_roi.sigRegionChangeFinished.connect(self.region_update)

    def region_update(self):
        shifted_data = self.data.get_shifted()
        self.sig_emitter.sig_ROI_changed.emit()
        self.update_mask_size()

    def update_mask_size(self):
        bounds = self.ft_roi.sceneBoundingRect()
        self.x1, self.y1, self.x2, self.y2 = int(bounds.x()), int(bounds.y()), int(bounds.x() + bounds.width()), int(
            bounds.y() + bounds.height())

        # Create a mask of zeros with minimum width and height
        mask = np.zeros(self.data.get_image_data().shape)
        mask[self.y1:self.y2 + 1, self.x1:self.x2 + 1] = 1


        # Based on another condition, invert the mask
        if self.area_region == 'Outside Area':
            mask = 1 - mask

        self.data.set_window_mask(mask)

    def calc_imag_ft(self):
        shifted_data = self.data.get_shifted()

        self.img_item_ft.setImage(shifted_data[self.mode])

    def add_scale_handles_ROI(self, roi: pg.ROI):
        positions = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        for pos in positions:
            roi.addScaleHandle(pos=pos, center=1 - pos)


