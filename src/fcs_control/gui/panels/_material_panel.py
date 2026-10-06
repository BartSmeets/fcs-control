"""
Builds MaterialPanel for material selection 

(which is used in logging)

"""
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


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

        self.elements: list[QLineEdit] = []

        # Intial Comboboxes
        self.add_line()


        # Add combox button
        add_btn = QPushButton("Add Element")
        add_btn.clicked.connect(self.add_line)
        layout.addWidget(add_btn)
        layout.addStretch()

    def add_line(self):
        """
        Add a Combobox widget to the MaterialPanel

        """
        row = QHBoxLayout()

        # Label
        label = QLabel(f"Element {len(self.elements) + 1}:")
        row.addWidget(label)

        # Combobox
        line = QLineEdit()
        row.addWidget(line)

        # Add remove button
        remove_btn = QPushButton('X')
        remove_btn.clicked.connect(lambda: self.remove_lineedit(line, row))
        row.addWidget(remove_btn)
        
        self.elements.append(line) # Stores the information (individual lines)
        self.material_layout.addLayout(row) # Adds row to material layout

    def remove_lineedit(self, line: QLineEdit, row: QHBoxLayout):
        """
        Remove a combobox by removing its row

        """
        self.elements.remove(line)

        while row.count():
            item = row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def get_settings(self):
        """
        Returns
        -------
        list[str]
            List of line contents (material selection)
            
        """
        return [
            line.text()
            for line in self.elements
        ]