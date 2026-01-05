# ============================================================
# workout_editor.py
# Workout editor window (WITH INTEGRATED VALIDATION)
# ============================================================

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from models import DataManager, Workout, Exercise
from utils import parse_time_input, seconds_to_mmss, generate_video_thumbnail
from PIL import Image, ImageTk
import cv2
from pathlib import Path


# ==================== VALIDATION FUNCTIONS ====================

def validate_video_path(video_path):
    """
    Validate video file path.

    Args:
        video_path (str): Path to video file

    Returns:
        tuple: (is_valid, error_message)
    """
    # Supported formats
    SUPPORTED_FORMATS = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
    MIN_FILE_SIZE = 1024  # 1 KB

    # Check if path is provided
    if not video_path:
        return False, "Video path is empty"

    # Check if path is a string
    if not isinstance(video_path, str):
        return False, f"Video path must be string, got {type(video_path)}"

    # Convert to Path object
    path = Path(video_path)

    # Check if file exists
    if not path.exists():
        return False, f"Video file does not exist: {video_path}"

    # Check if it's a file (not directory)
    if not path.is_file():
        return False, f"Path is not a file: {video_path}"

    # Check file extension
    file_extension = path.suffix.lower()
    if file_extension not in SUPPORTED_FORMATS:
        return False, f"Unsupported video format: {file_extension}"

    # Check file size
    file_size = path.stat().st_size

    if file_size < MIN_FILE_SIZE:
        return False, f"Video file too small ({file_size} bytes)"

    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        return False, f"Video file too large ({size_mb:.1f} MB). Maximum: 500 MB"

    # Check if file is readable
    if not os.access(video_path, os.R_OK):
        return False, f"Video file is not readable"

    # Try to open with OpenCV
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            cap.release()
            return False, "Cannot open video file (corrupted or invalid format)"

        # Try to read first frame
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return False, "Cannot read video frames (file may be corrupted)"

    except Exception as e:
        return False, f"Error validating video: {str(e)}"

    # All checks passed
    return True, None


def validate_duration(duration):
    """
    Validate exercise duration.

    Args:
        duration: Duration value to validate

    Returns:
        tuple: (is_valid, error_message, warning_message)
    """
    MIN_DURATION = 10  # 10 seconds
    MAX_DURATION = 3600  # 1 hour
    RECOMMENDED_MIN = 30  # 30 seconds
    RECOMMENDED_MAX = 600  # 10 minutes

    # Check if duration is provided
    if duration is None:
        return False, "Duration is required", None

    # Check if duration is a number
    if not isinstance(duration, (int, float)):
        return False, f"Duration must be a number", None

    # Convert to int
    try:
        duration = int(duration)
    except (ValueError, TypeError):
        return False, "Cannot convert duration to integer", None

    # Check if duration is positive
    if duration <= 0:
        return False, "Duration must be positive", None

    # Check minimum duration
    if duration < MIN_DURATION:
        return False, f"Duration too short ({duration}s). Minimum: {MIN_DURATION}s", None

    # Check maximum duration
    if duration > MAX_DURATION:
        return False, f"Duration too long ({duration}s). Maximum: {MAX_DURATION}s (60 minutes)", None

    # Check for warnings
    warning = None

    if duration < RECOMMENDED_MIN:
        warning = f"Duration is short ({duration}s). Recommended minimum: {RECOMMENDED_MIN}s"

    if duration > RECOMMENDED_MAX:
        duration_minutes = duration / 60
        warning = f"Duration is long ({duration_minutes:.1f} minutes). Recommended maximum: 10 minutes"

    # All checks passed
    return True, None, warning


