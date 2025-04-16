import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QLineEdit, QFileDialog, QLabel, QTextEdit,
                             QMessageBox)
from PyQt5.QtCore import Qt
from PIL import Image
import numpy as np
import math
import os

class SteganographyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Встраивание сообщения в изображение")
        self.setGeometry(100, 100, 400, 400)

        layout = QVBoxLayout()

        # Encode
        self.encode_label = QLabel("Шифрование")
        layout.addWidget(self.encode_label)

        self.carrier_paths = []
        self.carrier_path_input = QLineEdit()
        self.carrier_path_input.setPlaceholderText("Путь к изображениям-носителям")
        layout.addWidget(self.carrier_path_input)

        self.carrier_button = QPushButton("Выбрать изображения-носители")
        self.carrier_button.clicked.connect(self.select_carrier_images)
        layout.addWidget(self.carrier_button)

        self.secret_msg_input = QLineEdit()
        self.secret_msg_input.setPlaceholderText("Секретное сообщение")
        layout.addWidget(self.secret_msg_input)

        self.encode_button = QPushButton("Зашифровать")
        self.encode_button.clicked.connect(self.hide_message)
        layout.addWidget(self.encode_button)

        # Decode
        self.decode_label = QLabel("Расшифровка")
        layout.addWidget(self.decode_label)

        self.stego_paths = []
        self.stego_path_input = QLineEdit()
        self.stego_path_input.setPlaceholderText("Путь к стегоизображениям")
        layout.addWidget(self.stego_path_input)

        self.decode_button = QPushButton("Расшифровать")
        self.decode_button.clicked.connect(self.extract_message)
        layout.addWidget(self.decode_button)

        self.decoded_msg_output = QTextEdit()
        self.decoded_msg_output.setReadOnly(True)
        layout.addWidget(self.decoded_msg_output)

        self.psnr_output = QLabel()
        layout.addWidget(self.psnr_output)

        self.setLayout(layout)

    def select_carrier_images(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Image Files (*.pgm *.bmp)")
        if file_dialog.exec_():
            self.carrier_paths = file_dialog.selectedFiles()
            self.carrier_path_input.setText("; ".join(self.carrier_paths))

    def select_stego_images(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Image Files (*.pgm *.bmp)")
        if file_dialog.exec_():
            self.stego_paths = file_dialog.selectedFiles()
            self.stego_path_input.setText("; ".join(self.stego_paths))

    def hide_message(self):
        secret_msg = self.secret_msg_input.text()

        if not self.carrier_paths or not secret_msg:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите изображения-носители и введите сообщение.")
            return

        try:
            for carrier_path in self.carrier_paths:
                img = Image.open(carrier_path)
                pixels = np.array(img)

                msg_bits = ''.join(format(ord(c), '08b') for c in secret_msg) + '00000000'
                msg_pairs = [msg_bits[i:i+2] for i in range(0, len(msg_bits), 2)]

                height, width = pixels.shape
                pair_idx = 0

                for row in range(height):
                    for col in range(width):
                        if pair_idx >= len(msg_pairs):
                            break

                        pixel = pixels[row, col]
                        msb4 = (pixel & 0xF0) >> 4  # Получение 4 старших битов

                        # Формирование пар битов из MSB
                        leftpare = (msb4 & 0b1100) >> 2  # Биты 7-6
                        middlepare = (msb4 & 0b0110) >> 1  # Биты 6-5
                        rightpare = msb4 & 0b0011  # Биты 5-4

                        # Сравнение пар и модификация LSB
                        lsb3 = pixel & 0b111  # Младшие 3 бита

                        if pair_idx < len(msg_pairs) and leftpare == int(msg_pairs[pair_idx], 2):
                            lsb3 |= (1 << 2)  # Установка 3-го LSB
                            pair_idx += 1
                        else:
                            lsb3 &= ~(1 << 2) & 0b111  # Сброс 3-го LSB

                        if pair_idx < len(msg_pairs) and middlepare == int(msg_pairs[pair_idx], 2):
                            lsb3 |= (1 << 1)  # Установка 2-го LSB
                            pair_idx += 1
                        else:
                            lsb3 &= ~(1 << 1) & 0b111  # Сброс 2-го LSB

                        if pair_idx < len(msg_pairs) and rightpare == int(msg_pairs[pair_idx], 2):
                            lsb3 |= (1 << 0)  # Установка 1-го LSB
                            pair_idx += 1
                        else:
                            lsb3 &= ~(1 << 0) & 0b111  # Сброс 1-го LSB

                        # Обновление значения пикселя
                        new_pixel = (msb4 << 4) | lsb3
                        pixels[row, col] = new_pixel

                # Сохранение стегоизображения
                filename, file_extension = os.path.splitext(carrier_path)
                output_path = f"{filename}_stego_lab3{file_extension}"
                self.stego_paths.append(output_path)
                Image.fromarray(pixels.astype(np.uint8)).save(output_path)
                self.decoded_msg_output.append(f"Сообщение зашифровано в {output_path}\n")

            QMessageBox.information(self, "Успех", "Сообщение зашифровано во все выбранные изображения.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {e}")

    def extract_message(self):
        if not self.stego_paths:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите стегоизображения для расшифровки.")
            return

        try:
            full_message = ""
            for stego_path in self.stego_paths:
                img = Image.open(stego_path)
                pixels = np.array(img)
                msg_pairs = []

                for pixel in pixels.flatten():
                    msb4 = (pixel & 0xF0) >> 4

                    leftpare = (msb4 & 0b1100) >> 2
                    middlepare = (msb4 & 0b0110) >> 1
                    rightpare = msb4 & 0b0011

                    lsb3 = pixel & 0b111

                    if lsb3 & (1 << 2):  
                        msg_pairs.append(f"{leftpare:02b}")
                    if lsb3 & (1 << 1):  
                        msg_pairs.append(f"{middlepare:02b}")
                    if lsb3 & (1 << 0):  
                        msg_pairs.append(f"{rightpare:02b}")

                full_bits = ''.join(msg_pairs)
                msg_bytes = [full_bits[i:i+8] for i in range(0, len(full_bits), 8)]
                message = ''.join([chr(int(byte, 2)) for byte in msg_bytes if len(byte) == 8])
                full_message += f"Сообщение из {stego_path}: {message.split('\x00')[0]}\n"

                # Расчет PSNR
                if self.carrier_paths:
                    try:
                        # Используем первый carrier_path для расчета PSNR
                        original_path = stego_path.replace("_stego_lab3", "")
                        orig = np.array(Image.open(original_path)).astype(float)
                        stego = np.array(img).astype(float)
                        mse = np.mean((orig - stego) ** 2)
                        if mse == 0:
                            psnr = float('inf')
                        else:
                            psnr = 10 * math.log10(255**2 / mse)
                        full_message += f"PSNR для {stego_path}: {psnr:.2f} dB\n"
                    except Exception as e:
                        full_message += f"Ошибка при расчете PSNR для {stego_path}: {e}\n"
                else:
                    full_message += "Невозможно рассчитать PSNR: не выбраны оригинальные изображения.\n"

            self.decoded_msg_output.setText(full_message)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SteganographyApp()
    window.show()
    sys.exit(app.exec_())

