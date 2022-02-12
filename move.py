import pygame
import sys
import random
from pygame.locals import *

import mojimoji # 半角⇄全角変換

import os.path
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 色の定義
WHITE = (255, 255, 255)
WARNING = (255, 191, 0)
DANGER = (255, 101, 101)
BLACK = (0, 0, 0)
RED   = (255, 0, 0) # プレイヤーの体力・食料が僅かの時、ゲームオーバーの時
CYAN  = (0, 255, 255)
BLINK = [(224,255,255), (192,240,255), (128,224,255), (64,192,255), (128,224,255), (192,240,255)] # 選択中の戦闘コマンドなどを点滅させる

treasure = 0 # TRE_NAMEの添字 1,2,3：宝箱、4,5:繭

n_map = [[]] # 今いるマップを取得 4文字の文字列 前の2文字[:2]がモンスターエリア、後の2文字[2:]がマップ
map_w = 0
map_h = 0
M_WIDTH = 40 # 一マスの横幅
M_HEIGHT = 40 # 一マスの高さ
food = 1000 
potion = 0 # ポーションを使える回数（使うと全快する）
blazegem = 0 # blazeを使える回数
tmr = 0
area = 0 # 地図番号
talk_flag = False # 会話中か（会話中は動かない）
talk_end = False # 会話の最後か（aを押したら会話が終わりか）
talk_mes = [] # 会話の内容
talk_line = 0 # セリフの行数（talk_mesの何行目か）
talk_start = 0 # セリフを表示する最初の行数（会話の途中の場合は会話の途中の行数）
talk_yesno = False # yesnoクエスチョン中か
talk_yesno_i = 0 # yesnoクエスチョンの位置 0:はい、1：いいえ
rest_flag = False # 寝る選択をしたかどうか
cmd_flag = False # フィールドでコマンド画面を表示するか
cmd_x = 0 # コマンド選択の時の"▶︎"のx位置
cmd_y = 0 # コマンド選択の時の"▶︎"のy位置

imgWall = pygame.image.load("image/wall.png")
imgWall2 = pygame.image.load("image/wall2.png")
imgDark = pygame.image.load("image/dark.png")
imgPara = pygame.image.load("image/parameter.png")
imgItem = [
    pygame.image.load("image/potion.png"),
    pygame.image.load("image/blaze_gem.png"),
    pygame.image.load("image/spoiled.png"),
    pygame.image.load("image/apple.png"),
    pygame.image.load("image/meat.png")
]
imgFloor = [
    pygame.image.load("image/floor.png"),
    pygame.image.load("image/tbox.png"),
    pygame.image.load("image/cocoon.png"),
    pygame.image.load("image/stairs.png")
]
# タプルにすると大きさを変えられないのでリスト
imgmap = []
for i in range(129):
    imgmap.append(pygame.image.load("map/" + str(i) + ".png"))
STAND = [120, 121] # 台の画像(台の先の人に話せる)

imgperson1 = []
imgperson2 = []
for i in range(4):
    imgperson1.append(pygame.image.load("person/odd/" + str(i) + ".png"))
for i in range(4):
    imgperson2.append(pygame.image.load("person/even/" + str(i) + ".png"))

COMMAND = (("はなす", "じゅもん"), ("つよさ", "どうぐ"), ("そうび", "しらべる"))
TRE_NAME = ["Potion", "Blaze gem", "Food spoiled.", "Food +20", "Food +100"]

appear_rate = 90 # 敵が出る確率（0は0%）

