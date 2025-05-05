import os
import subprocess

def convert_mp3_to_wav(root_dir):
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith('.mp3'):
                mp3_path = os.path.join(dirpath, filename)
                wav_path = os.path.splitext(mp3_path)[0] + '.wav'

                # Convert using ffmpeg to 16-bit PCM WAV
                try:
                    subprocess.run(
                        ['ffmpeg', '-y', '-i', mp3_path, '-acodec', 'pcm_s16le', wav_path],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    os.remove(mp3_path)
                    print(f"Converted and removed: {mp3_path}")
                except subprocess.CalledProcessError:
                    print(f"Failed to convert: {mp3_path}")

if __name__ == "__main__":
    convert_mp3_to_wav("/home/komsky/UselessBox/uselessbox/audio/")
