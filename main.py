import os
import sys
import logging
import argparse
from datetime import datetime
from halo import Halo
from dotenv import load_dotenv
import openai
from voice_activity_detection import VADAudio
from chat_gpt_client import ChatGptClient
# from fancy_module import FancyInstructions
# import pvporcupine
import numpy as np
# from wled_proxy import WledProxy
# from speak_module import SpeakModule
# import asyncio
# from langdetect import detect
# libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'oled')
# if os.path.exists(libdir):
#     sys.path.append(libdir)
# from oled.oled_module import OLED_Display

class MainApplication:
    def __init__(self, args, vad_audio, chat_gpt_client, end_command="exit"):
        self.configure_logging()
        self.args = args
        self.vad_audio = vad_audio
        # self.fancy = fancy
        self.chat_gpt_client = chat_gpt_client
        self.spinner = Halo(spinner='line') if not self.args.nospinner else None
        self.listening_for_command = False
        self.current_folder = os.getcwd()
        self.keyword_file_path = os.path.join(self.current_folder, "arnold.ppn")
        # self.porcupine = pvporcupine.create(access_key=os.getenv("PORCUPINE"), keyword_paths=[self.keyword_file_path])
        # self.speak_module = SpeakModule(os.getenv("AZURE_KEY"), os.getenv("AZURE_REGION"))
        # self.wled = wled
        self.end_command = end_command
        # self.oled = OLED_Display()
        logging.debug("MainApplication initialized")

    def configure_logging(self):
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        logging.debug("Logging configured")

    # async def wait_for_wakeword(self):
    #     self.oled.write_smart_split("Waiting for wake word...")
    #     await self.wled.stop()
    #     frames = self.vad_audio.vad_collector()
    #     wav_data = bytearray()
    #     for frame in frames:
    #         if frame is not None:
    #             if self.spinner:
    #                 self.spinner.start()
    #                 await self.wled.pulse() 
    #             wav_data.extend(frame)
    #         else:
    #             if self.spinner:
    #                 self.spinner.stop()
    #             self.oled.write_smart_split("speech ended, looking for keyword")

    #             audio_data_np = np.frombuffer(wav_data, dtype=np.int16)
    #             for i in range(0, len(audio_data_np), self.porcupine.frame_length):
    #                 frame = audio_data_np[i:i+self.porcupine.frame_length]
    #                 if len(frame) == self.porcupine.frame_length:
    #                     keyword_index = self.porcupine.process(frame)
    #                     if keyword_index >= 0:
    #                         self.oled.write_smart_split("keyword detected")
    #                         return
    #             wav_data = bytearray()

    def listen_for_command(self):
        # self.oled.write_smart_split("Listening for command...")
        logging.debug("Listening for command...")
        # await self.wled.listening()
        wav_data = bytearray()
        vad = VADAudio(aggressiveness=self.args.vad_aggressiveness, device=self.args.device, input_rate=self.args.rate, file=self.args.file)
        frames = vad.vad_collector()
        for frame in frames:
            if frame is not None:
                if self.spinner:
                    self.spinner.start()
                    # await self.wled.pulse() 
                wav_data.extend(frame)
            else:
                if self.spinner:
                    self.spinner.stop()
                break

        # await self.wled.kit()
        date_piece = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f.wav")
        saved_file = os.path.join(self.args.savewav, f'savewav_{date_piece}')
        self.vad_audio.write_wav(saved_file, wav_data)
        with open(saved_file, "rb") as audio_file:
            api_response = openai.Audio.transcribe("whisper-1", audio_file )
            recognized_text = api_response.text.lower()
            print(f"You said: {recognized_text}")            
            
            if self.end_command in recognized_text:
                return False
            
            # language = detect(recognized_text)
            # if not (language == 'pl' or language == 'en' or language == 'hi'):
            #     # self.oled.write_smart_split("Not polish?")
            #     print("Detected unusual language, not responding")
            #     return True

            elif not api_response.text.strip() == "":
                # self.oled.write_smart_split("Thinking...")
                arnold_says = self.chat_gpt_client.call_chatgpt_with_history(api_response.text)
                print(f"ChatGPT: {arnold_says}")
                # self.oled.write_smart_split("Speaking...")
                # await self.wled.speaking()
                # self.speak_module.speak(arnold_says, language)
        if os.path.exists(saved_file):
            os.remove(saved_file)
        # await self.wled.stop()
        return True
    
    def run(self):
        self.listen_for_command()
                    

if __name__ == '__main__':
    load_dotenv()
    current_folder = os.getcwd()
    parser = argparse.ArgumentParser(description="Stream from microphone using VAD and OpenAI Whisper API")
    parser.add_argument('-v', '--vad_aggressiveness', type=int, default=2, help="Set aggressiveness of VAD: an integer between 0 and 3, 0 being the least aggressive about filtering out non-speech, 3 the most aggressive.")
    parser.add_argument('--nospinner', action='store_true', help="Disable spinner")
    parser.add_argument('-w', '--savewav', default=os.path.join(os.getcwd(),'audio/saved/'), help="Save .wav files of utterances to given directory")
    parser.add_argument('-f', '--file', help="Read from .wav file instead of microphone")
    parser.add_argument('-d', '--device', type=int, default=None, help="Device input index (Int) as listed by pyaudio.PyAudio.get_device_info_by_index(). If not provided, falls back to PyAudio.get_default_device().")
    parser.add_argument('-r', '--rate', type=int, default=16000, help="Input device sample rate. Default: 16000. Your device may require 44100.")
    args = parser.parse_args()
    if args.savewav:
        os.makedirs(args.savewav, exist_ok=True)

    vad_audio = VADAudio(aggressiveness=args.vad_aggressiveness, device=args.device, input_rate=args.rate, file=args.file)
    # wled = WledProxy()

    knight_rider_audio = os.path.join(current_folder, 'Audio/Effects/knight_rider.mp3')
    yes_master_audio = os.path.join(current_folder, 'Audio/Effects/yes_master.wav')

    # fancy = FancyInstructions(wled, knight_rider_audio, yes_master_audio)
    chat_gpt_client = ChatGptClient(api_key=os.getenv("CHATGPT_API_KEY"), model_type=os.getenv("GPT_MODEL_TYPE"), chat_history_filename="chatHistory.json")
    
    api_key = os.getenv("CHATGPT_API_KEY")
    openai.api_key = api_key
    end_command = "exit"
    app = MainApplication(args, vad_audio, chat_gpt_client, end_command)
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(app.run())
    
