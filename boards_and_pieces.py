
from typing import Callable
from base import *


class Piece(Base):
    def __init__(self, board: "Board", is_white: bool, pos: bytes, surf_path: str):
        super().__init__((board.get_width() / 8, board.get_height() / 8), board, {}, pygame.SRCALPHA)
        
        self.name = None
        
        self.SPEED = 0.1
        
        self.pos = pos
        self.board = board
        self.is_white = is_white
        
        self.rect.topleft = self._pos_from_bit_pos(self.pos)
        
        self.bit_board = 0
        self._move_count = 0
        
        self._kill_zones = 0
        self._valid_moves = 0
        
        self._moves: list[list[bytes, int]] = []
        
        self.set_skin(surf_path)
    
    def set_skin(self, path: str):
        skin = pygame.image.load(path)
        skin = pygame.transform.scale_by(
            skin,
            max(
                (self.get_width() * 0.85) / skin.get_width(),
                (self.get_height() * 0.85) / skin.get_height()
            )
        )
        
        self.blit(skin, skin.get_rect(center=(self.get_width() / 2, self.get_height() / 2)))
    
    def _visual_move(self, to: bytes):
        dx = (to[0] - self.pos[0]) * self.get_width()
        dy = (to[1] - self.pos[1]) * self.get_height()
        
        self.rect.x += dx * self.SPEED
        self.rect.y += dy * self.SPEED
    
    def _bit_move(self, to: bytes):
        self.board.capture(self.is_white, self.pos, to)
        self.pos = to
    
    def _pos_from_bit_pos(self, pos: bytes):
        return pos[0] * self.get_width(), pos[1] * self.get_height()
    
    def _update_kill_zones(self, valid_moves, pos, **kwargs):
        return self._update_valid_moves(valid_moves, pos, **kwargs)
    
    @staticmethod
    def _update_valid_moves(valid_moves: int, pos: bytes, **kwargs):
        raise NotImplementedError()
    
    def update_valid_moves(self):
        self._valid_moves = self._update_valid_moves(
            0,
            self.pos,
            is_white=self.is_white,
            team_bits=self.get_team_bits(),
            enemy_bits=self.get_enemy_bits(),
            enemy_kill_zones=(self.board.get_black_kill_zones() if self.is_white else self.board.get_white_kill_zones()),
            move_count=self._move_count,
            rook_bits=0
        )
        
        self._valid_moves %= MAX_BIT
        self._valid_moves = (self.get_team_bits() ^ self._valid_moves) & self._valid_moves
    
    def update_kill_zones(self):
        self._kill_zones = self._update_kill_zones(
            0,
            self.pos,
            is_white=self.is_white,
            team_bits=self.get_team_bits(),
            enemy_bits=self.get_enemy_bits(),
            enemy_kill_zones=(self.board.get_black_kill_zones() if self.is_white else self.board.get_white_kill_zones()),
            move_count=self._move_count,
            rook_bits=0
        )
        
        self._kill_zones %= MAX_BIT
        self._kill_zones = (self.get_team_bits() ^ self._kill_zones) & self._kill_zones
    
    def get_team_bits(self):
        return self.board.get_white_bits() if self.is_white else self.board.get_black_bits()
    
    def get_enemy_bits(self):
        return self.board.get_black_bits() if self.is_white else self.board.get_white_bits()
    
    def total_move(self, to: bytes, piece_set: Callable[["Piece"], None] | None = None, finished: Callable[[], None] | None = None):
        if self.pos[0] != to[0] or self.pos[1] != to[1]:
            bit_to = bit_byte_to_bits(to)
            
            if (bit_to & self.get_valid_moves()) == bit_to:
                self._moves.append([to, int(1 / self.SPEED), piece_set, finished])
                self._move_count += 1
                
                return
        
        if finished:
            finished()
    
    def get_valid_moves(self):
        return self._valid_moves
    
    def get_kill_zones(self):
        return self._kill_zones
    
    def update(self):
        if self._moves:
            move, count, piece_set, finished = self._moves[0]
            
            if count:
                self._visual_move(move)
                self._moves[0][1] -= 1
            else:
                prev_move = self.pos
                
                self._bit_move(move)
                
                self.rect.topleft = self._pos_from_bit_pos(self.pos)
                self._moves.pop(0)
                
                if piece_set and move != prev_move:
                    piece_set(self)
                
                if finished:
                    finished()


