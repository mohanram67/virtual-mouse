import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import screen_brightness_control as sbc
import math
import time
import logging
import tkinter as tk
from tkinter import ttk
from threading import Thread
from PIL import Image, ImageTk
import speech_recognition as sr
import pyttsx3
import datetime
import wikipedia
import webbrowser
import subprocess
import smtplib
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Get the screen size
screen_width, screen_height = pyautogui.size()

# Capture video from webcam
cap = cv2.VideoCapture(0)

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 170)
engine.setProperty('volume', 1)
recognizer = sr.Recognizer()

# Global Variables
prev_x, prev_y = 0, 0
curr_x, curr_y = 0, 0
click_threshold = 40  # Distance threshold for clicking
drag_threshold = 50  # Distance threshold for dragging
scroll_speed = 20  # Scrolling speed

# Function to make the assistant speak
def speak(audio):
    engine.say(audio)
    engine.runAndWait()

# Function to listen to user input
def take_command():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio, language='en-in')
            print(f"User said: {command}\n")
            return command.lower()
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that. Please repeat.")
            return "None"
        except sr.RequestError:
            speak("Network issue. Please check your connection.")
            return "None"

# Function to open websites
def open_website(query):
    sites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "stackoverflow": "https://stackoverflow.com",
        "wikipedia": "https://www.wikipedia.org"
    }
    for site in sites:
        if site in query:
            speak(f"Opening {site}")
            webbrowser.open(sites[site])
            return
    speak("Website not found in my database.")

# Function to process hand landmarks
def process_hand_landmarks(landmarks, frame_width, frame_height):
    global prev_x, prev_y, curr_x, curr_y
    index_finger_tip = landmarks[8]
    thumb_tip = landmarks[4]
    middle_finger_tip = landmarks[12]
    ring_finger_tip = landmarks[16]

    index_x, index_y = int(index_finger_tip.x * frame_width), int(index_finger_tip.y * frame_height)
    thumb_x, thumb_y = int(thumb_tip.x * frame_width), int(thumb_tip.y * frame_height)
    middle_x, middle_y = int(middle_finger_tip.x * frame_width), int(middle_finger_tip.y * frame_height)
    ring_x, ring_y = int(ring_finger_tip.x * frame_width), int(ring_finger_tip.y * frame_height)

    screen_x = np.interp(index_x, [0, frame_width], [0, screen_width])
    screen_y = np.interp(index_y, [0, frame_height], [0, screen_height])
    curr_x = prev_x + (screen_x - prev_x) / 7
    curr_y = prev_y + (screen_y - prev_y) / 7
    pyautogui.moveTo(curr_x, curr_y)
    prev_x, prev_y = curr_x, curr_y

    # Click detection
    distance = math.hypot(index_x - thumb_x, index_y - thumb_y)
    if distance < click_threshold:
        pyautogui.click()
        time.sleep(0.2)
    
    # Right Click detection
    right_click_distance = math.hypot(middle_x - thumb_x, middle_y - thumb_y)
    if right_click_distance < click_threshold:
        pyautogui.rightClick()
        time.sleep(0.2)
    
    # Scroll detection
    scroll_distance = math.hypot(ring_x - thumb_x, ring_y - thumb_y)
    if scroll_distance < click_threshold:
        pyautogui.scroll(scroll_speed)
        time.sleep(0.2)

    # Dragging detection
    if distance < drag_threshold:
        pyautogui.mouseDown()
    else:
        pyautogui.mouseUp()

    # Double click detection
    if distance < click_threshold:
        pyautogui.doubleClick()
        time.sleep(0.3)
    
    # Screen brightness control
    brightness_level = np.interp(index_y, [0, frame_height], [100, 0])
    sbc.set_brightness(int(brightness_level))

# GUI for Gesture and Voice Assistant
class GestureVoiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gesture & Voice Assistant")
        self.tab_control = ttk.Notebook(root)
        self.tab_mouse = ttk.Frame(self.tab_control)
        self.tab_assistant = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_mouse, text="Gesture Control")
        self.tab_control.add(self.tab_assistant, text="Voice Assistant")
        self.tab_control.pack(expand=1, fill="both")
        
        self.start_button = tk.Button(self.tab_mouse, text="Start Gesture Control", command=self.start_gesture)
        self.start_button.pack(pady=10)
        
        self.stop_button = tk.Button(self.tab_mouse, text="Stop Gesture Control", command=self.stop_gesture)
        self.stop_button.pack(pady=10)
        
        self.mic_button = tk.Button(self.tab_assistant, text="Activate Assistant", command=self.start_assistant)
        self.mic_button.pack(pady=10)
        
        self.log = tk.Text(self.tab_assistant, height=15, width=50)
        self.log.pack(pady=10)
        
        self.running = False
        self.assistant_running = False

    def start_gesture(self):
        self.running = True
        Thread(target=self.run_gesture).start()

    def stop_gesture(self):
        self.running = False

    def run_gesture(self):
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            frame_height, frame_width, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb_frame)
            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    process_hand_landmarks(hand_landmarks.landmark, frame_width, frame_height)
            cv2.imshow("Virtual Mouse", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

    def start_assistant(self):
        if not self.assistant_running:
            self.assistant_running = True
            Thread(target=self.run_assistant).start()

    def run_assistant(self):
        while self.assistant_running:
            command = take_command()
            if command == "none":
                continue
            
            # Check commands
            if "open" in command:
                open_website(command)
            elif "wikipedia" in command:
                command = command.replace("wikipedia", "")
                results = wikipedia.summary(command, sentences=2)
                speak(results)
            elif "time" in command:
                speak(f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')}")
            elif "date" in command:
                speak(f"Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')}")
            else:
                speak("Sorry, I don't understand the command.")

if __name__ == "__main__":
    root = tk.Tk()
    app = GestureVoiceApp(root)
    root.mainloop()