def validate_workout(workout):
    """
    Validate entire workout.

    Args:
        workout: Workout object

    Returns:
        tuple: (is_valid, errors, warnings)
    """
    errors = []
    warnings = []

    # Check workout name
    if not workout.name or not workout.name.strip():
        warnings.append("Workout has no name (will be displayed as 'Untitled')")

    # Check if workout has any exercises
    exercise_count = sum(1 for ex in workout.exercises if ex is not None)

    if exercise_count == 0:
        errors.append("Workout has no exercises")
        return False, errors, warnings

    # Validate each exercise
    for i, exercise in enumerate(workout.exercises):
        if exercise is None:
            continue

        # Validate video path
        is_valid, error = validate_video_path(exercise.video_path)
        if not is_valid:
            errors.append(f"Exercise {i + 1}: {error}")

        # Validate duration
        is_valid, error, warning = validate_duration(exercise.duration)
        if not is_valid:
            errors.append(f"Exercise {i + 1}: {error}")
        elif warning:
            warnings.append(f"Exercise {i + 1}: {warning}")

    # Check total workout duration
    total_duration = workout.get_total_duration()

    if total_duration < 60:
        warnings.append(f"Workout is very short (total: {total_duration}s)")

    if total_duration > 7200:  # 2 hours
        warnings.append(f"Workout is very long (total: {total_duration / 60:.0f} minutes)")

    # Return validation result
    is_valid = len(errors) == 0

    return is_valid, errors, warnings


# ==================== WORKOUT EDITOR CLASS ====================

