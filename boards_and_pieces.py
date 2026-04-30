
from base import *
from ui import PromoteEdit
from typing import Callable


class Piece(Base):
    def __init__(self, board: "Board", is_white: bool, pos: bytes, piece_style: str, O: bool, piece_type: str):
        self.board = board
        
        super().__init__(self.board.BLOCK_SIZE, board, {"topleft": self._pos_from_bit_pos(pos)}, pygame.SRCALPHA)
        
        self.name = None
        
        self.SPEED = 0.1
        
        self.pos = pos
        self.is_white = is_white
        self.piece_type = piece_type
        
        self._O = O
        
        self.bit_board = 0
        self.moves_count = 0
        
        self._kill_zones = 0
        self._valid_moves = 0
        self._attack_paths = ()
        self._king_attack_paths = ()
        
        self._moves: list[list[bytes, int]] = []
        
        self.set_skin(piece_style)
    
    def _init(self):
        pass
    
    @staticmethod
    def _update_kill_zones(valid_moves: int, pos: bytes, **kwargs) -> int:
        return kwargs["self"]._update_valid_moves(valid_moves, pos, **kwargs)
    
    @staticmethod
    def _update_valid_moves(valid_moves: int, pos: bytes, **kwargs) -> int:
        for path in kwargs["self"]._update_attack_paths(pos, None, **kwargs):
            valid_moves |= path
        
        return valid_moves
    
    @staticmethod
    def _update_attack_paths(pos: bytes, valid_paths: list[int] | None, **kwargs) -> tuple[int, ...]:
        raise NotImplementedError()
    
    def _visual_move(self, to: bytes):
        dx = (to[0] - self.pos[0]) * self.get_width()
        dy = (to[1] - self.pos[1]) * self.get_height()
        
        self.rect.x += dx * self.SPEED
        self.rect.y += dy * self.SPEED
    
    def _bit_move(self, to: bytes):
        self.capture(to)
        self.pos = to
    
    def _pos_from_bit_pos(self, pos: bytes):
        return pos[0] * self.board.BLOCK_SIZE[0], pos[1] * self.board.BLOCK_SIZE[0]
    
    def set_skin(self, piece_style: str, O: bool = None):
        self.piece_style = piece_style
        self._O = O if O is not None else self._O
        
        path = f"assets/pieces and boards/{"White" if self.is_white else "Black"} {self.piece_style}/{self.piece_type}" + f"{" O" if self._O else ""}.png"
        
        skin = pygame.image.load(path)
        skin = pygame.transform.scale_by(
            skin,
            max(
                (self.get_width() * 0.85) / skin.get_width(),
                (self.get_height() * 0.85) / skin.get_height()
            )
        )
        
        self.blit(skin, skin.get_rect(center=(self.get_width() / 2, self.get_height() / 2)))
    
    def update_valid_moves(self):
        self._valid_moves = self._update_valid_moves(
            0,
            self.pos,
            self=self,
            is_white=self.is_white,
            team_bits=self.board.get_team_bits(self.is_white),
            enemy_bits=self.board.get_enemy_bits(self.is_white),
            enemy_kill_zones=self.board.get_enemy_kill_zones(self.is_white),
            moves_count=self.moves_count
        ) % MAX_BIT
        
        self._valid_moves &= ~self.board.get_team_bits(self.is_white)
        self._valid_moves = self.filter_checks(self._valid_moves)
    
    def update_kill_zones(self):
        self._kill_zones = self._update_kill_zones(
            0,
            self.pos,
            self=self,
            is_white=self.is_white,
            moves_count=self.moves_count,
            team_bits=0,
            enemy_bits=self.board.get_enemy_bits(self.is_white) | self.board.get_team_bits(self.is_white),
            enemy_kill_zones=self.board.get_enemy_kill_zones(self.is_white)
        ) % MAX_BIT
        
        self._attack_paths = self._update_attack_paths(
            self.pos,
            0,
            self=self,
            is_white=self.is_white,
            moves_count=self.moves_count,
            team_bits=0,
            enemy_bits=self.board.get_enemy_bits(self.is_white) | self.board.get_team_bits(self.is_white),
            enemy_kill_zones=self.board.get_enemy_kill_zones(self.is_white)
        )
        
        self._king_attack_paths = self._update_attack_paths(
            self.pos,
            0,
            self=self,
            is_white=self.is_white,
            moves_count=self.moves_count,
            team_bits=0,
            enemy_bits=self.board.get_team_bits(self.is_white) | bit_byte_to_bits(self.board.get_enemy_king(self.is_white).pos),
            enemy_kill_zones=self.board.get_enemy_kill_zones(self.is_white)
        )
    
    def get_valid_moves(self):
        return self._valid_moves
    
    def get_kill_zones(self):
        return self._kill_zones
    
    def get_attack_paths(self):
        return self._attack_paths
    
    def get_king_attack_paths(self):
        return self._king_attack_paths
    
    def get_checking_enemies(self, king_bit: int):
        for piece in self.board.get_pointed_enemies(self.is_white):
            if king_bit & piece.get_kill_zones():
                yield piece
        
        for piece in self.board.get_pathed_enemies(self.is_white):
            if king_bit & piece.get_kill_zones():
                yield piece
    
    def capture(self, target: bytes):
        team_pieces = self.board.get_team_pieces(self.is_white)
        enemy_pieces = self.board.get_enemy_pieces(self.is_white)
        
        if target in enemy_pieces:
            self.board.capture_piece(enemy_pieces[target])
        
        captor_piece = team_pieces.pop(self.pos)
        
        team_pieces[target] = captor_piece
    
    def filter_checks(self, valid_moves: int):
        my_bit = bit_byte_to_bits(self.pos)
        king_bit = bit_byte_to_bits(self.board.get_team_king(self.is_white).pos)
        
        for piece in self.get_checking_enemies(king_bit):
            n_moves = bit_byte_to_bits(piece.pos)
            
            if isinstance(piece, (Queen, Rook, Bishop)):
                n_moves |= next(a_path for a_path in piece.get_attack_paths() if king_bit & a_path)
            
            valid_moves &= n_moves
        
        for piece in self.board.get_pathed_enemies(self.is_white):
            for i, ua_path in enumerate(piece.get_king_attack_paths()):
                a_path = piece.get_attack_paths()[i] % MAX_BIT
                
                if ua_path & king_bit and not ((self.board.get_team_bits(self.is_white) & ~(my_bit | king_bit)) & ua_path) and a_path & my_bit:
                    valid_moves &= a_path | bit_byte_to_bits(piece.pos)
        
        return valid_moves
    
    def total_move(self, to: bytes, piece_set: Callable[["Piece"], None] | None = None, finished: Callable[[], None] | None = None):
        if self.pos[0] != to[0] or self.pos[1] != to[1]:
            bit_to = bit_byte_to_bits(to)
            
            if bit_to & self.get_valid_moves():
                self._moves.append([to, int(1 / self.SPEED), piece_set, finished])
                self.moves_count += 1
                
                return
        
        if finished:
            finished()
    
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


