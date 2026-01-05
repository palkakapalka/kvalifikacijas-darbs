# ============================================================
# FILE 4: utils.py
# Utility functions
# ============================================================

import cv2
from PIL import Image


def format_duration(seconds):
    """Format seconds to readable format"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def parse_time_input(time_str):
    """Parse 'mm:ss' string to seconds"""
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes * 60 + seconds
        return 0
    except:
        return 0


def seconds_to_mmss(seconds):
    """Convert seconds to mm:ss format"""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def generate_video_thumbnail(video_path, size=(200, 150)):
    """Create video thumbnail"""
    try:
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()

        if ret:
            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img.thumbnail(size)
            return img
        return None
    except:
        return None


def get_video_duration(video_path):
    """Get video duration in seconds"""
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()

        if fps > 0:
            return int(frame_count / fps)
        return 0
    except:
        return 0