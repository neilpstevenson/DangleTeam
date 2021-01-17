#!/usr/bin/python3

from vosk import Model, KaldiRecognizer
import pyaudio
import os
import sys
import time, datetime
import json

from interfaces.Config import Config
from interfaces.VoiceRecognitionSharedIPC import VoiceRecognitionSharedIPC

class VoiceRecognitionProcessor:

    def __init__(self):
        # Get config
        config = Config()
        #self.resolution = config.get("lava.vision.resolution", (320, 240))
        config.save()
        
        if not os.path.exists("model"):
            print ("Folder 'model/' not found.")
            exit (1)
        print("Loading model...")
        model = Model("model")
        self.recognizer = KaldiRecognizer(model, 16000)
        
        # Create/overwrite result share memory
        self.results = VoiceRecognitionSharedIPC()
        self.results.create()
       
    def run(self):
        print("Opening stream...")
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
        stream.start_stream()

        print("Ready")

        last_text = "x"
        while True:
            start_time = datetime.datetime.now()
            data = stream.read(4000, False)
            read_time = datetime.datetime.now()
            if len(data) == 0:
                break
            if self.recognizer.AcceptWaveform(data):
                result_json = self.recognizer.Result()
                result = json.loads(result_json)
                text = result['text']
                full_result = True
            else:
                result_json = self.recognizer.PartialResult()
                result = json.loads(result_json)
                text = result['partial']
                full_result = False
            print(result_json)
            stream_elapsed = read_time - start_time 
            anal_elapsed = datetime.datetime.now() - read_time 
            print (f"{start_time.strftime('%H:%M:%S.%f')} - {stream_elapsed} / {anal_elapsed} - {text}")

            if full_result or last_text != text:
                last_text = text

                # Update the shared IPC
                words = []
                if full_result and text != "":
                    for res in result['result']:
                        #print(f"result2d: {res['word']}")
                        words.append(
                            VoiceRecognitionSharedIPC.VoiceRecognitionResult(
                                status = 2,
                                word = res['word'],
                                confidence = res['conf'],
                                timestamp = res['start']))
                else:
                    textwords = text.split(" ")
                    for res in textwords:
                        #print(f"result1: {text}")
                        words.append(
                            VoiceRecognitionSharedIPC.VoiceRecognitionResult(
                                status = 1,
                                word = res,
                                confidence = 0.5,
                                timestamp = 0))
                                
                self.results.shareResults(words)

if __name__ == "__main__":
    vp = VoiceRecognitionProcessor()
    while True:
        try:
            vp.run()
        except OSError:
            print(f"Microphone error, retry in 5 seconds")
            time.sleep(5.0)
