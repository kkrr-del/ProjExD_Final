import math
import random
import sys
import time

import pygame as pg

WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ
difficulty = 0  # ゲーム難易度初期化
stop = False  # ゲーム終了
objects = []  # ボタンリスト
records_list = 'final/records.txt'


def SE_load(filename):
    """
    第一引数に
    beam,explosion,gameover
    のいずれかを与えると効果音を再生する関数
    """
    if filename == "beam":
        pg.mixer.music.load("final/se/beam.wav")
        pg.mixer.music.play()
    if filename == "explosion":
        pg.mixer.music.load("final/se/explosion.wav")
        pg.mixer.music.play()
    if filename == "gameover":
        pg.mixer.music.load("final/se/gameover.wav")
        pg.mixer.music.play()


class Button:
    """
    ボタンを作成するクラス
    """

    def __init__(self, x, y, width, height, text, onclick):
        font = pg.font.SysFont("hg正楷書体pro", 70)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.onclick = onclick
        self.button_img = pg.Surface((self.width, self.height))
        self.button_rct = pg.Rect(self.x, self.y, self.width, self.height)
        self.button_txt = font.render(text, True, (20, 20, 20))
        objects.append(self)

    def update(self, screen: pg.Surface):
        mouse = pg.mouse.get_pos()  # マウスのイベント
        self.button_img.fill((255, 255, 255))
        if self.button_rct.collidepoint(mouse):
            self.button_img.fill((0, 102, 204))

            if pg.mouse.get_pressed(num_buttons=3)[0]:  # マウスを押すイベント
                self.button_img.fill((0, 102, 204))
                self.onclick()

        self.button_img.blit(
            self.button_txt,
            [
                self.button_rct.width / 2 - self.button_txt.get_rect().width / 2,
                self.button_rct.height / 2 - self.button_txt.get_rect().height / 2,
            ],
        )
        screen.blit(self.button_img, self.button_rct)


# 選択された難易度を確認する
def set_difficulty_simple():
    global difficulty
    difficulty = 1


def set_difficulty_normal():
    global difficulty
    difficulty = 2


def set_difficulty_hard():
    global difficulty
    difficulty = 4


def set_difficulty_adventure():
    global difficulty
    difficulty = 6


# ゲーム終了
def set_quit():
    global stop
    stop = True