class Bishop(Piece):
    def __init__(self, board, is_white, pos, surf_path):
        super().__init__(board, is_white, pos, surf_path)
        
        self.name = "Bishop"
    
    @staticmethod
    def _update_valid_moves(valid_moves, pos, **kwargs):
        team_bits = kwargs["team_bits"]
        enemy_bits = kwargs["enemy_bits"]
        
        top_left_mask = 0
        top_right_mask = 0
        bottom_left_mask = 0
        bottom_right_mask = 0
        
        for i in range(7):
            i_plus_one = i + 1
            
            top_focus = (7 - pos[1] + i_plus_one) * 8
            bottom_focus = (7 - pos[1] - i_plus_one) * 8
            left_focus = 7 - pos[0] + i_plus_one
            right_focus = 7 - pos[0] - i_plus_one
            
            path = bit_shift_left(4 * 2 ** (i * 2) + 1, right_focus) % 256
            
            top_left_mask |= (team_bits >> (top_focus + left_focus)) % 2
            top_right_mask |= bit_shift_right(team_bits, (top_focus + right_focus)) % 2
            bottom_left_mask |= bit_shift_right(team_bits, (bottom_focus + left_focus)) % 2
            bottom_right_mask |= bit_shift_right(team_bits, (bottom_focus + right_focus)) % 2
            
            top_path_mask = ((top_left_mask << max(right_focus + i_plus_one * 2, 0)) | bit_shift_left(top_right_mask, right_focus)) % 256
            bottom_path_mask = ((bottom_left_mask << max(right_focus + i_plus_one * 2, 0)) | bit_shift_left(bottom_right_mask, right_focus)) % 256
            
            top = (path & ~top_path_mask) << top_focus
            bottom = bit_shift_left((path & ~bottom_path_mask), bottom_focus)
            
            valid_moves |= (top | bottom)
            
            top_left_mask |= (enemy_bits >> (top_focus + left_focus)) % 2
            top_right_mask |= bit_shift_right(enemy_bits, (top_focus + right_focus)) % 2
            bottom_left_mask |= bit_shift_right(enemy_bits, (bottom_focus + left_focus)) % 2
            bottom_right_mask |= bit_shift_right(enemy_bits, (bottom_focus + right_focus)) % 2
        
        return valid_moves

class Rook(Piece):
    def __init__(self, board, is_white, pos, surf_path):
        super().__init__(board, is_white, pos, surf_path)
        
        self.name = "Rook"
    
    @staticmethod
    def _update_valid_moves(valid_moves, pos, **kwargs):
        team_bits = kwargs["team_bits"]
        enemy_bits = kwargs["enemy_bits"]
        
        top_mask = 0
        left_mask = 0
        right_mask = 0
        bottom_mask = 0
        
        team_horiz = (team_bits >> (7 - pos[1]) * 8) % 256
        enemy_horiz = (enemy_bits >> (7 - pos[1]) * 8) % 256
        
        central_row = 0
        
        for i in range(7):
            i_plus_one = i + 1
            
            top_focus = min(7 - pos[1] + i_plus_one, 7) * 8
            bottom_focus = max(7 - pos[1] - i_plus_one, 0) * 8
            
            path = bit_byte_to_bits(bytes([pos[0], 7]))
            
            top = path << top_focus
            bottom = path << bottom_focus
            
            top_mask |= (team_bits >> top_focus) % 256
            bottom_mask |= (team_bits >> bottom_focus) % 256
            
            top &= ~(top_mask << top_focus)
            bottom &= ~(bottom_mask << bottom_focus)
            
            valid_moves |= (top | bottom)
            
            top_mask |= (enemy_bits >> top_focus) % 256
            bottom_mask |= (enemy_bits >> bottom_focus) % 256
            
            left_focus = min(7 - pos[0] + i_plus_one, 7)
            right_focus = max(7 - pos[0] - i_plus_one, 0)
            
            left_mask |= (team_horiz >> left_focus) % 2
            right_mask |= (team_horiz >> right_focus) % 2
            
            central_row |= (((1 & ~left_mask) << left_focus) | ((1 & ~right_mask) << right_focus)) % 256
            
            left_mask |= (enemy_horiz >> left_focus) % 2
            right_mask |= (enemy_horiz >> right_focus) % 2
        
        valid_moves |= central_row << ((7 - pos[1]) * 8)
        
        return valid_moves

