import pygame
import sys
import random
from pygame.locals import *

import chara

import mojimoji # 半角⇄全角変換
import collections
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

# 1ページに表示する呪文の数
SPELL_SHOW_NUM = 8

# 画像の読み込み
imgBtlBG = pygame.image.load("image/btlbg.png")
imgEffect = [
    pygame.image.load("image/effect_a.png"), # 攻撃
    pygame.image.load("image/effect_b.png") # blaze
]

# 変数の宣言
idx = 0
tmr = 0
fl_max = 1 # 最高到達階層 タイトル画面に表示

party = 1 # パーティーの数
potion = 0 # ポーションを使える回数（使うと全快する）
blazegem = 0 # blazeを使える回数

monster = [] # 敵のオブジェクト
dead_monster = [] # 倒した敵のオブジェクト
emy_step = 0 # 敵が攻撃する時の動きの大きさ（前に出るステップの大きさ）
emy_blink = 0 # 攻撃した時に敵を点滅させる（奇数:表示させない、偶数:表示させる）

dmg_eff = 0 # 攻撃を受けた時に画面をゆらす
btl_cmd_x = 0 # コマンド選択の時の"▶︎"のx位置
btl_cmd_y = 0 # コマンド選択の時の"▶︎"のy位置
btl_enemy = 0 # 敵選択の時の"▶︎"の位置
battle_order = {} # 戦闘の順番
sel_spell_x = 0 # コマンドで選択する呪文の列位置
sel_spell_y = 0 # コマンドで選択する呪文の行位置
sel_spell_p = 0 # コマンドで選択する呪文のページ
tmp_sel_spell_i = 0 # 選択中の呪文（添字）
sel_spell_i = -1 # 選択した呪文（添字）
spell_target_i = 0 # 呪文の対象（monsterの添字）

COMMAND = (("こうげき", "どうぐ"), ("じゅもん", "そうび"), ("ぼうぎょ", "にげる"))
TRE_NAME = ["Potion", "Blaze gem", "Food spoiled.", "Food +20", "Food +100"]

delay_speed = 500 # 止める時間(ms)
escape_rate = 100 # 逃げる確率(100は100%逃げる)

def draw_text(bg, txt, x, y, fnt, col): # 影付き文字の表示
    sur = fnt.render(txt, True, BLACK)
    bg.blit(sur, [x+1, y+2])
    sur = fnt.render(txt, True, col)
    bg.blit(sur, [x, y])

def init_battle(bg, mon_area): # 戦闘に入る準備をする
    global monster
    num_enemy = random.randint(1, 4) # 本番
    sum_x = 0
    list_typ = [] # 出現モンスターのNoを格納（A列）
    list_mon_area = chara.get_mon_area_list() # モンスター全体のエリアをリストで取
    # 該当するエリアのモンスターの要素(=モンスターのNo)を取得,mon_areaはプレイヤーのいる場所のエリア モンスターNoが入る
    list_rand = [i for i, tmp in enumerate(list_mon_area) if tmp.find(str(mon_area)) != -1]
    for _ in range(num_enemy):
        typ = random.choice(list_rand)
        list_typ.append(typ)

    dic_typ = collections.Counter(list_typ) # 重複を抽出
    i = 0
    for k, v in dic_typ.items(): # k:typ、v:数（typの種類がvの数だけ存在）
        for j in range(v):
            monster.append(chara.Monster(k))
            if v != 1: # 同じ種類が複数いる時
                monster[i].set_name(j)
            sum_x += monster[i].img.get_width() + 35 # 35はモンスターの間隔
            monster[i].set_y(bg.get_height()*0.6 - monster[i].img.get_height()) # どのモンスターも画面の7割が一番下に揃える
            i += 1
    sum_x -= 35 # 最後のモンスターは間隔を開ける必要がない
    x_i_i = bg.get_width()/2 - sum_x/2 # 一番左のモンスターのx座標
    monster[0].set_x(x_i_i) # 1匹目
    for i in range(num_enemy-1): # 2匹目
        x_i_i += monster[i].img.get_width() + 35 # 2匹目以降のモンスターの横幅+間隔 (2匹目は1匹目の横幅+間隔分をずらす)
        monster[i+1].set_x(x_i_i) # 各モンスターのx座標 2匹目以降なので i+1

    if len(dic_typ) == 1: # １種類はモンスター名
        if num_enemy == 1: # １匹はそのまま表示
            return monster[0].name
        else: # 複数は" A"や" B"などを消す
            return monster[0].name[:-2] # モンスターが１種類
    else: # 複数種類
        return "まもののむれ" # モンスターが複数種類

def mon_overlap():
    # 呪文の対象のモンスターNoを取得（list_typに格納する）
    mon_no = [] # モンスターNoを格納
    for mon in monster: # 既にfor文の中であり、monを使っているので、ここでmonは使えない
        mon_no.append(mon.num)
    dic_typ = collections.Counter(mon_no) # 重複を抽出（倒すとmonsterが変わるので毎回取得） 例{9:1、1:1}
    list_typ = list(dic_typ.keys()) # キーをリストで取得（キーがモンスターNo）list_typ[0]=9,list_typ[1]=1
    return list_typ
    