class Rook(Piece):
    def __init__(self, board, is_white, pos, piece_style, O):
        super().__init__(board, is_white, pos, piece_style, O, "R")
    
    @staticmethod
    def _update_attack_paths(pos, valid_paths, **kwargs):
        t, b, l, r = valid_paths or [0, 0, 0, 0]
        
        team_bits = kwargs["team_bits"]
        enemy_bits = kwargs["enemy_bits"]
        
        top_mask = 0
        left_mask = 0
        right_mask = 0
        bottom_mask = 0
        
        team_horiz = (team_bits >> (7 - pos[1]) * 8) % 256
        enemy_horiz = (enemy_bits >> (7 - pos[1]) * 8) % 256
        
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
            
            t |= top
            b |= bottom
            
            top_mask |= (enemy_bits >> top_focus) % 256
            bottom_mask |= (enemy_bits >> bottom_focus) % 256
            
            left_focus = min(7 - pos[0] + i_plus_one, 7)
            right_focus = max(7 - pos[0] - i_plus_one, 0)
            
            left_mask |= (team_horiz >> left_focus) % 2
            right_mask |= (team_horiz >> right_focus) % 2
            
            l |= (((1 & ~left_mask) << left_focus) % 256) << ((7 - pos[1]) * 8)
            r |= (((1 & ~right_mask) << right_focus) % 256) << ((7 - pos[1]) * 8)
            
            left_mask |= (enemy_horiz >> left_focus) % 2
            right_mask |= (enemy_horiz >> right_focus) % 2
        
        return t, b, l, r