def draw_map(bg, fnt, player, people): # ダンジョンを描画する
    bg.fill(BLACK)
    x_range = int(bg.get_width() / M_WIDTH) # 画面の横幅の分割数（for文のレンジ） 22
    y_range = int(bg.get_height() / M_HEIGHT) # 画面の高さの分割数（for文のレンジ） 18
    for y in range(-8, 10): # 高さの分割数に合わせる 18
        for x in range(-10, 12): # 幅の分割数に合わせる 22
            if player.x < 10:
                X = (x+player.x)*M_WIDTH
            elif player.x > map_w-12:
                # 画面に見えない左側を引いている（map_w-x_range）
                X = (x-(map_w-x_range)+player.x)*M_WIDTH
            else:
                X = (x+10)*M_WIDTH
            if player.y < 8:
                Y = (y+player.y)*M_HEIGHT
            elif player.y > map_h-12:
                Y = (y-(map_h-y_range)+player.y)*M_HEIGHT
            else:
                Y = (y+8)*M_HEIGHT
            dx = player.x + x
            dy = player.y + y
            if 0 <= dx and dx < map_w and 0 <= dy and dy < map_h:
                bg.blit(imgmap[int(n_map[dy][dx][2:])], [X, Y])
            else:
                if dx < 0: # 右側が見切れるので、見切れた分だけ表示させる
                    X = (x+player.x+x_range)*M_WIDTH
                    if dy < 0: # 下側が見切れるので、見切れた分だけ表示させる
                        Y = (y+player.y+y_range)*M_HEIGHT
                        bg.blit(imgmap[int(n_map[dy+y_range][dx+x_range][2:])], [X, Y])
                    elif dy >= map_h: # 上側が見切れるので、見切れた分だけ表示させる
                        Y = (y-(map_h-y_range)+player.y)*M_HEIGHT - bg.get_height()
                        bg.blit(imgmap[int(n_map[dy-y_range][dx+x_range][2:])], [X, Y])
                    else:
                        bg.blit(imgmap[int(n_map[dy][dx+x_range][2:])], [X, Y])
                elif dx >= map_w: # dx < map_wの部分は「if 0 <= dx and dx < map_w and 0 <= dy and dy < map_h:」で表示
                    # 画面に見えない左側を引いている（map_w-x_range）
                    # 画面左から途中を描画、途中から右側は「dx < map_w」で表示
                    X = (x-(map_w-x_range)+player.x)*M_WIDTH - bg.get_width()
                    if dy < 0:
                        Y = (y+player.y+y_range)*M_HEIGHT
                        bg.blit(imgmap[int(n_map[dy+y_range][dx-x_range][2:])], [X, Y])
                    elif dy >= map_h:
                        Y = (y-(map_h-y_range)+player.y)*M_HEIGHT - bg.get_height()
                        bg.blit(imgmap[int(n_map[dy-y_range][dx-x_range][2:])], [X, Y])
                    else:
                        bg.blit(imgmap[int(n_map[dy][dx-x_range][2:])], [X, Y])
                else:
                    if dy < 0:
                        Y = (y+player.y+y_range)*M_HEIGHT
                        bg.blit(imgmap[int(n_map[dy+y_range][dx][2:])], [X, Y])
                    elif dy >= map_h:
                        Y = (y-(map_h-y_range)+player.y)*M_HEIGHT - bg.get_height()
                        bg.blit(imgmap[int(n_map[dy-y_range][dx][2:])], [X, Y])
                    # else:は「if 0 <= dx and dx < map_w and 0 <= dy and dy < map_h:」

            for i in range(len(people.x)): # 人の表示
                if dy==people.y[i] and dx==people.x[i]:
                    if tmr%2 != 0:
                        bg.blit(imgperson1[int(people.pic[i])], [X, Y])
                    else:
                        bg.blit(imgperson2[int(people.pic[i])], [X, Y])
                    
            # x=0,y=0の時にplayerを表示することは変わらない
            if x == 0 and y == 0: # 主人公キャラの表示
                bg.blit(player.img[player.a], [X, Y]) # 元はY-40、-40があると1ズレる

    if talk_flag:
        draw_message(bg, fnt)
    if cmd_flag:
        draw_para(bg, fnt, player) # 主人公の能力を表示

