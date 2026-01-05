# ============================================================
# FILE 1: main.py
# Main window + sidebar + entry point (WITH THEME LOADING)
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

        self.title("Fitness Application")
        self.geometry("1200x700")

        # Create grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar
        self.create_sidebar()

        # Active view area
        self.active_view = None
        self.show_workouts_view()

    def create_sidebar(self):
        """Create sidebar menu"""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        # "New Workout" button
        self.btn_new_workout = ctk.CTkButton(
            self.sidebar,
            text="+ New Workout",
            command=self.create_new_workout,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_new_workout.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Navigation buttons
        self.btn_workouts = ctk.CTkButton(
            self.sidebar,
            text="My Workouts",
            command=self.show_workouts_view
        )
        self.btn_workouts.grid(row=1, column=0, padx=20, pady=10)

        self.btn_gallery = ctk.CTkButton(
            self.sidebar,
            text="Gallery",
            command=self.show_gallery_view
        )
        self.btn_gallery.grid(row=2, column=0, padx=20, pady=10)

        self.btn_stats = ctk.CTkButton(
            self.sidebar,
            text="Statistics",
            command=self.show_statistics_view
        )
        self.btn_stats.grid(row=3, column=0, padx=20, pady=10)

        self.btn_settings = ctk.CTkButton(
            self.sidebar,
            text="Settings",
            command=self.show_settings_view
        )
        self.btn_settings.grid(row=4, column=0, padx=20, pady=10)

    def clear_active_view(self):
        """Clear active view area"""
        if self.active_view:
            self.active_view.destroy()

    def show_workouts_view(self):
        """Show workouts list"""
        self.clear_active_view()
        self.active_view = WorkoutsView(self)
        self.active_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_gallery_view(self):
        """Show video gallery"""
        self.clear_active_view()
        self.active_view = GalleryView(self)
        self.active_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_statistics_view(self):
        """Show statistics"""
        self.clear_active_view()
        self.active_view = StatisticsView(self)
        self.active_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_settings_view(self):
        """Show settings"""
        self.clear_active_view()
        self.active_view = SettingsView(self)
        self.active_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def create_new_workout(self):
        """Create new workout"""
        editor = WorkoutEditor(self)
        editor.grab_set()  # Modal window


def main():
    """Application entry point"""
    # Load saved theme from settings
    data_manager = DataManager()
    settings = data_manager.load_settings()
    saved_theme = settings.get("theme", "dark")

    print(f"Loading saved theme: {saved_theme}")

    # Apply saved theme
    ctk.set_appearance_mode(saved_theme)
    ctk.set_default_color_theme("blue")

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()