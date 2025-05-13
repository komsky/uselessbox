import os
import sys
import logging
import argparse
from datetime import datetime
from halo import Halo
from dotenv import load_dotenv
import openai
from openai import OpenAI
from voice_activity_detection import VADAudio
from chat_gpt_client import ChatGPTClient
import sounds
# from fancy_module import FancyInstructions
import pvporcupine
import numpy as np
# from wled_proxy import WledProxy
import SpeakModule
import asyncio
# from langdetect import detect
# libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'oled')
# if os.path.exists(libdir):
#     sys.path.append(libdir)
# from oled.oled_module import OLED_Display
import shutil
import time
from HandServo import HandServo
from TopServo import TopServo
import requests
import wsled
import random

EVENTS_URL = "http://127.0.0.1:5000/events"

class MainApplication:
    def __init__(self, args):
        self.configure_logging()
        
        logging.debug("Logging configured.Starting Main Application")
        self.args = args
        self.vad_audio = VADAudio(aggressiveness=args.vad_aggressiveness, device=args.device, input_rate=args.rate, file=args.file)
        # self.fancy = fancy
        self.chat_gpt_client =  ChatGPTClient(api_key=os.getenv("CHATGPT_API_KEY"), model=os.getenv("GPT_MODEL_TYPE"), history_file="chatHistory.json")
        self.spinner = Halo(spinner='line') if not self.args.nospinner else None
        self.listening_for_command = False
        self.current_folder = os.getcwd()
        self.keyword_file_path = os.path.join(self.current_folder, "hey-octo_en_raspberry-pi_v3_0_0.ppn")
        self.porcupine = pvporcupine.create(access_key=os.getenv("PORCUPINE"), keyword_paths=[self.keyword_file_path])
        # self.speak_module = SpeakModule(os.getenv("AZURE_KEY"), os.getenv("AZURE_REGION"))
        # self.wled = wled
        self.handServo = HandServo()
        self.topServo = TopServo()
        # self.oled = OLED_Display()
        self.openAiClient = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        self.resetChatHistory()
        logging.debug("MainApplication initialized")

    def resetChatHistory(self, sourceFile="chatHistory.starter.json", destinationFile="chatHistory.json"):
        logging.debug("Resetting chat history")
        if not os.path.exists(sourceFile):
            logging.debug(f"Error: Starter chat history '{sourceFile}' does not exist.")
            sys.exit(1)
        try:
            shutil.copyfile(sourceFile, destinationFile)
            logging.debug(f"Successfully overwritten '{destinationFile}' with '{sourceFile}'")
        except FileNotFoundError:
            logging.debug(f"Error: Source file '{sourceFile}' not found.")
            sys.exit(1)
        except PermissionError:
            logging.debug(f"Error: Permission denied when writing to '{destinationFile}'.")
            sys.exit(1)
        except Exception as e:
            logging.debug(f"An unexpected error occurred: {e}")
            sys.exit(1)

    def configure_logging(self):
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        logging.debug("Logging configured")

    async def wait_for_wakeword(self):
        print("Waiting for wake word...")
        frames = self.vad_audio.vad_collector()
        
        for frame in frames:
            if frame is None:
                if self.spinner:
                    self.spinner.stop()
                continue

            if self.spinner:
                self.spinner.start()

            # Convert stereo frame to mono (int16) for Porcupine
            stereo_samples = np.frombuffer(frame, dtype=np.int16).reshape(-1, 2)
            mono_samples = np.clip(stereo_samples.sum(axis=1), -32768, 32767).astype(np.int16)

            # Split mono_samples into chunks for Porcupine processing
            for i in range(0, len(mono_samples), self.porcupine.frame_length):
                subframe = mono_samples[i:i + self.porcupine.frame_length]
                if len(subframe) != self.porcupine.frame_length:
                    continue  # skip incomplete frame

                keyword_index = self.porcupine.process(subframe)
                if keyword_index >= 0:
                    if self.spinner:
                        self.spinner.stop()
                    print("Wakeword detected!")
                    return



    def listen_for_command(self):
        # self.oled.write_smart_split("Listening for command...")
        logging.debug("Listening for command...")
        # await self.wled.listening()
        wav_data = bytearray()
        vad = VADAudio(aggressiveness=self.args.vad_aggressiveness, device=self.args.device, input_rate=self.args.rate, file=self.args.file)
        #debug
        data = vad.read()               # or read_resampled()
        arr  = np.frombuffer(data, np.int16)
        print("raw int16 samples:", arr[:20])
        #debug
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
        vad.write_wav(saved_file, wav_data)
        with open(saved_file, "rb") as audio_file:
            api_response = self.openAiClient.audio.transcriptions.create(
                file=audio_file,       # your audio file handle
                model="whisper-1",     # the Whisper model
                language='pl',         # auto-detect if you omit this
                temperature=0,         # deterministic output
                response_format="text" # you?ll get resp.text back
            )

            recognized_text = api_response;
            print(f"You said: {recognized_text}")            
            
            if self.end_command in recognized_text:
                return False
            
            # language = detect(recognized_text)
            # if not (language == 'pl' or language == 'en' or language == 'hi'):
            #     # self.oled.write_smart_split("Not polish?")
            #     print("Detected unusual language, not responding")
            #     return True

            elif not api_response.strip() == "":
                # self.oled.write_smart_split("Thinking...")
                arnold_says = self.chat_gpt_client.call_chatgpt_with_history(api_response)
                # print(f"ChatGPT: {arnold_says}")
                # self.oled.write_smart_split("Speaking...")
                # await self.wled.speaking()
                # self.speak_module.speak(arnold_says, language)
        if os.path.exists(saved_file):
            os.remove(saved_file)
        # await self.wled.stop()
        return True
    
    def subscribe_toggle(self):
        while True:
            try:
                print("Connecting to events endpoint at", EVENTS_URL)
                with requests.get(EVENTS_URL, stream=True) as r:
                    for line in r.iter_lines(decode_unicode=True):
                        if line and line.startswith("data:"):
                            data = line.replace("data:", "").strip()
                            print("Received event:", data)

                            if data == "ON":
                                self.RandomAction()


            except Exception as e:
                print("Error while subscribing to toggle events:", e)
                time.sleep(5) 
    def RandomAction(self):
        random_number = random.randint(1, 4)
        if random_number == 1:
            self.Achmed()
        elif random_number == 2:
            self.WindowsXP()
        elif random_number == 3:
            self.Terminator()
        elif random_number == 4:
            self.Neostrada()

    def Achmed(self):
        wsled.on()        
        self.topServo.up()   
        sounds.play_file("audio/ahmed/ahmed_silence_I_kill_you.wav")
        self.handServo.turnOffToggleAndBack()  
        wsled.off()
        self.handServo.zero()
        time.sleep(0.5)
        self.topServo.zero()        
        time.sleep(1)
        self.topServo.up()   
        sounds.play_file("audio/ahmed/achmed-stop_touching_me_i_kill_you.wav")
        self.handServo.wiggleHand()
        self.topServo.zero()    
        
    def WindowsXP(self):
        wsled.on()
        self.topServo.up()   
        sounds.play_file("audio/windows_startup.wav")
        self.handServo.turnOffToggleAndBack()  
        wsled.off()
        self.handServo.zero()
        sounds.play_file("audio/windows_shutdown.wav")
        self.topServo.zero()        
        time.sleep(1)
        self.topServo.up()   
        self.handServo.wiggleHand()
        time.sleep(2)
        self.topServo.zero() 

    def Terminator(self):
        wsled.on()
        sounds.play_file("audio/Soundboard/Arnold_Terminator/im_a_cybernetic_organism_living_tissue_over_metal_endoskeleton.wav")
        self.topServo.up()   
        sounds.play_file("audio/Soundboard/Arnold_Terminator/hasta_la_vista_baby.wav")
        self.handServo.turnOffToggleAndBack()  
        wsled.off()
        sounds.play_file("audio/Soundboard/Arnold_Terminator/humans-inevitably-die.wav")
        self.topServo.zero()        
        time.sleep(1)
        self.topServo.up()   
        sounds.play_file("audio/Soundboard/Arnold_Terminator/talk_to_the_hand.wav")
        self.handServo.wiggleHand()        
        self.handServo.wiggleHand()        
        self.handServo.wiggleHand()        
        self.topServo.zero() 

    def Neostrada(self):
        wsled.on()
        self.topServo.up()           
        sounds.play_file("audio/long/neostrada_serce_i_rozum.wav")
        self.handServo.turnOffToggleAndBack()  
        wsled.off()
        self.topServo.zero()        
        time.sleep(1)
        self.topServo.up()   
        self.handServo.wiggleHand()        
        self.handServo.wiggleHand()        
        self.handServo.wiggleHand()        
        self.topServo.zero() 

    def run(self):
        # self.subscribe_toggle()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.wait_for_wakeword())
        
                    

if __name__ == '__main__':
    load_dotenv()
    current_folder = os.getcwd()
    parser = argparse.ArgumentParser(description="Stream from microphone using VAD and OpenAI Whisper API")
    parser.add_argument('-v', '--vad_aggressiveness', type=int, default=3, help="Set aggressiveness of VAD: an integer between 0 and 3, 0 being the least aggressive about filtering out non-speech, 3 the most aggressive.")
    parser.add_argument('--nospinner', action='store_true', help="Disable spinner")
    parser.add_argument('-w', '--savewav', default=os.path.join(os.getcwd(),'audio/saved/'), help="Save .wav files of utterances to given directory")
    parser.add_argument('-f', '--file', help="Read from .wav file instead of microphone")
    parser.add_argument('-d', '--device', type=int, default=1, help="Device input index (Int) as listed by pyaudio.PyAudio.get_device_info_by_index(). If not provided, falls back to PyAudio.get_default_device().")
    parser.add_argument('-r', '--rate', type=int, default=16000, help="Input device sample rate. Default: 16000. Your device may require 44100.")
    args = parser.parse_args()
    if args.savewav:
        os.makedirs(args.savewav, exist_ok=True)

    app = MainApplication(args)
    app.run()
    
  
    
