import os
import random
import sys
import time
import pygame as pg

WIDTH = 1100
HEIGHT = 650
NUM_OF_BOMBS = 5   # 複数爆弾
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate

class Score:
    def __init__(self):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.value = 0
        self._render()
    def _render(self):
        self.img = self.font.render(f"スコア：{self.value}", True, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)
    def add(self, n: int = 1):
        self.value += n
        self._render()
    def update(self, screen: pg.Surface):
        screen.blit(self.img, self.rct)

class Bird:
    delta = {
        pg.K_UP: (0, -5), pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0), pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)
    imgs = {
        (+5, 0): img,
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),
        (-5, 0): img0,
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),
    }
    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
    def change_img(self, num: int, screen: pg.Surface):
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)
    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]; sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if sum_mv != [0, 0]:
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)

class Beam:
    """複数発対応：updateは生存(True)/消滅(False)を返す"""
    def __init__(self, bird:"Bird"):
        self.img = pg.image.load("fig/beam.png")
        self.rct = self.img.get_rect()
        self.rct.centery = bird.rct.centery
        self.rct.left = bird.rct.right
        self.vx, self.vy = +5, 0
    def update(self, screen: pg.Surface) -> bool:
        # 進めて描画、画面外に出たらFalse
        self.rct.move_ip(self.vx, self.vy)
        alive = check_bound(self.rct) == (True, True)
        if alive:
            screen.blit(self.img, self.rct)
        return alive

class Bomb:
    def __init__(self, color: tuple[int, int, int], rad: int):
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5
    def update(self, screen: pg.Surface):
        yoko, tate = check_bound(self.rct)
        if not yoko: self.vx *= -1
        if not tate: self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

def spawn_bomb() -> Bomb:
    color = random.choice([(255,0,0), (255,165,0), (255,105,180)])
    rad = random.choice([8, 10, 12])
    return Bomb(color, rad)

def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")

    bird = Bird((300, 200))
    bombs = [spawn_bomb() for _ in range(NUM_OF_BOMBS)]  # 複数爆弾
    beams: list[Beam] = []                                # ★ 複数ビーム
    score = Score()

    clock = pg.time.Clock()
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))                  # ★ 発射して追加

        screen.blit(bg_img, [0, 0])

        # こうかとん vs 爆弾（当たったらゲームオーバー）
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)
                pg.display.update()
                time.sleep(1)
                return

        # ビーム vs 爆弾（当たったペアをNoneに）
        for bi, bomb in enumerate(bombs):
            if bomb is None:
                continue
            for i, beam in enumerate(beams):
                if beam is None:
                    continue
                if beam.rct.colliderect(bomb.rct):
                    score.add(1)        # 1点加算
                    bombs[bi] = None    # 爆弾消去
                    beams[i]  = None    # ビーム消去
                    break               # 1弾に複数ヒットしない想定

        # リストからNoneを除去（スライドの指示）
        bombs = [b for b in bombs if b is not None]
        beams = [b for b in beams if b is not None]

        # 更新・描画
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)

        # 画面外に出たビームは update が False を返すので捨てる
        alive_beams = []
        for beam in beams:
            if beam.update(screen):
                alive_beams.append(beam)
        beams = alive_beams

        for bomb in bombs:
            bomb.update(screen)

        score.update(screen)
        pg.display.update()
        clock.tick(50)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