class WorkoutEditor(ctk.CTkToplevel):
    """Workout editing window"""

    def __init__(self, master, workout=None, workout_index=None):
        super().__init__(master)

        self.master_window = master
        self.data_manager = DataManager()
        self.workout = workout if workout else Workout()
        self.workout_index = workout_index
        self.gallery_path = "data/gallery"

        # Window setup
        self.title("Workout Editor")
        self.geometry("900x700")

        # Make window modal
        self.transient(master)
        self.grab_set()

        # Create UI
        self.create_ui()

        # Load data if editing
        if workout:
            self.load_workout_data()

    def create_ui(self):
        """Create editor interface"""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=20, pady=20)

        title_text = "Edit Workout" if self.workout_index is not None else "New Workout"
        label = ctk.CTkLabel(
            header,
            text=title_text,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        label.pack(side="left")

        # Workout name field
        name_frame = ctk.CTkFrame(self)
        name_frame.pack(fill="x", padx=20, pady=(0, 20))

        name_label = ctk.CTkLabel(
            name_frame,
            text="Workout Name:",
            font=ctk.CTkFont(size=14)
        )
        name_label.pack(side="left", padx=10)

        self.name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="Enter name (optional)",
            width=400
        )
        self.name_entry.pack(side="left", padx=10)

        # Scrollable area for cells
        self.cells_frame = ctk.CTkScrollableFrame(self, height=400)
        self.cells_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Create 10 cells
        self.cells = []
        for i in range(10):
            cell = self.create_exercise_cell(i)
            cell.pack(fill="x", pady=5)
            self.cells.append(cell)

        # Bottom panel with buttons
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=20, pady=20)

        btn_cancel = ctk.CTkButton(
            bottom_frame,
            text="Cancel",
            command=self.cancel,
            width=150
        )
        btn_cancel.pack(side="right", padx=10)

        btn_save = ctk.CTkButton(
            bottom_frame,
            text="Save",
            command=self.save_workout,
            width=150,
            fg_color="green",
            hover_color="darkgreen"
        )
        btn_save.pack(side="right", padx=10)

    def create_exercise_cell(self, index):
        """Create exercise cell"""
        cell_frame = ctk.CTkFrame(self.cells_frame)

        # Cell number
        num_label = ctk.CTkLabel(
            cell_frame,
            text=f"{index + 1}.",
            font=ctk.CTkFont(size=16, weight="bold"),
            width=30
        )
        num_label.pack(side="left", padx=(10, 5))

        # Video preview
        preview_frame = ctk.CTkFrame(cell_frame, width=80, height=60, fg_color="gray20")
        preview_frame.pack(side="left", padx=5)
        preview_frame.pack_propagate(False)

        preview_label = ctk.CTkLabel(preview_frame, text="🎬", font=ctk.CTkFont(size=24))
        preview_label.pack(expand=True)

        # Save widget references
        cell_frame.preview_frame = preview_frame
        cell_frame.preview_label = preview_label

        # Video name
        video_label = ctk.CTkLabel(
            cell_frame,
            text="Not selected",
            font=ctk.CTkFont(size=12),
            width=220,
            anchor="w"
        )
        video_label.pack(side="left", padx=10, fill="x", expand=True)
        cell_frame.video_label = video_label

        # Validation status indicator
        status_label = ctk.CTkLabel(
            cell_frame,
            text="",
            font=ctk.CTkFont(size=16),
            width=25
        )
        status_label.pack(side="left", padx=5)
        cell_frame.status_label = status_label

        # Time field
        time_frame = ctk.CTkFrame(cell_frame, fg_color="transparent")
        time_frame.pack(side="left", padx=5)

        time_icon = ctk.CTkLabel(time_frame, text="🕐", font=ctk.CTkFont(size=16))
        time_icon.pack(side="left", padx=(0, 5))

        time_entry = ctk.CTkEntry(
            time_frame,
            placeholder_text="0:00",
            width=70
        )
        time_entry.pack(side="left")
        cell_frame.time_entry = time_entry

        # Bind validation on time entry change
        time_entry.bind('<FocusOut>', lambda e: self.validate_cell_duration(index))
        time_entry.bind('<Return>', lambda e: self.validate_cell_duration(index))

        # Select video button
        btn_select = ctk.CTkButton(
            cell_frame,
            text="Select",
            width=80,
            command=lambda idx=index: self.select_video(idx)
        )
        btn_select.pack(side="left", padx=5)

        # Clear button
        btn_clear = ctk.CTkButton(
            cell_frame,
            text="✖",
            width=40,
            fg_color="red",
            hover_color="darkred",
            command=lambda idx=index: self.clear_cell(idx)
        )
        btn_clear.pack(side="left", padx=5)

        # Save cell data
        cell_frame.video_path = None
        cell_frame.cell_index = index
        cell_frame.validation_error = None

        return cell_frame

    def validate_cell_video(self, cell_index):
        """Validate video in cell"""
        cell = self.cells[cell_index]

        if not cell.video_path:
            cell.status_label.configure(text="")
            return True

        # Validate video path
        is_valid, error = validate_video_path(cell.video_path)

        if is_valid:
            cell.status_label.configure(text="✓", text_color="green")
            cell.validation_error = None
            return True
        else:
            cell.status_label.configure(text="✗", text_color="red")
            cell.validation_error = error
            return False

    def validate_cell_duration(self, cell_index):
        """Validate duration in cell"""
        cell = self.cells[cell_index]

        time_str = cell.time_entry.get().strip()

        if not time_str:
            cell.time_entry.configure(border_color="gray")
            return True

        # Parse duration
        duration = parse_time_input(time_str)

        if duration == 0:
            cell.time_entry.configure(border_color="red")
            return False

        # Validate duration
        is_valid, error, warning = validate_duration(duration)

        if not is_valid:
            cell.time_entry.configure(border_color="red")
            cell.validation_error = error
            return False
        else:
            if warning:
                cell.time_entry.configure(border_color="orange")
            else:
                cell.time_entry.configure(border_color="gray")
            cell.validation_error = None
            return True

    def select_video(self, cell_index):
        """Open video selection window"""
        dialog = VideoSelectionDialog(self, self.gallery_path)
        self.wait_window(dialog)

        if dialog.selected_video:
            video_path = os.path.join(self.gallery_path, dialog.selected_video)

            # Validate video before setting
            is_valid, error = validate_video_path(video_path)

            if is_valid:
                self.set_cell_video(cell_index, dialog.selected_video)
            else:
                messagebox.showerror(
                    "Invalid Video",
                    f"Cannot use this video:\n{error}"
                )

    def set_cell_video(self, cell_index, video_filename):
        """Set video in cell"""
        cell = self.cells[cell_index]
        video_path = os.path.join(self.gallery_path, video_filename)

        # Update data
        cell.video_path = video_path
        cell.video_label.configure(text=video_filename)

        # Validate
        self.validate_cell_video(cell_index)

        # Update preview
        try:
            thumbnail = generate_video_thumbnail(video_path, size=(80, 60))
            if thumbnail:
                photo = ImageTk.PhotoImage(thumbnail)
                cell.preview_label.configure(image=photo, text="")
                cell.preview_label.image = photo
        except:
            pass

    def clear_cell(self, cell_index):
        """Clear cell"""
        cell = self.cells[cell_index]

        # Clear data
        cell.video_path = None
        cell.video_label.configure(text="Not selected")
        cell.time_entry.delete(0, 'end')
        cell.time_entry.configure(border_color="gray")
        cell.status_label.configure(text="")
        cell.validation_error = None

        # Reset preview
        cell.preview_label.configure(image="", text="🎬")
        cell.preview_label.image = None

    def load_workout_data(self):
        """Load workout data into editor"""
        # Name
        if self.workout.name:
            self.name_entry.insert(0, self.workout.name)

        # Exercises
        for i, exercise in enumerate(self.workout.exercises):
            if exercise and i < 10:
                cell = self.cells[i]

                # Video
                if os.path.exists(exercise.video_path):
                    filename = os.path.basename(exercise.video_path)
                    self.set_cell_video(i, filename)

                # Time
                time_str = seconds_to_mmss(exercise.duration)
                cell.time_entry.insert(0, time_str)

                # Validate
                self.validate_cell_duration(i)

    def save_workout(self):
        """Save workout with validation"""
        # Get name
        name = self.name_entry.get().strip()

        # Collect exercises from cells
        exercises = []
        has_validation_errors = False

        for i, cell in enumerate(self.cells):
            if cell.video_path:
                # Get time
                time_str = cell.time_entry.get().strip()
                duration = parse_time_input(time_str)

                if duration > 0:
                    # Validate before adding
                    video_valid = self.validate_cell_video(i)
                    duration_valid = self.validate_cell_duration(i)

                    if not video_valid or not duration_valid:
                        has_validation_errors = True

                    exercise = Exercise(cell.video_path, duration)
                    exercises.append(exercise)
                else:
                    # Invalid duration
                    has_validation_errors = True
                    exercises.append(None)
            else:
                exercises.append(None)

        # Check if there are validation errors
        if has_validation_errors:
            response = messagebox.askyesno(
                "Validation Errors",
                "Some exercises have validation errors (marked with ✗ or red border).\n\n"
                "Do you want to save anyway?",
                icon='warning'
            )

            if not response:
                return

        # Check that there's at least one exercise
        if not any(exercises):
            messagebox.showerror(
                "No Exercises",
                "Add at least one exercise with specified time!"
            )
            return

        # Create/update workout
        self.workout.name = name
        self.workout.exercises = exercises

        # Validate complete workout
        is_valid, errors, warnings = validate_workout(self.workout)

        # Show warnings if any
        if warnings:
            warning_text = "Warnings:\n\n" + "\n".join(f"• {w}" for w in warnings)
            warning_text += "\n\nDo you want to save anyway?"

            response = messagebox.askyesno(
                "Validation Warnings",
                warning_text,
                icon='warning'
            )

            if not response:
                return

        # Show errors if any
        if not is_valid:
            error_text = "Cannot save workout. Errors:\n\n" + "\n".join(f"• {e}" for e in errors)
            messagebox.showerror(
                "Validation Failed",
                error_text
            )
            return

        # Save to JSON
        workouts = self.data_manager.load_workouts()

        if self.workout_index is not None:
            # Update existing
            workouts[self.workout_index] = self.workout
        else:
            # Add new
            workouts.append(self.workout)

        self.data_manager.save_workouts(workouts)

        # Update workout list in main window
        if hasattr(self.master_window, 'show_workouts_view'):
            self.master_window.show_workouts_view()

        # Show success message
        messagebox.showinfo(
            "Success",
            "Workout saved successfully!"
        )

        # Close window
        self.destroy()

    def cancel(self):
        """Cancel editing"""
        self.destroy()


