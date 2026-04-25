
import pygame

MAX_BIT = 0x10000000000000000

def print_bitboard(bits: int):
    rep = bin(bits).removeprefix("0b")
    
    assert len(rep) <= 64
    
    sub_text = ""
    text = ""
    
    for i, c in enumerate((64 - len(rep)) * "0" + rep):
        if not (i + 1) % 8:
            text += sub_text + c + "\n"
            sub_text = ""
        else:
            sub_text += c
    
    print(text)
    print()

def bit_shift_left(bit: int, by: int):
    return (bit >> abs(by)) if by < 0 else (bit << by)

def bit_shift_right(bit: int, by: int):
    return (bit << abs(by)) if by < 0 else (bit >> by)

def bit_byte_to_bits(pos: bytes, value: int | None = None):
    return bit_shift_left(value or 1, (7 - pos[0]) + (7 - pos[1]) * 8)

def remove_bits(bits: int, remove: int, length: int):
    return bits & (((1 << length) - 1) ^ remove)


class Base(pygame.Surface):
    def __init__(self, size, parent: pygame.Surface, pos_kwargs: dict[str, tuple[float | int, float | int] | int | float], flags = 0):
        super().__init__(size, flags)
        
        self.parent = parent
        self.rect = self.get_rect(**pos_kwargs)
    
    def update(self):
        pass
    
    def draw(self):
        self.parent.blit(self, self.rect)
    
    def run(self):
        self.update()
        self.draw()

