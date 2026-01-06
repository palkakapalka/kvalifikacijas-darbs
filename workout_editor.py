# ============================================================
# workout_editor.py
# Workout editor window
# ============================================================

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from models import DataManager, Workout, Exercise
from utils import parse_time_input, seconds_to_mmss, generate_video_prev
from PIL import Image, ImageTk
import cv2
from pathlib import Path


# ==================== VALIDATION FUNCTIONS ====================

def validate_video_path(video_path):
    # Validate video file path.

    # Supported formats
    SUPPORTED_FORMATS = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']  # Allowed extensions
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB limit
    MIN_FILE_SIZE = 1024  # 1 KB minimum

    # Check if path is provided
    if not video_path:  # Empty path
        return False, "Video path is empty"

    # Check if path is a string
    if not isinstance(video_path, str):  # Type check
        return False, f"Video path must be string, got {type(video_path)}"

    # Convert to Path object
    path = Path(video_path)  # Pathlib object

    # Check if file exists
    if not path.exists():  # File missing
        return False, f"Video file does not exist: {video_path}"

    # Check if it's a file (not directory)
    if not path.is_file():  # Is directory
        return False, f"Path is not a file: {video_path}"

    # Check file extension
    file_extension = path.suffix.lower()  # Get extension
    if file_extension not in SUPPORTED_FORMATS:  # Invalid format
        return False, f"Unsupported video format: {file_extension}"

    # Check file size
    file_size = path.stat().st_size  # Get size

    if file_size < MIN_FILE_SIZE:  # Too small
        return False, f"Video file too small ({file_size} bytes)"

    if file_size > MAX_FILE_SIZE:  # Too large
        size_mb = file_size / (1024 * 1024)  # Convert to MB
        return False, f"Video file too large ({size_mb:.1f} MB). Maximum: 500 MB"

    # Check if file is readable
    if not os.access(video_path, os.R_OK):  # No read permission
        return False, f"Video file is not readable"

    # Try to open with OpenCV
    try:
        cap = cv2.VideoCapture(video_path)  # Open video
        if not cap.isOpened():  # Failed to open
            cap.release()  # Close video
            return False, "Cannot open video file (corrupted or invalid format)"

        # Try to read first frame
        ret, frame = cap.read()  # Read frame
        cap.release()  # Close video

        if not ret:  # No frame
            return False, "Cannot read video frames (file may be corrupted)"

    except Exception as e:  # Any error
        return False, f"Error validating video: {str(e)}"

    # All checks passed
    return True, None  # Valid video


def validate_duration(duration):
    # Validate exercise duration.

    MIN_DURATION = 10  # 10 seconds minimum
    MAX_DURATION = 3600  # 1 hour maximum
    RECOMMENDED_MIN = 30  # 30 seconds recommended
    RECOMMENDED_MAX = 600  # 10 minutes recommended

    # Check if duration is provided
    if duration is None:  # No value
        return False, "Duration is required", None

    # Check if duration is a number
    if not isinstance(duration, (int, float)):  # Not a number
        return False, f"Duration must be a number", None

    # Convert to int
    try:
        duration = int(duration)  # Convert to integer
    except (ValueError, TypeError):  # Conversion failed
        return False, "Cannot convert duration to integer", None

    # Check if duration is positive
    if duration <= 0:  # Zero or negative
        return False, "Duration must be positive", None

    # Check minimum duration
    if duration < MIN_DURATION:  # Too short
        return False, f"Duration too short ({duration}s). Minimum: {MIN_DURATION}s", None

    # Check maximum duration
    if duration > MAX_DURATION:  # Too long
        return False, f"Duration too long ({duration}s). Maximum: {MAX_DURATION}s (60 minutes)", None

    # Check for warnings
    warning = None  # No warning yet

    if duration < RECOMMENDED_MIN:  # Short but valid
        warning = f"Duration is short ({duration}s). Recommended minimum: {RECOMMENDED_MIN}s"

    if duration > RECOMMENDED_MAX:  # Long but valid
        duration_minutes = duration / 60  # Convert to minutes
        warning = f"Duration is long ({duration_minutes:.1f} minutes). Recommended maximum: 10 minutes"

    # All checks passed
    return True, None, warning  # Valid with warning


