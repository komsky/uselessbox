#we will play only wav files, so use pydub to play wav files
import pydub
from pydub import AudioSegment
from pydub.playback import play
import os
import platform
import sys
import random

core_path = os.path.dirname(os.path.abspath(__file__))

# Dictionary to map sound names to their file paths
sound_files = {
    "how_can_i_help": os.path.join(core_path, "audio/Effects/how_can_i_help_master.wav"),
    "knight_rider": os.path.join(core_path, "audio/Effects/knight_rider.wav"),
    "yes_master": os.path.join(core_path, "audio/Effects/yes_master.wav")
}
# Function to play a sound file
def play_sound(sound_file: str):
    """
    Play a sound file using the playsound library.    
    :param sound_file: Path to the sound file to be played.
    """
    # Check if the file exists
    if os.path.exists(sound_file):
        # Play the sound file
        try:
            # Load the sound file
            sound = AudioSegment.from_file(sound_file)
            print(f"Playing sound: {sound_file}")
            play(sound)
        except Exception as e:
            print(f"Error playing sound: {e}")
    else:
        print(f"Sound file '{sound_file}' not found.")
# Function to play a predefined sound based on the sound name
def play_predefined_sounds(sound_name: str):
    """
    Play a predefined sound based on the sound name.    
    :param sound_name: Name of the sound to be played.
    """
    # Check if the sound name exists in the dictionary
    if sound_name in sound_files:
        # Get the file path for the sound
        sound_file = sound_files[sound_name]
        # Play the sound file
        play_sound(sound_file)
    else:
        print(f"Sound '{sound_name}' not found.")

def play_random_greeting():
    """
    Play a random greeting sound.
    """
    # Read and list greeting sounds from /home/komsky/uselessbox/audio/Greetings/
    files = os.listdir(os.path.join(core_path, "audio/Greetings/"))
    # Filter for .wav files
    greetings = [f for f in files if f.endswith('.wav')]
    # Check if there are any greeting files
    if not greetings:
        print("No greeting sounds found.")
        return
    # Construct full paths for each greeting sound
    greetings = [os.path.join(os.path.join(core_path, "audio/Greetings/", f)) for f in greetings]

    # Play a random greeting sound
    play_sound(random.choice(greetings))
# Example usage     
if __name__ == "__main__":
    # Play a predefined sound
    play_predefined_sounds("yes_master")
    # Play a custom sound file
    play_sound(os.path.join(core_path, "audio/Soundboard/Arnold_Terminator/affirmative.wav"))
    play_random_greeting()