# ============================================================
# FILE 2: models.py
# All data models (WITH INDIVIDUAL WORKOUT STATS)
# ============================================================

import json
import os
import sqlite3
from datetime import datetime


# ==================== Exercise ====================
class Exercise:
    """Exercise (video + duration)"""

    def __init__(self, video_path="", duration=0):
        self.video_path = video_path
        self.duration = duration  # in seconds

    def to_dict(self):
        return {
            "video_path": self.video_path,
            "duration": self.duration
        }

    @staticmethod
    def from_dict(data):
        return Exercise(data["video_path"], data["duration"])


# ==================== Workout ====================
class Workout:
    """Workout (10 cells with exercises)"""

    def __init__(self, name="", exercises=None):
        self.name = name
        # Always 10 cells, some may be None
        if exercises is None:
            self.exercises = [None] * 10
        else:
            self.exercises = exercises + [None] * (10 - len(exercises))

    def get_total_duration(self):
        """Total duration in seconds"""
        return sum(ex.duration for ex in self.exercises if ex)

    def get_exercise_count(self):
        """Number of non-empty exercises"""
        return sum(1 for ex in self.exercises if ex)

    def to_dict(self):
        return {
            "name": self.name,
            "exercises": [ex.to_dict() if ex else None for ex in self.exercises]
        }

    @staticmethod
    def from_dict(data):
        exercises = []
        for ex_data in data["exercises"]:
            if ex_data:
                exercises.append(Exercise.from_dict(ex_data))
            else:
                exercises.append(None)
        return Workout(data["name"], exercises)


# ==================== DataManager ====================
class DataManager:
    """Application data management (JSON)"""

    def __init__(self, workouts_file="data/workouts.json",
                 settings_file="data/settings.json"):
        self.workouts_file = workouts_file
        self.settings_file = settings_file
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """Create files if they don't exist"""
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/gallery", exist_ok=True)

        if not os.path.exists(self.workouts_file):
            self.save_workouts([])

        if not os.path.exists(self.settings_file):
            self.save_settings({"theme": "dark", "gallery_path": "data/gallery"})

    def load_workouts(self):
        """Load all workouts"""
        try:
            with open(self.workouts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [Workout.from_dict(w) for w in data.get("workouts", [])]
        except:
            return []

    def save_workouts(self, workouts):
        """Save all workouts"""
        data = {"workouts": [w.to_dict() for w in workouts]}
        with open(self.workouts_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_settings(self):
        """Load settings"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"theme": "dark", "gallery_path": "data/gallery"}

    def save_settings(self, settings):
        """Save settings"""
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)


# ==================== Database ====================
class Database:
    """Statistics database management (SQLite)"""

    def __init__(self, db_file="data/statistics.db"):
        self.db_file = db_file
        os.makedirs("data", exist_ok=True)
        self._create_tables()

    def _create_tables(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS workout_history
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           workout_name
                           TEXT
                           NOT
                           NULL,
                           start_time
                           TIMESTAMP
                           NOT
                           NULL,
                           duration_seconds
                           INTEGER
                           NOT
                           NULL,
                           completed
                           BOOLEAN
                           NOT
                           NULL,
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_start_time ON workout_history(start_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workout_name ON workout_history(workout_name)')

        conn.commit()
        conn.close()

    def add_workout_session(self, workout_name, start_time, duration, completed):
        """Add workout record"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
                       INSERT INTO workout_history (workout_name, start_time, duration_seconds, completed)
                       VALUES (?, ?, ?, ?)
                       ''', (workout_name, start_time, duration, completed))

        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id

    def update_workout_session(self, session_id, duration, completed):
        """Update workout record"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
                       UPDATE workout_history
                       SET duration_seconds = ?,
                           completed        = ?
                       WHERE id = ?
                       ''', (duration, completed, session_id))

        conn.commit()
        conn.close()

    def get_total_workouts(self):
        """Total number of workouts"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM workout_history')
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_total_time(self):
        """Total workout time in seconds"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(duration_seconds) FROM workout_history')
        total = cursor.fetchone()[0] or 0
        conn.close()
        return total

    def get_last_workout(self):
        """Last workout (name, date)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT workout_name, start_time
                       FROM workout_history
                       ORDER BY start_time DESC LIMIT 1
                       ''')
        result = cursor.fetchone()
        conn.close()
        return result if result else (None, None)

    def get_completed_stats(self):
        """Completed and incomplete workouts"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed,
                              SUM(CASE WHEN completed = 0 THEN 1 ELSE 0 END) as incomplete
                       FROM workout_history
                       ''')
        result = cursor.fetchone()
        conn.close()
        return result if result else (0, 0)

    def get_workout_counts(self):
        """Execution count for each workout"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT workout_name,
                              COUNT(*) as count,
                              SUM(duration_seconds) as total_time,
                              ROUND(AVG(CASE WHEN completed = 1 THEN 100.0 ELSE 0.0 END), 1) as completion_rate
                       FROM workout_history
                       GROUP BY workout_name
                       ORDER BY count DESC
                       ''')
        results = cursor.fetchall()
        conn.close()
        return results

    def delete_session(self, session_id):
        """Delete record from history"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM workout_history WHERE id = ?', (session_id,))
        conn.commit()
        conn.close()

    # ==================== INDIVIDUAL WORKOUT STATS ====================

    def get_workout_total_executions(self, workout_name):
        """Total executions for specific workout"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM workout_history WHERE workout_name = ?', (workout_name,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_workout_total_time(self, workout_name):
        """Total time for specific workout"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(duration_seconds) FROM workout_history WHERE workout_name = ?', (workout_name,))
        total = cursor.fetchone()[0] or 0
        conn.close()
        return total

    def get_workout_last_execution(self, workout_name):
        """Last execution date for specific workout"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT start_time
                       FROM workout_history
                       WHERE workout_name = ?
                       ORDER BY start_time DESC LIMIT 1
                       ''', (workout_name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_workout_completed_stats(self, workout_name):
        """Completed vs incomplete for specific workout"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed,
                              SUM(CASE WHEN completed = 0 THEN 1 ELSE 0 END) as incomplete
                       FROM workout_history
                       WHERE workout_name = ?
                       ''', (workout_name,))
        result = cursor.fetchone()
        conn.close()
        return result if result else (0, 0)

    def get_workout_history(self, workout_name):
        """Get all sessions for specific workout"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT id, start_time, duration_seconds, completed
                       FROM workout_history
                       WHERE workout_name = ?
                       ORDER BY start_time DESC
                       ''', (workout_name,))
        results = cursor.fetchall()
        conn.close()
        return results

    def get_workout_average_duration(self, workout_name):
        """Average duration for completed sessions"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
                       SELECT AVG(duration_seconds)
                       FROM workout_history
                       WHERE workout_name = ?
                         AND completed = 1
                       ''', (workout_name,))
        result = cursor.fetchone()[0]
        conn.close()
        return int(result) if result else 0