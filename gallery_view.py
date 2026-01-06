# ============================================================
# gallery_view.py
# "Gallery" page
# ============================================================

import customtkinter as ctk
from tkinter import filedialog
import os
from PIL import Image
from utils import generate_video_prev


class GalleryView(ctk.CTkFrame):
    """Video library view"""

    def __init__(self, master):
        super().__init__(master)

        self.gallery_path = "data/gallery"  # Video storage path
        self.view_mode = "list"  # Display mode

        # Top panel
        self.create_top_panel()

        # Scrollable area for videos
        self.videos_frame = ctk.CTkScrollableFrame(self)  # Scrollable container
        self.videos_frame.pack(fill="both", expand=True, pady=10)

        # Load videos
        self.load_videos()

        # Drag & drop support
        self.setup_drag_drop()

    def create_top_panel(self):
        """Create top panel with buttons"""
        top_panel = ctk.CTkFrame(self)  # Top container
        top_panel.pack(fill="x", pady=(0, 10))

        # Title
        label = ctk.CTkLabel(
            top_panel,
            text="Video Library",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        label.pack(side="left", padx=20, pady=20)

        # Add video button
        btn_add = ctk.CTkButton(
            top_panel,
            text="+ Add Video",
            command=self.add_video_dialog,  # Open file dialog
            width=150
        )
        btn_add.pack(side="right", padx=20)

        # View toggle
        btn_toggle_view = ctk.CTkButton(
            top_panel,
            text="⊞ Grid / ☰ List",
            command=self.toggle_view,  # Switch view mode
            width=150
        )
        btn_toggle_view.pack(side="right", padx=10)

    def setup_drag_drop(self):
        #Setup drag & drop (basic implementation)
        pass

    def add_video_dialog(self):
        #Open video selection dialog
        filetypes = (  # Allowed file types
            ('Video files', '*.mp4 *.avi *.mkv *.mov'),
            ('All files', '*.*')
        )

        filenames = filedialog.askopenfilenames(  # Select multiple files
            title='Select video files',
            filetypes=filetypes
        )

        if filenames:
            self.add_videos(filenames)  # Copy selected files

    def add_videos(self, file_paths):
        #Add video files to library
        os.makedirs(self.gallery_path, exist_ok=True)  # Create folder

        for file_path in file_paths:
            # Copy file to gallery
            filename = os.path.basename(file_path)  # Get filename only
            dest_path = os.path.join(self.gallery_path, filename)  # Destination path

            # Check if exists
            if os.path.exists(dest_path):
                # Add number if file exists
                name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_path):  # Find unique name
                    filename = f"{name}_{counter}{ext}"  # Add counter
                    dest_path = os.path.join(self.gallery_path, filename)
                    counter += 1

            # Copy file
            import shutil
            shutil.copy2(file_path, dest_path)

        # Update display
        self.load_videos()  # Refresh video list

    def load_videos(self):
        #Load and display all videos from gallery
        for widget in self.videos_frame.winfo_children():
            widget.destroy()

        # Get list of video files
        if not os.path.exists(self.gallery_path):  # Check folder exists
            os.makedirs(self.gallery_path, exist_ok=True)  # Create if missing

        video_files = []  # Empty list
        for filename in os.listdir(self.gallery_path):  # Loop through files
            if filename.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):  # Check extension
                video_files.append(filename)  # Add to list

        if not video_files:  # Empty library
            label = ctk.CTkLabel(
                self.videos_frame,
                text="Library is empty.\nAdd videos using the 'Add Video' button",
                font=ctk.CTkFont(size=16)
            )
            label.pack(pady=50)
            return

        # Display videos
        if self.view_mode == "grid":  # Grid layout
            self.show_grid_view(video_files)
        else:  # List layout
            self.show_list_view(video_files)

    def show_grid_view(self, video_files):
        #Display videos in grid
        grid_container = ctk.CTkFrame(self.videos_frame, fg_color="transparent")
        grid_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Arrange videos in grid (3 columns)
        columns = 3  # Number of columns
        for i, filename in enumerate(video_files):
            row = i // columns  # Calculate row position
            col = i % columns  # Calculate column position

            video_card = self.create_video_card_grid(grid_container, filename)
            video_card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        for c in range(columns):
            grid_container.grid_columnconfigure(c, weight=1)

    def show_list_view(self, video_files):
        #Display videos in list
        for filename in video_files:  # Each video
            video_row = self.create_video_row_list(filename)
            video_row.pack(fill="x", pady=5, padx=10)

    def create_video_card_grid(self, parent, filename):
        #Create video card for grid
        card = ctk.CTkFrame(parent, width=250, height=250)

        video_path = os.path.join(self.gallery_path, filename)

        preview_frame = ctk.CTkFrame(card, width=230, height=150, fg_color="gray20")
        preview_frame.pack(pady=10, padx=10)
        preview_frame.pack_propagate(False)

        # Try to create preview
        try:
            prev = generate_video_prev(video_path, size=(230, 150))  # Generate preview
            if prev:
                ctk_image = ctk.CTkImage(
                    light_image=prev,
                    dark_image=prev,
                    size=prev.size
                )
                preview_label = ctk.CTkLabel(preview_frame, image=ctk_image, text="")
                preview_label.image = ctk_image
                preview_label.pack(expand=True)
            else:
                raise Exception("No preview")
        except Exception as e:
            # Placeholder if preview failed
            placeholder = ctk.CTkLabel(
                preview_frame,
                text="🎬",
                font=ctk.CTkFont(size=48)
            )
            placeholder.pack(expand=True)

        # Filename
        name_label = ctk.CTkLabel(
            card,
            text=filename,
            font=ctk.CTkFont(size=12),
            wraplength=230
        )
        name_label.pack(pady=5)

        # Delete button
        btn_delete = ctk.CTkButton(
            card,
            text="Delete",
            width=100,
            fg_color="red",
            hover_color="darkred",
            command=lambda: self.delete_video(filename)  # Delete  video
        )
        btn_delete.pack(pady=5)

        return card

    def create_video_row_list(self, filename):
        """Create video row for list"""
        row = ctk.CTkFrame(self.videos_frame)

        video_path = os.path.join(self.gallery_path, filename)

        # Mini preview
        preview_frame = ctk.CTkFrame(row, width=100, height=60, fg_color="gray20")
        preview_frame.pack(side="left", padx=10, pady=5)
        preview_frame.pack_propagate(False)

        try:
            prev = generate_video_prev(video_path, size=(100, 60))
            if prev:
                ctk_image = ctk.CTkImage(
                    light_image=prev,
                    dark_image=prev,
                    size=prev.size
                )
                preview_label = ctk.CTkLabel(preview_frame, image=ctk_image, text="")  # Show image
                preview_label.image = ctk_image
                preview_label.pack(expand=True)
            else:
                raise Exception("No preview")
        except Exception as e:
            placeholder = ctk.CTkLabel(preview_frame, text="🎬", font=ctk.CTkFont(size=24))
            placeholder.pack(expand=True)

        # Name
        name_label = ctk.CTkLabel(
            row,
            text=filename,  # Video name
            font=ctk.CTkFont(size=14),
            anchor="w"  # Left align
        )
        name_label.pack(side="left", padx=10, fill="x", expand=True)

        # Delete button
        btn_delete = ctk.CTkButton(
            row,
            text="Delete",
            width=100,
            fg_color="red",
            hover_color="darkred",
            command=lambda: self.delete_video(filename)  # Delete video
        )
        btn_delete.pack(side="right", padx=10)

        return row

    def delete_video(self, filename):
        #Delete video from library
        video_path = os.path.join(self.gallery_path, filename)  # Full path

        # Confirmation
        dialog = ctk.CTkInputDialog(  # Confirmation dialog
            text=f"Delete video '{filename}'?\nType 'yes' to confirm:",
            title="Confirm Deletion"
        )

        if dialog.get_input() == "yes":  # User confirmed
            try:
                os.remove(video_path)  # Delete file
                self.load_videos()  # Refresh display
            except Exception as e:
                print(f"Delete error: {e}")  # Print error

    def toggle_view(self):
        """Toggle display mode"""
        self.view_mode = "list" if self.view_mode == "grid" else "grid"  # Switch mode
        self.load_videos()  # Reload with new mode