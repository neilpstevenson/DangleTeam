#!/usr/bin/python3

import pygame
import textwrap
import pygame.freetype
import sys
 
pygame.init()
windowInfo = pygame.display.Info()
width = windowInfo.current_w
height = windowInfo.current_h
screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
clock = pygame.time.Clock()
 
text_font = pygame.freetype.SysFont('Verdana', width/7)
text_wrapped = textwrap.wrap("Hey there, Beautfiul weather today!", 14)
count = 0
while True:
    count += 1
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_q):
            # If pressed key is ESC or q, quit program
            pygame.quit()
            sys.exit()
     
    screen.fill((255, 255, 255))
    
    pos = (0,height/15)
    for t in text_wrapped:
        text_rendered,rect = text_font.render(t, fgcolor=(0,0,0))
        pygame.draw.rect(text_rendered, (128,128,128), (0,0,rect[0],rect[1]))
        print(f"{rect}")
        screen.blit(text_rendered, (width//2 - (rect[2]-rect[0])//2, pos[1]))
        pos = (pos[0],pos[1] + rect[1] * 7 // 5)
        
    pygame.display.flip()
    clock.tick(20)
    
