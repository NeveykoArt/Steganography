import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QFileDialog, QLabel, QTextEdit
from PyQt5.QtCore import Qt
from PIL import Image
import numpy as np
import math
import os

class SteganographyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Стеганография")
        self.setGeometry(100, 100, 400, 400)

        layout = QVBoxLayout()

        # Encode
        self.encode_label = QLabel("Шифрование")
        layout.addWidget(self.encode_label)

        self.carrier_path_input = QLineEdit()
        self.carrier_path_input.setPlaceholderText("Путь к изображению-носителю")
        layout.addWidget(self.carrier_path_input)

        self.carrier_button = QPushButton("Выбрать изображение-носитель")
        self.carrier_button.clicked.connect(self.select_carrier_image)
        layout.addWidget(self.carrier_button)

        self.secret_msg_input = QLineEdit()
        self.secret_msg_input.setPlaceholderText("Секретное сообщение")
        layout.addWidget(self.secret_msg_input)

        self.encode_button = QPushButton("Зашифровать")
        self.encode_button.clicked.connect(self.encode_message)
        layout.addWidget(self.encode_button)

        # Decode
        self.decode_label = QLabel("Расшифровка")
        layout.addWidget(self.decode_label)

        self.stego_path_input = QLineEdit()
        self.stego_path_input.setPlaceholderText("Путь к стегоизображению")
        layout.addWidget(self.stego_path_input)

        self.stego_button = QPushButton("Выбрать стегоизображение")
        self.stego_button.clicked.connect(self.select_stego_image)
        layout.addWidget(self.stego_button)

        self.decode_button = QPushButton("Расшифровать")
        self.decode_button.clicked.connect(self.decode_message)
        layout.addWidget(self.decode_button)

        self.decoded_msg_output = QTextEdit()
        self.decoded_msg_output.setReadOnly(True)
        layout.addWidget(self.decoded_msg_output)

        self.psnr_output = QLabel()
        layout.addWidget(self.psnr_output)

        self.setLayout(layout)

    def select_carrier_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать изображение-носитель", "", "Image Files (*.pgm)")
        self.carrier_path_input.setText(path)

    def select_stego_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать стегоизображение", "", "Image Files (*.pgm)")
        self.stego_path_input.setText(path)

    def encode_message(self):
        carrier_path = self.carrier_path_input.text()
        secret_msg = self.secret_msg_input.text()

        if not carrier_path or not secret_msg:
            self.decoded_msg_output.setText("Пожалуйста, заполните все поля.")
            return

        try:
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
            output_path = f"{filename}_stego{file_extension}"
            Image.fromarray(pixels.astype(np.uint8)).save(output_path)
            self.decoded_msg_output.setText(f"Сообщение зашифровано и сохранено в {output_path}")
            self.stego_path_input.setText(output_path)
        except Exception as e:
            self.decoded_msg_output.setText(f"Ошибка: {e}")

    def decode_message(self):
        stego_path = self.stego_path_input.text()

        if not stego_path:
            self.decoded_msg_output.setText("Пожалуйста, укажите путь к стегоизображению.")
            return

        try:
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

            # Расчет PSNR
            original_path = self.carrier_path_input.text()
            orig = np.array(Image.open(original_path)).astype(float)
            stego = np.array(img).astype(float)
            mse = np.mean((orig - stego) ** 2)
            if mse == 0:
                psnr = float('inf')
            else:
                psnr = 10 * math.log10(255**2 / mse)

            self.decoded_msg_output.setText(f"Расшифрованное сообщение: {message.split('\x00')[0]}")
            self.psnr_output.setText(f"PSNR: {psnr:.2f} dB")
        except Exception as e:
            self.decoded_msg_output.setText(f"Ошибка: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SteganographyApp()
    window.show()
    sys.exit(app.exec_())