class Bishop(Piece):
    def __init__(self, board, is_white, pos, piece_style, O):
        super().__init__(board, is_white, pos, piece_style, O, "B")
    
    @staticmethod
    def _update_attack_paths(pos, valid_paths, **kwargs):
        tr, tl, br, bl = (valid_paths or [0, 0, 0, 0])
        
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
            
            path1 = bit_shift_left(4 * 2 ** (i * 2), right_focus) % 256
            path2 = bit_shift_left(1, right_focus) % 256
            
            top_left_mask |= (team_bits >> (top_focus + left_focus)) % 2
            top_right_mask |= bit_shift_right(team_bits, (top_focus + right_focus)) % 2
            bottom_left_mask |= bit_shift_right(team_bits, (bottom_focus + left_focus)) % 2
            bottom_right_mask |= bit_shift_right(team_bits, (bottom_focus + right_focus)) % 2
            
            top_path_mask = ((top_left_mask << max(right_focus + i_plus_one * 2, 0)) | bit_shift_left(top_right_mask, right_focus)) % 256
            bottom_path_mask = ((bottom_left_mask << max(right_focus + i_plus_one * 2, 0)) | bit_shift_left(bottom_right_mask, right_focus)) % 256
            
            tr |= (path1 & ~top_path_mask) << top_focus
            tl |= (path2 & ~top_path_mask) << top_focus
            br |= bit_shift_left((path1 & ~bottom_path_mask), bottom_focus)
            bl |= bit_shift_left((path2 & ~bottom_path_mask), bottom_focus)
            
            top_left_mask |= (enemy_bits >> (top_focus + left_focus)) % 2
            top_right_mask |= bit_shift_right(enemy_bits, (top_focus + right_focus)) % 2
            bottom_left_mask |= bit_shift_right(enemy_bits, (bottom_focus + left_focus)) % 2
            bottom_right_mask |= bit_shift_right(enemy_bits, (bottom_focus + right_focus)) % 2
        
        return tr, tl, br, bl

class Queen(Piece):
    def __init__(self, board, is_white, pos, piece_style, O):
        super().__init__(board, is_white, pos, piece_style, O, "Q")
    
    @staticmethod
    def _update_attack_paths(pos, valid_paths, **kwargs):
        valid_paths = valid_paths or [0, 0, 0, 0, 0, 0, 0, 0]
        
        return Rook._update_attack_paths(pos, valid_paths[:4], **kwargs) + Bishop._update_attack_paths(pos, valid_paths[4:], **kwargs)