class Queen(Piece):
    def __init__(self, board, is_white, pos, surf_path):
        super().__init__(board, is_white, pos, surf_path)
        
        self.name = "Queen"
    
    @staticmethod
    def _update_valid_moves(valid_moves, pos, **kwargs):
        return Bishop._update_valid_moves(Rook._update_valid_moves(valid_moves, pos, **kwargs), pos, **kwargs)

class King(Piece):
    def __init__(self, board, is_white, pos, surf_path):
        super().__init__(board, is_white, pos, surf_path)
        
        self.name = "King"
    
    @staticmethod
    def _update_valid_moves(valid_moves, pos, **kwargs):
        enemy_kill_zones = kwargs["enemy_kill_zones"]
        
        middle_dir = (7 - pos[1]) * 8
        top_dir = (7 - pos[1] + 1) * 8
        bottom_dir = (7 - pos[1] - 1) * 8
        
        middle_mask = ((enemy_kill_zones >> middle_dir) % 256)
        top_mask = ((enemy_kill_zones >> top_dir) % 256)
        bottom_mask = (bit_shift_right(enemy_kill_zones, bottom_dir) % 256)
        
        off = bit_shift_left(5, 7 - pos[0] - 1) % 256
        vert = bit_byte_to_bits(bytes([pos[0], 7]))
        
        left_nd_right = off & ~middle_mask
        top_left_nd_right = off & ~top_mask
        bottom_left_nd_right = off & ~bottom_mask
        top_middle = vert & ~top_mask
        bottom_middle = vert & ~bottom_mask
        
        valid_moves |= (
            bit_shift_left(left_nd_right, middle_dir) |
            bit_shift_left(top_left_nd_right, top_dir) |
            bit_shift_left(bottom_left_nd_right, bottom_dir) |
            bit_shift_left(top_middle, top_dir) |
            bit_shift_left(bottom_middle, bottom_dir)
        )
        
        return valid_moves

class Knight(Piece):
    def __init__(self, board, is_white, pos, surf_path):
        super().__init__(board, is_white, pos, surf_path)
        
        self.name = "Knight"
    
    @staticmethod
    def _update_valid_moves(valid_moves, pos, **kwargs):
        off1 = bit_shift_left(5, (7 - pos[0]) - 1) % 256
        off2 = bit_shift_left(17, (7 - pos[0]) - 2) % 256
        
        valid_moves |= (
            bit_shift_left(off1, (7 - pos[1] + 2) * 8) |
            bit_shift_left(off1, (7 - pos[1] - 2) * 8) |
            bit_shift_left(off2, (7 - pos[1] + 1) * 8) |
            bit_shift_left(off2, (7 - pos[1] - 1) * 8)
        )
        
        return valid_moves

