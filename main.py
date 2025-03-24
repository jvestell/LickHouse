import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeView, QFileSystemModel, QLabel, QSplitter, QMessageBox
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QIcon, QFont
import json

from lick_editor import LickEditor
from create_lick_dialog import CreateLickDialog

class LickHouseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LickHouse - Guitar Lick Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set app style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ECECEC;
            }
            QTreeView {
                background-color: #F5F5F5;
                border-radius: 5px;
                padding: 5px;
                selection-background-color: #3498DB;
                font-size: 12px;
            }
            QSplitter::handle {
                background-color: #CCCCCC;
            }
            QLabel {
                color: #2C3E50;
            }
        """)
        
        # Set up data directory
        self.base_dir = os.path.join(os.path.expanduser("~"), "LickHouse")
        self.init_directory_structure()
        
        # Main layout setup
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create a splitter for resizable sections
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - File browser
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title for library section
        library_label = QLabel("Lick Library")
        library_label.setFont(QFont("Arial", 14, QFont.Bold))
        library_label.setAlignment(Qt.AlignCenter)
        library_label.setStyleSheet("color: #2C3E50; margin-bottom: 10px;")
        left_layout.addWidget(library_label)
        
        # Folder view
        self.folder_view = QTreeView()
        self.folder_view.setMinimumWidth(250)
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.base_dir)
        
        # Configure model to show directories and .lick files
        self.file_model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.file_model.setNameFilters(["*.lick"])  # Only filter files, not directories
        self.file_model.setNameFilterDisables(False)
        
        # Set up the view
        self.folder_view.setModel(self.file_model)
        self.folder_view.setRootIndex(self.file_model.index(self.base_dir))
        self.folder_view.clicked.connect(self.on_file_selected)
        self.folder_view.setColumnWidth(0, 200)
        self.folder_view.setHeaderHidden(True)
        self.folder_view.hideColumn(1)  # Size column
        self.folder_view.hideColumn(2)  # Type column
        self.folder_view.hideColumn(3)  # Date modified column
        self.folder_view.setAnimated(True)  # Enable animations for expanding/collapsing
        self.folder_view.setIndentation(20)  # Set indentation for better visual hierarchy
        
        # Force refresh of the view
        self.file_model.setRootPath(self.base_dir)
        self.folder_view.expandAll()  # Expand all folders by default
        left_layout.addWidget(self.folder_view)
        
        splitter.addWidget(left_panel)
        
        # Right panel - Lick editor and buttons
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        # Create lick button
        create_button = QPushButton("Create New Lick")
        create_button.setMinimumHeight(40)
        create_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #1F618D;
            }
        """)
        create_button.clicked.connect(self.create_new_lick)
        right_layout.addWidget(create_button)
        
        # Lick editor
        self.lick_editor = LickEditor()
        right_layout.addWidget(self.lick_editor)
        
        # Connect signals
        self.lick_editor.save_requested.connect(self.save_current_lick)
        self.lick_editor.delete_requested.connect(self.delete_current_lick)
        
        splitter.addWidget(right_panel)
        
        # Set the initial splitter sizes
        splitter.setSizes([250, 950])
        
        self.current_lick_path = None

    def init_directory_structure(self):
        """Initialize the default directory structure if it doesn't exist"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            
        default_folders = ["E Licks", "A Licks", "D Licks", "G Licks", "B Licks", "F Licks", "C Licks"]
        for folder in default_folders:
            folder_path = os.path.join(self.base_dir, folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
    
    def on_file_selected(self, index):
        """Handle file selection in the tree view"""
        try:
            path = self.file_model.filePath(index)
            if not path:
                return
                
            # Check if it's a file and has .lick extension
            if os.path.isfile(path) and path.lower().endswith('.lick'):
                self.current_lick_path = path
                self.load_lick(path)
            else:
                self.current_lick_path = None
        except Exception as e:
            print(f"Error in file selection: {str(e)}")  # Debug print
            self.current_lick_path = None
    
    def load_lick(self, path):
        """Load lick data from file into the editor"""
        try:
            if not os.path.isfile(path):
                raise FileNotFoundError(f"File not found: {path}")
                
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                if not content.strip():
                    raise ValueError("File is empty")
                    
                lick_data = json.loads(content)
                if not isinstance(lick_data, dict):
                    raise ValueError("Invalid lick data format")
                    
                # Ensure required fields exist
                if "name" not in lick_data:
                    lick_data["name"] = os.path.splitext(os.path.basename(path))[0]
                if "measures" not in lick_data:
                    lick_data["measures"] = [{"notes": []}]
                    
                # Load into editor
                self.lick_editor.load_lick(lick_data)
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")  # Debug print
            QMessageBox.warning(self, "Error Loading Lick", f"Invalid JSON format in lick file: {str(e)}")
            self.current_lick_path = None
        except FileNotFoundError as e:
            print(f"File not found: {str(e)}")  # Debug print
            QMessageBox.warning(self, "Error Loading Lick", str(e))
            self.current_lick_path = None
        except Exception as e:
            print(f"General error: {str(e)}")  # Debug print
            QMessageBox.warning(self, "Error Loading Lick", f"Could not load lick file: {str(e)}")
            self.current_lick_path = None
    
    def save_current_lick(self):
        """Save the current lick to file"""
        if not self.current_lick_path:
            QMessageBox.information(self, "No Lick Selected", "Please create a new lick or select an existing one to save.")
            return
        
        try:
            # Get data from editor
            lick_data = {
                "name": self.lick_editor.title_label.text(),
                "measures": self.lick_editor.fretboard.measures
            }
            
            # Save to file
            with open(self.current_lick_path, 'w', encoding='utf-8') as file:
                json.dump(lick_data, file, indent=4)
                
            QMessageBox.information(self, "Lick Saved", f"Lick saved successfully to {os.path.basename(self.current_lick_path)}.")
        except Exception as e:
            QMessageBox.warning(self, "Error Saving Lick", f"Could not save lick file: {str(e)}")
    
    def delete_current_lick(self):
        """Delete the current lick"""
        if not self.current_lick_path:
            QMessageBox.information(self, "No Lick Selected", "Please select a lick to delete.")
            return
            
        if not os.path.exists(self.current_lick_path):
            QMessageBox.warning(self, "Error", "Selected file no longer exists.")
            self.current_lick_path = None
            return
            
        reply = QMessageBox.question(self, "Confirm Delete", 
            f"Are you sure you want to delete '{os.path.basename(self.current_lick_path)}'?",
            QMessageBox.Yes | QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            try:
                os.remove(self.current_lick_path)
                self.current_lick_path = None
                self.lick_editor.load_lick({"name": "New Lick", "measures": [{"notes": []}]})
                QMessageBox.information(self, "Success", "Lick deleted successfully.")
            except PermissionError:
                QMessageBox.warning(self, "Error", "Permission denied. Cannot delete the file.")
            except Exception as e:
                QMessageBox.warning(self, "Error Deleting Lick", f"Could not delete lick file: {str(e)}")
                self.current_lick_path = None
                self.lick_editor.load_lick({"name": "New Lick", "measures": [{"notes": []}]})
    
    def create_new_lick(self):
        """Open dialog to create a new lick"""
        dialog = CreateLickDialog(self.base_dir)
        if dialog.exec_():
            lick_name, lick_path = dialog.get_lick_info()
            
            # Validate lick name
            if not lick_name or lick_name.isspace():
                QMessageBox.warning(self, "Invalid Name", "Please enter a valid lick name.")
                return
                
            # Check if file already exists
            if os.path.exists(lick_path):
                reply = QMessageBox.question(self, "File Exists", 
                    f"A lick with the name '{lick_name}' already exists in this folder. Do you want to overwrite it?",
                    QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            
            # Create empty lick file
            empty_lick = {
                "name": lick_name,
                "measures": [{"notes": []}]  # Start with one empty measure
            }
            
            try:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(lick_path), exist_ok=True)
                
                # Save the file
                with open(lick_path, 'w', encoding='utf-8') as file:
                    json.dump(empty_lick, file, indent=4)
                
                # Open the new lick in the editor
                self.current_lick_path = lick_path
                self.lick_editor.load_lick(empty_lick)
                
                # Update the file view to show the new file
                self.folder_view.setCurrentIndex(self.file_model.index(lick_path))
                
                QMessageBox.information(self, "Success", f"New lick '{lick_name}' created successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Error Creating Lick", f"Could not create lick file: {str(e)}")

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    window = LickHouseApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()