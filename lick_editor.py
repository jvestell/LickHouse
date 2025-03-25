from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QScrollArea, QFrame, QGraphicsView, QGraphicsScene, 
                             QGraphicsItem, QGraphicsTextItem, QGraphicsLineItem,
                             QGraphicsEllipseItem, QMessageBox)
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
        self.note_text_items = []  # For displaying note names
        
        # Colors
        self.background_color = QColor("#F5F5F5")  # Light gray background
        self.string_color = QColor("#555555")       # Dark gray strings
        self.fret_color = QColor("#777777")         # Medium gray frets
        self.nut_color = QColor("#333333")          # Darker gray for nut
        self.note_color = QColor("#3498DB")         # Matte blue for notes
        self.text_color = QColor("#FFFFFF")         # White text
        self.string_label_color = QColor("#2C3E50") # Dark blue-gray for labels
        self.faint_note_color = QColor(128, 128, 128, 128)  # Semi-transparent gray
        self.bold_note_color = QColor(64, 64, 64, 255)      # Solid dark gray
        
        # Note display state
        self.show_notes = False
        
        # Note mappings for each string (0-12 frets)
        self.string_notes = {
            0: ["E", "F", "F#", "G", "G#", "A", "A#", "B", "C", "C#", "D", "D#", "E"],  # High E
            1: ["B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],  # B
            2: ["G", "G#", "A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G"],  # G
            3: ["D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B", "C", "C#", "D"],  # D
            4: ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A"],  # A
            5: ["E", "F", "F#", "G", "G#", "A", "A#", "B", "C", "C#", "D", "D#", "E"],  # Low E
        }
        
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
        self.setDragMode(QGraphicsView.NoDrag)
    
    def update_label_positions(self):
        """Update positions of the note sequence and key labels"""
        pass  # Remove this method as it's no longer needed
    
    def detect_key(self, notes):
        """Detect the key/chord of the lick based on note patterns"""
        if not notes:
            return "No key detected"
            
        # Count occurrences of each note
        note_counts = {}
        for note in notes:
            if "fret" in note:
                string_idx = note.get("string")
                fret = note.get("fret")
                note_name = self.string_notes[string_idx][fret]
                note_counts[note_name] = note_counts.get(note_name, 0) + 1
        
        # Define chord patterns (root, third, fifth)
        chord_patterns = {
            "C": ["C", "E", "G"],
            "C#": ["C#", "F", "G#"],
            "D": ["D", "F#", "A"],
            "D#": ["D#", "G", "A#"],
            "E": ["E", "G#", "B"],
            "F": ["F", "A", "C"],
            "F#": ["F#", "A#", "C#"],
            "G": ["G", "B", "D"],
            "G#": ["G#", "C", "D#"],
            "A": ["A", "C#", "E"],
            "A#": ["A#", "D", "F"],
            "B": ["B", "D#", "F#"]
        }
        
        # Find the best matching key
        best_key = None
        best_score = 0
        
        for key, pattern in chord_patterns.items():
            score = 0
            for note in pattern:
                score += note_counts.get(note, 0)
            if score > best_score:
                best_score = score
                best_key = key
        
        return f"Key of {best_key}" if best_key else "No key detected"
    
    def get_note_sequence(self, notes):
        """Get the sequence of notes from left to right"""
        if not notes:
            return "No notes"
            
        # Sort notes by x position
        sorted_notes = sorted(notes, key=lambda n: n.get("x", 0))
        
        # Get note names in sequence
        note_sequence = []
        for note in sorted_notes:
            if "fret" in note:
                string_idx = note.get("string")
                fret = note.get("fret")
                note_name = self.string_notes[string_idx][fret]
                note_sequence.append(note_name)
            elif "technique" in note:
                note_sequence.append(note["technique"])
        
        return " → ".join(note_sequence)
    
    def toggle_notes(self, show):
        """Toggle the display of note names"""
        self.show_notes = show
        self.redraw_current_measure()
    
    def redraw_current_measure(self):
        """Redraw the current measure with or without notes"""
        self.clear_tablature()
        if self.current_measure < len(self.measures):
            self.draw_tablature(self.measures[self.current_measure])
    
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
        for item in self.string_lines + self.fret_lines + self.string_labels + self.note_items + self.note_text_items:
            if item and item.scene():
                self.scene.removeItem(item)
        
        # Clear all lists
        self.string_lines.clear()
        self.fret_lines.clear()
        self.string_labels.clear()
        self.note_items.clear()
        self.note_text_items.clear()
    
    def draw_tablature(self, measure_data):
        """Draw the tablature notes onto the fretboard"""
        if not measure_data or "notes" not in measure_data:
            return
            
        # Clear existing notes and note text
        self.clear_tablature()
            
        # Draw note names if enabled
        if self.show_notes:
            self.draw_note_names(measure_data["notes"])
            
        # Draw the tab notes
        for note in measure_data["notes"]:
            string_idx = note.get("string")
            x = note.get("x", 0)
            y = note.get("y", 0)
            
            if string_idx is not None:
                # Create note circle with text
                circle = QGraphicsEllipseItem(-10, -10, 20, 20)
                circle.setBrush(QBrush(self.note_color))
                circle.setPen(QPen(Qt.black, 1))
                circle.setPos(x, y)
                self.scene.addItem(circle)
                self.note_items.append(circle)
                
                # Add fret number or technique text
                if "fret" in note:
                    text = QGraphicsTextItem(str(note["fret"]))
                    text.setDefaultTextColor(self.text_color)
                    text.setFont(QFont("Arial", 9, QFont.Bold))
                elif "technique" in note:
                    text = QGraphicsTextItem(note["technique"])
                    text.setDefaultTextColor(Qt.black)
                    text.setFont(QFont("Arial", 9, QFont.Bold))
                else:
                    continue
                
                # Center the text in the circle
                text_width = text.boundingRect().width()
                text_height = text.boundingRect().height()
                text.setPos(x - text_width/2, y - text_height/2)
                self.scene.addItem(text)
                self.note_items.append(text)
    
    def draw_note_names(self, notes):
        """Draw note names for all frets, with different styling for used notes"""
        # Create a set of used positions for quick lookup
        used_positions = set()
        for note in notes:
            if "fret" in note:
                string_idx = note.get("string")
                fret = note.get("fret")
                used_positions.add((string_idx, fret))
        
        # Draw all possible note positions
        for string_idx in range(self.string_count):
            for fret in range(self.fret_count + 1):
                x = self.left_margin + (fret * self.fret_spacing)
                y = self.top_margin + (string_idx * self.string_spacing)
                
                # Get the note name for this position
                note_name = self.string_notes[string_idx][fret]
                
                # Create text item for note name
                note_text = QGraphicsTextItem(note_name)
                note_text.setFont(QFont("Arial", 8))
                
                # Set color based on whether this position is used
                if (string_idx, fret) in used_positions:
                    note_text.setDefaultTextColor(self.bold_note_color)
                    note_text.setFont(QFont("Arial", 8, QFont.Bold))
                else:
                    note_text.setDefaultTextColor(self.faint_note_color)
                
                # Position the text below the fret position
                text_width = note_text.boundingRect().width()
                note_text.setPos(x - text_width/2, y + 15)
                
                self.scene.addItem(note_text)
                self.note_text_items.append(note_text)
    
    def get_fret_from_x(self, x):
        """Convert x coordinate to nearest fret number"""
        fret_pos = (x - self.left_margin) / self.fret_spacing
        return max(0, min(self.fret_count, round(fret_pos)))
    
    def clear_tablature(self):
        """Clear all tablature notes and note names but keep the fretboard"""
        # Clear note items
        for item in self.note_items:
            if item and item.scene():
                self.scene.removeItem(item)
        self.note_items.clear()
        
        # Clear note text items
        for item in self.note_text_items:
            if item and item.scene():
                self.scene.removeItem(item)
        self.note_text_items.clear()
    
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
            
            # Get the dropped item text
            dropped_text = event.mimeData().text()
            
            # Ensure valid string
            if 0 <= string_idx < self.string_count:
                # Add note to the current measure
                if self.current_measure < len(self.measures):
                    # Handle techniques first
                    if dropped_text in ["h", "p", "/"]:
                        note = {
                            "string": string_idx,
                            "technique": dropped_text,
                            "x": pos.x(),
                            "y": pos.y()
                        }
                        self.measures[self.current_measure]["notes"].append(note)
                    # Handle fret numbers
                    elif dropped_text.isdigit():
                        fret = int(dropped_text)
                        # Ensure the fret is within valid range
                        if 0 <= fret <= self.fret_count:
                            # Add new note with exact position
                            note = {
                                "string": string_idx,
                                "fret": fret,  # Store the actual fret number
                                "x": pos.x(),
                                "y": pos.y()
                            }
                            self.measures[self.current_measure]["notes"].append(note)
                    
                    # Redraw tablature
                    self.clear_tablature()
                    self.draw_tablature(self.measures[self.current_measure])
            
            event.acceptProposedAction()
    
    def mousePressEvent(self, event):
        """Handle mouse press events for note deletion"""
        if event.button() == Qt.RightButton:
            pos = self.mapToScene(event.pos())
            
            # Check if clicked on a note
            for note in self.measures[self.current_measure]["notes"]:
                note_x = note.get("x", 0)
                note_y = note.get("y", 0)
                
                # Check if click is within note bounds (20x20 pixels)
                if (abs(pos.x() - note_x) <= 10 and abs(pos.y() - note_y) <= 10):
                    # Remove the note
                    self.measures[self.current_measure]["notes"].remove(note)
                    # Redraw tablature
                    self.clear_tablature()
                    self.draw_tablature(self.measures[self.current_measure])
        
        super().mousePressEvent(event)


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
        
        # Fret number buttons for dragging (0-12)
        fret_buttons_layout = QHBoxLayout()
        fret_buttons_layout.addWidget(QLabel("Fret Numbers:"))
        
        fret_button_widget = QWidget()
        fret_grid = QHBoxLayout(fret_button_widget)
        fret_grid.setSpacing(5)
        
        # Add open string (0) button first
        open_btn = DraggableButton("0", "0")
        fret_grid.addWidget(open_btn)
        
        # Add fret buttons 1-12
        for i in range(1, 13):
            btn = DraggableButton(str(i), str(i))
            fret_grid.addWidget(btn)
        
        fret_buttons_layout.addWidget(fret_button_widget)
        fret_buttons_layout.addStretch()
        editor_layout.addLayout(fret_buttons_layout)
        
        # Note sequence display
        self.note_sequence_label = QLabel("Notes: ")
        self.note_sequence_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                font-weight: bold;
                padding: 10px;
                background-color: #F5F5F5;
                border-radius: 5px;
                min-height: 35px;
                font-size: 16px;
            }
        """)
        editor_layout.addWidget(self.note_sequence_label)
        
        # Key display
        self.key_label = QLabel("Key: ")
        self.key_label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                font-weight: bold;
                padding: 10px;
                background-color: #F5F5F5;
                border-radius: 5px;
                min-height: 35px;
                font-size: 16px;
            }
        """)
        editor_layout.addWidget(self.key_label)
        
        # Show Notes toggle
        notes_toggle_layout = QHBoxLayout()
        notes_toggle_layout.addStretch()
        
        self.show_notes_toggle = QPushButton("Show Notes")
        self.show_notes_toggle.setCheckable(True)
        self.show_notes_toggle.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                padding: 8px 15px;
                min-width: 100px;
            }
            QPushButton:checked {
                background-color: #2ECC71;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
            QPushButton:checked:hover {
                background-color: #27AE60;
            }
        """)
        self.show_notes_toggle.clicked.connect(self.toggle_notes)
        notes_toggle_layout.addWidget(self.show_notes_toggle)
        notes_toggle_layout.addStretch()
        
        editor_layout.addLayout(notes_toggle_layout)
        
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
        
        # Add Delete Measure button with red style
        self.delete_measure_btn = QPushButton("Delete Measure")
        self.delete_measure_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #922B21;
            }
        """)
        self.delete_measure_btn.clicked.connect(self.delete_measure)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.measure_label)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.add_measure_btn)
        nav_layout.addWidget(self.delete_measure_btn)
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
    
    def toggle_notes(self):
        """Toggle the display of note names on the fretboard"""
        self.fretboard.toggle_notes(self.show_notes_toggle.isChecked())

    def update_note_display(self):
        """Update the note sequence and key displays"""
        if self.fretboard.current_measure < len(self.fretboard.measures):
            current_measure = self.fretboard.measures[self.fretboard.current_measure]
            notes = current_measure.get("notes", [])
            
            # Update note sequence
            note_sequence = []
            for note in sorted(notes, key=lambda n: n.get("x", 0)):
                if "fret" in note:
                    string_idx = note.get("string")
                    fret = note.get("fret")
                    note_name = self.fretboard.string_notes[string_idx][fret]
                    note_sequence.append(note_name)
                elif "technique" in note:
                    note_sequence.append(note["technique"])
            
            self.note_sequence_label.setText(f"Notes: {' → '.join(note_sequence)}")
            
            # Update key
            self.key_label.setText(f"Key: {self.fretboard.detect_key(notes)}")
    
    def load_measure(self, measure_index):
        """Load a specific measure into the view"""
        if 0 <= measure_index < len(self.fretboard.measures):
            self.fretboard.current_measure = measure_index
            self.fretboard.clear_tablature()
            self.fretboard.draw_tablature(self.fretboard.measures[measure_index])
            self.update_note_display()
            self.update_measure_label()
    
    def dropEvent(self, event):
        """Handle drop events to add notes to the fretboard"""
        pos = self.mapToScene(event.pos())
        
        # Check if within fretboard bounds
        if (self.left_margin <= pos.x() <= self.left_margin + (self.fret_count * self.fret_spacing) and
            self.top_margin <= pos.y() <= self.top_margin + ((self.string_count - 1) * self.string_spacing)):
            
            # Determine string and fret
            string_idx = round((pos.y() - self.top_margin) / self.string_spacing)
            
            # Get the dropped item text
            dropped_text = event.mimeData().text()
            
            # Ensure valid string
            if 0 <= string_idx < self.string_count:
                # Add note to the current measure
                if self.current_measure < len(self.measures):
                    # Handle techniques first
                    if dropped_text in ["h", "p", "/"]:
                        note = {
                            "string": string_idx,
                            "technique": dropped_text,
                            "x": pos.x(),
                            "y": pos.y()
                        }
                        self.measures[self.current_measure]["notes"].append(note)
                    # Handle fret numbers
                    elif dropped_text.isdigit():
                        fret = int(dropped_text)
                        # Ensure the fret is within valid range
                        if 0 <= fret <= self.fret_count:
                            # Add new note with exact position
                            note = {
                                "string": string_idx,
                                "fret": fret,  # Store the actual fret number
                                "x": pos.x(),
                                "y": pos.y()
                            }
                            self.measures[self.current_measure]["notes"].append(note)
                    
                    # Redraw tablature
                    self.clear_tablature()
                    self.draw_tablature(self.measures[self.current_measure])
            
            event.acceptProposedAction()
    
    def mousePressEvent(self, event):
        """Handle mouse press events for note deletion"""
        if event.button() == Qt.RightButton:
            # ... existing mouse press event code ...
            
            # After removing the note and redrawing
            self.update_note_display()

    def delete_measure(self):
        """Delete the current measure"""
        if len(self.fretboard.measures) > 1:  # Keep at least one measure
            # Show confirmation dialog
            reply = QMessageBox.question(
                self,
                'Delete Measure',
                'Are you sure you want to delete this measure?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                current_idx = self.fretboard.current_measure
                self.fretboard.measures.pop(current_idx)
                
                # If we deleted the last measure, move to the new last measure
                if current_idx >= len(self.fretboard.measures):
                    current_idx = len(self.fretboard.measures) - 1
                
                self.fretboard.load_measure(current_idx)
                self.update_measure_label()
                self.update_note_display()