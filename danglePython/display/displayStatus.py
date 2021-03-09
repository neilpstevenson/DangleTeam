#!/usr/bin/python3
import pygame
import textwrap
import pygame.freetype
import sys
import time
from interfaces.Config import Config
from interfaces.StatusSharedIPC import StatusSharedIPC

class DisplayStatus:

    def __init__(self):
        pygame.display.init()
        pygame.freetype.init()
        
        # Read result shared memory
        self.results = StatusSharedIPC()
        self.results.read()
        
        windowInfo = pygame.display.Info()
        self.width = min(1024,windowInfo.current_w)
        self.height = min(800,windowInfo.current_h)
        self.title_font = pygame.freetype.SysFont('Verdana', self.width/5)
        self.subTitle_font = pygame.freetype.SysFont('Verdana', self.width/8)
        self.additional_font = pygame.freetype.SysFont('Verdana', self.width/16)
        self.clock = pygame.time.Clock()
       
    def run(self):
         # Setup window
        screen = pygame.display.set_mode((self.width, self.height))#, pygame.FULLSCREEN)
        clock = pygame.time.Clock()

        pygame.display.set_caption('Status')

        last_title = "x"
        last_subtitle = ""
        last_additional = ""
        while last_title != "quit quit quit" :
            for event in pygame.event.get():
                if event.type == pygame.QUIT or \
                    (event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_q)):
                    # If pressed key is ESC or q, quit program
                    #pygame.quit()
                    sys.exit()

            # Get the next text
            title = "Long Title"#self.results.getTitle()
            subtitle = "This is a subtitle" #self.results.getSubtitle()
            additional = "This is a long line with lots of data that might not fit very well" #self.results.getAdditional()
            
            if last_title != title or last_subtitle != subtitle or last_additional != additional:
                last_title = title
                last_subtitle = subtitle
                last_additional = additional
                
                # Display the status
                screen.fill((255, 255, 255))
                
                pos = (0, self.height/20)
                # Large title at top
                text_rendered,rect = self.title_font.render(title, fgcolor=(0,0,0))
                screen.blit(text_rendered, (self.width//2 - (rect[2]-rect[0])//2, pos[1]))
                pos = (pos[0],pos[1] + rect[1] * 7 // 5)
                # Medium subtitle
                text_rendered,rect = self.subTitle_font.render(subtitle, fgcolor=(0,96,0))
                screen.blit(text_rendered, (self.width//2 - (rect[2]-rect[0])//2, pos[1]))
                pos = (pos[0],pos[1] + rect[1] * 7 // 5)
                # Small wrapped additional data
                text_wrapped = textwrap.wrap(additional, 24)
                for t in text_wrapped:
                    text_rendered,rect = self.additional_font.render(t, fgcolor=(128,128,128))
                    screen.blit(text_rendered, (self.width//2 - (rect[2]-rect[0])//2, pos[1]))
                    pos = (pos[0],pos[1] + rect[1] * 7 // 5)
                    
                pygame.display.flip()

            # limit update rate
            self.clock.tick(20) #frames/sec
