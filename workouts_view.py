# ============================================================
# FILE 3: workouts_view.py
# "My Workouts" page
# ============================================================

import customtkinter as ctk
from models import DataManager, Workout
from utils import format_duration


class WorkoutsView(ctk.CTkFrame):
    #Workouts list view

    def __init__(self, master):
        super().__init__(master)  # Initialize parent

        self.master_window = master  # Reference to main
        self.data_manager = DataManager()  # Data manager instance

        # Title
        self.label = ctk.CTkLabel(
            self,
            text="My Workouts",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.label.pack(pady=20)

        # Scrollable area for list
        self.workouts_frame = ctk.CTkScrollableFrame(self)  # Scrollable container
        self.workouts_frame.pack(fill="both", expand=True, pady=10)

        self.load_workouts()  # Load workouts

    def load_workouts(self):
        #Load and display workouts
        # Clear existing widgets
        for widget in self.workouts_frame.winfo_children():  # Get all children
            widget.destroy()  # Remove each widget

        workouts = self.data_manager.load_workouts()  # Load from JSON

        if not workouts:  # No workouts
            label = ctk.CTkLabel(
                self.workouts_frame,
                text="No workouts. Create your first one",
                font=ctk.CTkFont(size=16)
            )
            label.pack(pady=50)
            return

        for i, workout in enumerate(workouts):
            self.create_workout_row(workout, i)  # Create row widget

    def create_workout_row(self, workout, index):
        #Create workout row
        row = ctk.CTkFrame(self.workouts_frame)
        row.pack(fill="x", pady=5, padx=10)

        # Name
        name = workout.name if workout.name else "Untitled"  # Get name or default
        label_name = ctk.CTkLabel(
            row,
            text=name,  # Workout name
            font=ctk.CTkFont(size=16),
            anchor="w"
        )
        label_name.pack(side="left", padx=10, fill="x", expand=True)  # Take remaining space

        # Time
        total_seconds = workout.get_total_duration()  # Get total seconds
        time_text = format_duration(total_seconds)  # Format duration

        label_time = ctk.CTkLabel(row, text=time_text, width=100)  # Time label
        label_time.pack(side="left", padx=10)

        # Buttons
        btn_start = ctk.CTkButton(
            row,
            text="Start",
            width=80,
            command=lambda: self.start_workout(workout)  # Start handler
        )
        btn_start.pack(side="right", padx=5)

        btn_delete = ctk.CTkButton(
            row,
            text="Delete",
            width=80,
            fg_color="red",  # Red button
            hover_color="darkred",  # Dark red hover
            command=lambda: self.delete_workout(index)  # Delete handler
        )
        btn_delete.pack(side="right", padx=5)

        btn_edit = ctk.CTkButton(
            row,
            text="Edit",
            width=120,
            command=lambda: self.edit_workout(workout, index)  # Edit handler
        )
        btn_edit.pack(side="right", padx=5)

    def start_workout(self, workout):
        #Start workout
        from workout_player import WorkoutPlayer  # Import player
        player = WorkoutPlayer(self.master_window, workout)  # Create player window

    def edit_workout(self, workout, index):
        #Edit workout
        from workout_editor import WorkoutEditor  # Import editor
        editor = WorkoutEditor(self.master_window, workout, index)  # Open editor
        editor.wait_window()  # Wait for close
        self.load_workouts()  # Refresh list

    def delete_workout(self, index):
        #Delete workout
        workouts = self.data_manager.load_workouts()  # Load all workouts

        if 0 <= index < len(workouts):  # Valid index
            # Delete confirmation
            dialog = ctk.CTkInputDialog(
                text=f"Delete workout '{workouts[index].name}'?\nType 'yes' to confirm:",  # Confirmation message
                title="Confirm Deletion"
            )

            if dialog.get_input() == "yes":  # User confirmed
                workouts.pop(index)  # Remove workout
                self.data_manager.save_workouts(workouts)  # Save to file
                self.load_workouts()  # Refresh list