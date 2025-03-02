import sys
import numpy as np
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QPushButton,
    QLineEdit,
    QFormLayout,
    QWidget,
    QVBoxLayout,
    QTextEdit,
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Цифровой водяной знак методом CDB")
        self.setMinimumSize(600, 400)

        # Параметры по умолчанию
        self.cdb_coeff = 0.9
        self.cdb_range = 3
        self.seed = 0xAAAA
        self.input_image_format = None
        self.image = None
        self.bit_size = 0

        # Инициализация интерфейса
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        control_widget = QWidget()
        control_layout = QVBoxLayout()
        control_widget.setLayout(control_layout)

        form_layout = QFormLayout()
        self.cdb_coeff_input = QLineEdit(str(self.cdb_coeff))
        self.cdb_range_input = QLineEdit(str(self.cdb_range))

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Введите текст для встраивания...")
        form_layout.addRow("Текст для встраивания:", self.message_input)

        self.cdb_coeff_input.setMinimumWidth(200)
        self.cdb_range_input.setMinimumWidth(200)

        form_layout.addRow("коэффициент CDB:", self.cdb_coeff_input)
        form_layout.addRow("диапазон CDB:", self.cdb_range_input)
        control_layout.addLayout(form_layout)

        self.select_image_button = QPushButton("Выбрать изображение")
        self.hide_message_button = QPushButton("Спрятать сообщение")
        self.extract_message_button = QPushButton("Извлечь сообщение")
        self.save_image_button = QPushButton("Сохранить контейнер")
        self.test_cdb_button = QPushButton("Тест метода CDB")

        control_layout.addWidget(self.select_image_button)
        control_layout.addWidget(self.hide_message_button)
        control_layout.addWidget(self.extract_message_button)
        control_layout.addWidget(self.save_image_button)
        control_layout.addWidget(self.test_cdb_button)
        control_layout.addStretch()

        main_layout.addWidget(control_widget)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Результаты будут отображены здесь...")
        self.output_text.setMinimumHeight(200)
        main_layout.addWidget(self.output_text)

        self.setCentralWidget(main_widget)

        self.select_image_button.clicked.connect(self.select_image)
        self.hide_message_button.clicked.connect(self.hide_message)
        self.extract_message_button.clicked.connect(self.extract_message)
        self.save_image_button.clicked.connect(self.save_image)
        self.test_cdb_button.clicked.connect(self.test_cdb)

    def select_image(self):
        #Выбор изображения для обработки.
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.pgm *.png *.bmp *.jpg *.jpeg)"
        )
        if file_path:
            self.input_image_format = file_path.split('.')[-1].lower()
            self.image = QImage(file_path)
            self.output_text.append(f"Изображение загружено: {file_path}")

    def hide_message(self):
        #Встраивание сообщения в изображение.
        if self.image is None:
            self.output_text.append("Ошибка: изображение не загружено.")
            return

        # Получение параметров из полей ввода
        try:
            self.cdb_coeff = float(self.cdb_coeff_input.text())
            self.cdb_range = int(self.cdb_range_input.text())
        except ValueError:
            self.output_text.append("Ошибка: неверные значения параметров.")
            return

        # Получение текста из поля ввода
        message = self.message_input.toPlainText()
        if not message:
            self.output_text.append("Ошибка: текст для встраивания не введен.")
            return

        # Преобразование текста в биты
        message_bits = self.text_to_bits(message)
        self.bit_size = len(message_bits)
        self.output_text.append(f"Размер сообщения в битах: {self.bit_size}")

        self.output_text.append(f"Сообщение для встраивания: {message}")

        # Встраивание сообщения
        self.modified_image = self.cdb_inject(message_bits, self.image)
        self.output_text.append("Сообщение успешно встроено в изображение.\n")

    def extract_message(self):
        #Извлечение сообщения из изображения.
        if not hasattr(self, 'modified_image'):
            self.output_text.append("Ошибка: обработанное изображение отсутствует.")
            return

        # Извлечение сообщения
        img = self.modified_image
        message_bits = self.cdb_extract(img)

        # Преобразование битов в текст
        extracted_text = self.bits_to_text(message_bits)
        self.output_text.append(f"Извлеченное сообщение: {extracted_text}\n")  # Вывод в основное поле

    def save_image(self):
        #Сохранение обработанного изображения.
        if not hasattr(self, 'modified_image') or not self.input_image_format:
            self.output_text.append("Ошибка: изображение для сохранения отсутствует.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", f"{self.input_image_format.upper()} (*.{self.input_image_format})"
        )
        if file_path:
            self.modified_image.save(file_path, self.input_image_format)
            self.output_text.append(f"Изображение сохранено: {file_path}\n")

    def test_cdb(self):
        #Тестирование метода CDB.
        if self.image is None:
            self.output_text.append("Ошибка: изображение не загружено.")
            return

        # Получение параметров из полей ввода
        try:
            self.cdb_coeff = float(self.cdb_coeff_input.text())
            self.cdb_range = int(self.cdb_range_input.text())
        except ValueError:
            self.output_text.append("Ошибка: неверные значения параметров.")
            return

        # Получение текста из поля ввода
        message = self.message_input.toPlainText()
        if not message:
            self.output_text.append("Ошибка: текст для встраивания не введен.")
            return

        # Преобразование текста в биты
        message_bits = self.text_to_bits(message)
        self.bit_size = len(message_bits)  # Обновляем bit_size

        self.output_text.append(f"Оригинальное сообщение: {message}")

        # Встраивание и извлечение сообщения
        img = self.image
        modified_image = self.cdb_inject(message_bits, img)
        extracted_bits = self.cdb_extract(modified_image)

        # Преобразование битов в текст
        extracted_text = self.bits_to_text(extracted_bits)

        # Вывод результатов
        self.output_text.append(f"Извлеченное сообщение: {extracted_text}")

        # Оценка процента ошибок (сравнение битов)
        min_len = min(len(message_bits), len(extracted_bits))
        if min_len > 0: 
            error_rate = sum(1 for i in range(min_len) if message_bits[i] != extracted_bits[i]) / min_len * 100
            self.output_text.append(f"Процент ошибок: {error_rate:.2f}%\n")
        else:
            self.output_text.append("Невозможно оценить процент ошибок: нет битов для сравнения.\n")

    def cdb_inject(self, message_bits: list, img: QImage) -> QImage:
        #Встраивание сообщения в изображение по методу CDB.
        gen = np.random.RandomState(self.seed)
        new_img = QImage(img)  # Создаем копию изображения для изменений
        width = new_img.width()
        height = new_img.height()

        for bit in message_bits:
            x = gen.randint(0, width)
            y = gen.randint(0, height)

            pixel_color = new_img.pixelColor(x, y)
            red = pixel_color.redF()
            green = pixel_color.greenF()
            blue = pixel_color.blueF()
            brightness = 0.299 * red + 0.587 * green + 0.114 * blue
            new_blue = blue + (2 * bit - 1) * brightness * self.cdb_coeff
            new_blue = max(0.0, min(1.0, new_blue))
            pixel_color.setBlueF(new_blue)
            new_img.setPixelColor(x, y, pixel_color)
        return new_img

    def cdb_extract(self, img: QImage) -> list:
        #Извлечение сообщения из изображения по методу CDB.
        message_bits = []
        gen = np.random.RandomState(self.seed)
        width = img.width()
        height = img.height()
        for _ in range(self.bit_size):
            x = gen.randint(0, width)
            y = gen.randint(0, height)
            x_sum = sum(
                img.pixelColor(i, y).blueF()
                for i in range(max(x, 0), min(x + self.cdb_range, width - 1) + 1)
            )
            y_sum = sum(
                img.pixelColor(x, i).blueF()
                for i in range(max(y, 0), min(y + self.cdb_range, height - 1) + 1)
            )
            predicted_blue = (x_sum + y_sum - 2 * img.pixelColor(x, y).blueF()) / (
                4 * self.cdb_range
            )
            message_bits.append(int(img.pixelColor(x, y).blueF() > predicted_blue))
        return message_bits

    def text_to_bits(self, text: str) -> list:
        #Преобразование текста в список битов.
        bits = []
        for char in text:
            binary = bin(ord(char))[2:].zfill(8)
            bits.extend([int(b) for b in binary])
        return bits

    def bits_to_text(self, bits: list) -> str:
        #Преобразование списка битов в текст.
        text = ""
        if len(bits) % 8 != 0:
            self.output_text.append("Предупреждение: неполное количество битов для преобразования в текст.")
            return text

        for i in range(0, len(bits), 8):
            byte = bits[i:i + 8]
            char_code = int("".join(str(b) for b in byte), 2)
            try:
                text += chr(char_code)
            except ValueError:
                self.output_text.append(f"Ошибка: Недопустимый код символа: {char_code}")
                return text

        return text

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())