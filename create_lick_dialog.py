import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTreeView, QFileSystemModel,
                             QDialogButtonBox)
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QFont

class CreateLickDialog(QDialog):
    def __init__(self, base_dir, parent=None):
        super().__init__(parent)
        self.base_dir = base_dir
        self.selected_dir = base_dir
        self.setWindowTitle("Create New Lick")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Set dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #ECECEC;
            }
            QLabel {
                color: #2C3E50;
                font-weight: bold;
            }
            QLineEdit {
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #BDC3C7;
                background-color: #FFFFFF;
            }
            QTreeView {
                background-color: #FFFFFF;
                border-radius: 4px;
                border: 1px solid #BDC3C7;
                selection-background-color: #3498DB;
            }
            QPushButton {
                background-color: #3498DB;
                color: white;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #1F618D;
            }
            QDialogButtonBox > QPushButton {
                min-width: 80px;
            }
        """)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Dialog title
        title_label = QLabel("Create New Lick")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2C3E50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Lick name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Lick Name:")
        name_layout.addWidget(name_label)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter lick name...")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Folder selection
        folder_label = QLabel("Select Folder:")
        folder_label.setStyleSheet("margin-top: 10px;")
        layout.addWidget(folder_label)
        
        # Folder tree view
        self.folder_view = QTreeView()
        self.folder_view.setMinimumHeight(200)
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.base_dir)
        self.file_model.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
        
        self.folder_view.setModel(self.file_model)
        self.folder_view.setRootIndex(self.file_model.index(self.base_dir))
        self.folder_view.clicked.connect(self.on_folder_selected)
        self.folder_view.setColumnWidth(0, 250)
        self.folder_view.hideColumn(1)  # Size column
        self.folder_view.hideColumn(2)  # Type column
        self.folder_view.hideColumn(3)  # Date modified column
        
        layout.addWidget(self.folder_view)
        
        # Selected path display
        self.path_label = QLabel(f"Selected: {os.path.relpath(self.base_dir, self.base_dir)}")
        self.path_label.setStyleSheet("font-style: italic; font-weight: normal; color: #7F8C8D;")
        layout.addWidget(self.path_label)
        
        # Create new folder button
        new_folder_btn = QPushButton("Create New Folder")
        new_folder_btn.clicked.connect(self.create_new_folder)
        layout.addWidget(new_folder_btn)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_folder_selected(self, index):
        """Handle folder selection in the tree view"""
        self.selected_dir = self.file_model.filePath(index)
        rel_path = os.path.relpath(self.selected_dir, self.base_dir)
        self.path_label.setText(f"Selected: {rel_path}")
    
    def create_new_folder(self):
        """Create a new subfolder in the selected directory"""
        if not self.selected_dir:
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Folder")
        dialog.setStyleSheet(self.styleSheet())
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(20, 20, 20, 20)
        
        # Folder name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Folder Name:"))
        folder_name_input = QLineEdit()
        folder_name_input.setPlaceholderText("Enter folder name...")
        name_layout.addWidget(folder_name_input)
        dialog_layout.addLayout(name_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(button_box)
        
        if dialog.exec_():
            folder_name = folder_name_input.text().strip()
            if folder_name:
                new_folder_path = os.path.join(self.selected_dir, folder_name)
                try:
                    os.makedirs(new_folder_path, exist_ok=True)
                    # Update tree view to show new folder
                    self.folder_view.setCurrentIndex(
                        self.file_model.index(new_folder_path)
                    )
                    self.selected_dir = new_folder_path
                    rel_path = os.path.relpath(self.selected_dir, self.base_dir)
                    self.path_label.setText(f"Selected: {rel_path}")
                except Exception as e:
                    print(f"Error creating folder: {e}")
    
    def get_lick_info(self):
        """Return the lick name and path"""
        lick_name = self.name_input.text().strip()
        if not lick_name:
            lick_name = "Untitled Lick"
            
        # Create filename with .lick extension
        sanitized_name = lick_name.replace("/", "_").replace("\\", "_")
        lick_path = os.path.join(self.selected_dir, f"{sanitized_name}.lick")
        
        return lick_name, lick_path