def draw_battle(bg, fnt, obj, player): # 戦闘画面の描画 obj:戦闘で行動中のオブジェクト
    global emy_blink, dmg_eff
    bx = 0
    by = 0
    if dmg_eff > 0:
        dmg_eff = dmg_eff - 1
        bx = random.randint(-20, 20)
        by = random.randint(-10, 10)
    bg.blit(imgBtlBG, [bx, by])
    for i, mon in enumerate(monster):
        display_flg = False # 生存しているモンスターを表示
        if mon.hp> 0 and btl_enemy != i:
            display_flg = True
        elif mon.hp> 0 and btl_enemy == i: # 攻撃対象のモンスターにエフェクト効果
            if emy_blink%2 == 0:
                display_flg = True
        if display_flg:
            if mon is obj: # 行動中のモンスターなら行動エフェクト
                bg.blit(mon.img, [mon.x, mon.y+emy_step])
            else:
                # 呪文対象を決める(idx=25)、呪文対象がモンスター単体の時、呪文対象を表示させない（点滅させる）
                if idx == 25:
                    if chara.get_spell_target(player.mas_spell[sel_spell_i]) == 2: # 呪文の対象がモンスター単体
                        if i == spell_target_i and tmr%5 == 0:
                            pass
                        else:
                            bg.blit(mon.img, [mon.x, mon.y])
                    elif chara.get_spell_target(player.mas_spell[sel_spell_i]) == 3: # 呪文の対象がモンスターグループ
                        list_typ = mon_overlap() # 例{9:1、1:1} → [9, 1]を取得
                        if mon.num == list_typ[spell_target_i] and tmr%5 == 0: # モンスターNoとキーが一致したら呪文の対象モンスター
                            pass
                        else:
                            bg.blit(mon.img, [mon.x, mon.y])
                    elif chara.get_spell_target(player.mas_spell[sel_spell_i]) == 4: # 呪文の対象がモンスター全体
                        if tmr%5 == 0:
                            pass
                        else:
                            bg.blit(mon.img, [mon.x, mon.y])
                    else: # 回復系
                        bg.blit(mon.img, [mon.x, mon.y])
                else:
                    bg.blit(mon.img, [mon.x, mon.y])


            # 敵の体力を表示するバー
            x_i = mon.x + mon.img.get_width()/2 - 100 # 体力バーのx座標
            x_w = 200 # 体力バーの幅
            y_i = bg.get_height()*0.6 + 10 # モンスター表示の一番下（画面の７割）
            y_h = 10
            pygame.draw.rect(bg, WHITE, [x_i-2, y_i-2, x_w+4, y_h+4])
            pygame.draw.rect(bg, BLACK, [x_i, y_i, x_w, y_h])
            if mon.hp > 0:
                pygame.draw.rect(bg, (0,128,255), [x_i, y_i, x_w*mon.hp/mon.maxhp, y_h]) # 残り体力

    if emy_blink > 0:
        emy_blink = emy_blink - 1

    # プレイヤーのパラメータ表示
    x_i = int(bg.get_width()/4) # x座標の開始位置
    x_w = int(bg.get_width()/8) # 幅
    y_i = 20 # y座標の開始位置
    y_h = 120 # 高さ
    x_i_t = x_i+x_w/2-50 # テキストのx座標の開始位置
    if party == 1: # 一人の時の全体の表示幅
        x_w *= 1
    col = WHITE
    if player.hp < player.maxhp/4:
        col = DANGER
    elif player.hp < player.maxhp/2:
        col = WARNING
    pygame.draw.rect(bg, col, [x_i, y_i, x_w, y_h], 2, 5)
    pygame.draw.line(bg, col, [x_i, y_i+33], [x_i+x_w-1, y_i+33], 2) # -1がないと少し出る

    # 名前の表示（回復呪文の対象を選択中の時は点滅）
    if idx == 25 and chara.get_spell_target(player.mas_spell[sel_spell_i]) == 0: # 呪文の対象の選択中,呪文の対象が味方なら
        draw_text(bg, "{}".format(player.name), x_i_t, y_i+6, fnt, BLINK[tmr%6])
    else: # 呪文の対象の選択中でなければ
        draw_text(bg, "{}".format(player.name), x_i_t, y_i+6, fnt, col)
    if len(str(player.hp)) == 3:
        draw_text(bg, mojimoji.han_to_zen("H{}".format(player.hp)), x_i_t, y_i+36, fnt, col)
    elif len(str(player.hp)) == 2:
        draw_text(bg, mojimoji.han_to_zen("H {}".format(player.hp)), x_i_t, y_i+36, fnt, col)
    elif len(str(player.hp)) == 1:
        draw_text(bg, mojimoji.han_to_zen("H  {}".format(player.hp)), x_i_t, y_i+36, fnt, col)

    if len(str(player.mp)) == 3:
        draw_text(bg, mojimoji.han_to_zen("M{}".format(player.mp)), x_i_t, y_i+66, fnt, col)
    elif len(str(player.mp)) == 2:
        draw_text(bg, mojimoji.han_to_zen("M {}".format(player.mp)), x_i_t, y_i+66, fnt, col)
    elif len(str(player.mp)) == 1:
        draw_text(bg, mojimoji.han_to_zen("M  {}".format(player.mp)), x_i_t, y_i+66, fnt, col)
    
    if len(str(player.lv)) == 2:
        draw_text(bg, mojimoji.han_to_zen("L:{}".format(player.lv)), x_i_t, y_i+96, fnt, col)
    elif len(str(player.lv)) == 1:
        draw_text(bg, mojimoji.han_to_zen("L: {}".format(player.lv)), x_i_t, y_i+96, fnt, col)

    if idx == 11 or idx == 19: # コマンド選択 or モンスター選択（攻撃）
        # コマンド表示
        x_i = 50 # x座標の開始位置
        x_w = bg.get_width()*0.4
        y_i = bg.get_height()*0.6 + 40
        y_h = bg.get_height()*0.4 - 40 # 高さ
        if len(player.name) <= 2:
            x_i_t = x_i+x_w/2-25 # テキストのx座標の開始位置
        else:
            x_i_t = x_i+x_w/2-50 # テキストのx座標の開始位置
        y_i_t = y_i + 6
        pygame.draw.rect(bg, col, [x_i, y_i, x_w, y_h], 2, 5)
        pygame.draw.line(bg, col, [x_i, y_i+33], [x_i+x_w-1, y_i+33], 2) # -1がないと少し出る
        draw_text(bg, "{}".format(player.name), x_i_t, y_i_t, fnt, col)

        for i in range(3):
            for j in range(2):
                draw_text(bg, COMMAND[i][j], x_i+50+j*x_w/2, y_i+70+i*60, fnt, col)
        if idx == 11:
            if tmr%5 != 0:
                draw_text(bg, "▶︎", x_i+btl_cmd_x*x_w/2, y_i+70+btl_cmd_y*60, fnt, col)
        
        # 敵の名前表示
        x_i = bg.get_width()*0.4 + 60 # x座標の開始位置
        x_w = bg.get_width()*0.6 - 100 # 100は両端の50の合計
        y_i = bg.get_height()*0.6 + 40
        y_h = bg.get_height()*0.1 - 10 # 高さ(敵の名前1個分の高さ：62)
        x_i_t = x_i + 50 # テキストのx座標の開始位置
        y_i_t = y_i + 21 # テキストのy座標の開始位置 20+21+21=62の21
        pygame.draw.rect(bg, col, [x_i, y_i, x_w, y_h*len(monster)], 2, 5) # 枠
        for i, mon in enumerate(monster):
            draw_text(bg, "{}".format(mon.name), x_i_t, y_i_t+y_h*i, fnt, col) # font:20(20+21+21=62)
        if idx == 19:
            if tmr%5 != 0:
                draw_text(bg, "▶︎", x_i_t-50, y_i_t+y_h*btl_enemy, fnt, col) # btl_nenmy(モンスターの名前の位置)

    elif idx == 21 or idx == 25:
        # 呪文の表示
        x_i = 50 # x座標の開始位置
        x_w = bg.get_width()*0.7 - 50 # 幅（左端の50を引いた）
        y_i = bg.get_height()*0.6 + 40 # 6割+40のところからメッセージ枠を出す
        y_h = bg.get_height()*0.1 - 10 # 高さ（一個分の高さ）
        x_i_t = x_i + 50 # テキストのx座標の開始位置
        y_i_t = y_i + 21 # テキストのy座標の開始位置 20+21+21=62の21
        pygame.draw.rect(bg, col, [x_i, y_i, x_w, y_h*4], 2, 5)
        if (sel_spell_p+1)*SPELL_SHOW_NUM > len(player.mas_spell):
            end_i = len(player.mas_spell)
        else:
            end_i = (sel_spell_p+1)*SPELL_SHOW_NUM
        for i, spell in enumerate(player.mas_spell[sel_spell_p*SPELL_SHOW_NUM:end_i]): # 途中から最後まで表示
            if i%2 == 0: # 1列目
                draw_text(bg, "{}".format(spell), x_i_t, y_i_t+y_h*int(i/2), fnt, col)
            else: # 2列目
                draw_text(bg, "{}".format(spell), x_i_t+int(x_w/2), y_i_t+y_h*int(i/2), fnt, col)
        if tmr%5 != 0:
            draw_text(bg, "▶︎", x_i_t-50+int(x_w/2)*sel_spell_x, y_i_t+y_h*sel_spell_y, fnt, col)

        # 呪文の説明の表示
        x_i = bg.get_width()*0.7 + 5 # x座標の開始位置
        x_w = bg.get_width()*0.3 - 35 # 幅
        y_i = bg.get_height()*0.6 + 40 # 6割+40のところからメッセージ枠を出す
        y_h = bg.get_height()*0.1 - 10 # 高さ（一個分の高さ）
        x_i_t = x_i + 20 # テキストのx座標の開始位置
        y_i_t = y_i + 21 # テキストのy座標の開始位置 20+21+21=62の21
        pygame.draw.rect(bg, col, [x_i, y_i, x_w, y_h*4], 2, 5)
        pygame.draw.line(bg, col, [x_i, bg.get_height()*0.9], [x_i+x_w-1, bg.get_height()*0.9], 2) # -1がないと少し出る
        # 呪文の説明
        tmp_explain = chara.get_spell_explain(player.mas_spell[tmp_sel_spell_i]).split("\n")
        for i, tmp in enumerate(tmp_explain):
            draw_text(bg, "{}".format(tmp), x_i_t, y_i_t+y_h*i, fnt, col)
        # 呪文の消費MP/残りMP
        draw_text(bg, "{}/{}".format(chara.get_spell_usemp(player.mas_spell[tmp_sel_spell_i]), player.maxmp), x_i_t, bg.get_height()*0.9+20, fnt, col)
        
    else:
        # 戦闘メッセージ表示
        x_i = 50 # x座標の開始位置
        x_w = bg.get_width() - 100 # 幅（両端の50を引いたのが幅）
        y_i = bg.get_height()*0.6 + 40 # 6割+40のところからメッセージ枠を出す
        y_h = bg.get_height()*0.4 - 40 # 高さ
        pygame.draw.rect(bg, col, [x_i, y_i, x_w, y_h], 2, 5)

        for i in range(5): # 戦闘メッセージの表示
            draw_text(bg, message[i], x_i+10, y_i+10+i*40, fnt, col)


