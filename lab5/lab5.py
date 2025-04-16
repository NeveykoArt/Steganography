import sys
from PyQt5.QtWidgets import (
    QApplication, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget,
    QRadioButton, QFileDialog, QMessageBox, QGroupBox, QScrollArea, QFrame
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage
from PyQt5.QtCore import Qt, QRect
from PIL import Image
import math
import numpy as np
import os

import subprocess

def run_java_analysis(image_path):
    java_class_path = "/Users/revolution/Steganography/lab5"
    java_class = "RSAnalysis"
    
    try:
        result = subprocess.run(
            ["java" , "-cp", java_class_path, java_class, image_path],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return result.stdout
        else:
            print("Error executing Java program")
            print(result.stderr)

    except Exception as e:
        print(f"Error executing the Java program: {e}")

def image_to_array(image: QImage) -> np.ndarray:
    width, height = image.width(), image.height()
    ptr = image.bits()
    ptr.setsize(image.bytesPerLine() * height)
    
    if image.format() in [QImage.Format.Format_RGBA8888, QImage.Format.Format_ARGB32]:
        arr = np.array(ptr).reshape(height, width, 4)
        return arr[:, :, 2]
    elif image.format() == QImage.Format.Format_Grayscale8:
        arr = np.array(ptr).reshape(height, width)
        return arr
    else:
        converted = image.convertToFormat(QImage.Format.Format_RGBA8888)
        ptr = converted.bits()
        ptr.setsize(converted.bytesPerLine() * converted.height())
        arr = np.array(ptr).reshape(converted.height(), converted.width(), 4)
        return arr[:, :, 2]

def pred_aump(X: np.ndarray, m: int, d: int) -> tuple:
        sig_th = 1.0
        q = d + 1
        h, w_img = X.shape
        Kn = (h * w_img) // m
        H = np.zeros((m, q))
        x_vals = np.linspace(1/m, 1, m)
        for i in range(q):
            H[:, i] = x_vals ** i
        Y = np.zeros((m, Kn))
        count = 0
        for i in range(h):
            for j in range(w_img):
                block_idx = count // m
                row_in_block = count % m
                Y[row_in_block, block_idx] = X[i, j]
                count += 1
        p = np.linalg.lstsq(H, Y, rcond=None)[0]
        Ypred = H @ p
        Xpred = np.zeros_like(X)
        count = 0
        for i in range(h):
            for j in range(w_img):
                block_idx = count // m
                row_in_block = count % m
                Xpred[i, j] = Ypred[row_in_block, block_idx]
                count += 1
        sig2 = np.sum((Y - Ypred) ** 2, axis=0) / (m - q)
        sig2 = np.maximum(sig_th ** 2, sig2)
        s_n2 = Kn / np.sum(1.0 / sig2)
        w_block = np.sqrt(s_n2 / (Kn * (m - q))) / sig2
        w_full = np.zeros_like(X)
        count = 0
        for i in range(h):
            for j in range(w_img):
                block_idx = count // m
                w_full[i, j] = w_block[block_idx]
                count += 1
        return Xpred, w_full

class BitImageVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_image_paths = []
        self.selected_bit = 0
        self.changed_images = []
        self.initUI()
    
    def chi_square_analysis(self, image_path, block_size: int = 16) -> np.ndarray:
        image = QImage(image_path)
        arr = image_to_array(image)
        h, w = arr.shape
        rows, cols = h // block_size, w // block_size
        chi_values = np.zeros((rows, cols))
        for i in range(rows):
            for j in range(cols):
                block = arr[i*block_size:(i+1)*block_size, j*block_size:(j+1)*block_size]
                observed, _ = np.histogram(block, bins=256, range=(0, 256))
                expected = np.full(observed.shape, block.size / 256)
                chi_values[i, j] = np.sum((observed - expected) ** 2 / expected)
        return chi_values

    def aump_analysis(self, image_path, m: int = 8, d: int = 1) -> float:
        image = QImage(image_path)
        arr = np.zeros((image.height(), image.width()), dtype=np.float64)
        for y in range(image.height()):
            for x in range(image.width()):
                arr[y, x] = QColor(image.pixel(x, y)).red()
        X = arr.copy()
        Xpred, w = pred_aump(X, m, d)
        r = X - Xpred
        Xbar = X + 1 - 2 * (X.astype(int) % 2)
        beta = np.sum(w * (X - Xbar) * r)
        return beta
    
    def initUI(self):
        self.setWindowTitle("Атака на пустой контейнер")
        self.resize(800, 600)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        image_layout = QHBoxLayout()
        main_layout.addLayout(image_layout)

        self.create_changed_image_layout(image_layout)

        self.create_button_layout(main_layout)
        self.create_bit_selection_layout(main_layout)

        self.update_bit_visualization()

    def create_changed_image_layout(self, main_layout):
        changed_image_group = QGroupBox("Изменённые изображения / Контейнеры")
        changed_image_group.setAlignment(Qt.AlignCenter)

        self.container_scroll_area = QScrollArea()
        self.container_scroll_area.setWidgetResizable(True)
        self.container_scroll_area.setFrameShape(QFrame.NoFrame)

        self.container_widget = QWidget()
        self.container_layout = QVBoxLayout(self.container_widget)

        self.container_scroll_area.setWidget(self.container_widget)

        changed_image_layout = QVBoxLayout()
        changed_image_layout.addWidget(self.container_scroll_area)
        changed_image_group.setLayout(changed_image_layout)

        main_layout.addWidget(changed_image_group)

    def create_button_layout(self, main_layout):
        button_layout = QHBoxLayout()

        self.select_button = QPushButton("Выбрать изображения")
        self.select_button.clicked.connect(self.select_images)
        button_layout.addWidget(self.select_button)

        self.generate_button = QPushButton("Сгенерировать изображение")
        self.generate_button.clicked.connect(self.generate_bit_image)
        button_layout.addWidget(self.generate_button)

        self.analysis_button = QPushButton("Выполнить стегоанализ")
        self.analysis_button.clicked.connect(self.run_stego_analysis)
        button_layout.addWidget(self.analysis_button)

        main_layout.addLayout(button_layout)

    def create_bit_selection_layout(self, main_layout):
        bit_groupbox = QGroupBox("Выбор битов")
        bit_groupbox.setFixedSize(340, 120)

        bit_selection_layout = QHBoxLayout()
        self.bit_visualization_labels = []
        self.bit_radio_buttons = []

        for i in range(8):
            bit_layout = QVBoxLayout()

            visual_label = QLabel()
            visual_label.setFixedSize(40, 30)
            self.bit_visualization_labels.append(visual_label)

            radio_btn = QRadioButton()
            radio_btn.toggled.connect(self.update_selected_bit)
            self.bit_radio_buttons.append(radio_btn)

            bit_layout.addWidget(visual_label)
            bit_layout.addWidget(radio_btn)

            bit_selection_layout.addLayout(bit_layout)
            bit_selection_layout.setSpacing(5)

        bit_groupbox.setLayout(bit_selection_layout)
        main_layout.addWidget(bit_groupbox)

    def update_bit_visualization(self):
        for i in range(8):
            pixmap = QPixmap(40, 30)
            pixmap.fill(Qt.white)
            painter = QPainter(pixmap)

            color = QColor(255, 0, 0) if i == self.selected_bit else QColor(240, 240, 240)
            painter.fillRect(QRect(5, 5, 30, 20), color)
            painter.end()

            self.bit_visualization_labels[i].setPixmap(pixmap)

        self.bit_radio_buttons[self.selected_bit].setChecked(True)

    def select_images(self):
        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выбрать изображения",
            "",
            "Images (*.pgm *.bmp);;All Files (*)",
            options=options
        )
        if file_paths:
            self.selected_image_paths = file_paths

    def update_selected_bit(self):
        for i, btn in enumerate(self.bit_radio_buttons):
            if btn.isChecked():
                self.selected_bit = i
                break
        self.update_bit_visualization()

    def generate_bit_image(self):
        if not self.selected_image_paths:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите изображения!")
            return

        for i in reversed(range(self.container_layout.count())):
            widget = self.container_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        i = 1
        for image_path in self.selected_image_paths:
            img = Image.open(image_path)
            width, height = img.size
            new_image = Image.new("1", (width, height))
            for x in range(width):
                for y in range(height):
                    pixel = img.getpixel((x, y))
                    lsb = (pixel >> self.selected_bit) & 1
                    new_image.putpixel((x, y), 255 if lsb == 1 else 0)

            self.changed_images.append(new_image)
            self.display_changed_image(new_image, i)
            i = i + 1

    def display_changed_image(self, image, i):
        image.save("temp_changed_image" + str(i) + ".bmp", "BMP")
        pixmap = QPixmap("temp_changed_image" + str(i) + ".bmp").scaled(300, 300, aspectRatioMode=True)

        new_label = QLabel()
        new_label.setPixmap(pixmap)
        self.container_layout.addWidget(new_label)

    def run_stego_analysis(self):
        if not self.selected_image_paths:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите изображения!")
            return

        results = []
        for image_path in self.selected_image_paths:
            chi_val = self.chi_square_analysis(image_path)
            rs_val = run_java_analysis(image_path)
            aump_val = self.aump_analysis(image_path)

            result = (f"Результаты стегоанализа для {image_path}:\n"
                      f"Хи-квадрат (среднее): {chi_val.mean():.4f}\n"
                      f"RS-анализ: {rs_val}"
                      f"AUMP-показатель: {aump_val:.4f}\n\n")
            results.append(result)

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результаты анализа",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        if save_path:
            with open(save_path, "w") as f:
                f.writelines(results)
            QMessageBox.information(self, "Анализ завершён", f"Результаты сохранены в {save_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    visualizer = BitImageVisualizer()
    visualizer.show()
    sys.exit(app.exec_())