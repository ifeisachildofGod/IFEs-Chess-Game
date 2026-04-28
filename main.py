
import pygame
from sys import exit
from boards_and_pieces import Board

pygame.init()
pygame.display.set_caption("IFEs Chess Game")
screen = pygame.display.set_mode((1000, 600))
clock = pygame.time.Clock()


board = Board(screen, "rnbqkbnr p8 x32 P8 RNBQKBNR")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        
        board.event_handler(event)
    
    board.run()
    
    pygame.display.update()
    screen.fill((0, 0, 0))
    clock.tick(60)