def battle_command(bg, key): # コマンドの入力と表示
    global btl_cmd_x, btl_cmd_y
    ent = False # Trueで返すと選択したコマンド(btl_cmd)を実行する
    if key[K_UP] and btl_cmd_y > 0: # ↑キー
        btl_cmd_y -= 1
    elif key[K_DOWN] and btl_cmd_y < 2: # ↓キー
        btl_cmd_y += 1
    elif key[K_LEFT] and btl_cmd_x > 0: # ←キー
        btl_cmd_x -= 1
    elif key[K_RIGHT] and btl_cmd_x < 1: # →キー
        btl_cmd_x += 1
    elif key[K_SPACE] or key[K_RETURN]: # 決定s
        ent = True
    return ent

def attack_select(bg, key): # 物理攻撃の対象を選択
    global idx, btl_enemy
    ent = False
    if key[K_UP] and btl_enemy > 0: # ↑キー
        btl_enemy -= 1
    elif key[K_DOWN] and btl_enemy < len(monster)-1: # ↓キー
        btl_enemy += 1
    elif key[K_SPACE] or key[K_RETURN]: # 決定
        ent = True
    elif key[K_b]: # キャンセル
        idx = 11
    return ent

def spell_select(bg, key, player): # 呪文を選択
    global idx, sel_spell_x, sel_spell_y, sel_spell_p, tmp_sel_spell_i, sel_spell_i
    ent = False
    tmp_sel_spell_i = sel_spell_x+sel_spell_y*2+sel_spell_p*SPELL_SHOW_NUM # 選択している呪文（player.mas_spellの添字）
    max_p = len(player.mas_spell)//SPELL_SHOW_NUM # 呪文表示の最大のページ　８で割った商（整数）
    # 何ページ目かを取得する（左右の限界はそれ）
    # 列は２列
    if key[K_UP] and sel_spell_y > 0: # ↑キー
        sel_spell_y -= 1
    elif key[K_DOWN] and sel_spell_y < 3 and tmp_sel_spell_i+2 < len(player.mas_spell): # ↓キー  sel_spell_xとsel_spell_yの初期値は0(条件に=は入らない)
        sel_spell_y += 1
    elif key[K_LEFT] and sel_spell_x > 0: # ←キー
        sel_spell_x -= 1
    elif key[K_LEFT] and sel_spell_x == 0 and sel_spell_p > 0: # ←キー ページが0より大きければページを変える
        sel_spell_x = 1
        sel_spell_p -= 1
    elif key[K_LEFT] and sel_spell_x == 0 and sel_spell_p == 0: # ←キー ページが0の場合、maxにする
        sel_spell_x = 1
        sel_spell_p = max_p
        # ページ遷移後に覚えた呪文のmax数を超えたか
        # 列の確認・修正
        tmp_sel_spell_i = sel_spell_x+sel_spell_y*2+sel_spell_p*SPELL_SHOW_NUM
        if tmp_sel_spell_i >= len(player.mas_spell): # sel_spell_xは0始まりなので=がいる
            if len(player.mas_spell)%2 != 0: # 呪文の数が奇数の時は列を1列目にする
                sel_spell_x = 0
        # 行の確認・修正
        while True:
            tmp_sel_spell_i = sel_spell_x+sel_spell_y*2+sel_spell_p*SPELL_SHOW_NUM
            if tmp_sel_spell_i > len(player.mas_spell):
                sel_spell_y -= 1
            else:
                break
    elif key[K_RIGHT] and sel_spell_x < 1 and tmp_sel_spell_i+1 < len(player.mas_spell): # →キー sel_spell_xとsel_spell_yの初期値は0(条件に=は入らない)
        sel_spell_x += 1
    elif key[K_RIGHT] and sel_spell_x == 1 and sel_spell_p < max_p: # →キー ページが最大でなければページを変える
        sel_spell_x = 0
        sel_spell_p += 1
        # ページ遷移後に覚えた呪文のmax数を超えたか、超えていれば行を少なくする
        while True:
            tmp_sel_spell_i = sel_spell_x+sel_spell_y*2+sel_spell_p*SPELL_SHOW_NUM
            if tmp_sel_spell_i >= len(player.mas_spell): # sel_spell_xが0始まりなので=がいる
                sel_spell_y -= 1
            else:
                break
    elif key[K_RIGHT] and sel_spell_p == max_p: # →キー ページが最大の場合、0にする。 奇数の時にページ遷移しないので「sel_spell_x == 1」はいらない（ページ遷移しない時の「sel_spell_x == 0」は２つ上で判定するのでここに来ない）
        sel_spell_x = 0
        sel_spell_p = 0
    elif key[K_SPACE] or key[K_RETURN]: # 決定
        sel_spell_i = tmp_sel_spell_i
        ent = True
    elif key[K_b]: # キャンセル
        idx = 11 # idx=11でsel_spell_x,y,pが0になる(tmp_sel_spell_iが0になる)
    return ent

