#!/usr/bin/python3

from vosk import Model, KaldiRecognizer
import pyaudio
import os
import pygame
import textwrap
import pygame.freetype
import sys
import time
import json
import redboard

if not os.path.exists("model"):
    print ("Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
    exit (1)

print("Loading model...")
model = Model("model")
rec = KaldiRecognizer(model, 16000)

print("Opening stream...")
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()

print("Ready")

# Test window
pygame.init()
windowInfo = pygame.display.Info()
width = windowInfo.current_w
height = windowInfo.current_h
text_font = pygame.freetype.SysFont('Verdana', width/7)
screen = pygame.display.set_mode((width, height))#, pygame.FULLSCREEN)
clock = pygame.time.Clock()

pygame.display.set_caption('VOSK Voice Recognition Test')

# RedBoard motor control
rb = redboard.RedBoard()
def left():
    rb._set_motor_speed(0, 0.0)
    rb._set_motor_speed(1, 0.2)
    time.sleep(0.5)
    stop()
    
def right():
    rb._set_motor_speed(0, -0.2)
    rb._set_motor_speed(1, 0.0)
    time.sleep(0.5)
    stop()
    
def ahead():
    rb._set_motor_speed(0, -0.15)
    rb._set_motor_speed(1, 0.15)
    time.sleep(1.0)
    rb._set_motor_speed(0, -0.02)
    rb._set_motor_speed(1, 0.02)
    
def reverse():
    rb._set_motor_speed(0, 0.15)
    rb._set_motor_speed(1, -0.15)
    time.sleep(0.5)
    stop()
        
def stop():
    rb._set_motor_speed(0, 0.0)
    rb._set_motor_speed(1, 0.0)
    
def command(cmd):
    commands = { 
        'left': left,
        'right': right,
        'go': ahead,
        'reverse': reverse,
        'stop': stop,
        'top': stop
        }
    commands.get(cmd, lambda: None)()

last_text = "x"
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            stop()
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_q):
            # If pressed key is ESC or q, quit program
            stop()
            pygame.quit()
            sys.exit()

    data = stream.read(2000, False)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        result_json = rec.Result()
        colour = (0,96,0)
        text = json.loads(result_json)['text']
    else:
        result_json = rec.PartialResult()
        colour = (0,0,0)
        text = json.loads(result_json)['partial']
    print(result_json)

    if last_text != text:
        last_text = text
        # Display the command
        screen.fill((255, 255, 255))
        text_wrapped = textwrap.wrap(text, 14)
        
        pos = (0,height/15)
        for t in text_wrapped:
            text_rendered,rect = text_font.render(t, fgcolor=colour)
            screen.blit(text_rendered, (width//2 - (rect[2]-rect[0])//2, pos[1]))
            pos = (pos[0],pos[1] + rect[1] * 7 // 5)
            
        pygame.display.flip()

        # Adjust the motors
        command(text)

print(rec.FinalResult())