def validate_workout(workout):
    # Validate entire workout.

    errors = []  # Error list
    warnings = []  # Warning list

    # Check workout name
    if not workout.name or not workout.name.strip():  # Empty name
        warnings.append("Workout has no name (will be displayed as 'Untitled')")

    # Check if workout has any exercises
    exercise_count = sum(1 for ex in workout.exercises if ex is not None)  # Count non-None

    if exercise_count == 0:  # No exercises
        errors.append("Workout has no exercises")
        return False, errors, warnings  # Return immediately

    # Validate each exercise
    for i, exercise in enumerate(workout.exercises):  # Loop through
        if exercise is None:  # Empty slot
            continue  # Skip

        # Validate video path
        is_valid, error = validate_video_path(exercise.video_path)  # Check video
        if not is_valid:  # Invalid
            errors.append(f"Exercise {i + 1}: {error}")  # Add error

        # Validate duration
        is_valid, error, warning = validate_duration(exercise.duration)  # Check duration
        if not is_valid:  # Invalid
            errors.append(f"Exercise {i + 1}: {error}")  # Add error
        elif warning:  # Has warning
            warnings.append(f"Exercise {i + 1}: {warning}")  # Add warning

    # Check total workout duration
    total_duration = workout.get_total_duration()  # Get total time

    if total_duration < 60:  # Very short
        warnings.append(f"Workout is very short (total: {total_duration}s)")

    if total_duration > 7200:  # Very long (2 hours)
        warnings.append(f"Workout is very long (total: {total_duration / 60:.0f} minutes)")

    # Return validation result
    is_valid = len(errors) == 0  # No errors = valid

    return is_valid, errors, warnings  # Return result


# ==================== WORKOUT EDITOR CLASS ====================

