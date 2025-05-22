import sys
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit
)
from PySide6.QtGui import QRegularExpressionValidator
import bitarray
import bitarray.util


class Encoder:
    _CHAR_MAPPING = {
        "A": "Α", "B": "Β", "C": "С", "E": "Ε", "H": "Η",
        "K": "Κ", "M": "Μ", "P": "Ρ", "S": "Ѕ", "T": "Τ",
        "W": "Ԝ", "X": "Χ", "Y": "ϒ", "Z": "Ζ", "a": "а",
        "c": "ϲ", "d": "ԁ", "e": "е", "h": "һ", "j": "ϳ",
        "q": "ԛ", "z": "ᴢ"
    }
    _REVERSE_MAPPING = {v: k for k, v in _CHAR_MAPPING.items()}

    @classmethod
    def calculate_capacity(cls, text: str) -> int:
        return sum(1 for c in text if c in cls._CHAR_MAPPING or c in cls._REVERSE_MAPPING)

    @classmethod
    def encode_message(cls, source: str, message: str) -> tuple[int, str]:
        msg_bits = bitarray.bitarray()
        msg_bits.frombytes(message.encode("utf-8"))
        seed = np.random.randint(0, 20_000_000)
        chars = list(source)
        indices = np.random.RandomState(seed).permutation(len(chars)).tolist()

        bit_counter = 0
        for idx in indices:
            current_char = chars[idx]
            if current_char in cls._REVERSE_MAPPING:
                current_char = cls._REVERSE_MAPPING[current_char]

            if current_char in cls._CHAR_MAPPING:
                if bit_counter >= len(msg_bits):
                    break
                
                chars[idx] = cls._CHAR_MAPPING[current_char] if msg_bits[bit_counter] else current_char
                bit_counter += 1

        return seed, "".join(chars)

    @classmethod
    def decode_message(cls, encoded_text: str, msg_length: int, seed: int) -> str:
        msg_bits = bitarray.bitarray()
        indices = np.random.RandomState(seed).permutation(len(encoded_text)).tolist()

        for idx in indices:
            char = encoded_text[idx]
            if char in cls._CHAR_MAPPING:
                msg_bits.append(0)
            elif char in cls._REVERSE_MAPPING:
                msg_bits.append(1)
            
            if len(msg_bits) >= msg_length * 8:
                break

        return msg_bits[:msg_length*8].tobytes().decode("utf-8", "ignore")


class ControlPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._configure_validators()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        self.encode_btn = QPushButton("Encode")
        self.decode_btn = QPushButton("Decode")
        self.capacity_btn = QPushButton("Capacity Check")
        
        self.seed_input = QLineEdit(placeholderText="Seed")
        self.msg_length_input = QLineEdit(placeholderText="Message Length")

        self.main_layout.addStretch()
        self.main_layout.addWidget(self.encode_btn)
        self.main_layout.addWidget(self.decode_btn)
        self.main_layout.addWidget(self.capacity_btn)
        self.main_layout.addWidget(self.seed_input)
        self.main_layout.addWidget(self.msg_length_input)
        self.main_layout.addStretch()

    def _configure_validators(self):
        numeric_validator = QRegularExpressionValidator(r"^\d+$")
        self.seed_input.setValidator(numeric_validator)
        self.msg_length_input.setValidator(numeric_validator)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Steganography Tool")
        self._create_widgets()
        self._connect_actions()

    def _create_widgets(self):
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)

        self.editor_panel = QWidget()
        self.editor_layout = QHBoxLayout(self.editor_panel)

        self.source_editor = QTextEdit()
        self.result_editor = QTextEdit()
        self.controls = ControlPanel()

        self.editor_layout.addWidget(self.source_editor)
        self.editor_layout.addWidget(self.controls)
        self.editor_layout.addWidget(self.result_editor)

        self.message_input = QLineEdit(placeholderText="Enter message here")

        self.main_layout.addWidget(self.editor_panel)
        self.main_layout.addWidget(self.message_input)
        self.setCentralWidget(self.central_widget)

    def _connect_actions(self):
        self.controls.capacity_btn.clicked.connect(self._handle_capacity_check)
        self.controls.encode_btn.clicked.connect(self._perform_encoding)
        self.controls.decode_btn.clicked.connect(self._perform_decoding)

    def _handle_capacity_check(self):
        text = self.source_editor.toPlainText()
        capacity = Encoder.calculate_capacity(text)
        self.controls.msg_length_input.setText(str(capacity // 8))

    def _perform_encoding(self):
        try:
            source = self.source_editor.toPlainText()
            message = self.message_input.text()
            
            seed, result = Encoder.encode_message(source, message)
            self.controls.seed_input.setText(str(seed))
            self.controls.msg_length_input.setText(str(len(message)))
            self.result_editor.setPlainText(result)
        except Exception as e:
            self.result_editor.setPlainText(f"Encoding Error: {str(e)}")

    def _perform_decoding(self):
        try:
            encoded_text = self.source_editor.toPlainText()
            msg_length = int(self.controls.msg_length_input.text())
            seed = int(self.controls.seed_input.text())
            
            decoded = Encoder.decode_message(encoded_text, msg_length, seed)
            self.message_input.setText(decoded)
        except Exception as e:
            self.message_input.setText(f"Decoding Error: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 500)
    window.show()
    sys.exit(app.exec())