class Pawn(Piece):
    def __init__(self, board, is_white, pos, surf_path):
        super().__init__(board, is_white, pos, surf_path)
        
        self.name = "Pawn"
    
    def _update_kill_zones(self, valid_moves, pos, **kwargs):
        return valid_moves | bit_shift_left(bit_shift_left(5, 7 - pos[0] - 1) % 256, (7 - pos[1] + kwargs["is_white"] * 2 - 1) * 8)
    
    @staticmethod
    def _update_valid_moves(valid_moves, pos, **kwargs):
        is_white = kwargs["is_white"]
        team_bits = kwargs["team_bits"]
        enemy_bits = kwargs["enemy_bits"]
        move_count = kwargs["move_count"]
        
        direction = is_white * 2 - 1
        avoid = team_bits | enemy_bits
        
        single_next_level = (7 - pos[1] + direction) * 8
        double_next_level = (7 - pos[1] + (2 * direction)) * 8
        
        mask_1 = (avoid >> single_next_level) % 256
        mask_2 = (avoid >> double_next_level) % 256
        
        _vert = bit_byte_to_bits(bytes([pos[0], 7]))
        
        vert_single = _vert & ~mask_1
        vert_double = _vert & ~(mask_1 | mask_2)
        
        single_move = bit_shift_left(vert_single, single_next_level)
        double_move = ((move_count != 0) or (bit_shift_left(vert_double, double_next_level) + 1)) - 1
        capturables = bit_shift_left(bit_shift_left(5, 7 - pos[0] - 1) % 256, single_next_level) & enemy_bits
        
        valid_moves |= (
            single_move |
            double_move |
            capturables
        )
        
        return valid_moves


