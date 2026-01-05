# ============================================================
# statistics_view.py
# "Statistics" page (WITH INDIVIDUAL WORKOUT STATS)
# ============================================================

import customtkinter as ctk
from models import Database, DataManager
from utils import format_duration
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime


class StatisticsView(ctk.CTkFrame):
    """Workout statistics view"""

    def __init__(self, master):
        super().__init__(master)

        self.db = Database()
        self.data_manager = DataManager()
        self.selected_workout = "all"  # "all" or workout name

        # Title
        label = ctk.CTkLabel(
            self,
            text="Statistics",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        label.pack(pady=20)

        # Workout selection dropdown
        self.create_selector()

        # Scrollable area for statistics
        self.stats_frame = ctk.CTkScrollableFrame(self)
        self.stats_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Load statistics
        self.load_statistics()

    def create_selector(self):
        """Create dropdown list"""
        selector_frame = ctk.CTkFrame(self)
        selector_frame.pack(fill="x", padx=20, pady=(0, 10))

        label = ctk.CTkLabel(
            selector_frame,
            text="Select workout:",
            font=ctk.CTkFont(size=14)
        )
        label.pack(side="left", padx=10)

        # Get workouts list
        workouts = self.data_manager.load_workouts()
        workout_names = ["All Workouts"] + [w.name if w.name else f"Workout {i + 1}"
                                            for i, w in enumerate(workouts)]

        self.selector = ctk.CTkOptionMenu(
            selector_frame,
            values=workout_names,
            command=self.on_workout_selected,
            width=300
        )
        self.selector.set("All Workouts")
        self.selector.pack(side="left", padx=10)

    def on_workout_selected(self, choice):
        """Workout selection handler"""
        if choice == "All Workouts":
            self.selected_workout = "all"
        else:
            self.selected_workout = choice

        self.load_statistics()

    def load_statistics(self):
        """Load and display statistics"""
        # Clear
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        if self.selected_workout == "all":
            self.show_general_statistics()
        else:
            self.show_individual_statistics()

    def show_general_statistics(self):
        """Show general statistics for all workouts"""
        # Metric cards
        cards_frame = ctk.CTkFrame(self.stats_frame)
        cards_frame.pack(fill="x", pady=10)

        # 1. Total workouts
        total_workouts = self.db.get_total_workouts()
        self.create_metric_card(cards_frame, "Total Workouts", str(total_workouts), 0, 0)

        # 2. Total time
        total_seconds = self.db.get_total_time()
        total_time_text = format_duration(total_seconds)
        self.create_metric_card(cards_frame, "Total Time", total_time_text, 0, 1)

        # 3. Last workout
        last_name, last_date = self.db.get_last_workout()
        if last_name:
            date_obj = datetime.fromisoformat(last_date)
            date_text = date_obj.strftime("%d.%m.%Y")
            last_text = f"{last_name}\n{date_text}"
        else:
            last_text = "No data"
        self.create_metric_card(cards_frame, "Last Workout", last_text, 1, 0)

        # 4. Completed vs incomplete
        completed, incomplete = self.db.get_completed_stats()
        total = completed + incomplete
        if total > 0:
            completed_pct = int((completed / total) * 100)
            incomplete_pct = 100 - completed_pct
            completion_text = f"✓ {completed_pct}% / ✗ {incomplete_pct}%"
        else:
            completion_text = "No data"
        self.create_metric_card(cards_frame, "Completed", completion_text, 1, 1)

        # Graphs
        graphs_frame = ctk.CTkFrame(self.stats_frame)
        graphs_frame.pack(fill="both", expand=True, pady=20)

        # Pie chart (completed/incomplete)
        if total > 0:
            self.create_pie_chart(graphs_frame, completed, incomplete)

        # Workouts table
        self.create_workouts_table()

    def show_individual_statistics(self):
        """Show statistics for specific workout"""
        workout_name = self.selected_workout

        # Metric cards
        cards_frame = ctk.CTkFrame(self.stats_frame)
        cards_frame.pack(fill="x", pady=10)

        # 1. Execution count
        executions = self.db.get_workout_total_executions(workout_name)
        self.create_metric_card(cards_frame, "Executions", str(executions), 0, 0)

        # 2. Total time for this workout
        total_seconds = self.db.get_workout_total_time(workout_name)
        total_time_text = format_duration(total_seconds)
        self.create_metric_card(cards_frame, "Total Time", total_time_text, 0, 1)

        # 3. Last execution
        last_date = self.db.get_workout_last_execution(workout_name)
        if last_date:
            date_obj = datetime.fromisoformat(last_date)
            last_text = date_obj.strftime("%d.%m.%Y\n%H:%M")
        else:
            last_text = "Never"
        self.create_metric_card(cards_frame, "Last Execution", last_text, 1, 0)

        # 4. Completed vs incomplete
        completed, incomplete = self.db.get_workout_completed_stats(workout_name)
        total = completed + incomplete
        if total > 0:
            completed_pct = int((completed / total) * 100)
            incomplete_pct = 100 - completed_pct
            completion_text = f"✓ {completed_pct}% / ✗ {incomplete_pct}%"
        else:
            completion_text = "No data"
        self.create_metric_card(cards_frame, "Completed", completion_text, 1, 1)

        # Additional stats row
        stats_frame2 = ctk.CTkFrame(self.stats_frame)
        stats_frame2.pack(fill="x", pady=10)

        # 5. Average duration
        avg_duration = self.db.get_workout_average_duration(workout_name)
        avg_text = format_duration(avg_duration) if avg_duration > 0 else "No data"
        self.create_metric_card(stats_frame2, "Avg Duration", avg_text, 0, 0)

        # Graphs
        graphs_frame = ctk.CTkFrame(self.stats_frame)
        graphs_frame.pack(fill="both", expand=True, pady=20)

        # Pie chart
        if total > 0:
            self.create_pie_chart(graphs_frame, completed, incomplete, title=f"Completion: {workout_name}")

        # Execution history
        self.create_history_table(workout_name)

    def create_metric_card(self, parent, title, value, row, col):
        """Create metric card"""
        card = ctk.CTkFrame(parent, fg_color="gray25")
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # Configure weights
        parent.grid_columnconfigure(col, weight=1)
        parent.grid_rowconfigure(row, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        title_label.pack(pady=(20, 5))

        # Value
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        value_label.pack(pady=(5, 20))

    def create_pie_chart(self, parent, completed, incomplete, title="Workout Completion"):
        """Create pie chart"""
        # Create figure
        fig, ax = plt.subplots(figsize=(5, 4))

        # Data
        sizes = [completed, incomplete]
        labels = [f'Completed\n{completed}', f'Incomplete\n{incomplete}']
        colors = ['#4CAF50', '#F44336']

        # Build chart
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        ax.set_title(title, fontsize=14, pad=20)

        # Dark background
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')

        # Text color
        for text in ax.texts:
            text.set_color('white')

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=20)

    def create_workouts_table(self):
        """Create workouts table (for all workouts view)"""
        table_frame = ctk.CTkFrame(self.stats_frame)
        table_frame.pack(fill="x", pady=20, padx=10)

        # Table header
        header_label = ctk.CTkLabel(
            table_frame,
            text="Workout Statistics",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.pack(pady=10)

        # Column headers
        header_row = ctk.CTkFrame(table_frame, fg_color="gray30")
        header_row.pack(fill="x", padx=10, pady=5)

        headers = ["Name", "Executions", "Total Time", "% Completion"]
        widths = [300, 100, 150, 100]

        for i, (header, width) in enumerate(zip(headers, widths)):
            label = ctk.CTkLabel(
                header_row,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=width
            )
            label.pack(side="left", padx=5, pady=5)

        # Data
        workout_stats = self.db.get_workout_counts()

        if not workout_stats:
            no_data_label = ctk.CTkLabel(
                table_frame,
                text="No workout data",
                font=ctk.CTkFont(size=14)
            )
            no_data_label.pack(pady=20)
            return

        # Data rows
        for workout_name, count, total_time, completion_rate in workout_stats:
            row = ctk.CTkFrame(table_frame, fg_color="gray25")
            row.pack(fill="x", padx=10, pady=2)

            # Name (clickable)
            name_btn = ctk.CTkButton(
                row,
                text=workout_name,
                width=widths[0],
                anchor="w",
                fg_color="transparent",
                hover_color="gray35",
                command=lambda wn=workout_name: self.show_workout_stats(wn)
            )
            name_btn.pack(side="left", padx=5, pady=5)

            # Count
            count_label = ctk.CTkLabel(row, text=str(count), width=widths[1])
            count_label.pack(side="left", padx=5)

            # Time
            time_text = format_duration(total_time)
            time_label = ctk.CTkLabel(row, text=time_text, width=widths[2])
            time_label.pack(side="left", padx=5)

            # Percentage
            pct_label = ctk.CTkLabel(row, text=f"{completion_rate}%", width=widths[3])
            pct_label.pack(side="left", padx=5)

    def create_history_table(self, workout_name):
        """Create execution history table (for individual workout)"""
        table_frame = ctk.CTkFrame(self.stats_frame)
        table_frame.pack(fill="x", pady=20, padx=10)

        # Table header
        header_label = ctk.CTkLabel(
            table_frame,
            text="Execution History",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.pack(pady=10)

        # Column headers
        header_row = ctk.CTkFrame(table_frame, fg_color="gray30")
        header_row.pack(fill="x", padx=10, pady=5)

        headers = ["Date", "Time", "Duration", "Status"]
        widths = [150, 100, 150, 100]

        for i, (header, width) in enumerate(zip(headers, widths)):
            label = ctk.CTkLabel(
                header_row,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=width
            )
            label.pack(side="left", padx=5, pady=5)

        # Data
        history = self.db.get_workout_history(workout_name)

        if not history:
            no_data_label = ctk.CTkLabel(
                table_frame,
                text="No execution history",
                font=ctk.CTkFont(size=14)
            )
            no_data_label.pack(pady=20)
            return

        # Limit to last 20 sessions
        for session_id, start_time, duration, completed in history[:20]:
            row = ctk.CTkFrame(table_frame, fg_color="gray25")
            row.pack(fill="x", padx=10, pady=2)

            # Parse date
            date_obj = datetime.fromisoformat(start_time)

            # Date
            date_label = ctk.CTkLabel(
                row,
                text=date_obj.strftime("%d.%m.%Y"),
                width=widths[0]
            )
            date_label.pack(side="left", padx=5, pady=5)

            # Time
            time_label = ctk.CTkLabel(
                row,
                text=date_obj.strftime("%H:%M"),
                width=widths[1]
            )
            time_label.pack(side="left", padx=5)

            # Duration
            duration_text = format_duration(duration)
            duration_label = ctk.CTkLabel(row, text=duration_text, width=widths[2])
            duration_label.pack(side="left", padx=5)

            # Status
            status_text = "✓ Completed" if completed else "✗ Incomplete"
            status_color = "green" if completed else "red"
            status_label = ctk.CTkLabel(
                row,
                text=status_text,
                width=widths[3],
                text_color=status_color
            )
            status_label.pack(side="left", padx=5)

    def show_workout_stats(self, workout_name):
        """Show specific workout statistics"""
        # Find index in selector
        workouts = self.data_manager.load_workouts()
        for i, w in enumerate(workouts):
            name = w.name if w.name else f"Workout {i + 1}"
            if name == workout_name:
                self.selector.set(name)
                self.selected_workout = name
                self.load_statistics()
                break