# ============================================================
# Video selection dialog
# ============================================================

class VideoSelectionDialog(ctk.CTkToplevel):
    """Video selection dialog from gallery or adding new"""

    def __init__(self, master, gallery_path):
        super().__init__(master)

        self.gallery_path = gallery_path
        self.selected_video = None

        self.title("Select Video")
        self.geometry("600x500")

        # Make modal
        self.transient(master)
        self.grab_set()

        # Create UI
        self.create_ui()

    def create_ui(self):
        """Create dialog interface"""
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
            command=self.add_from_device,
            width=250
        )
        btn_add.pack(pady=10)

        # Videos list
        self.videos_frame = ctk.CTkScrollableFrame(self, height=300)
        self.videos_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.load_videos()

        # Cancel button
        btn_cancel = ctk.CTkButton(
            self,
            text="Cancel",
            command=self.destroy,
            width=150
        )
        btn_cancel.pack(pady=20)

    def load_videos(self):
        """Load videos list from gallery"""
        # Clear
        for widget in self.videos_frame.winfo_children():
            widget.destroy()

        # Get videos list
        if not os.path.exists(self.gallery_path):
            os.makedirs(self.gallery_path, exist_ok=True)

        video_files = []
        for filename in os.listdir(self.gallery_path):
            if filename.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
                video_files.append(filename)

        if not video_files:
            label = ctk.CTkLabel(
                self.videos_frame,
                text="Library is empty",
                font=ctk.CTkFont(size=14)
            )
            label.pack(pady=30)
            return

        # Display videos
        for filename in video_files:
            self.create_video_row(filename)

    def create_video_row(self, filename):
        """Create video row"""
        row = ctk.CTkFrame(self.videos_frame)
        row.pack(fill="x", pady=5, padx=10)

        # Preview
        video_path = os.path.join(self.gallery_path, filename)
        preview_frame = ctk.CTkFrame(row, width=80, height=60, fg_color="gray20")
        preview_frame.pack(side="left", padx=5)
        preview_frame.pack_propagate(False)

        try:
            thumbnail = generate_video_thumbnail(video_path, size=(80, 60))
            if thumbnail:
                photo = ImageTk.PhotoImage(thumbnail)
                preview_label = ctk.CTkLabel(preview_frame, image=photo, text="")
                preview_label.image = photo
                preview_label.pack()
            else:
                raise Exception("No thumbnail")
        except:
            preview_label = ctk.CTkLabel(preview_frame, text="🎬", font=ctk.CTkFont(size=24))
            preview_label.pack(expand=True)

        # Name
        name_label = ctk.CTkLabel(
            row,
            text=filename,
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        name_label.pack(side="left", padx=10, fill="x", expand=True)

        # Select button
        btn_select = ctk.CTkButton(
            row,
            text="Select",
            width=100,
            command=lambda fn=filename: self.select(fn)
        )
        btn_select.pack(side="right", padx=5)

    def select(self, filename):
        """Select video"""
        self.selected_video = filename
        self.destroy()

    def add_from_device(self):
        """Add video from device"""
        filetypes = (
            ('Video files', '*.mp4 *.avi *.mkv *.mov'),
            ('All files', '*.*')
        )

        filename = filedialog.askopenfilename(
            title='Select video',
            filetypes=filetypes
        )

        if filename:
            # Validate video first
            is_valid, error = validate_video_path(filename)

            if not is_valid:
                messagebox.showerror(
                    "Invalid Video",
                    f"Cannot add this video:\n{error}"
                )
                return

            # Copy to gallery
            import shutil
            basename = os.path.basename(filename)
            dest_path = os.path.join(self.gallery_path, basename)

            # Check if exists
            if os.path.exists(dest_path):
                name, ext = os.path.splitext(basename)
                counter = 1
                while os.path.exists(dest_path):
                    basename = f"{name}_{counter}{ext}"
                    dest_path = os.path.join(self.gallery_path, basename)
                    counter += 1

            shutil.copy2(filename, dest_path)

            # Select this video
            self.selected_video = basename
            self.destroy()