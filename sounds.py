from playsound import playsound
import os
import platform
import sys
import random

# Dictionary to map sound names to their file paths
sound_files = {
    "how_can_i_help": "/home/komsky/uselessbox/audio/Effects/how_can_i_help_master.wav",
    "knight_rider": "/home/komsky/uselessbox/audio/Effects/knight_rider.mp3",
    "yes_master": "/home/komsky/uselessbox/audio/Effects/yes_master.wav",
    "notification": "sounds/notification.mp3",
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
        playsound(sound_file)
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
    files = os.listdir("/home/komsky/uselessbox/audio/Greetings/")
    # Filter for .wav files
    greetings = [f for f in files if f.endswith('.wav')]
    # Check if there are any greeting files
    if not greetings:
        print("No greeting sounds found.")
        return
    # Construct full paths for each greeting sound
    greetings = [os.path.join("/home/komsky/uselessbox/audio/Greetings/", f) for f in greetings]

    # Play a random greeting sound
    play_sound(random.choice(greetings))
# Example usage     
if __name__ == "__main__":
    # Play a predefined sound
    play_predefined_sounds("yes_master")
    # Play a custom sound file
    play_sound("/home/komsky/uselessbox/audio/Soundboard/Arnold_Terminator/arnold_terminator.mp3")
    play_random_greeting()