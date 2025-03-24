from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QScrollArea, QFrame, QGraphicsView, QGraphicsScene, 
                             QGraphicsItem, QGraphicsTextItem, QGraphicsLineItem,
                             QGraphicsEllipseItem)
from PyQt5.QtCore import Qt, QRectF, QPointF, QMimeData, pyqtSignal
from PyQt5.QtGui import QPen, QFont, QColor, QBrush, QPainter, QDragEnterEvent, QDropEvent, QDrag
import json

class FretboardView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Configure view
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Fretboard dimensions
        self.string_count = 6
        self.fret_count = 12
        self.string_spacing = 30
        self.fret_spacing = 60
        self.left_margin = 40
        self.top_margin = 40
        
        # Current measure and note being edited
        self.current_measure = 0
        self.measures = []
        
        # Store references to graphics items
        self.string_lines = []
        self.fret_lines = []
        self.string_labels = []
        self.note_items = []
        
        # Colors
        self.background_color = QColor("#F5F5F5")  # Light gray background
        self.string_color = QColor("#555555")       # Dark gray strings
        self.fret_color = QColor("#777777")         # Medium gray frets
        self.nut_color = QColor("#333333")          # Darker gray for nut
        self.note_color = QColor("#3498DB")         # Matte blue for notes
        self.text_color = QColor("#FFFFFF")         # White text
        self.string_label_color = QColor("#2C3E50") # Dark blue-gray for labels
        
        # Set background color
        self.setBackgroundBrush(QBrush(self.background_color))
        
        # Draw the fretboard
        self.draw_fretboard()
        
        # Set fixed size based on fretboard dimensions
        width = self.left_margin + (self.fret_count * self.fret_spacing) + 50
        height = self.top_margin + ((self.string_count - 1) * self.string_spacing) + 50
        self.setFixedSize(width, height)
        
        # Adjust the scene rect to fit the fretboard
        self.scene.setSceneRect(0, 0, width, height)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.NoDrag)  # We only want to accept drops, not initiate drags
    
    def draw_fretboard(self):
        """Draw the guitar fretboard with strings and frets"""
        # Clear previous fretboard
        self.clear_all_items()
        
        # Draw strings (horizontal lines)
        for i in range(self.string_count):
            y = self.top_margin + (i * self.string_spacing)
            string_line = self.scene.addLine(
                self.left_margin, y, 
                self.left_margin + (self.fret_count * self.fret_spacing), y,
                QPen(self.string_color, 2)
            )
            self.string_lines.append(string_line)
            
            # Add string name (E, A, D, G, B, E from bottom to top)
            string_names = ["E", "B", "G", "D", "A", "E"]
            string_label = self.scene.addText(string_names[i], QFont("Arial", 10))
            string_label.setDefaultTextColor(self.string_label_color)
            string_label.setPos(self.left_margin - 25, y - 10)
            self.string_labels.append(string_label)
        
        # Draw frets (vertical lines)
        for i in range(self.fret_count + 1):
            x = self.left_margin + (i * self.fret_spacing)
            pen_color = self.nut_color if i == 0 else self.fret_color
            fret_line = self.scene.addLine(
                x, self.top_margin, 
                x, self.top_margin + ((self.string_count - 1) * self.string_spacing),
                QPen(pen_color, (3 if i == 0 else 1))  # Thicker line for nut (first fret)
            )
            self.fret_lines.append(fret_line)
    
    def clear_all_items(self):
        """Clear all graphics items from the scene"""
        # Remove all items from the scene
        for item in self.string_lines + self.fret_lines + self.string_labels + self.note_items:
            if item and item.scene():
                self.scene.removeItem(item)
        
        # Clear all lists
        self.string_lines.clear()
        self.fret_lines.clear()
        self.string_labels.clear()
        self.note_items.clear()
    
    def draw_tablature(self, measure_data):
        """Draw the tablature notes onto the fretboard"""
        if not measure_data or "notes" not in measure_data:
            return
            
        # Clear existing notes
        for item in self.note_items:
            if item and item.scene():
                self.scene.removeItem(item)
        self.note_items.clear()
            
        for note in measure_data["notes"]:
            string_idx = note.get("string")
            fret = note.get("fret")
            
            if string_idx is not None and fret is not None:
                y = self.top_margin + (string_idx * self.string_spacing)
                x = self.left_margin + (fret * self.fret_spacing) - (self.fret_spacing / 2)
                
                # Create note circle with text
                circle = QGraphicsEllipseItem(-10, -10, 20, 20)
                circle.setBrush(QBrush(self.note_color))
                circle.setPen(QPen(Qt.black, 1))
                circle.setPos(x, y)
                self.scene.addItem(circle)
                self.note_items.append(circle)
                
                # Add fret number text
                text = QGraphicsTextItem(str(fret))
                text.setDefaultTextColor(self.text_color)
                text.setFont(QFont("Arial", 9, QFont.Bold))
                # Center the text in the circle
                text_width = text.boundingRect().width()
                text_height = text.boundingRect().height()
                text.setPos(x - text_width/2, y - text_height/2)
                self.scene.addItem(text)
                self.note_items.append(text)
                
                # Add notation for techniques if present
                technique = note.get("technique")
                if technique:
                    tech_text = self.scene.addText(technique, QFont("Arial", 8))
                    tech_text.setDefaultTextColor(Qt.black)
                    tech_text.setPos(x + 15, y - 25)
                    self.note_items.append(tech_text)
    
    def clear_tablature(self):
        """Clear all tablature notes but keep the fretboard"""
        # Clear only the note items
        for item in self.note_items:
            if item and item.scene():
                self.scene.removeItem(item)
        self.note_items.clear()
    
    def load_measure(self, measure_index):
        """Load a specific measure into the view"""
        if 0 <= measure_index < len(self.measures):
            self.current_measure = measure_index
            self.clear_tablature()
            self.draw_tablature(self.measures[measure_index])
    
    def dragEnterEvent(self, event):
        """Handle drag enter events for drop operations"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """Handle drag move events"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop events to add notes to the fretboard"""
        pos = self.mapToScene(event.pos())
        
        # Check if within fretboard bounds
        if (self.left_margin <= pos.x() <= self.left_margin + (self.fret_count * self.fret_spacing) and
            self.top_margin <= pos.y() <= self.top_margin + ((self.string_count - 1) * self.string_spacing)):
            
            # Determine string and fret
            string_idx = round((pos.y() - self.top_margin) / self.string_spacing)
            fret_pos = (pos.x() - self.left_margin) / self.fret_spacing
            fret = max(0, min(self.fret_count, round(fret_pos)))
            
            # Get the dropped item text
            dropped_text = event.mimeData().text()
            
            # Check if it's a fret number or technique
            if dropped_text.isdigit():
                fret = int(dropped_text)
                technique = None
            else:
                technique = dropped_text
            
            # Ensure valid string
            if 0 <= string_idx < self.string_count:
                # Add or update note to the current measure
                if self.current_measure < len(self.measures):
                    # Find existing note on this string
                    existing_note_idx = -1
                    for i, existing_note in enumerate(self.measures[self.current_measure]["notes"]):
                        if existing_note.get("string") == string_idx:
                            existing_note_idx = i
                            break
                    
                    if dropped_text.isdigit():
                        # Adding/updating a fret number
                        note = {"string": string_idx, "fret": fret}
                        if existing_note_idx >= 0:
                            # Keep technique if it exists
                            if "technique" in self.measures[self.current_measure]["notes"][existing_note_idx]:
                                note["technique"] = self.measures[self.current_measure]["notes"][existing_note_idx]["technique"]
                            # Update existing note
                            self.measures[self.current_measure]["notes"][existing_note_idx] = note
                        else:
                            # Add new note
                            self.measures[self.current_measure]["notes"].append(note)
                    else:
                        # Adding a technique
                        if existing_note_idx >= 0:
                            # Update existing note with technique
                            self.measures[self.current_measure]["notes"][existing_note_idx]["technique"] = technique
                    
                    # Redraw tablature
                    self.clear_tablature()
                    self.draw_tablature(self.measures[self.current_measure])
            
            event.acceptProposedAction()