class King(Piece):
    def __init__(self, board, is_white, pos, piece_style, O):
        super().__init__(board, is_white, pos, piece_style, O, "K")
        
        self.rooks = {}
        self.castleable_bits = 0
    
    def _init(self):
        super()._init()
        
        for piece in self.board.get_team_pieces(self.is_white).values():
            if isinstance(piece, Rook):
                self.rooks[piece] = [0, 0]
    
    def total_move(self, to, piece_set = None, finished = None):
        super().total_move(to, piece_set, finished)
        
        castling = bit_byte_to_bits(to) & self.castleable_bits
        
        if castling:
            for rook, (rc, kc) in self.rooks.items():
                if kc == castling:
                    rook._valid_moves |= rc
                    
                    rook.total_move(bits_to_bit_byte(rc), lambda piece: self.board.temp_updates.remove(piece))
                    self.board.temp_updates.append(rook)
    
    def filter_checks(self, valid_moves):
        king_bit = bit_byte_to_bits(self.pos)
        
        for piece in self.get_checking_enemies(king_bit):
            n_moves = bit_byte_to_bits(piece.pos)
            
            if isinstance(piece, (Queen, Rook, Bishop)):
                n_moves |= piece._update_valid_moves(
                    0,
                    piece.pos,
                    is_white=piece.is_white,
                    team_bits=0,
                    enemy_bits=0,
                    enemy_kill_zones=0,
                    moves_count=piece.moves_count,
                    self=piece
                )
            
            valid_moves &= ~n_moves
        
        return valid_moves
    
    @staticmethod
    def _update_attack_paths(pos, valid_paths, **kwargs):
        pass
    
    @staticmethod
    def _update_valid_moves(valid_moves, pos, **kwargs):
        self = kwargs["self"]
        team_bits = kwargs["team_bits"]
        moves_count = kwargs["moves_count"]
        enemy_kill_zones = kwargs["enemy_kill_zones"]
        
        middle_dir = (7 - pos[1]) * 8
        top_dir = (7 - pos[1] + 1) * 8
        bottom_dir = (7 - pos[1] - 1) * 8
        
        middle_mask = ((enemy_kill_zones >> middle_dir) % 256)
        top_mask = ((enemy_kill_zones >> top_dir) % 256)
        bottom_mask = (bit_shift_right(enemy_kill_zones, bottom_dir) % 256)
        
        left = bit_shift_left(4, 7 - pos[0] - 1) % 256
        right = bit_shift_left(1, 7 - pos[0] - 1) % 256
        center = bit_byte_to_bits(bytes([pos[0], 7]))
        
        i = 0
        self.castleable_bits = 0
        rooks = list(self.rooks)
        for _ in range(len(rooks)):
            rook = rooks[i]
            
            castleable = (
                rook.pos and
                moves_count + rook.moves_count == 0 and
                not (team_bits >> (7 - pos[1]) * 8 + (7 - max(pos[0], rook.pos[0]) + 1)) % (1 << (abs(pos[0] - rook.pos[0]) - 1)) and
                next(self.get_checking_enemies(bit_byte_to_bits(pos)), None) is None
            )
            
            if castleable:
                d = pos[0] - rook.pos[0]
                
                sign = int(abs(d) / d if d else 0)
                
                king_castle_bit = bit_shift_left(bit_byte_to_bits(bytes([pos[0], 7])), abs(d // 2) * sign) << (7 - pos[1]) * 8
                rook_castle_bit = bit_shift_right(bit_byte_to_bits(bytes([rook.pos[0], 7])), (abs(d // 2) + 1 - ((d * sign) % 2)) * sign) << (7 - rook.pos[1]) * 8
                
                if not king_castle_bit & enemy_kill_zones:
                    self.castleable_bits |= king_castle_bit
                    self.rooks[rook] = [rook_castle_bit, king_castle_bit]
            elif moves_count + rook.moves_count != 0 or not rook.pos:
                self.rooks.pop(rook)
                rooks.pop(i)
                
                i -= 1
            
            i += 1
        
        return valid_moves | (
            bit_shift_left(center & ~top_mask, top_dir) |
            bit_shift_left(center & ~bottom_mask, bottom_dir) |
            bit_shift_left(left & ~middle_mask, middle_dir) |
            bit_shift_left(right & ~middle_mask, middle_dir) |
            bit_shift_left(left & ~top_mask, top_dir) |
            bit_shift_left(right & ~top_mask, top_dir) |
            bit_shift_left(left & ~bottom_mask, bottom_dir) |
            bit_shift_left(right & ~bottom_mask, bottom_dir) |
            self.castleable_bits
        )

class Knight(Piece):
    def __init__(self, board, is_white, pos, piece_style, O):
        super().__init__(board, is_white, pos, piece_style, O, "N")
    
    @staticmethod
    def _update_attack_paths(pos, valid_paths, **kwargs):
        pass
    
    @staticmethod
    def _update_valid_moves(valid_moves, pos, **kwargs):
        upper_left = bit_shift_left(4, 7 - pos[0] - 1) % 256
        upper_right = bit_shift_left(1, 7 - pos[0] - 1) % 256
        lower_left = bit_shift_left(16, 7 - pos[0] - 2) % 256
        lower_right = bit_shift_left(1, 7 - pos[0] - 2) % 256
        
        return valid_moves | (
            bit_shift_left(upper_left, (7 - pos[1] + 2) * 8)|
            bit_shift_left(upper_right, (7 - pos[1] + 2) * 8)|
            bit_shift_left(lower_left, (7 - pos[1] + 1) * 8)|
            bit_shift_left(lower_right, (7 - pos[1] + 1) * 8)|
            bit_shift_left(lower_left, (7 - pos[1] - 1) * 8)|
            bit_shift_left(lower_right, (7 - pos[1] - 1) * 8)|
            bit_shift_left(upper_left, (7 - pos[1] - 2) * 8)|
            bit_shift_left(upper_right, (7 - pos[1] - 2) * 8)
        )

class Pawn(Piece):
    def __init__(self, board, is_white, pos, piece_style, O):
        super().__init__(board, is_white, pos, piece_style, O, "P")
        
        self.double_moved = False
        self.en_pesant_pawns = {}
    
    def _bit_move(self, to):
        curr_pos = self.pos
        
        super()._bit_move(to)
        
        if abs(curr_pos[1] - to[1]) == 2:
            self.double_moved = True
        
        en_pesant_piece = self.en_pesant_pawns.get(self.pos)
        if en_pesant_piece:
            self.board.capture_piece(en_pesant_piece)
        
        if self.pos[1] in (0, 7):
            self.promote()
    
    def _promote(self, promote_piece_cls: type[Piece]):
        pos = self.pos
        
        piece = promote_piece_cls(self.board, self.is_white, self.pos, self.piece_style, self._O)
        piece._init()
        
        piece.update_valid_moves()
        piece.update_kill_zones()
        
        self.board.pieces.add(piece)
        
        self.board.remove_piece(self)
        
        team_pieces = self.board.get_team_pieces(self.is_white)
        team_pieces[pos] = piece
        
        del self
    
    @staticmethod
    def _update_attack_paths(pos, valid_paths, **kwargs):
        pass
    
    @staticmethod
    def _update_kill_zones(valid_moves, pos, **kwargs):
        return valid_moves | (
            bit_shift_left(bit_shift_left(4, 7 - pos[0] - 1) % 256, (7 - pos[1] + kwargs["is_white"] * 2 - 1) * 8) |
            bit_shift_left(bit_shift_left(1, 7 - pos[0] - 1) % 256, (7 - pos[1] + kwargs["is_white"] * 2 - 1) * 8)
        )
    
    @staticmethod
    def _update_valid_moves(valid_moves, pos, **kwargs):
        self = kwargs["self"]
        is_white = kwargs["is_white"]
        team_bits = kwargs["team_bits"]
        enemy_bits = kwargs["enemy_bits"]
        moves_count = kwargs["moves_count"]
        
        enemy_pieces = self.board.get_enemy_pieces(is_white)
        
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
        double_move = ((moves_count != 0) or (bit_shift_left(vert_double, double_next_level) + 1)) - 1
        capturables = self._update_kill_zones(0, pos, **kwargs) & enemy_bits
        
        en_pesant = 0
        en_pesant_enemies = (
            enemy_pieces.get(bytes([pos[0] - 1, pos[1]])) if pos[0] else None,
            enemy_pieces.get(bytes([pos[0] + 1, pos[1]])) if pos[0] - 7 else None
        )
        self.en_pesant_pawns.clear()
        
        for enemy in en_pesant_enemies:
            if enemy and isinstance(enemy, Pawn) and enemy.double_moved and self.board.moves[-1][1] == enemy.pos:
                ep_pos = bytes([enemy.pos[0], enemy.pos[1] - direction])
                en_pesant |= bit_byte_to_bits(ep_pos)
                
                self.en_pesant_pawns[ep_pos] = enemy
        
        valid_moves |= (
            single_move |
            double_move |
            capturables |
            en_pesant
        )
        
        return valid_moves
    
    def promote(self):
        def destroyed(edit: PromoteEdit):
            self.board.temp_draws.remove(edit)
            self.board.temp_updates.remove(edit)
            
            self.board.pause_event = False
        
        promote_edit = PromoteEdit(
            self.board,
            self.board.BLOCK_SIZE,
            self._promote,
            self.is_white,
            self.board.board_style,
            self.piece_style,
            self._O,
            {"Q": Queen, "R": Rook, "B": Bishop, "N": Knight},
            {("midtop" if self.pos[1] == 0 else "midbottom"): (self.pos[0] * self.get_width() + self.get_width() / 2, (0 if self.pos[1] == 0 else self.board.get_height()))},
            destroyed
        )
        
        self.board.temp_draws.append(promote_edit)
        self.board.temp_updates.append(promote_edit)
        
        self.board.pause_event = True


class Board(Base):
    def __init__(self, screen: pygame.Surface):
        super().__init__((min(screen.get_size()), min(screen.get_size())), screen, {"center": (screen.get_width() / 2, screen.get_height() / 2)})
        
        self.BLOCK_SIZE = self.get_width() / 8, self.get_height() / 8
        
        self.moves = []
        self.captures = []
        
        self._turn_tracker = True
        self._move_selected = False
        
        self._prev_moves = [None, None, None]
        
        self.is_check = False
        self.pause_event = False
        
        self.focus_piece = None
        self.board_style = None
        
        self.background = pygame.Surface(self.get_size())
        
        self.focus_overlay_surface = pygame.Surface(self.BLOCK_SIZE, pygame.SRCALPHA)
        self.focus_overlay_surface.fill("darkgrey")
        self.focus_overlay_surface.set_alpha(125)
        
        self.capture_overlay_surface = pygame.Surface(self.BLOCK_SIZE, pygame.SRCALPHA)
        self.capture_overlay_surface.fill("red")
        self.capture_overlay_surface.set_alpha(150)
        
        self.temp_draws: list[Piece] = []
        self.temp_updates: list[Piece] = []
    
    def _no_focus(self):
        self.focus_piece = None
    
    def _piece_placed(self, piece: Piece):
        self._turn_tracker = not self._turn_tracker
        
        piece.update_kill_zones()
        
        self._prev_moves[1] = piece.pos
        self._prev_moves[2] = self._prev_moves[0]
        self._prev_moves[0] = None
        
        for e_pieces in self.pieces:
            e_pieces.update_kill_zones()

        self.moves.append((self._prev_moves[0], piece.pos))
    
    def set_data(
        self,
        white_pieces: dict[bytes, Piece],
        black_pieces: dict[bytes, Piece],
        white_king: King,
        black_king: King
    ):
        self.white_pieces = white_pieces
        self.black_pieces = black_pieces
        
        self._white_king = white_king
        self._black_king = black_king
        
        self.pieces = set(list(self.white_pieces.values()) + list(self.black_pieces.values()))
        
        for piece in self.pieces:
            piece._init()
            piece.update_valid_moves()
            piece.update_kill_zones()
    
    def remove_piece(self, piece: Piece):
        team_pieces = self.get_team_pieces(piece.is_white)
        
        team_pieces.pop(piece.pos)
        self.pieces.remove(piece)
        
        piece.pos = None
    
    def capture_piece(self, piece: Piece):
        self.remove_piece(piece)
        
        self.captures.append(piece)
    
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
    
    def set_piece_style(self, style: str):
        for piece in self.pieces:
            piece.set_skin(style)
    
    def get_team_pieces(self, is_white: bool):
        return self.white_pieces if is_white else self.black_pieces
    
    def get_enemy_pieces(self, is_white: bool):
        return self.black_pieces if is_white else self.white_pieces
    
    def get_team_bits(self, is_white: bool):
        bits = 0
        
        if is_white:
            for pos in self.white_pieces:
                bits |= bit_byte_to_bits(pos)
        else:
            for pos in self.black_pieces:
                bits |= bit_byte_to_bits(pos)
        
        return bits
    
    def get_enemy_bits(self, is_white: bool):
        bits = 0
        
        if is_white:
            for pos in self.black_pieces:
                bits |= bit_byte_to_bits(pos)
        else:
            for pos in self.white_pieces:
                bits |= bit_byte_to_bits(pos)
        
        return bits
    
    def get_pathed_enemies(self, is_white: bool):
        enemies: list[Piece] = []
        
        if is_white:
            for piece in self.black_pieces.values():
                if isinstance(piece, (Queen, Rook, Bishop)):
                    enemies.append(piece)
        else:
            for piece in self.white_pieces.values():
                if isinstance(piece, (Queen, Rook, Bishop)):
                    enemies.append(piece)
        
        return enemies
    
    def get_pointed_enemies(self, is_white: bool):
        enemies: list[Piece] = []
        
        if is_white:
            for piece in self.black_pieces.values():
                if not isinstance(piece, (Queen, Rook, Bishop)):
                    enemies.append(piece)
        else:
            for piece in self.white_pieces.values():
                if not isinstance(piece, (Queen, Rook, Bishop)):
                    enemies.append(piece)
        
        return enemies
    
    def get_enemy_kill_zones(self, is_white: bool):
        bits = 0
        
        if is_white:
            for pieces in self.black_pieces.values():
                bits |= pieces.get_kill_zones()
        else:
            for pieces in self.white_pieces.values():
                bits |= pieces.get_kill_zones()
        
        return bits
    
    def get_team_king(self, is_white: bool):
        return self._white_king if is_white else self._black_king
    
    def get_enemy_king(self, is_white: bool):
        return self._black_king if is_white else self._white_king
    
    def do_pos_from_bits(self, bits, action: Callable[[int, int], None], *, _count = None):
        _count = _count or 0
        
        if bits:
            if bits % 2:
                action(7 - (_count % 8), 7 - (_count // 8))
            
            _count += 1
            
            self.do_pos_from_bits(bits >> 1, action, _count=_count)
    
    def event_handler(self, event):
        if not self.pause_event and event.type == pygame.MOUSEBUTTONDOWN:
            m_pos = event.pos[0] - self.rect.left, event.pos[1] - self.rect.top
            
            for piece in (self.white_pieces.values() if self._turn_tracker else self.black_pieces.values()):
                if piece.rect.collidepoint(m_pos) and piece != self.focus_piece:
                    piece.update_valid_moves()
                    
                    if piece.get_valid_moves():
                        self.focus_piece = piece
                        self._prev_moves[0] = self.focus_piece.pos
                        
                        self._move_selected = False
                    
                    break
            else:
                if self.focus_piece is not None:
                    pos = bytes([int(m_pos[0] // self.BLOCK_SIZE[0]), int(m_pos[1] // self.BLOCK_SIZE[1])])
                    
                    self.focus_piece.total_move(pos, self._piece_placed, self._no_focus)
                    self._move_selected = True
        
        for piece in self.temp_updates:
            piece.event_handler(event)
    
    def update(self):
        self.rect.center = (self.parent.get_width() / 2, self.parent.get_height() / 2)
        
        if self.focus_piece:
            self.focus_piece.update()
        
        for piece in self.temp_updates:
            piece.update()
    
    def draw(self):
        self.blit(self.background, (0, 0))
        
        for pos in self._prev_moves:
            if pos:
                self.blit(
                    self.focus_overlay_surface,
                    (pos[0] * self.BLOCK_SIZE[0], pos[1] * self.BLOCK_SIZE[1])
                )
        
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
                        self.capture_overlay_surface,
                        (x * self.BLOCK_SIZE[0], y * self.BLOCK_SIZE[1])
                    )
                )
            )
            
            self._move_selected = False
        
        for piece in (self.pieces - set([self.focus_piece])):
            piece.draw()
        
        for piece in self.temp_draws:
            piece.draw()
        
        if self.focus_piece:
            self.focus_piece.draw()
        
        return super().draw()


