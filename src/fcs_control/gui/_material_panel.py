"""
Builds MaterialPanel for material selection 

(which is used in logging)

"""
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

# Elements to choose from
ELEMENTS = [
    'H2', 'D2', 'He',
    'C', 'C60', 'CO2', 'N2', 'O',
    'Al', 'Si', 'Ar',
    'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
    'Nb', 'Rh', 'Pd', 'Ag'
]


class MaterialPanel(QGroupBox):
    """
    Build the material panel

    Intially combines two option
    But can be extended, see `add_combobox` and `remove_combobox`

    """
    def __init__(self, parent=None):
        super().__init__('Material Selection', parent)

        # Layout
        layout = QVBoxLayout(self)  # Total layout
        self.material_layout = QVBoxLayout()    # Materials selection (no button)
        layout.addLayout(self.material_layout)

        self.elements = []

        # Intial Comboboxes
        self.add_combobox()
        self.add_combobox()

        # Add combox button
        add_btn = QPushButton("Add Element")
        add_btn.clicked.connect(self.add_combobox)
        layout.addWidget(add_btn)
        layout.addStretch()

    def add_combobox(self):
        """
        Add a Combobox widget to the MaterialPanel

        """
        row = QHBoxLayout()

        # Label
        label = QLabel(f"Element {len(self.elements) + 1}:")
        row.addWidget(label)

        # Combobox
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItems(ELEMENTS)
        row.addWidget(combo)

        # Add remove button
        remove_btn = QPushButton('X')
        remove_btn.clicked.connect(lambda: self.remove_combobox(combo, row))
        row.addWidget(remove_btn)
        
        self.elements.append(combo) # Stores the information (individual comboboxes)
        self.material_layout.addLayout(row) # Adds row to material layout

    def remove_combobox(self, combo, row):
        """
        Remove a combobox by removing its row

        """
        self.elements.remove(combo)

        while row.count():
            item = row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def get_settings(self):
        """
        Returns
        -------
        list[str]
            List of box contents (material selection)
            
        """
        return [
            box.currentText()
            for box in self.elements
        ]