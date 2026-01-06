# ============================================================
# settings_view.py
# "Settings" page
# ============================================================

import customtkinter as ctk
from models import DataManager


class SettingsView(ctk.CTkFrame):
    #Application settings view

    def __init__(self, master):
        super().__init__(master)

        self.master_window = master  # Reference to main
        self.data_manager = DataManager()  # Data manager instance
        self.settings = self.data_manager.load_settings()  # Load current settings

        # Title
        label = ctk.CTkLabel(
            self,
            text="Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        label.pack(pady=20)

        # Container for settings
        settings_container = ctk.CTkFrame(self)
        settings_container.pack(fill="both", expand=True, padx=50, pady=20)

        # Theme setting
        self.create_theme_setting(settings_container)  # Create theme controls

    def create_theme_setting(self, container):
        #Create theme setting
        theme_frame = ctk.CTkFrame(container)
        theme_frame.pack(fill="x", pady=20, padx=20)

        # Setting title
        theme_label = ctk.CTkLabel(
            theme_frame,
            text="Theme",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        theme_label.pack(anchor="w", padx=20, pady=(20, 10))

        # Description
        desc_label = ctk.CTkLabel(
            theme_frame,
            text="Choose light or dark theme for the application",
            font=ctk.CTkFont(size=12),
            text_color="gray"  # Gray text
        )
        desc_label.pack(anchor="w", padx=20, pady=(0, 20))

        # Container for switch
        switch_container = ctk.CTkFrame(theme_frame, fg_color="transparent")
        switch_container.pack(fill="x", padx=20, pady=(0, 20))

        # "Light" label
        light_label = ctk.CTkLabel(
            switch_container,
            text="☀️ Light",
            font=ctk.CTkFont(size=14)
        )
        light_label.pack(side="left", padx=(0, 20))

        # Switch
        current_theme = self.settings.get("theme", "dark")  # Get saved theme
        switch_var = ctk.StringVar(value=current_theme)  # Variable for switch

        self.theme_switch = ctk.CTkSwitch(
            switch_container,
            text="",
            variable=switch_var,  # Bind to variable
            onvalue="dark",  # Value when on
            offvalue="light",  # Value when off
            command=self.toggle_theme  # Toggle function
        )
        self.theme_switch.pack(side="left")

        # Set correct state
        if current_theme == "dark":  # If dark theme
            self.theme_switch.select()  # Switch on
        else:
            self.theme_switch.deselect()  # Switch off

        # "Dark" label
        dark_label = ctk.CTkLabel(
            switch_container,
            text="🌙 Dark",
            font=ctk.CTkFont(size=14)
        )
        dark_label.pack(side="left", padx=(20, 0))

        # Info message
        info_frame = ctk.CTkFrame(theme_frame, fg_color="gray25")
        info_frame.pack(fill="x", padx=20, pady=(0, 20))

        info_label = ctk.CTkLabel(
            info_frame,
            text="ℹ️ Changes will take effect after restarting the application",
            font=ctk.CTkFont(size=12),
            anchor="w"  # Left align
        )
        info_label.pack(padx=15, pady=15, anchor="w")

    def toggle_theme(self):
        #Toggle theme
        # Get current saved theme
        current_theme = self.settings.get("theme", "dark")  # Current theme

        # Toggle to opposite theme
        new_theme = "light" if current_theme == "dark" else "dark"  # Switch theme

        # DEBUG: Show what's happening
        print(f"Current: {current_theme}, Switching to: {new_theme}")  # Debug output

        # Save to settings
        self.settings["theme"] = new_theme  # Update settings
        self.data_manager.save_settings(self.settings)  # Save to file