class WorkoutEditor(ctk.CTkToplevel):
    # Workout editing window

    def __init__(self, master, workout=None, workout_index=None):
        super().__init__(master)  # Initialize parent

        self.master_window = master  # Reference to main
        self.data_manager = DataManager()  # Data manager instance
        self.workout = workout if workout else Workout()  # Existing or new
        self.workout_index = workout_index  # Index for editing
        self.gallery_path = "data/gallery"  # Video folder path

        # Window setup
        self.title("Workout Editor")  # Window title
        self.geometry("900x700")  # Window size

        # Make window modal
        self.transient(master)  # Link to parent
        self.grab_set()  # Block parent window

        # Create UI
        self.create_ui()  # Build interface

        # Load data if editing
        if workout:  # Editing existing
            self.load_workout_data()  # Load workout data

    def create_ui(self):
        # Create editor interface
        # Header
        header = ctk.CTkFrame(self)  # Header container
        header.pack(fill="x", padx=20, pady=20)

        title_text = "Edit Workout" if self.workout_index is not None else "New Workout"  # Dynamic title
        label = ctk.CTkLabel(
            header,
            text=title_text,  # Show title
            font=ctk.CTkFont(size=24, weight="bold")
        )
        label.pack(side="left")

        # Workout name field
        name_frame = ctk.CTkFrame(self)  # Name container
        name_frame.pack(fill="x", padx=20, pady=(0, 20))

        name_label = ctk.CTkLabel(
            name_frame,
            text="Workout Name:",
            font=ctk.CTkFont(size=14)
        )
        name_label.pack(side="left", padx=10)

        self.name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="Enter name (optional)",  # Placeholder text
            width=400
        )
        self.name_entry.pack(side="left", padx=10)

        # Scrollable area for cells
        self.cells_frame = ctk.CTkScrollableFrame(self, height=400)  # Scrollable container
        self.cells_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Create 10 cells
        self.cells = []  # Empty list
        for i in range(10):  # Loop 10 times
            cell = self.create_exercise_cell(i)  # Create cell widget
            cell.pack(fill="x", pady=5)  # Add to frame
            self.cells.append(cell)  # Save reference

        # Bottom panel with buttons
        bottom_frame = ctk.CTkFrame(self)  # Bottom container
        bottom_frame.pack(fill="x", padx=20, pady=20)

        btn_cancel = ctk.CTkButton(
            bottom_frame,
            text="Cancel",
            command=self.cancel,  # Cancel handler
            width=150
        )
        btn_cancel.pack(side="right", padx=10)

        btn_save = ctk.CTkButton(
            bottom_frame,
            text="Save",
            command=self.save_workout,  # Save handler
            width=150,
            fg_color="green",  # Green button
            hover_color="darkgreen"  # Dark green hover
        )
        btn_save.pack(side="right", padx=10)

    def create_exercise_cell(self, index):
        # Create exercise cell
        cell_frame = ctk.CTkFrame(self.cells_frame)  # Cell container

        # Cell number
        num_label = ctk.CTkLabel(
            cell_frame,
            text=f"{index + 1}.",  # Cell number (1-10)
            font=ctk.CTkFont(size=16, weight="bold"),
            width=30
        )
        num_label.pack(side="left", padx=(10, 5))

        # Video preview
        preview_frame = ctk.CTkFrame(cell_frame, width=80, height=60, fg_color="gray20")  # Preview container
        preview_frame.pack(side="left", padx=5)
        preview_frame.pack_propagate(False)  # Fixed size

        preview_label = ctk.CTkLabel(preview_frame, text="🎬", font=ctk.CTkFont(size=24))  # Video icon
        preview_label.pack(expand=True)

        # Save widget references
        cell_frame.preview_frame = preview_frame  # Save frame reference
        cell_frame.preview_label = preview_label  # Save label reference

        # Video name
        video_label = ctk.CTkLabel(
            cell_frame,
            text="Not selected",  # Default text
            font=ctk.CTkFont(size=12),
            width=220,
            anchor="w"  # Left align
        )
        video_label.pack(side="left", padx=10, fill="x", expand=True)
        cell_frame.video_label = video_label  # Save reference

        # Validation status indicator
        status_label = ctk.CTkLabel(
            cell_frame,
            text="",  # Empty by default
            font=ctk.CTkFont(size=16),
            width=25
        )
        status_label.pack(side="left", padx=5)
        cell_frame.status_label = status_label  # Save reference

        # Time field
        time_frame = ctk.CTkFrame(cell_frame, fg_color="transparent")  # Transparent container
        time_frame.pack(side="left", padx=5)

        time_icon = ctk.CTkLabel(time_frame, text="🕐", font=ctk.CTkFont(size=16))  # Clock icon
        time_icon.pack(side="left", padx=(0, 5))

        time_entry = ctk.CTkEntry(
            time_frame,
            placeholder_text="0:00",  # Placeholder format
            width=70
        )
        time_entry.pack(side="left")
        cell_frame.time_entry = time_entry  # Save reference

        # Bind validation on time entry change
        time_entry.bind('<FocusOut>', lambda e: self.validate_cell_duration(index))  # Validate on unfocus
        time_entry.bind('<Return>', lambda e: self.validate_cell_duration(index))  # Validate on Enter

        # Select video button
        btn_select = ctk.CTkButton(
            cell_frame,
            text="Select",
            width=80,
            command=lambda idx=index: self.select_video(idx)  # Select video handler
        )
        btn_select.pack(side="left", padx=5)

        # Clear button
        btn_clear = ctk.CTkButton(
            cell_frame,
            text="✖",  # X symbol
            width=40,
            fg_color="red",  # Red button
            hover_color="darkred",  # Dark red hover
            command=lambda idx=index: self.clear_cell(idx)  # Clear handler
        )
        btn_clear.pack(side="left", padx=5)

        # Save cell data
        cell_frame.video_path = None  # No video initially
        cell_frame.cell_index = index  # Save index
        cell_frame.validation_error = None  # No error initially

        return cell_frame  # Return widget

    def validate_cell_video(self, cell_index):
        # Validate video in cell
        cell = self.cells[cell_index]  # Get cell

        if not cell.video_path:  # No video selected
            cell.status_label.configure(text="")  # Clear status
            return True  # Valid (empty)

        # Validate video path
        is_valid, error = validate_video_path(cell.video_path)  # Check video

        if is_valid:  # Video is valid
            cell.status_label.configure(text="✓", text_color="green")  # Green checkmark
            cell.validation_error = None  # Clear error
            return True  # Valid
        else:  # Video is invalid
            cell.status_label.configure(text="✗", text_color="red")  # Red X
            cell.validation_error = error  # Save error
            return False  # Invalid

    def validate_cell_duration(self, cell_index):
        # Validate duration in cell
        cell = self.cells[cell_index]  # Get cell

        time_str = cell.time_entry.get().strip()  # Get time text

        if not time_str:  # Empty field
            cell.time_entry.configure(border_color="gray")  # Gray border
            return True  # Valid (empty)

        # Parse duration
        duration = parse_time_input(time_str)  # Convert to seconds

        if duration == 0:  # Invalid format
            cell.time_entry.configure(border_color="red")  # Red border
            return False  # Invalid

        # Validate duration
        is_valid, error, warning = validate_duration(duration)  # Check duration

        if not is_valid:  # Duration invalid
            cell.time_entry.configure(border_color="red")  # Red border
            cell.validation_error = error  # Save error
            return False  # Invalid
        else:
            if warning:  # Has warning
                cell.time_entry.configure(border_color="orange")  # Orange border
            else:
                cell.time_entry.configure(border_color="gray")  # Gray border
            cell.validation_error = None  # Clear error
            return True  # Valid

    def select_video(self, cell_index):
        # Open video selection window
        dialog = VideoSelectionDialog(self, self.gallery_path)  # Create dialog
        self.wait_window(dialog)  # Wait for close

        if dialog.selected_video:  # Video was selected
            video_path = os.path.join(self.gallery_path, dialog.selected_video)  # Full path

            # Validate video before setting
            is_valid, error = validate_video_path(video_path)  # Check video

            if is_valid:  # Video is valid
                self.set_cell_video(cell_index, dialog.selected_video)  # Set video
            else:  # Video is invalid
                messagebox.showerror(
                    "Invalid Video",
                    f"Cannot use this video:\n{error}"  # Show error
                )

    def set_cell_video(self, cell_index, video_filename):
        # Set video in cell
        cell = self.cells[cell_index]  # Get cell
        video_path = os.path.join(self.gallery_path, video_filename)  # Full path

        # Update data
        cell.video_path = video_path  # Save path
        cell.video_label.configure(text=video_filename)  # Show filename

        # Validate
        self.validate_cell_video(cell_index)  # Validate video

        # Update preview
        try:
            prev = generate_video_prev(video_path, size=(80, 60))  # Create preview
            if prev:  # Preview created
                photo = ImageTk.PhotoImage(prev)  # Convert to Tkinter
                cell.preview_label.configure(image=photo, text="")  # Show image
                cell.preview_label.image = photo  # Keep reference
        except:
            pass  # Ignore errors

    def clear_cell(self, cell_index):
        # Clear cell
        cell = self.cells[cell_index]  # Get cell

        # Clear data
        cell.video_path = None  # Remove video path
        cell.video_label.configure(text="Not selected")  # Reset label
        cell.time_entry.delete(0, 'end')  # Clear time field
        cell.time_entry.configure(border_color="gray")  # Gray border
        cell.status_label.configure(text="")  # Clear status
        cell.validation_error = None  # Clear error

        # Reset preview
        cell.preview_label.configure(image="", text="🎬")  # Show icon
        cell.preview_label.image = None  # Remove reference

    def load_workout_data(self):
        # Load workout data into editor
        # Name
        if self.workout.name:  # Has name
            self.name_entry.insert(0, self.workout.name)  # Insert name

        # Exercises
        for i, exercise in enumerate(self.workout.exercises):  # Loop exercises
            if exercise and i < 10:  # Valid exercise
                cell = self.cells[i]  # Get cell

                # Video
                if os.path.exists(exercise.video_path):  # Video exists
                    filename = os.path.basename(exercise.video_path)  # Get filename
                    self.set_cell_video(i, filename)  # Set video

                # Time
                time_str = seconds_to_mmss(exercise.duration)  # Format time
                cell.time_entry.insert(0, time_str)  # Insert time

                # Validate
                self.validate_cell_duration(i)  # Validate duration

    def save_workout(self):
        # Save workout with validation
        # Get name
        name = self.name_entry.get().strip()  # Get workout name

        # Collect exercises from cells
        exercises = []  # Empty list
        has_validation_errors = False  # No errors yet

        for i, cell in enumerate(self.cells):  # Loop cells
            if cell.video_path:  # Has video
                # Get time
                time_str = cell.time_entry.get().strip()  # Get time text
                duration = parse_time_input(time_str)  # Parse to seconds

                if duration > 0:  # Valid duration
                    # Validate before adding
                    video_valid = self.validate_cell_video(i)  # Check video
                    duration_valid = self.validate_cell_duration(i)  # Check duration

                    if not video_valid or not duration_valid:  # Has errors
                        has_validation_errors = True  # Mark errors

                    exercise = Exercise(cell.video_path, duration)  # Create exercise
                    exercises.append(exercise)  # Add to list
                else:
                    # Invalid duration
                    has_validation_errors = True  # Mark errors
                    exercises.append(None)  # Add None
            else:
                exercises.append(None)  # Add None

        # Check if there are validation errors
        if has_validation_errors:  # Has errors
            response = messagebox.askyesno(
                "Validation Errors",
                "Some exercises have validation errors (marked with ✗ or red border).\n\n"
                "Do you want to save anyway?",  # Ask user
                icon='warning'
            )

            if not response:  # User cancelled
                return  # Exit function

        # Check that there's at least one exercise
        if not any(exercises):  # No exercises
            messagebox.showerror(
                "No Exercises",
                "Add at least one exercise with specified time!"  # Show error
            )
            return  # Exit function

        # Create/update workout
        self.workout.name = name  # Set name
        self.workout.exercises = exercises  # Set exercises

        # Validate complete workout
        is_valid, errors, warnings = validate_workout(self.workout)  # Validate all

        # Show warnings if any
        if warnings:  # Has warnings
            warning_text = "Warnings:\n\n" + "\n".join(f"• {w}" for w in warnings)  # Format warnings
            warning_text += "\n\nDo you want to save anyway?"  # Add question

            response = messagebox.askyesno(
                "Validation Warnings",
                warning_text,  # Show warnings
                icon='warning'
            )

            if not response:  # User cancelled
                return  # Exit function

        # Show errors if any
        if not is_valid:  # Has errors
            error_text = "Cannot save workout. Errors:\n\n" + "\n".join(f"• {e}" for e in errors)  # Format errors
            messagebox.showerror(
                "Validation Failed",
                error_text  # Show errors
            )
            return  # Exit function

        # Save to JSON
        workouts = self.data_manager.load_workouts()  # Load all workouts

        if self.workout_index is not None:  # Editing existing
            # Update existing
            workouts[self.workout_index] = self.workout  # Replace workout
        else:
            # Add new
            workouts.append(self.workout)  # Add to list

        self.data_manager.save_workouts(workouts)  # Save to file

        # Update workout list in main window
        if hasattr(self.master_window, 'show_workouts_view'):  # Main window has method
            self.master_window.show_workouts_view()  # Refresh workouts view

        # Show success message
        messagebox.showinfo(
            "Success",
            "Workout saved successfully!"  # Success message
        )

        # Close window
        self.destroy()  # Close editor

    def cancel(self):
        # Cancel editing
        self.destroy()  # Close window


