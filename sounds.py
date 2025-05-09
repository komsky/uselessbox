import pydub
from pydub import AudioSegment
from pydub.playback import play
import os
import platform
import sys
import random
import time

core_path = os.path.dirname(os.path.abspath(__file__))

sound_files = {
    "how_can_i_help": os.path.join(core_path, "audio/Effects/how_can_i_help_master.wav"),
    "knight_rider": os.path.join(core_path, "audio/Effects/knight_rider.wav"),
    "yes_master": os.path.join(core_path, "audio/Effects/yes_master.wav")
}

def play_file(file:str):
    file_path = os.path.join(core_path, file)
    if os.path.exists(file_path):
        play_sound(file_path)
    else:
        print(f"Sound file '{file_path}' not found.")

def play_sound(sound_file: str):
    if os.path.exists(sound_file):
        try:
            sound = AudioSegment.from_file(sound_file)
            print(f"Playing sound: {sound_file}")
            play(sound)
            time.sleep(0.1)  # Small delay to ensure playback completes
        except Exception as e:
            print(f"Error playing sound: {e}")
    else:
        print(f"Sound file '{sound_file}' not found.")
        
def play_predefined_sounds(sound_name: str):
    if sound_name in sound_files:
        sound_file = sound_files[sound_name]
        play_sound(sound_file)
    else:
        print(f"Sound '{sound_name}' not found.")

def play_random_greeting():
    files = os.listdir(os.path.join(core_path, "audio/Greetings/"))
    greetings = [f for f in files if f.endswith('.wav')]
    if not greetings:
        print("No greeting sounds found.")
        return
    greetings = [os.path.join(os.path.join(core_path, "audio/Greetings/", f)) for f in greetings]
    play_sound(random.choice(greetings))
# Example usage     
if __name__ == "__main__":
    play_predefined_sounds("yes_master")
    play_sound(os.path.join(core_path, "audio/Soundboard/Arnold_Terminator/affirmative.wav"))
    play_random_greeting()
    play_file("audio/windows_startup.wav")