class Board(Base):
    def __init__(self, screen: pygame.Surface, board: str):
        super().__init__((min(screen.get_size()), min(screen.get_size())), screen, {"center": (screen.get_width() / 2, screen.get_height() / 2)})
        
        self._class_text_map = {
            Rook: "r",
            Bishop: "b",
            Knight: "n",
            Queen: "q",
            King: "k",
            Pawn: "p",
            type(None): "x"
        }
        self._text_class_map = {v: k for k, v in self._class_text_map.items()}
        
        self.BLOCK_SIZE = self.get_width() / 8, self.get_height() / 8
        
        self._captures = []
        self._turn_tracker = True
        self._move_selected = False
        
        self.focus_piece = None
        self.board_style = None
        
        self.background = pygame.Surface(self.get_size())
        
        self.set_board_style("Brown")
        self.white_pieces, self.black_pieces = self.parse_string_board(board, "Default", True)
        
        self.kill_overlay_surface = pygame.Surface(self.BLOCK_SIZE, pygame.SRCALPHA)
        self.kill_overlay_surface.fill("lightblue")
        self.kill_overlay_surface.set_alpha(120)
        
        self.pieces = set(list(self.white_pieces.values()) + list(self.black_pieces.values()))
        
        for piece in self.pieces:
            piece.update_valid_moves()
            piece.update_kill_zones()
            piece.update_valid_moves()
            piece.update_kill_zones()
    
    def _no_focus(self):
        self.focus_piece = None
    
    def _piece_placed(self, piece: Piece):
        self._turn_tracker = not self._turn_tracker
        
        piece.update_kill_zones()
    
    def set_board_style(self, style: str):
        self.board_style = style
        
        board = pygame.image.load(f"assets/pieces and boards/Board {self.board_style}.png")
        board = pygame.transform.scale_by(
            board,
            max(
                self.get_width() / board.get_width(),
                self.get_height() / board.get_height()
            )
        )
        
        self.background.blit(board, board.get_rect(center=(self.background.get_width() / 2, self.background.get_height() / 2)))
    
    def set_piece_style(self, style: str, O: bool = False):
        for piece in self.pieces:
            piece.set_skin(f"assets/pieces and boards/{"White" if piece.is_white else "Black"} {style}/{piece.name}{" O" if O else ""}.png")
    
    def parse_string_board(self, string: str, style: str, O: bool = False):
        index = 0
        
        white_pieces: dict[bytes, Piece] = {}
        black_pieces: dict[bytes, Piece] = {}
        
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
                
                for i in range(amount):
                    pos = bytes([index % 8 + i, index // 8])
                    
                    if c.islower():
                        color = "Black"
                        pieces = black_pieces
                    else:
                        color = "White"
                        pieces = white_pieces
                    
                    piece_path = f"assets/pieces and boards/{color} " + style + "/{}" + f"{" O" if O else ""}.png"
                    
                    cls = self._text_class_map[c.lower()]
                    
                    if cls != type(None):
                        pieces[pos] = cls(self, not c.islower(), pos, piece_path.format(c.upper()))
                
                index += amount

        return white_pieces, black_pieces
    
    def to_string_board(self):
        string = ""
        
        pieces = self.white_pieces.copy()
        pieces.update(self.black_pieces)
        
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
            
            c = self._class_text_map[piece.__class__]
            
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
    
    def get_white_bits(self):
        bits = 0
        for pos in self.white_pieces:
            bits |= bit_byte_to_bits(pos)
        
        return bits
    
    def get_black_bits(self):
        bits = 0
        
        for pos in self.black_pieces:
            bits |= bit_byte_to_bits(pos)
        
        return bits
    
    def get_white_valid_moves(self):
        bits = 0
        
        for i, pieces in enumerate(self.white_pieces.values()):
            bits |= pieces.get_valid_moves()
        
        return bits
    
    def get_black_valid_moves(self):
        bits = 0
        
        for pieces in self.black_pieces.values():
            bits |= pieces.get_valid_moves()
        
        return bits
    
    def get_white_kill_zones(self):
        bits = 0
        
        for pieces in self.white_pieces.values():
            bits |= pieces.get_kill_zones()
        
        return bits
    
    def get_black_kill_zones(self):
        bits = 0
        
        for pieces in self.black_pieces.values():
            bits |= pieces.get_kill_zones()
        
        return bits
    
    def capture(self, captor_state: bool, captor: bytes, prisoner: bytes):
        pris_pieces = self.black_pieces if captor_state else self.white_pieces
        cap_pieces = self.white_pieces if captor_state else self.black_pieces
        
        if prisoner in pris_pieces:
            prisoner_piece = pris_pieces.pop(prisoner)
            self.pieces.remove(prisoner_piece)
            
            self._captures.append(prisoner_piece)
        
        captor_piece = cap_pieces.pop(captor)
        
        cap_pieces[prisoner] = captor_piece
    
    def do_pos_from_bits(self, bits, action: Callable[[int, int], None], *, _count = None):
        _count = _count or 0
        
        if bits:
            if bits % 2:
                action(7 - (_count % 8), 7 - (_count // 8))
            
            _count += 1
            
            self.do_pos_from_bits(bits >> 1, action, _count=_count)
    
    def event_handler(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            m_pos = (event.pos[0] - self.rect.left, event.pos[1] - self.rect.top)
            
            if self.focus_piece is None:
                for piece in (self.white_pieces.values() if self._turn_tracker else self.black_pieces.values()):
                    if piece.rect.collidepoint(m_pos):
                        piece.update_valid_moves()
                        
                        if piece.get_valid_moves():
                            self.focus_piece = piece
                
                self._move_selected = False
            else:
                pos = bytes([int(m_pos[0] // self.BLOCK_SIZE[0]), int(m_pos[1] // self.BLOCK_SIZE[1])])
                
                self.focus_piece.total_move(pos, self._piece_placed, self._no_focus)
                self._move_selected = True
    
    def update(self):
        self.rect.center = (self.parent.get_width() / 2, self.parent.get_height() / 2)
        
        if self.focus_piece:
            self.focus_piece.update()
    
    def draw(self):
        self.blit(self.background, (0, 0))
        
        if self.focus_piece and not self._move_selected:
            self.do_pos_from_bits(
                self.focus_piece.get_valid_moves(),
                lambda x, y: (
                    pygame.draw.circle(
                        self,
                        self.board_style.lower(),
                        (x * self.BLOCK_SIZE[0] + self.BLOCK_SIZE[0] / 2, y * self.BLOCK_SIZE[1] + self.BLOCK_SIZE[1] / 2),
                        sum(self.BLOCK_SIZE) / 10
                    )
                    
                    if bytes([x, y]) not in self.white_pieces and bytes([x, y]) not in self.black_pieces else
                    
                    self.blit(
                        self.kill_overlay_surface,
                        (x * self.BLOCK_SIZE[0], y * self.BLOCK_SIZE[1])
                    )
                )
            )
            
            self._move_selected = False
        
        for piece in (self.pieces - set([self.focus_piece])):
            piece.draw()
        
        if self.focus_piece:
            self.focus_piece.draw()
        
        return super().draw()


