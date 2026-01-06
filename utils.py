# ============================================================
# utils.py
# Utility functions
# ============================================================

import cv2
from PIL import Image


def format_duration(seconds):
    #Format seconds to readable format
    hours = seconds // 3600  # Calculate hours
    minutes = (seconds % 3600) // 60  # Calculate minutes
    secs = seconds % 60  # Calculate seconds

    if hours > 0:  # Has hours
        return f"{hours}h {minutes}m"  # Show hours/minutes
    elif minutes > 0:  # Has minutes
        return f"{minutes}m {secs}s"  # Show minutes/seconds
    else:
        return f"{secs}s"  # Show seconds only


def parse_time_input(time_str):
    #Parse 'mm:ss' string to seconds
    try:
        parts = time_str.strip().split(':')  # Split by ":"
        if len(parts) == 2:  # Valid format
            minutes = int(parts[0])  # Parse minutes
            seconds = int(parts[1])  # Parse seconds
            return minutes * 60 + seconds  # Convert to seconds
        return 0  # Invalid format
    except:
        return 0  # Parse error


def seconds_to_mmss(seconds):
    #Convert seconds to mm:ss format
    minutes = seconds // 60  # Calculate minutes
    secs = seconds % 60  # Remaining seconds
    return f"{minutes}:{secs:02d}"  # Format with padding


def generate_video_prev(video_path, size=(200, 150)):
    #Create video preview
    try:
        cap = cv2.VideoCapture(video_path)  # Open video
        ret, frame = cap.read()  # Read first frame
        cap.release()  # Close video

        if ret:  # Frame read successfully
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img.thumbnail(size)
            return img
        return None
    except:
        return None


def get_video_duration(video_path):
    #Get video duration in seconds
    try:
        cap = cv2.VideoCapture(video_path)  # Open video
        fps = cap.get(cv2.CAP_PROP_FPS)  # Get frames per second
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)  # Get total frames
        cap.release()  # Close video

        if fps > 0:  # Valid FPS
            return int(frame_count / fps)  # Calculate duration
        return 0  # Invalid FPS
    except:
        return 0  # Error occurred