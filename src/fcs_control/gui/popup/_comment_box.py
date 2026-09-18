from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QTextEdit, QVBoxLayout


class CommentBox(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Comment Box")



        layout = QVBoxLayout()
        description = QLabel("Do you have any final comments?")
        self.textbox = QTextEdit()
        self.submit = QPushButton("Send it!")
        self.submit.clicked.connect(self.accept)

        layout.addWidget(description)
        layout.addWidget(self.textbox)
        layout.addWidget(self.submit)

        self.setLayout(layout)

    def get_comment(self) -> str:
        return self.textbox.toPlainText()