def move_player(key, player, people): # 主人公の移動
    global tmr, food, potion, blazegem, treasure, area
    global talk_flag, talk_mes, talk_end, talk_start, talk_yesno, talk_yesno_i
    global cmd_flag, cmd_x, cmd_y

    # 方向キーで上下左右に移動
    x = player.x # 移動したかを確認する為に今の位置を保存
    y = player.y
    posi_flag = False # 行こうとしている先に人がいるかいないか（いたら移動できない）
    if not talk_flag: # 会話中でない時は動ける、会話できる
        if key[K_UP] == 1:
            if cmd_flag: # コマンド選択中
                if cmd_y > 0:
                    cmd_y -= 1
            else:
                player.d = 0
                if player.y > 0:
                    if int(n_map[player.y-1][player.x][2:]) < 101:
                        for i in range(len(people.x)): # 人と重ならないか
                            if player.y-1 == people.y[i] and player.x == people.x[i]:
                                posi_flag = True
                        if not posi_flag:
                            player.y = player.y - 1
        elif key[K_DOWN] == 1:
            if cmd_flag: # コマンド選択中
                if cmd_y < 2:
                    cmd_y += 1
            else:
                player.d = 1
                if player.y < map_h-1: # map_hになるとout of rangeになる
                    if int(n_map[player.y+1][player.x][2:]) < 101: # player.y+1なので、player.y=map_h-1の時out of rangeになる
                        for i in range(len(people.x)):
                            if player.y+1 == people.y[i] and player.x == people.x[i]:
                                posi_flag = True
                        if not posi_flag:
                            player.y = player.y + 1
        elif key[K_LEFT] == 1:
            if cmd_flag: # コマンド選択中
                if cmd_x > 0 :
                    cmd_x -= 1
            else:
                player.d = 2
                if player.x > 0:
                    if int(n_map[player.y][player.x-1][2:]) < 101:
                        for i in range(len(people.x)):
                            if player.y == people.y[i] and player.x-1 == people.x[i]:
                                posi_flag = True
                        if not posi_flag:
                            player.x = player.x - 1
        elif key[K_RIGHT] == 1:
            if cmd_flag: # コマンド選択中
                if cmd_x < 1:
                    cmd_x += 1
            else:
                player.d = 3
                if player.x < map_w-1:
                    if int(n_map[player.y][player.x+1][2:]) < 101:
                        for i in range(len(people.x)):
                            if player.y == people.y[i] and player.x+1 == people.x[i]:
                                posi_flag = True
                        if not posi_flag:
                            player.x = player.x + 1
        elif key[K_a] == 1:
            talk_flag, talk_mes = talk_judge(player, people)
            if not talk_flag:
                cmd_flag = True
        elif key[K_b] == 1:
            if cmd_flag:
                cmd_flag = False

    else: # 会話中
        if key[K_a] == 1:
            if talk_end: # 会話の最後でaを押したら会話終了（会話情報をリセット）
                talk_end = False
                talk_mes = []
                talk_flag = False
                talk_start = 0
                talk_yesno = False
            else: # 会話の途中でaを押したら続きの会話を表示する
                talk_start = talk_line + 1 # #pageの次の行から表示する
        if talk_yesno: # yesnoクエスチョン中
            if key[K_UP] == 1:
                talk_yesno_i = 0
            elif key[K_DOWN] == 1:
                talk_yesno_i = 1
            elif key[K_a] == 1:
                talk_start = talk_line
                if talk_yesno_i == 0:
                    while True:
                        talk_start += 1
                        if talk_mes[talk_start] == "#yes":
                            talk_start += 1
                            break
                elif talk_yesno_i == 1:
                    while True:
                        talk_start += 1
                        if talk_mes[talk_start] == "#no":
                            talk_start += 1
                            break
                talk_yesno_i = 0 # ▶︎をはいの位置に戻す（複数回、回答する時用）
                talk_yesno = False

    
    player.a = player.d*2 + tmr%2 # 0:上 1:下 2:左 3:右
    if player.x != x or player.y != y: # 移動したら食料の量と体力を計算
        # player.a = player.a + tmr%2 # 移動したら足踏みのアニメーション
        # n_map[y][x] = 0 # いた場所を0にする
        if food > 0:
            food = food - 1
            if player.hp < player.maxhp:
                player.hp = player.hp + 1
        else:
            player.hp = player.hp - 5
            if player.hp <= 0:
                player.hp = 0
                pygame.mixer.music.stop()
                tmr = 0
                return 9
        if int(n_map[player.y][player.x][:2]) != 99: # モンスターエリアが99は敵が出ない
            if random.randint(0, 99) < appear_rate: # 敵出現
                tmr = 0
                return 10
    if area == 0: # マップ
        if int(n_map[player.y][player.x][2:]) == 13 or int(n_map[player.y][player.x][2:]) == 14:
            area = 1
            return 11
    elif area == 1:
        if player.y == 23 and player.x == 3:
            area = 0 # マップ
            return 11
    return 1