def spell_target_select(bg, key, player): # 呪文の対象を選択
    global idx, spell_target_i
    ent = False
    if chara.get_spell_target(player.mas_spell[sel_spell_i]) <= 1: # 呪文の対象が味方、味方が複数にした時は味方単体の時に選択できるようにする（party）
        if key[K_SPACE] or key[K_RETURN]: # 決定
            ent = True
    elif chara.get_spell_target(player.mas_spell[sel_spell_i]) == 2: # 呪文の対象がモンスター単体
        if key[K_LEFT] and spell_target_i > 0: # ←キー
            spell_target_i -= 1
        elif key[K_RIGHT] and spell_target_i < len(monster)-1: # →キー
            spell_target_i += 1
        elif key[K_SPACE] or key[K_RETURN]: # 決定
            ent = True
    elif chara.get_spell_target(player.mas_spell[sel_spell_i]) == 3: # 呪文の対象がモンスターグループ
        list_typ = mon_overlap()
        if key[K_LEFT] and spell_target_i > 0: # ←キー
            spell_target_i -= 1
        elif key[K_RIGHT] and spell_target_i < len(list_typ)-1: # →キー
            spell_target_i += 1
        elif key[K_SPACE] or key[K_RETURN]: # 決定
            ent = True
    elif chara.get_spell_target(player.mas_spell[sel_spell_i]) == 4: # 呪文の対象がモンスター全体
        if key[K_SPACE] or key[K_RETURN]: # 決定
            ent = True
    if key[K_b]: # キャンセル
        idx = 21 # idx=21 で spell_target_i=0にしている
    return ent

