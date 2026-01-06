# ============================================================
# main.py
# Main window
# ============================================================

import customtkinter as ctk
from workouts_view import WorkoutsView
from gallery_view import GalleryView
from statistics_view import StatisticsView
from settings_view import SettingsView
from workout_editor import WorkoutEditor
from models import DataManager


class MainWindow(ctk.CTk):
    """Main application window"""

    def __init__(self):
        super().__init__()

        self.title("Fitness Application")  # Window title
        self.geometry("1200x700")  # Window size

        # Create grid
        self.grid_columnconfigure(1, weight=1)  # Column 1 stretches
        self.grid_rowconfigure(0, weight=1)  # Row 0 stretches

        # Create sidebar
        self.create_sidebar()

        # Active view area
        self.active_view = None  # Current screen
        self.show_workouts_view()  # Default screen

    def create_sidebar(self):
        # Create sidebar menu
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)  # Left panel
        self.sidebar.grid(row=0, column=0, sticky="nsew")  # Place at left
        self.sidebar.grid_rowconfigure(6, weight=1)  # Push buttons up

        # "New Workout" button
        self.btn_new_workout = ctk.CTkButton(
            self.sidebar,
            text="+ New Workout",
            command=self.create_new_workout,  # Open editor
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_new_workout.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Navigation buttons
        self.btn_workouts = ctk.CTkButton(
            self.sidebar,
            text="My Workouts",
            command=self.show_workouts_view  # Show workouts screen
        )
        self.btn_workouts.grid(row=1, column=0, padx=20, pady=10)

        self.btn_gallery = ctk.CTkButton(
            self.sidebar,
            text="Gallery",
            command=self.show_gallery_view  # Show gallery screen
        )
        self.btn_gallery.grid(row=2, column=0, padx=20, pady=10)

        self.btn_stats = ctk.CTkButton(
            self.sidebar,
            text="Statistics",
            command=self.show_statistics_view  # Show stats screen
        )
        self.btn_stats.grid(row=3, column=0, padx=20, pady=10)

        self.btn_settings = ctk.CTkButton(
            self.sidebar,
            text="Settings",
            command=self.show_settings_view  # Show settings screen
        )
        self.btn_settings.grid(row=4, column=0, padx=20, pady=10)

    def clear_active_view(self):
        #Clear active view area
        if self.active_view:  # Check exists
            self.active_view.destroy()

    def show_workouts_view(self):
        #Show workouts list
        self.clear_active_view()  # Remove old screen
        self.active_view = WorkoutsView(self)  # Create workouts screen
        self.active_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_gallery_view(self):
        #Show video gallery
        self.clear_active_view()  # Remove old screen
        self.active_view = GalleryView(self)  # Create gallery screen
        self.active_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_statistics_view(self):
        #Show statistics
        self.clear_active_view()  # Remove old screen
        self.active_view = StatisticsView(self)  # Create stats screen
        self.active_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_settings_view(self):
        #Show settings
        self.clear_active_view()  # Remove old screen
        self.active_view = SettingsView(self)  # Create settings screen
        self.active_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def create_new_workout(self):
        #Create new workout
        editor = WorkoutEditor(self)  # Open editor window
        editor.grab_set()


def main():
    # Load saved theme from settings
    data_manager = DataManager()  # Create data manager
    settings = data_manager.load_settings()  # Load settings
    saved_theme = settings.get("theme")  # Get theme setting


    # Apply saved theme
    ctk.set_appearance_mode(saved_theme)  # Set theme

    app = MainWindow()  # Create main window
    app.mainloop()  # Start event loop


if __name__ == "__main__":
    main()  # Start application