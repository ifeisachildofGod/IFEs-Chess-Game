
from typing import Callable

import pygame
from base import Base


class PromoteEdit(Base):
    def __init__(
        self,
        parent: Base,
        block_size: tuple[float, float],
        on_selected: Callable[[type], None],
        is_white: bool,
        board_style: str,
        piece_style: str,
        O: bool,
        text_class_map: dict[str, type],
        rect_kwargs,
        destroyed: Callable[["PromoteEdit"], None] | None = None
    ):
        self.border_width = 3
        
        super().__init__((block_size[0] + self.border_width * 2, block_size[1] * 4 + self.border_width * 2), parent, rect_kwargs, pygame.SRCALPHA)
        
        self.board_style = board_style
        self.on_selected = on_selected
        self.text_class_map = text_class_map
        
        self._destroyed = destroyed
        
        self.option: list[pygame.Rect] = []
        
        self.piece_text_types = list(self.text_class_map)
        
        for i, piece_type in enumerate(self.piece_text_types):
            p_option = pygame.Surface(block_size, pygame.SRCALPHA)
            p_option_rect = p_option.get_rect(topleft=(self.border_width, self.border_width + i * block_size[1]))
            
            skin = pygame.image.load(f"assets/pieces and boards/{"White" if is_white else "Black"} {piece_style}/{piece_type}{" O" if O else ""}.png")
            skin = pygame.transform.scale_by(
                skin,
                max(
                    (p_option.get_width() * 0.85) / skin.get_width(),
                    (p_option.get_height() * 0.85) / skin.get_height()
                )
            )
            
            p_option.blit(skin, skin.get_rect(center=(block_size[0] / 2, block_size[1] / 2)))
            
            self.option.append((p_option, p_option_rect))
        
        self.hover_surf = pygame.Surface(block_size)
        self.hover_surf.fill("grey")
        self.hover_surf.set_alpha(150)
        self.hover_rect = self.hover_surf.get_rect()
        
        self.focus_piece_type = None
    
    def event_handler(self, event):
        if event.type == pygame.MOUSEMOTION:
            m_pos = event.pos[0] - self.rect.left - self.parent.rect.left, event.pos[1] - self.rect.top - self.parent.rect.top
            
            for i, (_, rect) in enumerate(self.option):
                if rect.collidepoint(m_pos):
                    self.focus_piece_type = self.piece_text_types[i]
                    
                    self.hover_rect.topleft = self.border_width, self.border_width + i * rect.height
                    
                    break
            else:
                self.focus_piece_type = None
        elif event.type == pygame.MOUSEBUTTONDOWN and self.focus_piece_type:
            self.on_selected(self.text_class_map[self.focus_piece_type])
            
            self.destroy()
    
    def destroy(self):
        if self._destroyed:
            self._destroyed(self)
        
        del self
    
    def draw(self):
        pygame.draw.rect(
            self,
            self.board_style.lower(),
            (
                self.border_width,
                self.border_width,
                self.rect.width - self.border_width * 2,
                self.rect.height - self.border_width * 2
            ),
            0,
        )
        
        if self.focus_piece_type:
            self.blit(self.hover_surf, self.hover_rect)
        
        for params in self.option:
            self.blit(*params)
        
        pygame.draw.rect(self, "black", ((0, 0), self.rect.size), self.border_width, 8)
        
        super().draw()

