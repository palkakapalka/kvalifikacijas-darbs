# ============================================================
# models.py
# All data models
# ============================================================

import json
import os
import sqlite3
from datetime import datetime


# ==================== Exercise ====================
class Exercise:
    #Exercise (video + duration)

    def __init__(self, video_path="", duration=0):
        self.video_path = video_path  # Path to video
        self.duration = duration  # Duration in seconds

    def to_dict(self):
        #Convert to dictionary
        return {
            "video_path": self.video_path,
            "duration": self.duration
        }

    @staticmethod
    def from_dict(data):
        #Create from dictionary
        return Exercise(data["video_path"], data["duration"])


# ==================== Workout ====================
class Workout:
    #Workout (10 cells with exercises)

    def __init__(self, name="", exercises=None):
        self.name = name  # Workout name
        # Always 10 cells, some may be None
        if exercises is None:
            self.exercises = [None] * 10  # Create 10 empty
        else:
            self.exercises = exercises + [None] * (10 - len(exercises))  # Pad to 10

    def get_total_duration(self):
        #Total duration in seconds
        return sum(ex.duration for ex in self.exercises if ex)  # Sum non-None exercises

    def get_exercise_count(self):
        #Number of non-empty exercises
        return sum(1 for ex in self.exercises if ex)  # Count non-None

    def to_dict(self):
        #Convert to dictionary
        return {
            "name": self.name,
            "exercises": [ex.to_dict() if ex else None for ex in self.exercises]  # Convert each exercise
        }

    @staticmethod
    def from_dict(data):
        #Create from dictionary
        exercises = []  # Empty list
        for ex_data in data["exercises"]:  # Loop through exercises
            if ex_data:  # If not None
                exercises.append(Exercise.from_dict(ex_data))  # Create Exercise object
            else:
                exercises.append(None)  # Keep None
        return Workout(data["name"], exercises)  # Create Workout


# ==================== DataManager ====================
class DataManager:
    #Application data management (JSON)

    def __init__(self, workouts_file="data/workouts.json", settings_file="data/settings.json"):
        self.workouts_file = workouts_file  # Workouts JSON path
        self.settings_file = settings_file  # Settings JSON path
        self._ensure_files_exist()  # Create if missing

    def _ensure_files_exist(self):
        #Create files if they don't exist
        os.makedirs("data", exist_ok=True)  # Create data folder
        os.makedirs("data/gallery", exist_ok=True)  # Create gallery folder

        if not os.path.exists(self.workouts_file):  # No workouts file
            self.save_workouts([])  # Create empty

        if not os.path.exists(self.settings_file):  # No settings file
            self.save_settings({"theme": "dark", "gallery_path": "data/gallery"})  # Create defaults

    def load_workouts(self):
        #Load all workouts
        try:
            with open(self.workouts_file, 'r', encoding='utf-8') as f:  # Open file
                data = json.load(f)  # Parse JSON
            return [Workout.from_dict(w) for w in data.get("workouts", [])]
        except:
            return []  # Return empty list

    def save_workouts(self, workouts):
        #Save all workouts
        data = {"workouts": [w.to_dict() for w in workouts]}  # Convert to dicts
        with open(self.workouts_file, 'w', encoding='utf-8') as f:  # Open file
            json.dump(data, f, ensure_ascii=False, indent=2)  # Write JSON

    def load_settings(self):
        #Load settings
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:  # Open file
                return json.load(f)  # Parse JSON
        except:
            return {"theme": "dark", "gallery_path": "data/gallery"}  # Return defaults

    def save_settings(self, settings):
        """Save settings"""
        with open(self.settings_file, 'w', encoding='utf-8') as f:  # Open file
            json.dump(settings, f, ensure_ascii=False, indent=2)  # Write JSON