# ============================================================
# Video selection dialog
# ============================================================

class VideoSelectionDialog(ctk.CTkToplevel):
    # Video selection dialog from gallery or adding new

    def __init__(self, master, gallery_path):
        super().__init__(master)  # Initialize parent

        self.gallery_path = gallery_path  # Gallery path
        self.selected_video = None  # No selection yet

        self.title("Select Video")  # Dialog title
        self.geometry("600x500")  # Dialog size

        # Make modal
        self.transient(master)  # Link to parent
        self.grab_set()  # Block parent

        # Create UI
        self.create_ui()  # Build interface

    def create_ui(self):
        # Create dialog interface
        # Title
        label = ctk.CTkLabel(
            self,
            text="Select video from library",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        label.pack(pady=20)

        # Add new video button
        btn_add = ctk.CTkButton(
            self,
            text="+ Add video from device",
            command=self.add_from_device,  # Add video handler
            width=250
        )
        btn_add.pack(pady=10)

        # Videos list
        self.videos_frame = ctk.CTkScrollableFrame(self, height=300)  # Scrollable list
        self.videos_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.load_videos()  # Load videos

        # Cancel button
        btn_cancel = ctk.CTkButton(
            self,
            text="Cancel",
            command=self.destroy,  # Close dialog
            width=150
        )
        btn_cancel.pack(pady=20)

    def load_videos(self):
        # Load videos list from gallery
        # Clear
        for widget in self.videos_frame.winfo_children():  # Get all widgets
            widget.destroy()  # Remove each

        # Get videos list
        if not os.path.exists(self.gallery_path):  # Gallery missing
            os.makedirs(self.gallery_path, exist_ok=True)  # Create folder

        video_files = []  # Empty list
        for filename in os.listdir(self.gallery_path):  # Loop files
            if filename.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):  # Video format
                video_files.append(filename)  # Add to list

        if not video_files:  # No videos
            label = ctk.CTkLabel(
                self.videos_frame,
                text="Library is empty",
                font=ctk.CTkFont(size=14)
            )
            label.pack(pady=30)
            return  # Exit function

        # Display videos
        for filename in video_files:  # Each video
            self.create_video_row(filename)  # Create row

    def create_video_row(self, filename):
        # Create video row
        row = ctk.CTkFrame(self.videos_frame)  # Row container
        row.pack(fill="x", pady=5, padx=10)

        # Preview
        video_path = os.path.join(self.gallery_path, filename)  # Full path
        preview_frame = ctk.CTkFrame(row, width=80, height=60, fg_color="gray20")  # Preview container
        preview_frame.pack(side="left", padx=5)
        preview_frame.pack_propagate(False)  # Fixed size

        try:
            prev = generate_video_prev(video_path, size=(80, 60))  # Create preview
            if prev:  # preview created
                photo = ImageTk.PhotoImage(prev)
                preview_label = ctk.CTkLabel(preview_frame, image=photo, text="")  # Show image
                preview_label.image = photo  # Keep reference
                preview_label.pack()
            else:
                raise Exception("No preview")  # Trigger fallback
        except:
            preview_label = ctk.CTkLabel(preview_frame, text="🎬", font=ctk.CTkFont(size=24))  # Video icon
            preview_label.pack(expand=True)

        # Name
        name_label = ctk.CTkLabel(
            row,
            text=filename,  # Video name
            font=ctk.CTkFont(size=12),
            anchor="w"  # Left align
        )
        name_label.pack(side="left", padx=10, fill="x", expand=True)

        # Select button
        btn_select = ctk.CTkButton(
            row,
            text="Select",
            width=100,
            command=lambda fn=filename: self.select(fn)  # Select handler
        )
        btn_select.pack(side="right", padx=5)

    def select(self, filename):
        # Select video
        self.selected_video = filename  # Save selection
        self.destroy()  # Close dialog

    def add_from_device(self):
        # Add video from device
        filetypes = (  # Allowed types
            ('Video files', '*.mp4 *.avi *.mkv *.mov'),
            ('All files', '*.*')
        )

        filename = filedialog.askopenfilename(  # Open file dialog
            title='Select video',
            filetypes=filetypes
        )

        if filename:  # File selected
            # Validate video first
            is_valid, error = validate_video_path(filename)  # Check video

            if not is_valid:  # Invalid video
                messagebox.showerror(
                    "Invalid Video",
                    f"Cannot add this video:\n{error}"  # Show error
                )
                return  # Exit function

            # Copy to gallery
            import shutil
            basename = os.path.basename(filename)  # Get filename
            dest_path = os.path.join(self.gallery_path, basename)  # Destination path

            # Check if exists
            if os.path.exists(dest_path):  # File exists
                name, ext = os.path.splitext(basename)  # Split name/extension
                counter = 1  # Start counter
                while os.path.exists(dest_path):  # Find unique name
                    basename = f"{name}_{counter}{ext}"  # Add counter
                    dest_path = os.path.join(self.gallery_path, basename)  # New path
                    counter += 1  # Increment counter

            shutil.copy2(filename, dest_path)  # Copy file

            # Select this video
            self.selected_video = basename  # Save selection
            self.destroy()  # Close dialog