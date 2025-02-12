import sys
from PyQt5.QtWidgets import (QApplication, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QRadioButton, QFileDialog, QMessageBox, QGroupBox)
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, QRect
from PIL import Image

class BitImageVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_image_path = None
        self.selected_bit = 0
        self.changed_image = None
        self.initUI()



    def initUI(self):
        self.setWindowTitle("Атака на пустой контейнер")
        self.resize(800, 600)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        image_layout = QHBoxLayout()
        main_layout.addLayout(image_layout)

        self.create_base_image_layout(image_layout)
        self.create_changed_image_layout(image_layout)

        self.create_button_layout(main_layout)
        self.create_bit_selection_layout(main_layout)

        self.update_bit_visualization()



    def create_base_image_layout(self, main_layout):
        original_image_group = QGroupBox("Исходное изображение")
        original_image_group.setFixedSize(260, 300)
        original_image_group.setAlignment(Qt.AlignCenter)

        self.original_image_display = QLabel()
        self.original_image_label = QLabel("Изображение не выбрано")
        self.original_image_label.setAlignment(Qt.AlignCenter)
        self.original_image_display.setAlignment(Qt.AlignCenter)

        image_layout = QVBoxLayout()
        image_layout.addWidget(self.original_image_display)
        image_layout.addWidget(self.original_image_label)
        original_image_group.setLayout(image_layout)

        main_layout.addWidget(original_image_group)



    def create_changed_image_layout(self, main_layout):
        changed_image_group = QGroupBox("Измененное изображение")
        changed_image_group.setFixedSize(260, 300)
        changed_image_group.setAlignment(Qt.AlignCenter)

        self.changed_image_display = QLabel()
        self.changed_image_label = QLabel("Изображение не сгенерировано")
        self.changed_image_label.setAlignment(Qt.AlignCenter)
        self.changed_image_display.setAlignment(Qt.AlignCenter)

        changed_image_layout = QVBoxLayout()
        changed_image_layout.addWidget(self.changed_image_display)
        changed_image_layout.addWidget(self.changed_image_label)
        changed_image_group.setLayout(changed_image_layout)

        main_layout.addWidget(changed_image_group)



    def create_button_layout(self, main_layout):
        button_layout = QHBoxLayout()

        self.select_button = QPushButton("Выбрать изображение")
        self.select_button.clicked.connect(self.select_image)
        button_layout.addWidget(self.select_button)

        self.generate_button = QPushButton("Сгенерировать изображение")
        self.generate_button.clicked.connect(self.generate_bit_image)
        button_layout.addWidget(self.generate_button)

        self.save_button = QPushButton("Сохранить изображение")
        self.save_button.clicked.connect(self.save_image)
        button_layout.addWidget(self.save_button)

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







    def select_image(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать изображение PGM", "", "Images (*.pgm);;All Files (*)", options=options)
        if file_path:
            self.selected_image_path = file_path
            self.display_image(file_path)



    def display_image(self, path):
        pixmap = QPixmap(path).scaled(300, 300, aspectRatioMode=True)
        self.original_image_display.setPixmap(pixmap)
        self.original_image_label.setText("")



    def update_selected_bit(self):
        for i, btn in enumerate(self.bit_radio_buttons):
            if btn.isChecked():
                self.selected_bit = i
                break
        self.update_bit_visualization()



    def generate_bit_image(self):
        if not self.selected_image_path:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите изображение!")
            return

        img = Image.open(self.selected_image_path)
        width, height = img.size
        new_image = Image.new("1", (width, height))

        for x in range(width):
            for y in range(height):
                pixel = img.getpixel((x, y))
                lsb = (pixel >> self.selected_bit) & 1
                new_image.putpixel((x, y), 255 if lsb == 1 else 0)

        self.changed_image = new_image
        self.display_changed_image(new_image)



    def display_changed_image(self, image):
        image.save("temp_changed_image.bmp", "BMP")
        pixmap = QPixmap("temp_changed_image.bmp").scaled(300, 300, aspectRatioMode=True)
        self.changed_image_display.setPixmap(pixmap)
        self.changed_image_label.setText("")



    def save_image(self):
        if self.changed_image is None:
            QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте изображение!")
            return

        output_folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if not output_folder:
            return

        output_path = f"{output_folder}/bit_{self.selected_bit}.bmp"
        self.changed_image.save(output_path, "BMP")
        QMessageBox.information(self, "Успех", f"Изображение сохранено: {output_path}")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    visualizer = BitImageVisualizer()
    visualizer.show()
    sys.exit(app.exec_())