# ==================== Database ====================
class Database:
    #Statistics database management (SQLite)

    def __init__(self, db_file="data/statistics.db"):
        self.db_file = db_file  # Database file path
        os.makedirs("data", exist_ok=True)  # Create folder
        self._create_tables()  # Create tables

    def _create_tables(self):
        #Create tables if they don't exist
        conn = sqlite3.connect(self.db_file)  # Connect to database
        cursor = conn.cursor()  # Create cursor

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS workout_history
                       (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           workout_name TEXT NOT NULL,
                           start_time TIMESTAMP NOT NULL,
                           duration_seconds INTEGER NOT NULL,
                           completed BOOLEAN NOT NULL,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                       ''')  # Create table

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_start_time ON workout_history(start_time)')  # Index for dates
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workout_name ON workout_history(workout_name)')  # Index for names

        conn.commit()  # Save
        conn.close()

    def add_workout_session(self, workout_name, start_time, duration, completed):
        #Add workout record
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor

        cursor.execute('''
                       INSERT INTO workout_history (workout_name, start_time, duration_seconds, completed)
                       VALUES (?, ?, ?, ?)
                       ''', (workout_name, start_time, duration, completed))  # Insert record

        session_id = cursor.lastrowid  # Get new ID
        conn.commit()  # Save
        conn.close()
        return session_id  # Return ID

    def update_workout_session(self, session_id, duration, completed):
        #Update workout record
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor

        cursor.execute('''
                       UPDATE workout_history
                       SET duration_seconds = ?, completed = ?
                       WHERE id = ?
                       ''', (duration, completed, session_id))  # Update record

        conn.commit()  # Save
        conn.close()

    def get_total_workouts(self):
        #Total number of workouts
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor
        cursor.execute('SELECT COUNT(*) FROM workout_history')  # Count all
        count = cursor.fetchone()[0]  # Get result
        conn.close()
        return count

    def get_total_time(self):
        #Total workout time in seconds
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor
        cursor.execute('SELECT SUM(duration_seconds) FROM workout_history')  # Sum durations
        total = cursor.fetchone()[0] or 0  # Get result
        conn.close()
        return total

    def get_last_workout(self):
        #Last workout (name, date)
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor
        cursor.execute('''
                       SELECT workout_name, start_time
                       FROM workout_history
                       ORDER BY start_time DESC LIMIT 1
                       ''')  # Get latest
        result = cursor.fetchone()  # Get result
        conn.close()
        return result if result else (None, None)

    def get_completed_stats(self):
        #Completed and incomplete workouts
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor
        cursor.execute('''
                       SELECT SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed,
                              SUM(CASE WHEN completed = 0 THEN 1 ELSE 0 END) as incomplete
                       FROM workout_history
                       ''')  # Count both types
        result = cursor.fetchone()  # Get result
        conn.close()
        return result if result else (0, 0)  # Return counts

    def get_workout_counts(self):
        #Execution count for each workout
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor
        cursor.execute('''
                       SELECT workout_name,
                              COUNT(*) as count,
                              SUM(duration_seconds) as total_time,
                              ROUND(AVG(CASE WHEN completed = 1 THEN 100.0 ELSE 0.0 END), 1) as completion_rate
                       FROM workout_history
                       GROUP BY workout_name
                       ORDER BY count DESC
                       ''')  # Group by name
        results = cursor.fetchall()  # Get all results
        conn.close()
        return results  # Return list

    def delete_session(self, session_id):
        #Delete record from history
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor
        cursor.execute('DELETE FROM workout_history WHERE id = ?', (session_id,))  # Delete by ID
        conn.commit()  # Save
        conn.close()

    # ==================== INDIVIDUAL WORKOUT STATS ====================

    def get_workout_total_executions(self, workout_name):
        #Total executions for specific workout
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor
        cursor.execute('SELECT COUNT(*) FROM workout_history WHERE workout_name = ?', (workout_name,))  # Count by name
        count = cursor.fetchone()[0]  # Get result
        conn.close()
        return count

    def get_workout_total_time(self, workout_name):
        #Total time for specific workout
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor
        cursor.execute('SELECT SUM(duration_seconds) FROM workout_history WHERE workout_name = ?', (workout_name,))  # Sum by name
        total = cursor.fetchone()[0] or 0  # Get result
        conn.close()
        return total

    def get_workout_last_execution(self, workout_name):
        #Last execution date for specific workout
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor
        cursor.execute('''
                       SELECT start_time
                       FROM workout_history
                       WHERE workout_name = ?
                       ORDER BY start_time DESC LIMIT 1
                       ''', (workout_name,))  # Get latest
        result = cursor.fetchone()  # Get result
        conn.close()
        return result[0] if result else None  # Return date

    def get_workout_completed_stats(self, workout_name):
        #Completed/incomplete for specific workout
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor
        cursor.execute('''
                       SELECT SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed,
                              SUM(CASE WHEN completed = 0 THEN 1 ELSE 0 END) as incomplete
                       FROM workout_history
                       WHERE workout_name = ?
                       ''', (workout_name,))  # Count by name
        result = cursor.fetchone()  # Get result
        conn.close()
        return result if result else (0, 0)  # Return counts

    def get_workout_history(self, workout_name):
        #Get all sessions for specific workout
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor
        cursor.execute('''
                       SELECT id, start_time, duration_seconds, completed
                       FROM workout_history
                       WHERE workout_name = ?
                       ORDER BY start_time DESC
                       ''', (workout_name,))  # Get all sessions
        results = cursor.fetchall()  # Get all results
        conn.close()
        return results  # Return list

    def get_workout_average_duration(self, workout_name):
        #Average duration for completed sessions
        conn = sqlite3.connect(self.db_file)  # Connect
        cursor = conn.cursor()  # Create cursor
        cursor.execute('''
                       SELECT AVG(duration_seconds)
                       FROM workout_history
                       WHERE workout_name = ? AND completed = 1
                       ''', (workout_name,))
        result = cursor.fetchone()[0]  # Get result
        conn.close()
        return int(result) if result else 0  # Return average