def check_spell_effect(player):
    list_tmp = []
    list_tmp.extend([player])
    list_tmp.extend(monster)
    check_message = []
    for obj in list_tmp:
        if obj.turn_sukara != 0:
            obj.turn_sukara -= 1
            if obj.turn_sukara == 0:
                check_message.append(obj.name + " のスカラ効果が消えた！")
                obj.invalid_sukara() # スカラ効果を消す
                obj.check_dfs()
        if obj.turn_rukani != 0:
            obj.turn_rukani -= 1
            if obj.turn_rukani == 0:
                check_message.append(obj.name + " のルカニ効果が消えた！")
                obj.invalid_rukani() # ルカニ効果を消す
                obj.check_dfs()
        if obj.turn_baikiruto != 0:
            obj.turn_baikiruto -= 1
            if obj.turn_baikiruto == 0:
                check_message.append(obj.name + " のバイキルト効果が消えた！")
                obj.invalid_baikiruto() # バイキルト効果を消す
        if obj.turn_henatos != 0:
            obj.turn_henatos -= 1
            if obj.turn_henatos == 0:
                check_message.append(obj.name + " のヘナトス効果が消えた！")
                obj.invalid_henatos() # ヘナトス効果を消す
        if obj.turn_manusa != 0:
            obj.turn_manusa -= 1
            if obj.turn_manusa == 0:
                check_message.append(obj.name + " のマヌーサ効果が消えた！")
                obj.invalid_manusa() # マヌーサ効果を消す
        if obj.turn_sleep != 0:
            obj.turn_sleep -= 1
            if obj.turn_sleep == 0:
                check_message.append(obj.name + " はめをさました！")
                obj.invalid_sleep() # ラリホー効果を消す
    return check_message
    
def set_battle_turn(num, player): # 0:通常、1:先制攻撃、2:不意打ち
    global battle_order
    tmp_order = {}
    # 素早さの順に並べる（戦闘順）
    if num == 0 or num == 1:
        r = random.randint(66, 100)
        tmp_order[player] = int(player.quick * r/100)
    if num == 0 or num == 2:
        for mon in monster:
            r = random.randint(66, 100)
            tmp_order[mon] = int(mon.quick * r/100)
    # [(obj, atk), (ojb, atk), ...]のリストになる
    battle_order = sorted(tmp_order.items(), key=lambda x:x[1], reverse=True)

def get_battle_turn(player):
    global battle_order
    if not battle_order: # 全員行動したらプレイヤーのコマンド選択
        return None, 27 # 呪文効果の確認へ
    # [(obj, atk), (ojb, atk), ...]のリスト、[0][0]で先頭（ターン）のobjを取得
    turn_key = battle_order[0][0]
    battle_order.pop(0) # 先頭を削除

    return turn_key, turn_key.act

def del_battle_turn(obj1): # ターン内に気絶したオブエクトを削除（気絶したオブジェクトが攻撃しないように）
    for i, obj2 in enumerate(battle_order): # 行がobj2に入る, iはi行目
        if obj1 is obj2[0]: # obj2[0]は各行の1列目（オブジェクト）２列目は素早さ
            battle_order.pop(i) # i行目を削除

def do_attack(target, dmg, obj): # 物理攻撃、呪文攻撃にも使う
    tmp_exp = 0
    monster[target].hp -= dmg
    if monster[target].hp <= 0:
        monster[target].hp = 0
        set_message(obj.name + " は " + monster[target].name + " をやっつけた！")
        tmp_exp += monster[target].exp
    return tmp_exp

def check_monster():
    global idx, tmr
    for mon in reversed(monster): # 複数の時、逆から消さないと倒せないモンスターが出る
        if mon.hp == 0:
            del_battle_turn(mon) # ターンオブジェクトから消す（倒したモンスターは攻撃しない）
            dead_monster.append(mon) # 先に加える
            monster.remove(mon)
    if not monster: # 空だとFalseを返すので not monsterがTrueだと空
        idx = 16 # 勝利
        tmr = 0

# 戦闘メッセージの表示処理
message = [""]*5
def init_message():
    for i in range(5):
        message[i] = ""
    
def set_message(msg):
    for i in range(5):
        if message[i] == "":
            message[i] = msg
            return
    for i in range(4): # 下が最新のメッセージ
        message[i] = message[i+1]
    message[4] = msg

