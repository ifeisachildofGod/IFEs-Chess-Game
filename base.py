
import math
import pygame

MAX_BIT = 0x10000000000000000

def print_bitboard(*bits: int, sep=" ", end="\n"):
    reps = [(64 - len(b)) * "0" + b for bit in bits if (b := bin(bit).removeprefix("0b"))]
    
    for rep in reps:
        assert len(rep) <= 64
    
    text = ""
    sub_texts = ["" for _ in bits]
    
    for i in range(64):
        sub_texts = [sub_text + reps[_i][i] for _i, sub_text in enumerate(sub_texts)]
        
        if not (i + 1) % 8:
            text += sep.join(sub_texts) + ("\n" if i != 63 else end)
            sub_texts = ["" for _ in bits]
    
    print(text)

def bit_shift_left(bit: int, by: int):
    return (bit >> abs(by)) if by < 0 else (bit << by)

def bit_shift_right(bit: int, by: int):
    return (bit << abs(by)) if by < 0 else (bit >> by)

def bit_byte_to_bits(pos: bytes, value: int | None = None):
    return bit_shift_left(value or 1, (7 - pos[0]) + (7 - pos[1]) * 8)

def bits_to_bit_byte(bits: int):
    return bytes([7 - (int(math.log2(bits)) % 8), 7 - (int(math.log2(bits)) // 8)])

def remove_bits(bits: int, remove: int, length: int):
    return bits & (((1 << length) - 1) ^ remove)


class Base(pygame.Surface):
    def __init__(self, size, parent: "pygame.Surface | Base", pos_kwargs: dict[str, tuple[float | int, float | int] | int | float], flags = 0):
        super().__init__(size, flags)
        
        self.parent = parent
        self.rect = self.get_rect(**pos_kwargs)
    
    def event_handler(self, event: pygame.event.Event):
        pass
    
    def update(self):
        pass
    
    def draw(self):
        self.parent.blit(self, self.rect)
    
    def run(self):
        self.update()
        self.draw()

