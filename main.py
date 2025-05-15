import os
import sys
import logging
import argparse
from datetime import datetime
from halo import Halo
from dotenv import load_dotenv
import openai
from openai import OpenAI
from cobravoice import CobraDetector
from chat_gpt_client import OpenAIClient
import sounds
from wakeword import WakeWordDetector
import numpy as np
import speak
import asyncio
import shutil
import time
from hand import HandServo
from top import TopServo
import requests
import wsled
import random
import wave
from datetime import datetime


EVENTS_URL = "http://127.0.0.1:5000/events"

class MainApplication:
    def __init__(self, args):
        self.configure_logging()
        
        logging.debug("Logging configured.Starting Main Application")
        self.args = args
        self.detector = CobraDetector(access_key=os.getenv("PICOVOICE"))
        self.ai_client =  OpenAIClient(api_key=os.getenv("CHATGPT_API_KEY"), model=os.getenv("GPT_MODEL_TYPE"), history_file="chatHistory.json")
        self.spinner = Halo(spinner='line') if not self.args.nospinner else None
        self.listening_for_command = False
        self.current_folder = os.getcwd()
        self.keyword_file_path = os.path.join(self.current_folder, "hey-octo_en_raspberry-pi_v3_0_0.ppn")
        self.wakeword = WakeWordDetector(access_key=os.getenv("PICOVOICE"),keyword_paths="hey-octo_en_raspberry-pi_v3_0_0.ppn")
        self.handServo = HandServo()
        self.topServo = TopServo()
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
        root = logging.getLogger()              # the root logger
        root.setLevel(logging.DEBUG)            # capture DEBUG and above

        sh = logging.StreamHandler(sys.stdout)  # send logs to stdout
        sh.setLevel(logging.DEBUG)              # only DEBUG+ on this handler
        fmt = logging.Formatter(
            '%(asctime)s %(levelname)-8s %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        sh.setFormatter(fmt)

        root.addHandler(sh)
        logging.debug("Logging configured")


    async def listen_for_command(self):
        logging.debug("Waiting for wakeword...")   
        await self.wakeword.wait_for_wakeword()
        logging.debug("Wakeword detected, starting command processing")
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        wav_path = os.path.join(self.args.savewav, f"utt_{ts}.wav")
        try:
            print("Speak now...")
            wsled.listening()
            print(f"Waiting for utterance (threshold={args.threshold}, silence={args.silence_timeout}s)")
            pcm = await self.detector.wait_for_utterance(args.threshold, args.silence_timeout)

            self.detector.save_wav(pcm, wav_path)
            print(f"Saved utterance to {wav_path}")
            wsled.thinking()
            #use whisper for stt and then ask chatgpt for response
            stt = self.ai_client.transcribe_audio(wav_path)
            print(f"Transcribed text: {stt}")
            #use chatgpt for response
            response = self.ai_client.call_chatgpt(stt)
            print(f"ChatGPT response: {response}")
            #use tts for response
            await speak.speak_male(response)
            # await self.wled.stop()
            return True
        finally:
            wsled.off()
            if os.path.exists(wav_path):
                os.remove(wav_path)
            self.listening_for_command = False
            print("Listening stopped.")
    
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
        # # self.subscribe_toggle()
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(self.listen_for_command())     
        asyncio.run(self.listen_for_command())

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
    
  
    
