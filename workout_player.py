# ============================================================
# workout_player.py
# Workout playback window
# ============================================================

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import threading
import time
from datetime import datetime
from models import Database
from utils import seconds_to_mmss, generate_video_prev


class WorkoutPlayer(ctk.CTkToplevel):
    # Workout playback window

    def __init__(self, master, workout):
        super().__init__(master)

        self.workout = workout
        self.db = Database()

        # Playback state
        self.is_playing = False
        self.is_paused = False
        self.is_fullscreen = False
        self.is_resting = False  # Flag for rest period
        self.current_exercise_index = 0
        self.current_time = 0  # Current exercise time in seconds
        self.total_elapsed = 0  # Total workout elapsed time
        self.session_id = None  # DB session ID
        self.session_start_time = None

        # Get list of non-empty exercises
        self.exercises = [ex for ex in workout.exercises if ex is not None]

        if not self.exercises:
            self.destroy()
            return

        # Video
        self.video_capture = None
        self.video_thread = None
        self.stop_video_thread = False

        # Window setup
        self.title(f"Workout: {workout.name if workout.name else 'Untitled'}")
        self.geometry("1000x700")

        # Window close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create UI
        self.create_ui()

        # Start workout
        self.start_workout()

    def create_ui(self):
        # Create player interface
        # Top panel with info
        self.create_top_panel()

        # Video area
        self.video_frame = ctk.CTkFrame(self, fg_color="black")
        self.video_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Canvas for video display
        self.video_canvas = ctk.CTkCanvas(
            self.video_frame,
            bg="black",
            highlightthickness=0
        )
        self.video_canvas.pack(fill="both", expand=True)

        # Current exercise timer (overlay on video)
        self.exercise_timer_label = ctk.CTkLabel(
            self.video_frame,
            text="0:00",
            font=ctk.CTkFont(size=48, weight="bold"),
            fg_color="black",
            bg_color="black"
        )
        self.exercise_timer_label.place(relx=0.5, rely=0.5, anchor="center")

        # Control panel
        self.create_control_panel()

    def create_top_panel(self):
        # Create top panel
        top_panel = ctk.CTkFrame(self, height=60)
        top_panel.pack(fill="x", padx=10, pady=(10, 0))
        top_panel.pack_propagate(False)

        # Progress "Exercise X of Y"
        total_exercises = len(self.exercises)
        self.progress_label = ctk.CTkLabel(
            top_panel,
            text=f"Exercise 1 of {total_exercises}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.progress_label.pack(side="left", padx=20)

        # Total workout timer (top right corner)
        self.total_timer_label = ctk.CTkLabel(
            top_panel,
            text="Total Time: 0:00",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.total_timer_label.pack(side="right", padx=20)

    def create_control_panel(self):
        # Create control panel
        control_panel = ctk.CTkFrame(self, height=80)
        control_panel.pack(fill="x", padx=10, pady=10)
        control_panel.pack_propagate(False)

        # Start/Pause button
        self.play_pause_btn = ctk.CTkButton(
            control_panel,
            text="▶ Start",
            command=self.toggle_play_pause,
            width=150,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.play_pause_btn.pack(side="left", padx=20)

        # Fullscreen button
        self.fullscreen_btn = ctk.CTkButton(
            control_panel,
            text="⛶ Fullscreen",
            command=self.toggle_fullscreen,
            width=150,
            height=50
        )
        self.fullscreen_btn.pack(side="right", padx=20)

    def start_workout(self):
        # Start workout
        # Record start in DB
        workout_name = self.workout.name if self.workout.name else "Untitled"
        self.session_start_time = datetime.now()
        self.session_id = self.db.add_workout_session(
            workout_name,
            self.session_start_time,
            0,
            False
        )

        # Load first exercise
        self.load_exercise(0)

    def load_exercise(self, index):
        # Load exercise by index
        if index >= len(self.exercises):
            # Workout completed
            self.finish_workout(completed=True)
            return

        self.current_exercise_index = index
        self.current_time = 0

        exercise = self.exercises[index]

        # Stop previous video (but don't join from same thread)
        self.stop_video_thread = True
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None

        # Update progress
        total = len(self.exercises)
        self.progress_label.configure(text=f"Exercise {index + 1} of {total}")

        # Load video
        self.video_capture = cv2.VideoCapture(exercise.video_path)

        if not self.video_capture.isOpened():
            print(f"Error opening video: {exercise.video_path}")
            # Skip to next
            self.after(100, lambda: self.next_exercise())
            return

        # Get FPS
        self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        if self.fps == 0:
            self.fps = 30  # Default

        # Start playback if not paused
        if self.is_playing and not self.is_paused:
            self.start_video_playback()

    def start_video_playback(self):
        # Start video playback
        self.stop_video_thread = False
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()

    def video_loop(self):
        # Video playback loop
        exercise = self.exercises[self.current_exercise_index]
        duration = exercise.duration

        frame_delay = 1.0 / self.fps

        while not self.stop_video_thread and self.current_time < duration:
            if self.is_paused:
                time.sleep(0.1)
                continue

            # Read frame
            ret, frame = self.video_capture.read()

            if not ret:
                # Loop video
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            # Convert to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Display frame
            self.display_frame(frame)

            # Update timers
            self.current_time += frame_delay
            self.total_elapsed += frame_delay
            self.update_timers()

            time.sleep(frame_delay)

        # Exercise completed - schedule on main thread
        if not self.stop_video_thread:
            self.after(0, self.on_exercise_complete)

    def display_frame(self, frame):
        # Display frame on canvas
        try:
            # Check if canvas still exists
            if not self.video_canvas.winfo_exists():
                return

            # Get canvas dimensions
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                return

            # Resize frame
            img = Image.fromarray(frame)
            img.thumbnail((canvas_width, canvas_height))

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)

            # Display on canvas
            self.video_canvas.delete("all")
            self.video_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=photo
            )

            # Keep reference
            self.video_canvas.image = photo
        except Exception as e:
            # Silently ignore display errors (widget might be destroyed)
            pass

    def update_timers(self):
        # Update timers
        try:
            # Check if widgets still exist
            if not self.exercise_timer_label.winfo_exists() or not self.total_timer_label.winfo_exists():
                return

            exercise = self.exercises[self.current_exercise_index]
            remaining = exercise.duration - self.current_time

            # Exercise timer
            timer_text = seconds_to_mmss(int(remaining))
            self.exercise_timer_label.configure(text=timer_text)

            # Total timer
            total_text = f"Total Time: {seconds_to_mmss(int(self.total_elapsed))}"
            self.total_timer_label.configure(text=total_text)
        except Exception as e:
            # Silently ignore timer errors (widget might be destroyed)
            pass

    def on_exercise_complete(self):
        # Exercise completion handler
        # Stop video capture (but don't join thread - we're in it!)
        self.stop_video_thread = True
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None

        # Check if there's next exercise
        if self.current_exercise_index + 1 < len(self.exercises):
            # Show preview of next exercise with 10 sec timer
            self.show_rest_period()
        else:
            # Workout completed
            self.finish_workout(completed=True)

    def show_rest_period(self):
        # Show 10-second rest period with preview
        # Set resting flag
        self.is_resting = True

        # Clear canvas
        self.video_canvas.delete("all")

        # Get next exercise
        next_exercise = self.exercises[self.current_exercise_index + 1]

        # Show preview
        try:
            prev = generate_video_prev(next_exercise.video_path, size=(400, 300))
            if prev:
                photo = ImageTk.PhotoImage(prev)

                canvas_width = self.video_canvas.winfo_width()
                canvas_height = self.video_canvas.winfo_height()

                self.video_canvas.create_image(
                    canvas_width // 2,
                    canvas_height // 2,
                    image=photo
                )
                self.video_canvas.image = photo
        except Exception as e:
            print(f"Preview error: {e}")

        # Show "Next Exercise" text
        canvas_width = self.video_canvas.winfo_width()
        self.video_canvas.create_text(
            canvas_width // 2,
            50,
            text="Next Exercise",
            font=("Arial", 24, "bold"),
            fill="white"
        )

        # Countdown 10 seconds
        self.rest_countdown(10)

    def rest_countdown(self, seconds):
        # Rest period countdown
        # Check if window still exists
        try:
            if not self.winfo_exists():
                return
        except:
            return

        if seconds > 0 and self.is_resting and not self.is_paused:
            # Show timer
            try:
                self.exercise_timer_label.configure(text=f"Rest: {seconds}")

                # Update total timer
                self.total_elapsed += 1
                total_text = f"Total Time: {seconds_to_mmss(int(self.total_elapsed))}"
                self.total_timer_label.configure(text=total_text)

                # Next second
                self.after(1000, lambda: self.rest_countdown(seconds - 1))
            except:
                pass
        elif self.is_resting and not self.is_paused:
            # Rest period finished - load next exercise
            self.is_resting = False
            self.next_exercise()

    def next_exercise(self):
        # Move to next exercise
        self.load_exercise(self.current_exercise_index + 1)

    def toggle_play_pause(self):
        # Toggle play/pause
        if not self.is_playing:
            # First start
            self.is_playing = True
            self.play_pause_btn.configure(text="⏸ Pause")
            self.start_video_playback()
        else:
            # Pause/resume
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.play_pause_btn.configure(text="▶ Continue")
            else:
                self.play_pause_btn.configure(text="⏸ Pause")
                # Resume video or rest countdown
                if self.is_resting:
                    # Rest countdown will resume automatically via its condition check
                    pass
                elif not self.video_thread or not self.video_thread.is_alive():
                    self.start_video_playback()

    def toggle_fullscreen(self):
        # Toggle fullscreen mode
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)

        if self.is_fullscreen:
            self.fullscreen_btn.configure(text="⛶ Exit")
        else:
            self.fullscreen_btn.configure(text="⛶ Fullscreen")

    def finish_workout(self, completed=True):
        # Finish workout
        # Stop video
        self.stop_video_thread = True
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None

        # Update DB record
        if self.session_id:
            self.db.update_workout_session(
                self.session_id,
                int(self.total_elapsed),
                completed
            )

        # Show message
        if completed:
            msg = "Workout Completed!"
        else:
            msg = "Workout Interrupted"

        try:
            result_dialog = ctk.CTkInputDialog(
                text=f"{msg}\nTotal Time: {seconds_to_mmss(int(self.total_elapsed))}",
                title="Result"
            )
        except:
            pass

        # Close window
        try:
            self.destroy()
        except:
            pass

    def on_close(self):
        # Window close handler
        # Stop video
        self.stop_video_thread = True
        self.is_resting = False  # Stop rest countdown

        if self.video_capture:
            try:
                self.video_capture.release()
            except:
                pass
            self.video_capture = None

        # Save partial progress
        if self.session_id:
            try:
                self.db.update_workout_session(
                    self.session_id,
                    int(self.total_elapsed),
                    False  # Not completed
                )
            except:
                pass

        try:
            self.destroy()
        except:
            pass