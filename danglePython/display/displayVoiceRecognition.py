#!/usr/bin/python3
import pygame
import textwrap
import pygame.freetype
import sys
import time
from interfaces.Config import Config
from interfaces.VoiceRecognitionSharedIPC import VoiceRecognitionSharedIPC

class DisplayVoiceRecognition:

    def __init__(self):
        pygame.display.init()
        pygame.freetype.init()
        
        # Read result shared memory
        self.results = VoiceRecognitionSharedIPC()
        self.results.read()
        #self.results.clearCurrentResults()
        
        windowInfo = pygame.display.Info()
        self.width = min(1024,windowInfo.current_w)
        self.height = min(800,windowInfo.current_h)
        self.text_font = pygame.freetype.SysFont('Verdana', self.width/7)
        self.clock = pygame.time.Clock()
       
    def run(self):
         # Setup window
        screen = pygame.display.set_mode((self.width, self.height))#, pygame.FULLSCREEN)
        clock = pygame.time.Clock()

        pygame.display.set_caption('Voice Recognition Results')

        last_text = "x"
        last_status = -1
        while last_text != "quit quit quit" :
            for event in pygame.event.get():
                if event.type == pygame.QUIT or \
                    (event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_q)):
                    # If pressed key is ESC or q, quit program
                    #pygame.quit()
                    sys.exit()

            # Get the next word
            status, words = self.results.getLastWords()
            # Create as a single string
            sentence = " ".join(words)
            final = (status == 2)
            #print(f"({final} {status}) {sentence}")
            if last_text != sentence or last_status != status:
                last_text = sentence
                last_status = status
                
                if final:
                    colour = (0,96,0)
                else:
                    colour = (0,0,0)

                # Display the sentence
                screen.fill((255, 255, 255))
                text_wrapped = textwrap.wrap(sentence, 14)
                
                pos = (0, self.height/15)
                for t in text_wrapped:
                    text_rendered,rect = self.text_font.render(t, fgcolor=colour)
                    screen.blit(text_rendered, (self.width//2 - (rect[2]-rect[0])//2, pos[1]))
                    pos = (pos[0],pos[1] + rect[1] * 7 // 5)
                    
                pygame.display.flip()

            # limit update rate
            self.clock.tick(20) #frames/sec
