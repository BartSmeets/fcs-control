from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

ELEMENTS = [
    'H2', 'D2', 'He',
    'C', 'C60', 'CO2', 'N2', 'O',
    'Al', 'Si', 'Ar',
    'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
    'Nb', 'Rh', 'Pd', 'Ag'
]

class MaterialPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__('Material Selection', parent)

        layout = QVBoxLayout(self)
        self.material_layout = QVBoxLayout()
        layout.addLayout(self.material_layout)

        self.elements = []

        self.add_combobox()
        self.add_combobox()

        add_btn = QPushButton("Add Element")
        add_btn.clicked.connect(self.add_combobox)
        layout.addWidget(add_btn)
        layout.addStretch()

    def add_combobox(self):
        row = QHBoxLayout()

        label = QLabel(f"Element {len(self.elements) + 1}:")
        row.addWidget(label)

        combo = QComboBox()
        combo.setEditable(True)
        combo.addItems(ELEMENTS)
        row.addWidget(combo)

        # Add remove button
        remove_btn = QPushButton('X')
        remove_btn.clicked.connect(lambda: self.remove_combobox(combo, row))
        row.addWidget(remove_btn)
        
        self.elements.append(combo)
        self.material_layout.addLayout(row)

    def remove_combobox(self, combo, row):
        self.elements.remove(combo)

        while row.count():
            item = row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def get_settings(self):
        return [
            box.currentText()
            for box in self.elements
        ]