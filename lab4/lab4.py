import sys
import math
import numpy as np
from PIL import Image

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLineEdit, QFileDialog, QLabel, QTextEdit
)
from PyQt5.QtCore import Qt
import os

def to_bin(msg):
    return ''.join(f'{ord(c):08b}' for c in msg)

def from_bin(bits):
    return ''.join(chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8))

def psnr(img1, img2):
    arr1 = np.array(img1, dtype=float)
    arr2 = np.array(img2, dtype=float)
    mse = np.mean((arr1 - arr2) ** 2)
    if mse == 0:
        return float('inf')
    return 20 * math.log10(255.0 / math.sqrt(mse))

def hide(img_path, message, out_path):
    img = Image.open(img_path)
    pix = np.array(img, dtype=int)
    bits = to_bin(message)
    bit_idx = 0
    M, N = pix.shape
    stego = pix.copy()

    for x in range(0, M - 2, 2):
        for y in range(0, N - 2, 2):
            Omin = np.min([pix[x, y], pix[x+2, y], pix[x, y+2], pix[x+2, y+2]])
            Omax = np.max([pix[x, y], pix[x+2, y], pix[x, y+2], pix[x+2, y+2]])

            C = np.zeros((2, 2), dtype=int)
            C[0, 0] = pix[x, y]
            C[0, 1] = (Omax + ((pix[x, y] + pix[x, y+2]) // 2)) // 2
            C[1, 0] = (Omax + ((pix[x, y] + pix[x+2, y]) // 2)) // 2
            C[1, 1] = (C[1, 0] + C[0, 1]) // 2

            vk = [C[0, 1] - Omin, C[1, 0] - Omin, C[1, 1] - Omin]

            for idx, (dx, dy) in enumerate([(0, 1), (1, 0), (1, 1)]):
                ak = math.floor(math.log2(vk[idx])) if vk[idx] > 0 else 0
                if ak > 0 and bit_idx + ak <= len(bits):
                    Rk = int(bits[bit_idx:bit_idx + ak], 2)
                    bit_idx += ak
                    if (dx, dy) == (1, 1):
                        ref = min(C[1, 0], C[0, 1])
                    else:
                        ref = max(pix[x, y], pix[x + 2*dx, y + 2*dy])
                    stego[x + dx, y + dy] = ref - Rk
                else:
                    stego[x + dx, y + dy] = C[dx, dy]
    Image.fromarray(np.clip(stego, 0, 255).astype(np.uint8)).save(out_path)

def extract(stego_path, msg_length):
    stego_img = Image.open(stego_path)
    stego = np.array(stego_img, dtype=int)
    bits = ''
    extracted = 0
    M, N = stego.shape

    for x in range(0, M - 2, 2):
        for y in range(0, N - 2, 2):
            Omin = np.min([stego[x, y], stego[x+2, y], stego[x, y+2], stego[x+2, y+2]])
            Omax = np.max([stego[x, y], stego[x+2, y], stego[x, y+2], stego[x+2, y+2]])

            C = np.zeros((2, 2), dtype=int)
            C[0, 0] = stego[x, y]
            C[0, 1] = (Omax + (stego[x, y] + stego[x, y+2]) // 2) // 2
            C[1, 0] = (Omax + (stego[x, y] + stego[x+2, y]) // 2) // 2
            C[1, 1] = (C[1, 0] + C[0, 1]) // 2

            vk = [C[0, 1] - Omin, C[1, 0] - Omin, C[1, 1] - Omin]

            for idx, (dx, dy) in enumerate([(0, 1), (1, 0), (1, 1)]):
                ak = math.floor(math.log2(vk[idx])) if vk[idx] > 0 else 0
                if ak > 0 and extracted + ak <= msg_length * 8:
                    if (dx, dy) == (1, 1):
                        ref = min(C[1, 0], C[0, 1])
                    else:
                        ref = max(stego[x, y], stego[x + 2*dx, y + 2*dy])

                    Rk = ref - stego[x + dx, y + dy]
                    if Rk < 0:
                        Rk = 0
                    bits += f'{Rk:0{ak}b}'
                    extracted += ak

                if extracted >= msg_length * 8:
                    return from_bin(bits[:msg_length * 8])
    return from_bin(bits[:msg_length * 8])

class SteganographyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Встраивание сообщения в изображение методом IMNP")
        self.setGeometry(100, 100, 400, 400)
        self.msg_length = 0

        layout = QVBoxLayout()

        # Шифрование
        self.encode_label = QLabel("Шифрование")
        layout.addWidget(self.encode_label)

        self.carrier_path_input = QLineEdit()
        self.carrier_path_input.setPlaceholderText("Путь к изображению (BMP/PGM)")
        layout.addWidget(self.carrier_path_input)

        self.carrier_button = QPushButton("Выбрать изображение")
        self.carrier_button.clicked.connect(self.select_carrier_image)
        layout.addWidget(self.carrier_button)

        self.secret_msg_input = QLineEdit()
        self.secret_msg_input.setPlaceholderText("Секретное сообщение")
        layout.addWidget(self.secret_msg_input)

        self.encode_button = QPushButton("Зашифровать")
        self.encode_button.clicked.connect(self.hide_message)
        layout.addWidget(self.encode_button)

        # Расшифровка
        self.decode_label = QLabel("Расшифровка")
        layout.addWidget(self.decode_label)

        self.stego_path_input = QLineEdit()
        self.stego_path_input.setPlaceholderText("Путь к стегоизображению (BMP/PGM)")
        layout.addWidget(self.stego_path_input)

        self.stego_button = QPushButton("Выбрать стегоизображение")
        self.stego_button.clicked.connect(self.select_stego_image)
        layout.addWidget(self.stego_button)

        self.decode_button = QPushButton("Расшифровать")
        self.decode_button.clicked.connect(self.extract_message)
        layout.addWidget(self.decode_button)

        self.decoded_msg_output = QTextEdit()
        self.decoded_msg_output.setReadOnly(True)
        layout.addWidget(self.decoded_msg_output)

        self.psnr_output = QLabel()
        layout.addWidget(self.psnr_output)

        self.setLayout(layout)

    def select_carrier_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать изображение-носитель",
            "",
            "Image Files (*.pgm *.bmp)"
        )
        if path:
            self.carrier_path_input.setText(path)

    def select_stego_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать стегоизображение",
            "",
            "Image Files (*.pgm *.bmp)"
        )
        if path:
            self.stego_path_input.setText(path)

    def hide_message(self):
        carrier_path = self.carrier_path_input.text()
        secret_msg = self.secret_msg_input.text()

        if not carrier_path or not secret_msg:
            self.decoded_msg_output.setText("Заполните все поля для шифрования.")
            return

        try:
            self.msg_length = len(secret_msg)

            filename, file_extension = os.path.splitext(carrier_path)
            output_path = f"{filename}_stego{file_extension}"

            hide(carrier_path, secret_msg, output_path)

            original_img = Image.open(carrier_path)
            stego_img = Image.open(output_path)
            psnr_value = psnr(original_img, stego_img)

            self.decoded_msg_output.setText(
                f"Сообщение зашифровано.\nСтегоизображение сохранено: {output_path}\nPSNR: {psnr_value:.2f} dB"
            )
            self.stego_path_input.setText(output_path)

        except Exception as e:
            self.decoded_msg_output.setText(f"Ошибка при шифровании: {str(e)}")

    def extract_message(self):
        stego_path = self.stego_path_input.text()
        if not stego_path:
            self.decoded_msg_output.setText("Укажите путь к стегоизображению.")
            return

        if not self.msg_length:
            self.decoded_msg_output.setText(
                "Неизвестна длина сообщения."
            )
            return

        try:
            extracted_secret = extract(stego_path, self.msg_length)

            original_path = self.carrier_path_input.text()
            if not original_path:
                self.decoded_msg_output.setText(
                    f"Расшифрованное сообщение: {extracted_secret}\n"
                    "Неизвестен путь к исходному изображению, PSNR не вычислен."
                )
                return

            original_img = Image.open(original_path)
            stego_img = Image.open(stego_path)
            psnr_value = psnr(original_img, stego_img)

            self.decoded_msg_output.setText(f"Расшифрованное сообщение: {extracted_secret}")
            self.psnr_output.setText(f"PSNR: {psnr_value:.2f} dB")

        except Exception as e:
            self.decoded_msg_output.setText(f"Ошибка при расшифровании: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SteganographyApp()
    window.show()
    sys.exit(app.exec_())