
import pygame
from sys import exit
from boards_and_pieces import *

pygame.init()
pygame.display.set_caption("IFEs Chess Game")
screen = pygame.display.set_mode((1000, 600))
clock = pygame.time.Clock()


class_text_map = {
    Rook: "r",
    Bishop: "b",
    Knight: "n",
    Queen: "q",
    King: "k",
    Pawn: "p",
    type(None): "x"
}
text_class_map = {v: k for k, v in class_text_map.items()}


def from_string_to_board(string: str, board_style: str, piece_style: str, O: bool = False):
    board = Board(screen)
    
    index = 0
    
    white_pieces: dict[bytes, Piece] = {}
    black_pieces: dict[bytes, Piece] = {}
    
    white_king = None
    black_king = None
    
    amount = 1
    
    for i, c in enumerate(string):
        if c.isalpha():
            amount = 1
            
            new_amount = ""
            
            for _c in string[i + 1:]:
                if not _c.isnumeric():
                    break
                
                new_amount += _c
            
            if new_amount:
                amount = int(new_amount)
            
            is_white = not c.islower()
            
            for i in range(amount):
                pos = bytes([index % 8 + i, index // 8])
                
                pieces = white_pieces if is_white else black_pieces
                
                cls = text_class_map[c.lower()]
                
                if cls != type(None):
                    pieces[pos] = cls(board, is_white, pos, piece_style, O)
                    
                    if isinstance(pieces[pos], King):
                        if is_white:
                            white_king = pieces[pos]
                        else:
                            black_king = pieces[pos]
            
            index += amount
    
    board.set_board_style(board_style)
    board.set_data(white_pieces, black_pieces, white_king, black_king)
    
    return board

def from_board_to_string(board: Board):
    string = ""
    
    pieces = board.white_pieces.copy()
    pieces.update(board.black_pieces)
    
    prev = ""
    amount = -1
    
    temp = ""
    prev_temp = ""
    
    pieces_str = ""
    
    for i in range((8 * 8) + 1):
        x = i % 8
        y = i // 8
        
        amount += 1
        piece = pieces.get(bytes([x, y]))
        
        c = class_text_map[piece.__class__]
        
        if prev and prev != c:
            temp = pieces_str[-1] + (str(amount) if amount != 1 else "")
            
            string += temp if not prev_temp or (len(temp) == 1 and len(prev_temp) == 1) else " " + temp
            
            prev_temp = temp
            
            amount = 0
        
        prev = c
        pieces_str += c.upper() if piece and piece.is_white else c
    
    index = None
    
    for i, c in enumerate(reversed(list(string))):
        if c and not c.isnumeric():
            if c != "x":
                break
            else:
                index = len(string) - i - 1
    
    if index:
        string = string[:index]
    
    return string

board_params = "rnbqkbnr p8 x32 P8 RNBQKBNR", "Brown", "Default", True

board = from_string_to_board(*board_params)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        
        board.event_handler(event)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and board.WHITE_WINS + board.BLACK_WINS + board.DRAW:
                board = from_string_to_board(*board_params)
    
    board.run()
    
    pygame.display.update()
    screen.fill((0, 0, 0))
    clock.tick(60)