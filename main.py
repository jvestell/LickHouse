import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeView, QFileSystemModel, QLabel, QSplitter, QMessageBox, QMenu, QFileDialog
from PyQt5.QtCore import Qt, QDir, QMimeData
from PyQt5.QtGui import QIcon, QFont, QDragEnterEvent, QDropEvent
import json
import shutil

from lick_editor import LickEditor
from create_lick_dialog import CreateLickDialog

class CustomTreeView(QTreeView):
    def __init__(self, parent=None, base_dir=None):
        super().__init__(parent)
        self.base_dir = base_dir
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTreeView.InternalMove)
        self.setSelectionMode(QTreeView.SingleSelection)
        
    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        index = self.indexAt(event.pos())
        if not index.isValid():
            return
            
        path = self.model().filePath(index)
        if not path:
            return
            
        # Create context menu
        menu = QMenu(self)
        
        # Add delete action for both files and folders
        if os.path.isfile(path) and path.lower().endswith('.lick'):
            delete_action = menu.addAction("Delete File")
            delete_action.triggered.connect(lambda: self.delete_item(path))
        elif os.path.isdir(path) and path != self.base_dir:
            delete_action = menu.addAction("Delete Folder")
            delete_action.triggered.connect(lambda: self.delete_item(path))
        
        # Show the menu
        menu.exec_(self.mapToGlobal(event.pos()))
    
    def delete_item(self, path):
        """Delete a file or folder"""
        is_folder = os.path.isdir(path)
        item_type = "Folder" if is_folder else "File"
        name = os.path.basename(path)
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{name}' and all its contents?" if is_folder else f"Are you sure you want to delete '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Get the parent directory before deletion
                parent_dir = os.path.dirname(path)
                
                if is_folder:
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                
                # Refresh the model by setting the root path again
                self.model().setRootPath(self.model().rootPath())
                
                QMessageBox.information(self, "Success", f"{item_type} deleted successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete {item_type.lower()}: {str(e)}")
    
    def dragEnterEvent(self, event):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            # Check if any of the dragged files are .lick files
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.lick'):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move events"""
        if event.mimeData().hasUrls():
            # Check if we're over a valid drop target (folder)
            index = self.indexAt(event.pos())
            if index.isValid():
                path = self.model().filePath(index)
                if os.path.isdir(path) or path == self.base_dir:  # Allow root directory
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def dropEvent(self, event):
        """Handle drop events for files"""
        if not event.mimeData().hasUrls():
            event.ignore()
            return
            
        # Get the target folder
        target_index = self.indexAt(event.pos())
        if not target_index.isValid():
            event.ignore()
            return
            
        target_path = self.model().filePath(target_index)
        if not os.path.isdir(target_path):
            target_path = os.path.dirname(target_path)
            
        success = False
        for url in event.mimeData().urls():
            source_path = url.toLocalFile()
            if not source_path.lower().endswith('.lick'):
                continue
                
            try:
                filename = os.path.basename(source_path)
                target_file = os.path.join(target_path, filename)
                
                # Handle duplicate files
                if os.path.exists(target_file):
                    reply = QMessageBox.question(
                        self,
                        "File Exists",
                        f"A file with the name '{filename}' already exists in this folder. Do you want to overwrite it?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        continue
                
                # Move the file instead of copying
                shutil.move(source_path, target_file)
                success = True
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not move file: {str(e)}")
        
        if success:
            # Refresh the view
            self.model().setRootPath(self.model().rootPath())
            self.expandAll()
            event.acceptProposedAction()
        else:
            event.ignore()

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
        
        # Set up data directory in Documents folder for cloud sync
        self.base_dir = os.path.join(os.path.expanduser("~"), "Documents", "LickHouse")
        self.init_directory_structure()
        
        # Check if the directory is in a cloud-synced location
        self.check_cloud_sync()
        
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
        
        # Folder view using custom TreeView
        self.folder_view = CustomTreeView(base_dir=self.base_dir)
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

    def check_cloud_sync(self):
        """Check if the LickHouse directory is in a cloud-synced location"""
        # Common Google Drive paths
        google_drive_paths = [
            os.path.expanduser("~\\Google Drive"),
            os.path.expanduser("~\\Google Drive\\My Drive"),
            os.path.expanduser("~\\Google Drive\\Shared drives")
        ]
        
        # Find the first existing Google Drive path
        google_drive_path = None
        for path in google_drive_paths:
            if os.path.exists(path):
                google_drive_path = path
                break
        
        if google_drive_path:
            # If we found Google Drive, suggest using it
            reply = QMessageBox.question(
                self,
                "Google Drive Sync",
                f"Google Drive was detected at: {google_drive_path}\n\n"
                "Would you like to store your licks in Google Drive for automatic syncing?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # Create LickHouse folder in Google Drive
                self.base_dir = os.path.join(google_drive_path, "LickHouse")
                self.init_directory_structure()
                
                # Show sync instructions
                QMessageBox.information(
                    self,
                    "Sync Setup Complete",
                    "Your licks will now automatically sync with Google Drive.\n\n"
                    "Important notes:\n"
                    "1. Changes will sync automatically when you save\n"
                    "2. You can access your licks from any device with Google Drive\n"
                    "3. Make sure Google Drive is running for sync to work\n"
                    "4. If you see a cloud icon in Google Drive, the file is synced"
                )
                return
        
        # If no Google Drive found or user declined, use Documents folder
        documents_path = os.path.expanduser("~\\Documents")
        cloud_sync_warning = """
            For the best experience with LickHouse across multiple computers:
            1. Make sure your Documents folder is synced with a cloud service (Dropbox, Google Drive, or OneDrive)
            2. The LickHouse folder will be created in your Documents folder
            3. Your licks will automatically sync across all your computers
            
            Would you like to continue with the default location in Documents?
        """
        
        reply = QMessageBox.question(
            self,
            "Cloud Sync Recommendation",
            cloud_sync_warning,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.No:
            # Let user choose a different location
            new_dir = QFileDialog.getExistingDirectory(
                self,
                "Choose LickHouse Location",
                documents_path,
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            if new_dir:
                self.base_dir = os.path.join(new_dir, "LickHouse")
                self.init_directory_structure()
            else:
                # If user cancels, use default location
                self.base_dir = os.path.join(documents_path, "LickHouse")
                self.init_directory_structure()

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    window = LickHouseApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()