def main(screen, clock, font, fontS, player, area):
    global idx, tmr, fl_max
    global potion, blazegem
    global emy_step, emy_blink, dmg_eff
    global btl_cmd_x, btl_cmd_y, btl_enemy
    global sel_spell_x, sel_spell_y, sel_spell_p, sel_spell_i, spell_target_i

    idx = 10
    tmr = 0
    dmg = 0 # プレイヤーが与えるダメージ、受けるダメージ
    spell_blink = "" # 呪文演出
    lif_p = 0 # レベルアップ時の最大体力の上げ幅
    str_p = 0 # レベルアップ時の攻撃力の上げ幅

    turn_obj = "" # 戦闘で行動するオブジェクト
    btl_exp = 0 # 戦闘で獲得した経験値（逃げたら0）
    btl_start = 0 # 0:通常、1:先制攻撃、2:不意打ち
    mon_typ = "" # モンスターの種類が複数："まもののむれ"、１種類：モンスターの名前
    mon_area = area # プレイヤーのいる場所のモンスターエリア

    se = [ # 効果音とジングル
        pygame.mixer.Sound("sound/ohd_se_attack.ogg"),
        pygame.mixer.Sound("sound/ohd_se_blaze.ogg"),
        pygame.mixer.Sound("sound/ohd_se_potion.ogg"),
        pygame.mixer.Sound("sound/ohd_jin_gameover.ogg"),
        pygame.mixer.Sound("sound/ohd_jin_levup.ogg"),
        pygame.mixer.Sound("sound/ohd_jin_win.ogg")
    ]

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        tmr = tmr + 1
        key = pygame.key.get_pressed()


        if idx == 9: # ゲームオーバー
            if tmr == 10:
                monster.clear() # モンスターオブジェクトを削除
                dead_monster.clear()
                return 0

        elif idx == 10: # 戦闘開始
            if tmr == 1:
                mon_typ = init_battle(screen, mon_area)
                init_message()
            elif tmr <= 4:
                bx = (4-tmr)*220
                by = 0
                screen.blit(imgBtlBG, [bx, by]) # バトル画面を右から左へ挿入していく
                draw_text(screen, "Encounter!", 350, 200, font, WHITE)
            elif tmr == 5:
                set_message(monster[0].name + " が現れた！")
                draw_battle(screen, fontS, turn_obj, player)
            elif tmr == 6:
                if len(monster) >= 2:
                    set_message(monster[1].name + " が現れた！")
                    draw_battle(screen, fontS, turn_obj, player)
                    pygame.time.delay(delay_speed)
            elif tmr == 7:
                if len(monster) >= 3:
                    set_message(monster[2].name + " が現れた！")
                    draw_battle(screen, fontS, turn_obj, player)
                    pygame.time.delay(delay_speed)
            elif tmr == 8:
                if len(monster) == 4:
                    set_message(monster[3].name + " が現れた！")
                    draw_battle(screen, fontS, turn_obj, player)
                    pygame.time.delay(delay_speed)
            elif tmr == 9:
                btl_start = random.randint(1, 32)
                if btl_start == 1: # 先制攻撃
                    init_message()
                    if random.randint(0, 1) == 0:
                        set_message("しかし " + mon_typ + "は")
                        set_message("まだ こちらに きづいていない！")
                    else:
                        set_message("しかし " + mon_typ + "は")
                        set_message("おどろき とまどっている！")
                    draw_battle(screen, fontS, turn_obj, player)
                    pygame.time.delay(delay_speed)
                elif btl_start == 2: # 不意打ち
                    init_message()
                    if random.randint(0, 1) == 0:
                        set_message(mon_typ + "は")
                        set_message("いきなり おそいかかってきた！")
                    else:
                        set_message(mon_typ + "は")
                        set_message(player.name + "が みがまえるまえに")
                        set_message("おそいかかってきた！")
                    draw_battle(screen, fontS, turn_obj, player)
                    pygame.time.delay(delay_speed)
                else: # 通常攻撃
                    btl_start = 0
                    
            elif tmr <= 16:
                draw_battle(screen, fontS, turn_obj, player)
                pygame.time.delay(delay_speed)
                init_message()
                if btl_start == 2: # 表示時間の問題でここで改めて判定
                    idx = 23
                else:
                    idx = 11
                tmr = 0

        elif idx == 11: # プレイヤーのターン（入力待ち）
            btl_enemy = 0
            player.use_defense = False # ぼうぎょを元に戻す（ぼうぎょ効果を消す）（呪文効果が残っているか確認）
            player.check_dfs()

            draw_battle(screen, fontS, turn_obj, player)
            if battle_command(screen, key) == True:
                if COMMAND[btl_cmd_y][btl_cmd_x] == "こうげき":
                    idx = 19
                    tmr = 0
                if COMMAND[btl_cmd_y][btl_cmd_x] == "じゅもん":
                    idx = 21 # 呪文の選択
                    tmr = 0
                if COMMAND[btl_cmd_y][btl_cmd_x] == "ぼうぎょ":
                    player.act = 18 # get_battle_turnの戻り値idxを18
                    player.use_defense = True
                    player.check_dfs() # 選択した時点で防御力2倍（ターンが回ってきてからではない）
                    idx = 23
                    tmr = 0
                if COMMAND[btl_cmd_y][btl_cmd_x] == "にげる":
                    idx = 14
                    tmr = 0

                # コマンドの位置のリセット
                btl_cmd_x = 0
                btl_cmd_y = 0
                # 呪文位置のリセット
                sel_spell_x = 0
                sel_spell_y = 0
                sel_spell_p = 0

        elif idx == 19: # 敵の選択
            draw_battle(screen, fontS, turn_obj, player)
            if attack_select(screen, key) == True:
                player.act = 12 # get_battle_turnの戻り値idxを12
                idx = 23
                tmr = 0

        elif idx == 23: # ターンセット
            set_battle_turn(btl_start, player)
            for mon in monster:
                mon.set_monster_com()
            btl_start = 0 # 戦闘は通常に戻す
            idx = 24
        elif idx == 24: # ターン確認
            tmr = 0 # 0にしないと idx=12では battle_calに行かない()(ここに来た時点で+1されているので、ここに来る前に0にしても意味がない)
            turn_obj, idx = get_battle_turn(player)
        elif idx == 27: # 呪文効果の確認
            check_message = check_spell_effect(player) # 関数がないと全ての呪文効果ごとに↓を記載する必要がある
            for mes in check_message:
                set_message(mes)
                draw_battle(screen, fontS, turn_obj, player)
                pygame.display.update() # if turn_obj is None: にしてidxを11にするとここに来ない
                pygame.time.delay(delay_speed)
            init_message()
            if player.flag_sleep: # party
                idx = 23 # ターンセット（眠っている時はコマンド選択できない）
            else:
                idx = 11

        elif idx == 12: # プレイヤーの攻撃
            draw_battle(screen, fontS, turn_obj, player)
            if tmr == 1:
                set_message(turn_obj.name + " のこうげき！")
                dmg, get_message = player.attack(monster[btl_enemy])
            if 2 <= tmr and tmr <= 4:
                screen.blit(imgEffect[0], [monster[btl_enemy].x+monster[btl_enemy].img.get_width()-tmr*80, tmr*80])
            if tmr == 5:
                emy_blink = 5
                for mes in get_message:
                    set_message(mes) # ここにdpygame.time.delayを入れると emy_blink のエフェクトが止まってしまう
            if tmr == 11:
                tmp_exp = do_attack(btl_enemy, dmg, turn_obj)
                if dmg != 0 and tmp_exp == 0 and monster[btl_enemy].flag_sleep: # 攻撃を受けた かつ 生きている かつ 眠っている
                    if random.randint(0, 99) < 55:
                        monster[btl_enemy].invalid_sleep()
                        set_message(monster[btl_enemy].name + " はめをさました！")
                btl_exp += tmp_exp
                check_monster()
            if tmr == 16:
                init_message()
                idx = 24 # ターンの確認

        elif idx == 13: # 敵のターン、敵の攻撃
            draw_battle(screen, fontS, turn_obj, player)
            if tmr == 1:
                if turn_obj.skill[turn_obj.skill_no] == "攻撃":
                    dmg, message = turn_obj.attack(player)
                elif turn_obj.skill[turn_obj.skill_no] == "痛恨の一撃":
                    dmg, message = turn_obj.grief(player)
                set_message(message[0])
                emy_step = 30
            if tmr == 9:
                for i, mes in enumerate(message):
                    if i == 0:
                        continue
                    set_message(mes)
                if dmg > 0:
                    dmg_eff = 5
                else:
                    dmg_eff = 0
                emy_step = 0
            if tmr == 15: # party
                player.hp = player.hp - dmg
                if player.hp <= 0:
                    player.hp = 0
                    idx = 15 # 敗北
                    tmr = 0
                else:
                    if dmg != 0 and player.flag_sleep: # 攻撃を受けた かつ 生きている かつ 眠っている
                        if random.randint(0, 99) < 55:
                            player.invalid_sleep()
                            set_message(player.name + " はめをさました！")
            if tmr == 20:
                init_message()
                idx = 24 # ターンの確認

        elif idx == 14: # 逃げられる？
            draw_battle(screen, fontS, turn_obj, player)
            if tmr == 1:
                set_message(player.name + " は逃げ出した！")
            if tmr == 5:
                flag_s = True
                for mon in monster:
                    if not mon.flag_sleep:
                        flag_s = False
                        break
                if flag_s or btl_start == 1 or random.randint(0, 99) < escape_rate: # 全員寝ている か 先制攻撃 は逃げられる
                    idx = 22 # 戦闘終了
                else:
                    set_message("しかし、まわりこまれてしまった！")
            if tmr == 10:
                init_message()
                btl_start = 2 # 不意打ちと同じ状態にする
                idx = 23 # ターンセット
                tmr = 0
             
        elif idx == 15: # 敗北
            draw_battle(screen, fontS, turn_obj, player)
            if tmr == 1:
                pygame.mixer.music.stop()
                set_message(player.name + " は気絶した...")
            if tmr == 11:
                idx = 9 # ゲームオーバー
                tmr = 0

        elif idx == 16: # 勝利
            draw_battle(screen, fontS, turn_obj, player)
            if tmr == 1:
                if len(dead_monster) != 1: # １匹の時はいらない
                    set_message(player.name + " は " + mon_typ + " をやっつけた！")
                pygame.mixer.music.stop()
                # se[5].play()
                player.exp += btl_exp
            if tmr == 5:
                set_message(player.name + " は " + str(btl_exp) + "ポイントの けいけんちを かくとく！")
                if player.exp >= player.lv_exp:
                    idx = 17
                    tmr = 0
                
            if tmr == 10:
                idx = 22 # 戦闘終了

        elif idx == 17: # レベルアップ
            draw_battle(screen, fontS, turn_obj, player)
            if tmr == 5:
                set_message(player.name + " はレベルが上がった！")
                player.lv_up()
            if tmr == 21:
                init_message()
                set_message("最大HP："+str(player.maxhp))
            if tmr == 26:
                set_message("素早さ："+str(player.quick))
            if tmr == 30:
                set_message("攻撃力："+str(player.atk))
            if tmr == 34:
                set_message("防御力："+str(player.dfs))
            if tmr == 38:
                tmp_spell = player.master_spell()
                if tmp_spell != "":
                    set_message(tmp_spell + " を覚えた")
            if tmr == 40:
                if player.exp >= player.lv_exp:
                    idx = 17
                    tmr = 0
            if tmr == 45:
                idx = 22 # 戦闘終了
        
        elif idx == 18: # ぼうぎょ
            draw_battle(screen, fontS, turn_obj, player)
            if tmr == 1:
                set_message(turn_obj.name + "は みをまもっている。")
            if tmr == 5:
                init_message()
                idx = 24 # ターンの確認
        elif idx == 20: # Potion
            draw_battle(screen, fontS, turn_obj, player)
            if tmr == 1:
                set_message("Potion!")
            if tmr == 6:
                player.hp = player.maxhp
                potion = potion - 1
            if tmr == 11:
                idx = 13 # 敵のターン
                tmr = 0

        elif idx == 21: # コマンドで呪文を選択
            sel_spell_i = 0 # ▶︎の表示位置はsel_spell_x, sel_spell_y
            spell_target_i = 0
            draw_battle(screen, fontS, turn_obj, player)
            if spell_select(screen, key, player) == True:
                idx = 25
                tmr = 0

        elif idx == 22: # 戦闘終了
            idx = 1
            monster.clear() # モンスターオブジェクトを削除
            dead_monster.clear()
            btl_exp = 0
            player.spell_reset()
            return 1

        elif idx == 25: # 呪文の攻撃対象を決める
            draw_battle(screen, fontS, turn_obj, player)
            if spell_target_select(screen, key, player) == True:
                player.act = 26 # get_battle_turnの戻り値idxを26
                idx = 23
                tmr = 0
        elif idx == 26: # 呪文発動
            draw_battle(screen, fontS, turn_obj, player)
            
            spell_point = 0 # プレイヤーが与えるダメージ、受けるダメージ 呪文用
            if tmr == 1:
                spell_blink = chara.get_spell_blink(player.mas_spell[tmp_sel_spell_i]) # 呪文演出（いろ）
                spell_blink = spell_blink.split(",")
                set_message(turn_obj.name + " は " + turn_obj.mas_spell[sel_spell_i] + " となえた！")
            if 2 <= tmr and tmr <= 4:
                pygame.draw.rect(screen, spell_blink[tmr%3], [0, 0, screen.get_width(), screen.get_height()])
            if tmr == 8:
                if turn_obj.check_mp(turn_obj.mas_spell[sel_spell_i]): # mpが足りていたら
                    spell_target_no = chara.get_spell_target(turn_obj.mas_spell[sel_spell_i]) # 呪文の対象(0:味方単体,1:味方全員,2:敵単体,3:敵グループ,4:敵全体)
                    if spell_target_no == 0: # 呪文の対象が味方単体
                        spell_point, spell_message = turn_obj.use_spell(turn_obj.mas_spell[sel_spell_i], player, spell_target_no)
                        if spell_point != -1: # 回復系、-1は補助系
                            player.hp += spell_point
                            if player.hp > player.maxhp:
                                player.hp = player.maxhp
                        set_message(spell_message)
                    elif spell_target_no == 1: # 呪文の対象が味方全体(party)
                        pass
                    elif spell_target_no == 2: # 呪文の対象がモンスター単体
                        spell_point, spell_message = turn_obj.use_spell(turn_obj.mas_spell[sel_spell_i], monster[spell_target_i], spell_target_no)
                        set_message(spell_message)
                        if spell_point != -1: # 攻撃系、-1は補助系
                            btl_exp += do_attack(spell_target_i, spell_point, turn_obj)
                        check_monster()
                    elif spell_target_no == 3: # 呪文の対象がモンスターグループ
                        # 呪文の対象のモンスターNoを取得（list_typに格納する）して、対象モンスターNoの数を取得する→　dic_typ[list_typ[spell_target_i]]
                        # ↓対象オブジェクトも返すようにするか？
                        list_typ = mon_overlap() # 例{9:1、1:1}、→ [9, 1]を取得
                        for i, mon in enumerate(monster):
                            if mon.num == list_typ[spell_target_i]:
                                spell_point, spell_message = turn_obj.use_spell(turn_obj.mas_spell[sel_spell_i], mon, spell_target_no)
                                set_message(spell_message)
                                if spell_point != -1: # 攻撃系
                                    btl_exp += do_attack(i, spell_point, turn_obj)
                                draw_battle(screen, fontS, turn_obj, player)
                                pygame.display.update()
                                pygame.time.delay(delay_speed)
                        check_monster()
                    elif spell_target_no == 4: # 呪文の対象がモンスター全体
                        for i, mon in enumerate(monster):
                            spell_point, spell_message = turn_obj.use_spell(turn_obj.mas_spell[sel_spell_i], mon, spell_target_no)
                            set_message(spell_message)
                            btl_exp += do_attack(i, spell_point, turn_obj)
                            draw_battle(screen, fontS, turn_obj, player)
                            pygame.display.update()
                            pygame.time.delay(delay_speed)
                        check_monster()
                else:
                    set_message("しかし MPがたりない！")
           
            if tmr == 16:
                init_message()
                idx = 24 # ターンの確認

        elif idx == 28: # ラリホーが効いた
            draw_battle(screen, fontS, turn_obj, player)
            if tmr == 1:
                if turn_obj.flag_sleep: # 眠っている
                    set_message(turn_obj.name + "は ねむっている")
                else: # ラリホーは効いたけど、攻撃などで起きた
                    idx = 24 # 何も表示させない
            if tmr == 6:
                init_message()
                idx = 24
        elif idx == 29:
            draw_battle(screen, fontS, turn_obj, player)
            if tmr == 1:
                set_message(turn_obj.name + "は どうしていいのか　わからない！")
            if tmr == 6:
                init_message()
                idx = 24

        pygame.display.update()
        clock.tick(10)


