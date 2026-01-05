# ============================================================
# FILE 3: workouts_view.py
# "My Workouts" page
# ============================================================

import customtkinter as ctk
from models import DataManager, Workout
from utils import format_duration


class WorkoutsView(ctk.CTkFrame):
    """Workouts list view"""

    def __init__(self, master):
        super().__init__(master)

        self.master_window = master
        self.data_manager = DataManager()

        # Title
        self.label = ctk.CTkLabel(
            self,
            text="My Workouts",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.label.pack(pady=20)

        # Scrollable area for list
        self.workouts_frame = ctk.CTkScrollableFrame(self)
        self.workouts_frame.pack(fill="both", expand=True, pady=10)

        self.load_workouts()

    def load_workouts(self):
        """Load and display workouts"""
        # Clear existing widgets
        for widget in self.workouts_frame.winfo_children():
            widget.destroy()

        workouts = self.data_manager.load_workouts()

        if not workouts:
            label = ctk.CTkLabel(
                self.workouts_frame,
                text="No workouts. Create your first one!",
                font=ctk.CTkFont(size=16)
            )
            label.pack(pady=50)
            return

        for i, workout in enumerate(workouts):
            self.create_workout_row(workout, i)

    def create_workout_row(self, workout, index):
        """Create workout row"""
        row = ctk.CTkFrame(self.workouts_frame)
        row.pack(fill="x", pady=5, padx=10)

        # Name
        name = workout.name if workout.name else "Untitled"
        label_name = ctk.CTkLabel(
            row,
            text=name,
            font=ctk.CTkFont(size=16),
            anchor="w"
        )
        label_name.pack(side="left", padx=10, fill="x", expand=True)

        # Time
        total_seconds = workout.get_total_duration()
        time_text = format_duration(total_seconds)

        label_time = ctk.CTkLabel(row, text=time_text, width=100)
        label_time.pack(side="left", padx=10)

        # Buttons
        btn_start = ctk.CTkButton(
            row,
            text="Start",
            width=80,
            command=lambda: self.start_workout(workout)
        )
        btn_start.pack(side="right", padx=5)

        btn_delete = ctk.CTkButton(
            row,
            text="Delete",
            width=80,
            fg_color="red",
            hover_color="darkred",
            command=lambda: self.delete_workout(index)
        )
        btn_delete.pack(side="right", padx=5)

        btn_edit = ctk.CTkButton(
            row,
            text="Edit",
            width=120,
            command=lambda: self.edit_workout(workout, index)
        )
        btn_edit.pack(side="right", padx=5)

    def start_workout(self, workout):
        """Start workout"""
        from workout_player import WorkoutPlayer
        player = WorkoutPlayer(self.master_window, workout)

    def edit_workout(self, workout, index):
        """Edit workout"""
        from workout_editor import WorkoutEditor
        editor = WorkoutEditor(self.master_window, workout, index)
        editor.wait_window()
        self.load_workouts()  # Refresh list after closing editor

    def delete_workout(self, index):
        """Delete workout"""
        workouts = self.data_manager.load_workouts()

        if 0 <= index < len(workouts):
            # Delete confirmation
            dialog = ctk.CTkInputDialog(
                text=f"Delete workout '{workouts[index].name}'?\nType 'yes' to confirm:",
                title="Confirm Deletion"
            )

            if dialog.get_input() == "yes":
                workouts.pop(index)
                self.data_manager.save_workouts(workouts)
                self.load_workouts()  # Refresh list