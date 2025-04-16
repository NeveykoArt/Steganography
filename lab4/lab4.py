import sys
import math
import numpy as np
from PIL import Image
import os

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLineEdit, QFileDialog, QTextEdit
)

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
    inter = pix.copy()

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
                inter[x + dx, y + dy] = C[dx, dy]

    Image.fromarray(np.clip(stego, 0, 255).astype(np.uint8)).save(out_path)
    return Image.fromarray(np.clip(inter, 0, 255).astype(np.uint8))

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

                # Если мы достигли нужной длины (в битах), возвращаем результат
                if extracted >= msg_length * 8:
                    return from_bin(bits[:msg_length * 8])

    return from_bin(bits[:msg_length * 8])

class SteganographyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Встраивание/Извлечение сообщения (IMNP)")
        self.setGeometry(100, 100, 600, 400)

        self.selected_paths = []
        self.msg_length = 0

        layout = QVBoxLayout()

        self.select_images_button = QPushButton("Выбрать изображения")
        self.select_images_button.clicked.connect(self.select_images)
        layout.addWidget(self.select_images_button)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Введите секретное сообщение для встраивания")
        layout.addWidget(self.message_input)

        self.embed_button = QPushButton("Встроить")
        self.embed_button.clicked.connect(self.embed_message)
        layout.addWidget(self.embed_button)

        self.extract_button = QPushButton("Извлечь")
        self.extract_button.clicked.connect(self.extract_message)
        layout.addWidget(self.extract_button)

        self.info_output = QTextEdit()
        self.info_output.setReadOnly(True)
        layout.addWidget(self.info_output)

        self.setLayout(layout)

    def select_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите изображения (BMP/PGM)",
            "",
            "Image Files (*.pgm *.bmp)"
        )
        if paths:
            self.selected_paths = paths
            self.info_output.setText(
                "Выбрано изображений: {}\n\n".format(len(paths)) +
                "\n".join(paths)
            )

    def embed_message(self):
        if not self.selected_paths:
            self.info_output.setText("Сначала выберите изображения.")
            return

        message = self.message_input.text()
        if not message:
            self.info_output.setText("Введите сообщение для встраивания.")
            return

        self.msg_length = len(message)
        results = []
        for path in self.selected_paths:
            try:
                filename, ext = os.path.splitext(path)
                stego_path = f"{filename}_stego_lab4{ext}"

                inter_img = hide(path, message, stego_path)
                stego_img = Image.open(stego_path)
                psnr_val = psnr(inter_img, stego_img)

                results.append(
                    f"Файл: {path}\n"
                    f"Стего: {stego_path}\n"
                    f"PSNR: {psnr_val:.2f} dB\n"
                )
            except Exception as e:
                results.append(
                    f"Ошибка при встраивании в файл {path}: {str(e)}\n"
                )

        self.info_output.setText(
            "Встраивание завершено. Результаты:\n\n" + "\n".join(results)
        )

    def extract_message(self):
        if not self.selected_paths:
            self.info_output.setText("Сначала выберите изображения.")
            return

        if self.msg_length == 0:
            self.info_output.setText("Неизвестна длина сообщения (сначала выполните встраивание).")
            return

        results = []
        for path in self.selected_paths:
            try:
                filename, ext = os.path.splitext(path)
                stego_path = f"{filename}_stego_lab4{ext}"

                extracted = extract(stego_path, self.msg_length)
                results.append(f"Файл: {stego_path}\nИзвлечённое сообщение: {extracted}\n")
            except Exception as e:
                results.append(f"Ошибка при извлечении из файла {path}: {str(e)}\n")

        self.info_output.setText(
            "Извлечение завершено. Результаты:\n\n" + "\n".join(results)
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SteganographyApp()
    window.show()
    sys.exit(app.exec_())