def talk_judge(player, people):
    flag = False # 会話中か（会話中は動かない）
    mes = [] # 会話の内容
    if player.d == 0: # 上向きの時
        for i in range(len(people.x)): # 人の表示
            if people.y[i] == player.y-1 and people.x[i] == player.x:
                flag = True
                mes = people.talk[i].split("\n")
                break
            for std in STAND:
                if int(n_map[player.y-1][player.x][2:]) == std: # 自分がいるところより一個上に台がある時
                    if people.y[i] == player.y-2 and people.x[i] == player.x: # 自分がいるところより2個上に人がいれば話す
                        flag = True
                        mes = people.talk[i].split("\n")
                        break
    elif player.d == 1: # 下向きの時
        for i in range(len(people.x)): # 人の表示
            if people.y[i] == player.y+1 and people.x[i] == player.x:
                flag = True
                mes = people.talk[i].split("\n")
                break
            for std in STAND:
                if int(n_map[player.y+1][player.x][2:]) == std: # 自分がいるところより一個下に台がある時
                    if people.y[i] == player.y+2 and people.x[i] == player.x: # 自分がいるところより2個下に人がいれば話す
                        flag = True
                        mes = people.talk[i].split("\n")
                        break
    elif player.d == 2: # 左向きの時
        for i in range(len(people.x)): # 人の表示
            if people.y[i] == player.y and people.x[i] == player.x-1:
                flag = True
                mes = people.talk[i].split("\n")
                break
            for std in STAND:
                if int(n_map[player.y][player.x-1][2:]) == std: # 自分がいるところより一個左に台がある時
                    if people.y[i] == player.y and people.x[i] == player.x-2: # 自分がいるところより2個左に人がいれば話す
                        flag = True
                        mes = people.talk[i].split("\n")
                        break
    elif player.d == 3: # 右向きの時
        for i in range(len(people.x)): # 人の表示
            if people.y[i] == player.y and people.x[i] == player.x+1:
                flag = True
                mes = people.talk[i].split("\n")
                break
            for std in STAND:
                if int(n_map[player.y][player.x+1][2:]) == std: # 自分がいるところより一個右に台がある時
                    if people.y[i] == player.y and people.x[i] == player.x+2: # 自分がいるところより2個右に人がいれば話す
                        flag = True
                        mes = people.talk[i].split("\n")
                        break
    return flag, mes