class DraggableButton(QPushButton):
    def __init__(self, text, mime_text, parent=None):
        super().__init__(text, parent)
        self.mime_text = mime_text
        self.setFixedSize(40, 40)  # Make buttons square for a cleaner look
        
        # Apply a nice style
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #1F618D;
            }
        """)
    
    def mouseMoveEvent(self, event):
        """Enable drag and drop for buttons"""
        if event.buttons() & Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.mime_text)
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)


class LickEditor(QWidget):
    # Add signals for saving and deleting
    save_requested = pyqtSignal(dict)
    delete_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set background color
        self.setStyleSheet("background-color: #ECECEC;")
        
        self.init_ui()
        
        # Data structure for the lick
        self.lick_data = {
            "name": "New Lick",
            "measures": [{"notes": []}]  # Start with one empty measure
        }
    
    def init_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        
        # Lick title display
        self.title_label = QLabel("New Lick")
        self.title_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #2C3E50; margin: 5px;")
        layout.addWidget(self.title_label)
        
        # Tablature editor area
        editor_widget = QWidget()
        editor_widget.setStyleSheet("background-color: #F5F5F5; border-radius: 10px;")
        editor_layout = QVBoxLayout(editor_widget)
        
        # Fret number buttons for dragging (1-12)
        fret_buttons_layout = QHBoxLayout()
        fret_buttons_layout.addWidget(QLabel("Fret Numbers:"))
        
        fret_button_widget = QWidget()
        fret_grid = QHBoxLayout(fret_button_widget)
        fret_grid.setSpacing(5)
        
        for i in range(1, 13):  # Frets 1-12
            btn = DraggableButton(str(i), str(i))
            fret_grid.addWidget(btn)
        
        fret_buttons_layout.addWidget(fret_button_widget)
        fret_buttons_layout.addStretch()
        editor_layout.addLayout(fret_buttons_layout)
        
        # Fretboard view
        self.fretboard = FretboardView()
        editor_layout.addWidget(self.fretboard)
        
        # Technique buttons for dragging
        technique_layout = QHBoxLayout()
        technique_layout.addWidget(QLabel("Techniques:"))
        
        # Style for technique buttons
        technique_style = """
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #922B21;
            }
        """
        
        self.slide_btn = DraggableButton("Slide", "/")
        self.slide_btn.setStyleSheet(technique_style)
        self.slide_btn.setFixedWidth(80)
        
        self.hammer_btn = DraggableButton("Hammer-on", "h")
        self.hammer_btn.setStyleSheet(technique_style)
        self.hammer_btn.setFixedWidth(80)
        
        self.pull_btn = DraggableButton("Pull-off", "p")
        self.pull_btn.setStyleSheet(technique_style)
        self.pull_btn.setFixedWidth(80)
        
        technique_layout.addWidget(self.slide_btn)
        technique_layout.addWidget(self.hammer_btn)
        technique_layout.addWidget(self.pull_btn)
        technique_layout.addStretch()
        
        editor_layout.addLayout(technique_layout)
        
        # Measure navigation
        nav_layout = QHBoxLayout()
        
        # Style for navigation buttons
        nav_btn_style = """
            QPushButton {
                background-color: #27AE60;
                color: white;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1E8449;
            }
        """
        
        self.prev_btn = QPushButton("← Previous Measure")
        self.prev_btn.setStyleSheet(nav_btn_style)
        self.prev_btn.clicked.connect(self.previous_measure)
        
        self.measure_label = QLabel("Measure 1/1")
        self.measure_label.setAlignment(Qt.AlignCenter)
        self.measure_label.setStyleSheet("font-weight: bold; color: #2C3E50;")
        
        self.next_btn = QPushButton("Next Measure →")
        self.next_btn.setStyleSheet(nav_btn_style)
        self.next_btn.clicked.connect(self.next_measure)
        
        self.add_measure_btn = QPushButton("+ Add Measure")
        self.add_measure_btn.setStyleSheet(nav_btn_style)
        self.add_measure_btn.clicked.connect(self.add_measure)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.measure_label)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.add_measure_btn)
        editor_layout.addLayout(nav_layout)
        
        # Button layout for save and delete
        button_layout = QHBoxLayout()
        
        # Save button
        self.save_btn = QPushButton("Save Lick")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
            QPushButton:pressed {
                background-color: #7D3C98;
            }
        """)
        self.save_btn.clicked.connect(self.save_lick)
        button_layout.addWidget(self.save_btn)
        
        # Delete button
        self.delete_btn = QPushButton("Delete Lick")
        self.delete_btn.setMinimumHeight(40)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #922B21;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_lick)
        button_layout.addWidget(self.delete_btn)
        
        editor_layout.addLayout(button_layout)
        
        layout.addWidget(editor_widget)
    
    def load_lick(self, lick_data):
        """Load lick data into the editor"""
        self.lick_data = lick_data
        self.title_label.setText(lick_data.get("name", "Untitled Lick"))
        
        # Load measures
        self.fretboard.measures = lick_data.get("measures", [{"notes": []}])
        if not self.fretboard.measures:
            self.fretboard.measures = [{"notes": []}]
        
        # Reset to first measure
        self.fretboard.current_measure = 0
        self.fretboard.load_measure(0)
        
        # Update measure label
        self.update_measure_label()
    
    def update_measure_label(self):
        """Update the measure number display"""
        current = self.fretboard.current_measure + 1
        total = len(self.fretboard.measures)
        self.measure_label.setText(f"Measure {current}/{total}")
    
    def previous_measure(self):
        """Navigate to the previous measure"""
        if self.fretboard.current_measure > 0:
            self.fretboard.load_measure(self.fretboard.current_measure - 1)
            self.update_measure_label()
    
    def next_measure(self):
        """Navigate to the next measure"""
        if self.fretboard.current_measure < len(self.fretboard.measures) - 1:
            self.fretboard.load_measure(self.fretboard.current_measure + 1)
            self.update_measure_label()
    
    def add_measure(self):
        """Add a new measure after the current one"""
        current_idx = self.fretboard.current_measure
        self.fretboard.measures.insert(current_idx + 1, {"notes": []})
        self.fretboard.load_measure(current_idx + 1)
        self.update_measure_label()
    
    def save_lick(self):
        """Signal to save the current lick data"""
        # Prepare the current lick data
        current_data = {
            "name": self.title_label.text(),
            "measures": self.fretboard.measures
        }
        # Emit the signal with the current data
        self.save_requested.emit(current_data)
    
    def delete_lick(self):
        """Signal to delete the current lick"""
        self.delete_requested.emit()