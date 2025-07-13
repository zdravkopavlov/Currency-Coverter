from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QFont, QDoubleValidator
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit

EXCHANGE_RATE = 1.95583

# Custom QLineEdit that intercepts Space and Tab
class NoSpaceLineEdit(QLineEdit):
    def __init__(self, switch_callback=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.switch_callback = switch_callback

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Space, Qt.Key_Tab):
            if self.switch_callback:
                self.switch_callback()
            return  # Prevent entering space/tab
        super().keyPressEvent(event)

class ConverterWorkflow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Конвертор BGN → EUR (прототип)")
        self.mode = 0  # 0 = цена, 1 = плащане

        font = QFont("Arial", 20)

        # Step 1: Цена
        self.label_price = QLabel("Цена (лв.):")
        self.label_price.setFont(font)
        self.input_price = NoSpaceLineEdit(self.toggle_mode)
        self.input_price.setFont(font)
        self.input_price.setPlaceholderText("0.00")
        self.input_price.setMaxLength(10)
        self.input_price.setValidator(QDoubleValidator(0.00, 99999.99, 2))
        self.input_price.textChanged.connect(self.update_eur)
        self.label_eur = QLabel("Евро: 0.00 €")
        self.label_eur.setFont(font)

        # Step 2: Плащане
        self.label_paid = QLabel("Дадено (лв.):")
        self.label_paid.setFont(font)
        self.input_paid = NoSpaceLineEdit(self.toggle_mode)
        self.input_paid.setFont(font)
        self.input_paid.setPlaceholderText("0.00")
        self.input_paid.setMaxLength(10)
        self.input_paid.setValidator(QDoubleValidator(0.00, 99999.99, 2))
        self.input_paid.textChanged.connect(self.update_change)
        self.label_change = QLabel("Ресто (евро): 0.00 €")
        self.label_change.setFont(font)

        # Layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label_price)
        self.layout.addWidget(self.input_price)
        self.layout.addWidget(self.label_eur)
        self.layout.addWidget(self.label_paid)
        self.layout.addWidget(self.input_paid)
        self.layout.addWidget(self.label_change)
        self.setLayout(self.layout)
        self.setFixedSize(500, 250)

        self.set_mode(0)
        self.input_price.setFocus()

    def set_mode(self, mode):
        self.mode = mode
        if mode == 0:
            self.label_price.show()
            self.input_price.show()
            self.label_eur.show()
            self.label_paid.hide()
            self.input_paid.hide()
            self.label_change.hide()
            self.input_price.setFocus()
            self.input_price.selectAll()
        else:
            self.label_price.hide()
            self.input_price.hide()
            self.label_eur.hide()
            self.label_paid.show()
            self.input_paid.show()
            self.label_change.show()
            self.input_paid.setFocus()
            self.input_paid.selectAll()
            self.update_change()
        self.adjustSize()  # Fix window resizing

    def toggle_mode(self):
        if self.mode == 0 and self.parse_value(self.input_price.text()) > 0:
            self.set_mode(1)
        else:
            self.set_mode(0)

    def update_eur(self):
        value = self.parse_value(self.input_price.text())
        eur = value / EXCHANGE_RATE if value else 0
        self.label_eur.setText(f"Евро: {eur:.2f} €")

    def update_change(self):
        price = self.parse_value(self.input_price.text())
        paid = self.parse_value(self.input_paid.text())
        change = (paid - price) / EXCHANGE_RATE if paid > 0 and price > 0 else 0
        self.label_change.setText(f"Ресто (евро): {change:.2f} €")

    def parse_value(self, text):
        try:
            return float(text.replace(',', '.'))
        except Exception:
            return 0

    def keyPressEvent(self, event):
        # Esc closes the window
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    import sys
    app = QApplication([])
    w = ConverterWorkflow()
    w.show()
    sys.exit(app.exec_())