def draw_message(bg, fnt):
    global talk_line, talk_end, talk_yesno, rest_flag
    # (880,720)
    col = WHITE
    x_i = bg.get_width()*0.1/2 # x座標の開始位置
    x_w = bg.get_width()*0.9 # 横幅
    y_i = bg.get_height()*0.6 # y座標の開始位置
    y_h = bg.get_height()*0.4-10 # 高さ
    x_i_t = x_i + 30 # テキストのx座標の開始位置
    y_i_t = y_i + 30 # テキストのy座標の開始位置
    pygame.draw.rect(bg, BLACK, [x_i, y_i, x_w, y_h], 0, 5) # 枠
    pygame.draw.rect(bg, col, [x_i, y_i, x_w, y_h], 2, 5) # 枠

    x_yesno_i = bg.get_width()*0.7 # x座標の開始位置
    x_yesno_w = bg.get_width()*0.2 # 横幅
    y_yesno_i = bg.get_height()*0.1 # y座標の開始位置
    y_yesno_h = bg.get_height()*0.15 # 高さ
    x_yesno_i_t = x_yesno_i + 60 # テキストのx座標の開始位置
    y_yesno_i_t = y_yesno_i + 30 # テキストのy座標の開始位置

    i = 0
    talk_line = talk_start
    while True:
        if talk_mes[talk_line] == "#end": # 会話の最後を表示している
            talk_end = True
            break
        elif talk_mes[talk_line] == "#page": # 会話の途中を表示している（会話の続きがある）
            if tmr%5 != 0: # 点滅
                draw_text(bg, "{}".format("▼"), x_i_t, y_i_t+30*i, fnt, col)
                i += 1
            break
        elif talk_mes[talk_line] == "#yesrest": # 休む
            rest_flag = True
            break
        elif talk_mes[talk_line] == "#yesno": # 会話の途中を表示している（会話の続きがある）、yesnoのの後には必ず#pageか#endを持ってくる必要がある
            pygame.draw.rect(bg, BLACK, [x_yesno_i, y_yesno_i, x_yesno_w, y_yesno_h], 0, 5) # 枠
            pygame.draw.rect(bg, col, [x_yesno_i, y_yesno_i, x_yesno_w, y_yesno_h], 2, 5) # 枠
            draw_text(bg, "{}".format("はい"), x_yesno_i_t, y_yesno_i_t, fnt, col)
            draw_text(bg, "{}".format("いいえ"), x_yesno_i_t, y_yesno_i_t+30, fnt, col)
            if tmr%5 != 0: # 点滅
                draw_text(bg, "{}".format("▶︎"), x_yesno_i_t-50, y_yesno_i_t+30*talk_yesno_i, fnt, col)
            talk_yesno = True
            break
        elif talk_mes[talk_line] == "#no": # yesを選択した時は#noの件を#pageか#endまで飛ばす
            while True:
                talk_line += 1
                if talk_mes[talk_line] == "#page":
                    if tmr%5 != 0: # 点滅
                        draw_text(bg, "{}".format("▼"), x_i_t, y_i_t+30*i, fnt, col)
                        i += 1
                    break
                elif talk_mes[talk_line] == "#end":
                    talk_end = True
                    break
            break # 外のwhileからbreak
        else:
            draw_text(bg, "{}".format(talk_mes[talk_line]), x_i_t, y_i_t+30*i, fnt, col)
            i += 1
        talk_line += 1

def draw_para(bg, fnt, player): # 主人公の能力を表示
    col = WHITE
    x_c_i = bg.get_width()*0.05 # x座標の開始位置
    x_c_w = bg.get_width()*0.4 # 横幅
    y_c_i = bg.get_height()*0.05 # y座標の開始位置
    y_c_h = bg.get_height()*0.25 # 高さ
    x_c_i_t = x_c_i + 50 # テキストのx座標の開始位置
    y_c_i_t = y_c_i + 30 # テキストのy座標の開始位置
    pygame.draw.rect(bg, BLACK, [x_c_i, y_c_i, x_c_w, y_c_h], 0, 5) # 枠
    pygame.draw.rect(bg, col, [x_c_i, y_c_i, x_c_w, y_c_h], 2, 5) # 枠

    for i in range(3):
        for j in range(2):
            draw_text(bg, COMMAND[i][j], x_c_i_t+j*x_c_w/2, y_c_i_t+i*50, fnt, col)
    if tmr%5 != 0:
        draw_text(bg, "▶︎", x_c_i_t-50+cmd_x*x_c_w/2, y_c_i_t+cmd_y*50, fnt, col)

    x_p_i = bg.get_width()*0.8 # x座標の開始位置
    x_p_w = bg.get_width()*0.15 # 横幅
    y_p_i = bg.get_height()*0.75 # y座標の開始位置
    y_p_h = bg.get_height()*0.25-20 # 高さ
    x_p_i_t = x_p_i + x_p_w/2 - 40 # テキストのx座標の開始位置
    y_p_i_t = y_p_i + 20 # テキストのy座標の開始位置
    pygame.draw.rect(bg, BLACK, [x_p_i, y_p_i, x_p_w, y_p_h], 0, 5) # 枠
    pygame.draw.rect(bg, col, [x_p_i, y_p_i, x_p_w, y_p_h], 2, 5) # 枠
    draw_text(bg, "{}".format(player.name), x_p_i_t, y_p_i_t, fnt, col)
    if len(str(player.hp)) == 3:
        draw_text(bg, mojimoji.han_to_zen("H{}".format(player.hp)), x_p_i_t, y_p_i_t+36, fnt, col)
    elif len(str(player.hp)) == 2:
        draw_text(bg, mojimoji.han_to_zen("H {}".format(player.hp)), x_p_i_t, y_p_i_t+36, fnt, col)
    elif len(str(player.hp)) == 1:
        draw_text(bg, mojimoji.han_to_zen("H  {}".format(player.hp)), x_p_i_t, y_p_i_t+36, fnt, col)

    if len(str(player.mp)) == 3:
        draw_text(bg, mojimoji.han_to_zen("M{}".format(player.mp)), x_p_i_t, y_p_i_t+66, fnt, col)
    elif len(str(player.mp)) == 2:
        draw_text(bg, mojimoji.han_to_zen("M {}".format(player.mp)), x_p_i_t, y_p_i_t+66, fnt, col)
    elif len(str(player.mp)) == 1:
        draw_text(bg, mojimoji.han_to_zen("M  {}".format(player.mp)), x_p_i_t, y_p_i_t+66, fnt, col)
    
    if len(str(player.lv)) == 2:
        draw_text(bg, mojimoji.han_to_zen("L:{}".format(player.lv)), x_p_i_t, y_p_i_t+96, fnt, col)
    elif len(str(player.lv)) == 1:
        draw_text(bg, mojimoji.han_to_zen("L: {}".format(player.lv)), x_p_i_t, y_p_i_t+96, fnt, col)