def check_bound(obj: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か画面外かを判定し，真理値タプルを返す
    引数 obj:オブジェクト(爆弾,こうかとん,ビーム)SurfaceのRect
    戻り値:横方向,縦方向のはみ出し判定結果(画面内:True/画面外:False)
    """
    yoko, tate = True, True
    if obj.left < 0 or WIDTH < obj.right:  # 横方向のはみ出し判定
        yoko = False
    if obj.top < 0 or HEIGHT < obj.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て,dstがどこにあるかを計算し,方向ベクトルをタプルで返す
    引数1 org:爆弾SurfaceのRect
    引数2 dst:こうかとんSurfaceのRect
    戻り値:orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx - org.centerx, dst.centery - org.centery
    norm = math.sqrt(x_diff**2 + y_diff**2)
    return x_diff / norm, y_diff / norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """

    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num:こうかとん画像ファイル名の番号
        引数2 xy:こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"final/fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"
        self.hyper_life = -1

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num:こうかとん画像ファイル名の番号
        引数2 screen:画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"final/fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def change_state(self, state: str, hyper_life: int):
        """
        こうかとんの状態を切り替えるメソッド
        引数1 state :こうかとんの状態(normal or hyper)
        引数2 hyper_life : ハイパーモードの発動時間
        """
        self.state = state
        self.hyper_life = hyper_life

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst:押下キーの真理値リスト
        引数2 screen:画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                self.rect.move_ip(+self.speed * mv[0], +self.speed * mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if check_bound(self.rect) != (True, True):
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    self.rect.move_ip(-self.speed * mv[0], -self.speed * mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]

        if self.state == "hyper":
            self.image = pg.transform.laplacian(self.image)
        self.hyper_life -= 1
        if self.hyper_life < 0:
            self.change_state("normal", -1)

        screen.blit(self.image, self.rect)

    def get_direction(self) -> tuple[int, int]:
        return self.dire


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """

    colors = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
        (0, 255, 255),
    ]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy:爆弾を投下する敵機
        引数2 bird:攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        color = random.choice(__class__.colors)
        # 爆弾円の色：クラス変数からランダム選択
        self.image = pg.Surface((2 * rad, 2 * rad))
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery + emy.rect.height / 2
        if difficulty < 5:  # モードによる設定
            self.speed = 6 * difficulty  # 難易度によるスピード設定
        else:
            self.speed = 10

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen:画面Surface
        """
        self.rect.move_ip(+self.speed * self.vx, +self.speed * self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """

    def __init__(self, bird: Bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird:ビームを放つこうかとん
        """
        super().__init__()
        level = Level()
        self.vx, self.vy = bird.get_direction()
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(
            pg.image.load("final/fig/beam.png"), angle, 2.0
        )
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery + bird.rect.height * self.vy
        self.rect.centerx = bird.rect.centerx + bird.rect.width * self.vx
        self.speed = 10
        SE_load("beam")

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen:画面Surface
        """
        self.rect.move_ip(+self.speed * self.vx, +self.speed * self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """

    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj:爆発するBombまたは敵機インスタンス
        引数2 life:爆発時間
        """
        super().__init__()
        img = pg.image.load("final/fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life
        SE_load("explosion")

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life // 10 % 2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """

    imgs = [pg.image.load(f"final/fig/alien{i}.png") for i in range(1, 4)]

    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vy = +6
        self.bound = random.randint(50, HEIGHT / 2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動(降下)させる
        ランダムに決めた停止位置_boundまで降下したら,_stateを停止状態に変更する
        引数 screen:画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy


class Gravity(pg.sprite.Sprite):
    """
    重力球に関するクラス
    """

    colors = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
        (0, 255, 255),
    ]

    def __init__(self, bird: Bird, rad: int, life: int):
        """
        重力球Surfacewo生成する
        引数1 bird:重力球の中心となるこうかとん
        引数2 rad:重力球の半径
        引数3 life:発動時間
        """
        super().__init__()
        self.image = pg.Surface((2 * rad, 2 * rad))
        pg.draw.circle(self.image, (10, 10, 10), (rad, rad), rad)
        self.image.set_alpha(200)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()

        self.rect.centerx = bird.rect.centerx
        self.rect.centery = bird.rect.centery + bird.rect.height / 2
        self.life = life

    def update(self):
        """
        発動時間を1減算する
        """
        self.life -= 1
        if self.life < 0:
            self.kill()


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾:1点
    敵機:10点
    """

    def __init__(self):
        self.font = pg.font.SysFont("hg正楷書体pro", 50)
        self.color = (0, 0, 0)
        self.score = 0
        self.image = self.font.render(f"スコア： {self.score}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH - 1400, 200

    def score_up(self, add):
        self.score += add

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"スコア： {self.score}", 0, self.color)
        screen.blit(self.image, self.rect)


class High_Score_Game:
    """
    ゲーム中で記録を表示、更新するクラス
    """

    def __init__(self):
        self.font = pg.font.SysFont("hg正楷書体pro", 50)
        self.color = (0, 0, 0)
        with open(records_list, mode = 'r') as f:
            self.high_score = int(f.read())
        self.image = self.font.render(f"記録： {self.high_score}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH - 1400, 275
    def score_up(self, add):
        self.high_score += add
    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"記録： {self.high_score}", 0, self.color)
        screen.blit(self.image, self.rect)


class High_Score_Menu:
    """
    メニューで記録を表示、更新するクラス
    """

    def __init__(self):
        self.font = pg.font.SysFont("hg正楷書体pro", 50)
        self.color = (0, 0, 0)
        with open(records_list, mode = 'r') as f:
            self.high_score = int(f.read())
        self.image = self.font.render(f"記録： {self.high_score}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 780, 200
    def score_up(self, add):
        self.high_score += add
    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"記録： {self.high_score}", 0, self.color)
        screen.blit(self.image, self.rect)


class Shield(pg.sprite.Sprite):
    """
    防御壁に関するクラス
    """

    def __init__(self, bird: Bird, life: int):
        """
        防御壁を生成する
        引数1 bird: こうかとんのインスタンス
        引数2 life: 防御壁の発動時間
        """
        super().__init__()
        self.yoko, self.tate = bird.get_direction()
        self.image = pg.transform.rotozoom(
            pg.Surface((20, bird.rect.height * 2)), 0, 1.0
        )
        pg.draw.rect(self.image, (0, 0, 0), pg.Rect(0, 0, 20, bird.rect.height * 2))
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx + bird.rect.width * self.yoko
        self.rect.centery = bird.rect.centery + bird.rect.height * self.tate
        self.life = life

    def update(self):
        """
        防御壁の発動時間を1減算し、0未満になったらkill
        """
        self.life -= 1
        if self.life < 0:
            self.kill()


class CharLife:
    """
    キャラクター(こうかとん)の残機数に関するクラス
    """

    # LEVEL = {
    #     "初級": 3,
    #     "中級": 2,
    #     "上級": 1,
    # }

    def __init__(self, level: str):
        """
        ライフを作成する
        args1:ゲームの難易度
        """
        # フォント設定
        self.font = pg.font.SysFont("hg正楷書体pro", 40)
        self.color = (0, 0, 0)  # 色設定
        self.level = difficulty  # オブジェクトLEVELに応じた数字(life)
        self.life = "★" * self.level  # self.levelの数だけ★を作成
        self.image = self.font.render(f"残機：{self.life}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH - 1350, 50

    def life_kill(self):
        self.level -= 1
        self.life = "★" * self.level
        print(self.life, self.level)

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"残機：{self.life}", 0, self.color)
        screen.blit(self.image, self.rect)


class Level:
    """
    ゲームのレベルに関するクラス
    """

    def __init__(self):
        self.font = pg.font.SysFont("hg正楷書体pro", 50)
        self.color = (0, 0, 0)
        self.exp = 0
        self.lim = 10
        self.level = 1
        self.image = self.font.render(f"レベル： {self.level}", 0, self.color)

    def exp_up(self, add: int):
        """
        経験値,レベルの計算を行う
        """
        self.exp += add
        if self.exp >= self.lim:  # 経験値上限self.limを累積経験値self.expが超えたら
            self.level += 1  # レベルが一つ上がる
            self.exp -= self.lim
            self.lim += random.randint(1, 5)

    def update(self, screen: pg.surface):
        """
        レベルの表示の更新を行う
        """
        self.image = self.font.render(f"レベル： {self.level}", 0, self.color)
        screen.blit(self.image, (WIDTH - 1530, 100))


def game():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("final/fig/pg_bg.jpg")
    score = Score()
    high_score = High_Score_Game()
    if difficulty < 5:
        char_life = CharLife(difficulty)
    else:
        char_life = CharLife(1)
    expe = Level()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()

    exps = pg.sprite.Group()  # 爆発のグループ
    emys = pg.sprite.Group()  # 敵機のグループ
    exps = pg.sprite.Group()

    gras = pg.sprite.Group()

    shields = pg.sprite.Group()

    bgm = pg.mixer.Sound("final/se/bgm.wav")
    bgm.play()

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))

            if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
                if score.score > 50:
                    if score.score == high_score.high_score:
                        score.score_up(-50)
                        high_score.score_up(-50)
                    else:
                        score.score_up(-50)
                    gras.add(Gravity(bird, 200, 500))

            if event.type == pg.KEYDOWN and event.key == pg.K_LSHIFT:
                bird.speed = 20  # 高速化時speed：20

            if event.type == pg.KEYDOWN and event.key == pg.K_CAPSLOCK:
                if score.score > 50 and len(shields) == 0:
                    shields.add(Shield(bird, 400))
                    if score.score == high_score.high_score:
                        score.score -= 50
                        high_score.high_score -= 50
                    else:
                        score.score -= 50

            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT:
                if score.score > 100:
                    bird.change_state("hyper", 500)
                    if score.score == high_score.high_score:
                        score.score_up(-100)
                        high_score.score_up(-100)
                    else:
                        score.score_up(-100)

        screen.blit(bg_img, [0, 0])
        if difficulty < 5:  # モードによる設定
            if tmr % 200 == 0:
                # 難易度による敵機を出現させる
                for i in range(difficulty):
                    emys.add(Enemy())
        else:
            if tmr < 100:
                # 時間とともに難しくなるモード
                if tmr % 200 == 0:
                    emys.add(Enemy())
            else:
                if tmr % 200 == 0:
                    for i in range(tmr // 100):
                        emys.add(Enemy())

        for emy in emys:
            if difficulty < 5:  # モードによる設定
                if emy.state == "stop" and tmr * difficulty % emy.interval == 0:
                    # 敵機が停止状態に入ったら，難易度によるintervalに応じて爆弾投下
                    bombs.add(Bomb(emy, bird))
            else:
                if emy.state == "stop" and tmr % emy.interval == 0:
                    # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                    bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            expe.exp_up(3)  # 経験値3獲得
            if difficulty < 5:  # モードによる設定
                score.score_up(10 * difficulty)  # 難易度による点数アップ

            else:
                score.score_up(10 * (len(emys) + 1))  # 敵数による点数アップ

            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            expe.exp_up(1)  # 経験値1獲得
            if difficulty < 5:  # モードによる設定
                score.score_up(1 * difficulty)  # 難易度による点数アップ

            else:
                score.score_up(1 * (len(bombs) + 1))  # 爆弾数による点数アップ


        if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:
            if bird.state == "hyper":
                if difficulty < 5:
                    score.score_up(1 * difficulty)  # 難易度による点数アップ

                else:
                    score.score_up(1 * (len(bombs) + 1))  # 爆弾数による点数アップ  # 1点アップ
                continue
            if char_life.level > 1:
                char_life.life_kill()
                continue
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            """
            BGMを停止＆GameOverの効果音再生
            """
            SE_load(
                "gameover"
            )  # SE_load関数で第一引数に何の効果音か(beam,explosion,gameover)を与えてあげると効果音が流れる
            bgm.stop()  # GameOverになったらBGMを停止する
            """
            半透明な黒いrectを表示
            """
            image = pg.Surface((1600, 900))
            r = pg.draw.rect(image, pg.Color(0, 0, 0, 0), pg.Rect(0, 0, 1600, 900))
            image.set_alpha(200)
            screen.blit(image, r)
            """
            GameOver等の文字の表示
            """
            font1 = pg.font.SysFont(
                "hg正楷書体pro", 150
            )  # 第一引数でフォントの名前を選択し、第2引数でフォントサイズを記述
            font2 = pg.font.SysFont("hg正楷書体pro", 50)  # 第一引数でフォントの名前を選択し、第2引数でフォントサイズを記述
            text1 = font1.render("GameOver", True, (255, 0, 0))
            text2 = font2.render(f"得点は{score.score}点でした", True, (255, 0, 0))
            text3 = font2.render(f"記録は{high_score.high_score}点です", True, (255,0,0))
            screen.blit(text1, (450, 300)) #GameOverと450,300の位置に配置
            screen.blit(text2, (625, 475)) #scoreを625,450の位置に配置
            screen.blit(text3, (625, 550))

            pg.display.update()
            time.sleep(2)
            return

        for bomb in pg.sprite.groupcollide(bombs, gras, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            if difficulty < 5:  # モードによる設定
                score.score_up(1 * difficulty)  # 難易度による点数アップ

            else:
                score.score_up(1 * (len(bombs) + 1))  # 爆弾数による点数アップ

        for bomb in pg.sprite.groupcollide(bombs, shields, True, False).keys():
            exps.add(Explosion(bomb, 50))
            if difficulty < 5:  # モードによる設定
                score.score_up(1 * difficulty)  # 難易度による点数アップ

            else:
                score.score_up(1 * (len(bombs) + 1))  # 爆弾数による点数アップ

        if score.score >= high_score.high_score:
            high_score.high_score = score.score
            with open(records_list, mode = 'w') as f:
                f.write(str(high_score.high_score))

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)

        gras.update()
        gras.draw(screen)

        shields.update()
        shields.draw(screen)

        ##add char_life
        char_life.update(screen)

        score.update(screen)
        high_score.update(screen)
        expe.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


def main():
    global stop
    global difficulty

    # メニューの画像
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()
    
    menu_kokaton_1 = pg.transform.rotozoom(pg.image.load("final/fig/4.png"), 0, 2.5)
    sub_kokaton = pg.transform.rotozoom(pg.image.load("final/fig/3.png"), 0, 2.5)
    menu_kokaton_2 = pg.transform.flip(sub_kokaton, True, False)
    font = pg.font.SysFont("hg正楷書体pro", 100)
    title = font.render("真！こうかとん無双", 1, (0, 0, 0))
    

    while True:
        high_score = High_Score_Menu()
        screen.fill((117, 200, 236)) 
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
        # メニュー
        screen.blit(title, (350, 60))
        high_score.update(screen)
        pg.draw.rect(screen, (255, 255, 255), (600, 250, 400, 550))
        pg.draw.rect(screen, (0, 102, 204), (592, 242, 416, 566), 8)
        screen.blit(menu_kokaton_1, [1150, 665])
        screen.blit(menu_kokaton_2, [200, 100])
        # メニューのボタン
        Button(600, 250, 400, 100, "イージー", set_difficulty_simple)
        Button(600, 350, 400, 100, "ノーマル", set_difficulty_normal)
        Button(600, 450, 400, 100, "ハード", set_difficulty_hard)
        Button(600, 550, 400, 100, "エキストラ", set_difficulty_adventure)
        Button(600, 700, 400, 100, "終了", set_quit)
        for object in objects:
            object.update(screen)

        # ゲーム難易度を選択ボタンを押したら、ゲームスタート
        if difficulty >= 1:
            game()
            difficulty = 0

        # ゲーム終了ボタンを押したら、ゲーム終了
        if stop is True:
            return

        pg.display.update()
        clock.tick(1000)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