def draw_text(bg, txt, x, y, fnt, col): # 影付き文字の表示
    sur = fnt.render(txt, True, BLACK)
    bg.blit(sur, [x+1, y+2])
    sur = fnt.render(txt, True, col)
    bg.blit(sur, [x, y])

def main(screen, clock, font, fontS, use_map, player, people):
    global n_map, map_w, map_h, rest_flag, talk_start
    global tmr
    n_map = use_map
    map_w = len(n_map[0])
    map_h = len(n_map)
    idx = 1 # 歩く
    # 画像の大きさを変える
    for i, img in enumerate(imgmap):
        imgmap[i] = pygame.transform.scale(img, (M_WIDTH, M_HEIGHT))

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        tmr += 1
        key = pygame.key.get_pressed()

        if idx == 1:
            idx = move_player(key, player, people)
            draw_map(screen, fontS, player, people)
            if rest_flag:
                idx = 2
                tmr = 0
        elif idx == 2: # 画面切り替え（階段）
            draw_map(screen, fontS, player, people)
            if 1 <= tmr and tmr <= 5:
                h = 80*tmr
                pygame.draw.rect(screen, BLACK, [0, 0, 880, h]) # 上側を閉じていく
                pygame.draw.rect(screen, BLACK, [0, 720-h, 880, h]) # 下側を閉じていく
            if tmr == 5:
                if rest_flag: # 休んでいる時なら会話を進める
                    talk_start = talk_line + 1
                    player.rest()
            if 6 <= tmr and tmr <= 9:
                h = 80*(10-tmr)
                pygame.draw.rect(screen, BLACK, [0, 0, 880, h]) # 上側を開いていく
                pygame.draw.rect(screen, BLACK, [0, 720-h, 880, h]) # 下側を開いていく
            if tmr == 10:
                rest_flag = False
                idx = 1
                tmr = 0 # 一応

        elif idx == 3: # アイテム入手もしくはトラップ（宝箱・繭）
            draw_map(screen, fontS, player, people)
            screen.blit(imgItem[treasure], [320, 220]) # アイテム画像
            draw_text(screen, TRE_NAME[treasure], 380, 240, font, WHITE) # アイテムテキスト
            if tmr == 10:
                idx = 1
        elif idx == 9:
            if tmr <= 30:
                PL_TURN = [2, 4, 0, 6]
                player.a = PL_TURN[tmr%4] # プレイヤーを回転
                if tmr == 30:
                    player.a = 8 # 倒れた絵
                draw_map(screen, fontS, player, people)
            elif tmr == 31:
                draw_text(screen, "You died.", 360, 240, font, RED)
                draw_text(screen, "Game over.", 360, 380, font, RED)
            elif tmr == 80:
                return 0
        elif idx == 10: # 戦闘 モンスターエリアを返す
            return 10, int(n_map[player.y][player.x][:2])
        elif idx == 11: # マップ遷移
            return 2, area
        pygame.display.update()
        clock.tick(10)


