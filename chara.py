import gspread
import pygame
import random
from pygame.locals import *

import os.path
os.chdir(os.path.dirname(os.path.abspath(__file__)))

#ServiceAccountCredentials：Googleの各サービスへアクセスできるservice変数を生成します。
from oauth2client.service_account import ServiceAccountCredentials 

#2つのAPIを記述しないとリフレッシュトークンを3600秒毎に発行し続けなければならない
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

#認証情報設定
#ダウンロードしたjsonファイル名をクレデンシャル変数に設定（秘密鍵、Pythonファイルから読み込みしやすい位置に置く）
credentials = ServiceAccountCredentials.from_json_keyfile_name('xxxxx.json', scope)

#OAuth2の資格情報を使用してGoogle APIにログインします。
gc = gspread.authorize(credentials)

#共有設定したスプレッドシートキーを変数[SPREADSHEET_KEY]に格納する。
SPREADSHEET_KEY = 'xxxxxx'

wb = gc.open_by_key(SPREADSHEET_KEY)
ws_chara = wb.worksheet("勇者")
ws_mon = wb.worksheet("モンスター")
ws_spell = wb.worksheet("呪文")
ws_person = wb.worksheet("人物")

chara1_name = ws_chara.acell('C2').value
chara1_maxhp = ws_chara.col_values(5) # E列
chara1_hp = ws_chara.acell('F2').value
chara1_maxmp = ws_chara.col_values(7) # G列
chara1_mp = ws_chara.acell('H2').value
chara1_quick = ws_chara.col_values(9) # I列
chara1_atk = ws_chara.col_values(10) # J列
chara1_dfs = ws_chara.col_values(11) # K列
chara1_exp = ws_chara.col_values(12) # L列
chara1_spell = ws_chara.col_values(13) # M列 覚える呪文

mon_name = ws_mon.col_values(2) # B列
mon_maxhp = ws_mon.col_values(4) # D列
mon_quick = ws_mon.col_values(8) # H列
mon_atk = ws_mon.col_values(9) # I列
mon_dfs = ws_mon.col_values(10) # J列
mon_exp = ws_mon.col_values(11) # K列　経験値
mon_area = ws_mon.col_values(12) # L列　エリア
mon_skill = ws_mon.col_values(13) # M列　特技

spell_name = ws_spell.col_values(1) # A列
spell_usemp = ws_spell.col_values(2) # B列
spell_lo = ws_spell.col_values(3) # C列
spell_up = ws_spell.col_values(4) # D列
spell_explain = ws_spell.col_values(5) # E列 呪文の説明
spell_target = ws_spell.col_values(6) # F列
spell_blink = ws_spell.col_values(7) # G列 呪文のいろ

spell_usemp_dict = {}
spell_lo_dict = {}
spell_up_dict = {}
spell_explain_dict = {}
spell_target_dict = {}
spell_blink_dict = {}

for i, tmp in enumerate(spell_name[1:], 1): # 呪文の性能を辞書型で取得
    spell_usemp_dict.setdefault(tmp, int(spell_usemp[i]))
    spell_lo_dict.setdefault(tmp, int(spell_lo[i]))
    spell_up_dict.setdefault(tmp, int(spell_up[i]))
    spell_explain_dict.setdefault(tmp, spell_explain[i])
    spell_target_dict.setdefault(tmp, int(spell_target[i]))
    spell_blink_dict.setdefault(tmp, spell_blink[i])

person_place = ws_person.col_values(1) # A列　場所
person_x = ws_person.col_values(2) # B列　x
person_y = ws_person.col_values(3) # C列　y
person_pic = ws_person.col_values(4) # D列　画像
person_talk = ws_person.col_values(5) # E列　言葉

class Chara():
    def __init__(self):
        self.act = 0 # 戦闘のコマンド（行動）12:プレイヤー攻撃、13:モンスター攻撃、18:防御

        self.x = 0 # プレイヤーのx座標, モンスター画像の表示位置
        self.y = 0 # プレイヤーのy座標, モンスター画像の表示位置

        self.use_defense = False # 防御を使っているか
        self.turn_sukara = 0 # スカラの有効ターン
        self.num_sukara = 0 # スカラを使った回数
        self.turn_rukani = 0 # ルカニの有効ターン
        self.num_rukani = 0 # ルカニが効いた回数
        self.turn_baikiruto = 0 # バイキルトの有効ターン
        self.turn_henatos = 0 # ヘナトスの有効ターン
        self.turn_manusa = 0 # マヌーサの有効ターン
        self.flag_manusa = False # マヌーサにかかっているか
        self.turn_sleep = 0 # ラリホーの有効ターン
        self.flag_sleep = False # ラリホーにかかっているか
    def check_mp(self, str_spell):
        if self.mp < spell_usemp_dict[str_spell]:
            return False
        else:
            self.mp -= spell_usemp_dict[str_spell] # 消費mp
            return True
    def use_spell(self, str_spell, target, spell_target_no): # デフォルト値を取らない引数がデフォルト値を取る引数の後になっているとエラーになる
        # 戻り値が-1は状態変化の呪文
        if str_spell == "スカラ":
            tmp_dfs = self.sukara(target)
            if tmp_dfs < 1000: # ぼうぎょしていない状態で1000未満
                message = target.name + " の しゅびりょくが " + str(int(0.5 * target.get_dfs())) + "ふえた！"
            else:
                message = target.name + " の しゅびりょくが 最大になった！"
            return -1, message # -1は補助系呪文
        elif str_spell == "ルカニ":
            tmp_dfs = self.rukani(target)
            if tmp_dfs == -1:
                message = target.name + " には きかなかった！"
            elif target.dfs > 0: # elifにしないと、「きかなかった」も上書きされる
                message = target.name + " の しゅびりょくを " + str(int(0.5 * target.get_dfs())) + "さげた！"
            else:
                message = target.name + " の しゅびりょくが ０になった！"
            return -1, message
        elif str_spell == "バイキルト":
            tmp_atk = self.baikiruto(target)
            if tmp_atk > 0:
                message = target.name + " の こうげきりょくが " + str(tmp_atk) + "ふえた！"
            elif tmp_atk == 0: # 効果はなくても残りターンは増える
                message = target.name + " には こうかが なかった！"
            # 減ることは無いので、elseは省略
            return -1, message
        elif str_spell == "ヘナトス":
            tmp_atk = self.henatos(target)
            if tmp_atk == -1:
                message = target.name + " には きかなかった！"
            elif tmp_atk > 0:
                message = target.name + " の こうげきりょくを " + str(tmp_atk) + "さげた！"
            elif tmp_atk == 0: # 効果はなくても残りターンは増える
                message = target.name + " には こうかが なかった！"
            # 増えることは無いので、elseは省略
            return -1, message
        elif str_spell == "マヌーサ":
            tmp = self.manusa(target)
            if tmp == -1:
                message = target.name + " には きかなかった！"
            elif tmp == 1:
                message = target.name + "は まぼろしに つつまれている！"
            elif tmp == 2:
                message = target.name + "は まぼろしに つつまれた！"
            return -1, message
        elif str_spell == "ラリホー":
            tmp = self.rariho(target)
            if tmp == -1:
                message = target.name + " には きかなかった！"
            elif tmp == 1:
                message = target.name + "は ねむっている！"
            elif tmp == 2:
                message = target.name + "を ねむらせた！"
            return -1, message
        elif str_spell == "ラリホーマ":
            tmp = self.rarihoma(target)
            if tmp == -1:
                message = target.name + " には きかなかった！"
            elif tmp == 1:
                message = target.name + "は ねむっている！"
            elif tmp == 2:
                message = target.name + "を ねむらせた！"
            return -1, message

        point = random.randint(spell_lo_dict[str_spell], spell_up_dict[str_spell])
        if spell_target_no == 0 or spell_target_no == 1: # ターゲット(0:味方単体,1:味方全員,2:敵単体,3:敵グループ,4:敵全体)(party)
            message = target.name + " の キズが かいふくした！"
        else:
            message = target.name + "に " + str(point) + "ポイントのダメージを与えた！"
        return point, message

    def check_dfs(self): # 防御力計算（ターン開始の時も確認している）
        self.dfs = self.get_dfs() # 元に戻す
        # 元々の守備力*0.5を足したり、引いたりする
        self.dfs += int(0.5 * self.get_dfs()) * self.num_sukara # スカラ効果 アップした数字をメッセージに出す為、アップする数字にint
        self.dfs -= int(0.5 * self.get_dfs()) * self.num_rukani # ルカニ効果 アップした数字をメッセージに出す為、アップする数字にint
        tmp = self.dfs
        if self.use_defense: # ぼうぎょを使っている
            self.dfs *= 2
        if self.dfs > 999:
            self.dfs = 999
        if self.dfs < 0:
            self.dfs = 0
        return tmp # ぼうぎょする前の防御力を返す(ぼうぎょする前の防御力で1000未満か判定)
    def sukara(self, target): # スカラ
        target.num_sukara += 1 # スカラ継続中に使った回数　現在のスカラの効果(元の防御力*0.5 をnum_sukara倍して、元の防御力にプラスする)
        target.turn_sukara = random.randint(4, 5) # 効果の残りターン
        return target.check_dfs() # ぼうぎょする前の防御力を返す
    def invalid_sukara(self):
        self.turn_sukara = 0 # 戦闘の最後に元に戻すため
        self.num_sukara = 0
    def rukani(self, target): # ルカニ
        if random.randint(0, 99) < spell_up_dict["ルカニ"]: # 呪文の上限値が成功率
            target.num_rukani += 1
        else:
            return -1
        target.turn_rukani = random.randint(4, 5) # 効果の残りターン
        return target.check_dfs()
    def invalid_rukani(self):
        self.turn_rukani = 0 # 戦闘の最後に元に戻すため
        self.num_rukani = 0

    def baikiruto(self, target): # バイキルト
        tmp_atk = target.atk # 現在の攻撃力
        target.atk += target.get_atk() # 本来の攻撃力を足す（2倍）
        if target.atk > target.get_atk()*2: # 本来の攻撃力の2倍より大きいなら、2倍にする
            target.atk = target.get_atk()*2
        tmp_atk = target.atk - tmp_atk
        target.turn_baikiruto = random.randint(4, 5) # 効果の残りターン
        return tmp_atk # 変更後から変更前を引いた値
    def invalid_baikiruto(self): # バイキルト効果が消えたら
        # 半分にしているので奇数の時にズレる可能性がある
        self.atk -= self.get_atk() # 元をひく（２段階下げる）
        if self.atk < self.get_atk(): # 元より小さいなら
            self.atk = int(0.5 * self.get_atk()) # 半分にする(どんなに小さくても半分まで)
    def henatos(self, target): # ヘナトス
        if random.randint(0, 99) < spell_up_dict["ヘナトス"]: # 呪文の上限値が成功率
            tmp_atk = target.atk # 現在の攻撃力
            if target.atk >= target.get_atk(): # 元の攻撃力以上なら下げる、既に元の攻撃力より小さいなら変えない(どんなに小さくても半分まで)
                target.atk -= int(0.5 * target.get_atk()) # 元の攻撃力の半分をひく
            tmp_atk = tmp_atk - target.atk # 少なくなるので、元の値からひく
            target.turn_henatos = random.randint(4, 5) # 効果の残りターン
            return tmp_atk
        else: # 効かなかった
            return -1
    def invalid_henatos(self): # ヘナトス効果が消えたら
        if self.atk < self.get_atk(): # 元より小さいなら
            self.atk = self.get_atk() # 元に戻す
        elif self.atk == self.get_atk(): # 元と同じなら
            self.atk += int(0.5 * self.get_atk()) # 1.5倍
        else: # 元より大きいなら
            self.atk = 2 * self.get_atk() # 2倍（どんなに大きくても2倍まで）

    def manusa(self, target): # マヌーサ
        if random.randint(0, 99) < spell_up_dict["マヌーサ"]: # 呪文の上限値が成功率
            target.turn_manusa = random.randint(4, 5) # 効果の残りターン
            if target.flag_manusa:
                return 1 # 既にラリホーにかかっている
            else:
                target.flag_manusa = True
                return 2
        else: # 効かなかった
            return -1
    def invalid_manusa(self):
        self.turn_manusa = 0
        self.flag_manusa = False

    def rariho(self, target): # ラリホー
        if random.randint(0, 99) < spell_up_dict["ラリホー"]: # 呪文の上限値が成功率
            target.act = 28 # 眠っている行動
            target.turn_sleep = random.randint(4, 5) # 効果の残りターン
            if target.flag_sleep:
                return 1 # 既にラリホーにかかっている
            else:
                target.flag_sleep = True
                return 2
        else: # 効かなかった
            return -1
    def rarihoma(self, target): # ラリホーマ
        if random.randint(0, 99) < spell_up_dict["ラリホーマ"]: # 呪文の上限値が成功率
            target.act = 28 # 眠っている行動
            target.turn_sleep = random.randint(4, 5) # 効果の残りターン
            if target.flag_sleep:
                return 1 # 既にラリホーにかかっている
            else:
                target.flag_sleep = True
                return 2
        else: # 効かなかった
            return -1
    def invalid_sleep(self):
        self.turn_sleep = 0
        self.flag_sleep = False


    def spell_reset(self):
        self.invalid_sukara()
        self.invalid_rukani()
        self.check_dfs()
        self.turn_baikiruto = 0 # バイキルトの残りターン
        self.turn_henatos = 0 # ヘナトスの残りターン
        self.atk = self.get_atk() # 攻撃力を元に戻す
        self.invalid_manusa() # マヌーサの効果を消す
        self.invalid_sleep() # ラリホー、ラリホーマの効果を消す


class Brave(Chara):
    def __init__(self):
        super(Brave, self).__init__()
        self.name = chara1_name
        self.lv = 1
        self.maxhp = int(chara1_maxhp[self.lv])
        self.hp = 30
        self.maxmp = int(chara1_maxmp[self.lv])
        self.mp = 10
        self.quick = int(chara1_quick[self.lv])
        self.atk = int(chara1_atk[self.lv])
        self.dfs = int(chara1_dfs[self.lv])
        self.lv_exp = int(chara1_exp[self.lv])
        self.exp = 0
        self.mas_spell = [] # 覚えた呪文
        if chara1_spell[self.lv] != "": # レベル1で覚える呪文があるなら
            self.mas_spell.append(chara1_spell[1]) # mas:マスター

        self.img = [
                pygame.image.load("image/mychr0.png"), # 上
                pygame.image.load("image/mychr1.png"), # 上
                pygame.image.load("image/mychr2.png"), # 下
                pygame.image.load("image/mychr3.png"), # 下
                pygame.image.load("image/mychr4.png"), # 左
                pygame.image.load("image/mychr5.png"), # 左
                pygame.image.load("image/mychr6.png"), # 右
                pygame.image.load("image/mychr7.png"), # 右
                pygame.image.load("image/mychr8.png") # 倒れた
            ]
        for i, img in enumerate(self.img):
            self.img[i] = pygame.transform.scale(img, (40, 40))
        self.d = 0 # プレイヤーの向き 0:上 1:下 2:左 3:右
        self.a = 0 # imgPlayerの添字

    def attack(self, obj):
        message = [] # pygameでは改行できない
        # attackをBraveとMonsterに分ける（会心か痛恨かが分からない、メッセージが違う）
        # 会心の一撃、通常攻撃の会心では、敵の守備力に関わらず、攻撃力と同程度のダメージを与える(ダメージ幅は±5%)
        # 会心の一撃は回避やマヌーサなどの影響を受けないので一番最初に
        if random.random() < 1/32:
            base_dmg = self.get_atk()
            min_dmg = int(base_dmg - 0.05*base_dmg)
            max_dmg = int(base_dmg + 0.05*base_dmg)
            dmg = random.randint(min_dmg, max_dmg)
            message.append("かいしんの　いちげき！")
            message.append(obj.name + "に " + str(dmg) + "ポイントの ダメージ！！")
            return dmg, message
        
        if self.flag_manusa: # 攻撃者がマヌーサにかかっている
            if random.random() > 3/8: # 命中率が37.5%
                message.append("ミス！" + obj.name + "に ダメージを あたえられない！")
                return 0, message
        
        # 素早さ400未満では素早さが80上がるごとに回避率が1/192上がり、400以上では素早さが25上がるごとに回避率が1/32上がる。
        # つまり素早さ0では回避率1/64、素早さ400で回避率1/24、素早さ500で回避率1/6となる。
        if not obj.flag_sleep: # 眠っていないなら（眠っていたらかわさない）
            if obj.quick <= 400:
                avoid = 1/64 + obj.quick//80 * (1/192)
            elif obj.quick <= 500:
                avoid = 1/64 + obj.quick//80 * (1/192) + (obj.quick-400)//25 * (1/32)
            else:
                avoid = 1/6
            if random.random() < avoid:
                dmg = 0
                if random.randint(0, 1) == 0:
                    message.append(obj.name + "は ひらりと みをかわした！")
                else:
                    message.append(obj.name + "は すばやく みをかわした！")
                return dmg, message
        
        base_dmg = self.atk/2 - obj.dfs/4
        if base_dmg <= 0:
            base_dmg = 0
        width_dmg = base_dmg/16 + 1
        min_dmg = int(base_dmg - width_dmg) if base_dmg != 0 else 0
        max_dmg = int(base_dmg + width_dmg)
        dmg = random.randint(min_dmg, max_dmg)
        if dmg > 0:
            message.append(obj.name + "に " + str(dmg) + "ポイントの ダメージ！！")
        else:
            message.append("ミス！" + obj.name + "に ダメージを あたえられない！")
        return dmg, message


    def reset(self): # タイトル画面
        self.maxhp = int(chara1_maxhp[1])
        self.hp = self.maxhp
        self.mp = self.maxmp
    def lv_up(self):
        self.lv += 1
        self.maxhp = int(chara1_maxhp[self.lv])
        self.maxmp = int(chara1_maxmp[self.lv])
        self.quick = int(chara1_quick[self.lv])
        self.atk = int(chara1_atk[self.lv])
        self.dfs = int(chara1_dfs[self.lv])
        self.lv_exp = int(chara1_exp[self.lv])
    def get_dfs(self):
        return int(chara1_dfs[self.lv])
    def get_atk(self):
        return int(chara1_atk[self.lv])
    def master_spell(self):
        if chara1_spell[self.lv] != "": # レベルアップして覚える呪文があるなら
            self.mas_spell.append(chara1_spell[self.lv])
            return chara1_spell[self.lv]
        return ""
    def rest(self): # 寝た時
        self.hp = self.maxhp
        self.mp = self.maxmp

class Monster(Chara):
    def __init__(self, num):
        super(Monster, self).__init__()
        self.num = num
        self.img = pygame.image.load("image/enemy"+str(num)+".png")
        self.name = mon_name[num]
        self.maxhp = int(mon_maxhp[num])
        self.hp = self.maxhp
        self.quick = int(mon_quick[num])
        self.atk = int(mon_atk[num])
        self.dfs = int(mon_dfs[num])
        self.exp = int(mon_exp[num])
        self.skill = mon_skill[num].split(",")
        self.skill_no = 0 # skillの添字

    def set_name(self, num):
        if num == 0:
            self.name += " A"
        elif num == 1:
            self.name += " B"
        elif num == 2:
            self.name += " C"
        elif num == 3:
            self.name += " D"
    def set_x(self, x):
        self.x = x
    def set_y(self, y):
        self.y = y
    def get_dfs(self):
        return int(mon_dfs[self.num])
    def get_atk(self):
        return int(mon_atk[self.num])

    def attack(self, obj):
        message = []
        message.append(self.name + " の攻撃！")
        if self.flag_manusa: # 攻撃者がマヌーサにかかっている
            if random.random() > 3/8: # 命中率が37.5%
                message.append("ミス！" + obj.name + " は ダメージを うけない！")
                return 0, message
        # 素早さ400未満では素早さが80上がるごとに回避率が1/192上がり、400以上では素早さが25上がるごとに回避率が1/32上がる。
        # つまり素早さ0では回避率1/64、素早さ400で回避率1/24、素早さ500で回避率1/6となる。
        if not obj.flag_sleep: # 眠っていないなら（眠っていたらかわさない）
            if obj.quick <= 400:
                avoid = 1/64 + obj.quick//80 * (1/192)
            elif obj.quick <= 500:
                avoid = 1/64 + obj.quick//80 * (1/192) + (obj.quick-400)//25 * (1/32)
            else:
                avoid = 1/6
            if random.random() < avoid:
                dmg = 0
                if random.randint(0, 1) == 0:
                    message.append(obj.name + "は ひらりと みをかわした！")
                else:
                    message.append(obj.name + "は すばやく みをかわした！")
                return dmg, message
        
        base_dmg = self.atk/2 - obj.dfs/4
        if base_dmg <= 0:
            base_dmg = 0
        width_dmg = base_dmg/16 + 1
        min_dmg = int(base_dmg - width_dmg) if base_dmg != 0 else 0
        max_dmg = int(base_dmg + width_dmg)
        dmg = random.randint(min_dmg, max_dmg)
        if dmg > 0:
            message.append(obj.name + "は " + str(dmg) + "ポイントの ダメージを うけた！")
        else:
            message.append("ミス！" + obj.name + " は ダメージを うけない！")
        return dmg, message

    def grief(self, obj):
        message = []
        message.append(self.name + " のこうげき！")
        base_dmg = self.atk
        min_dmg = int(self.atk - 0.05*self.atk)
        max_dmg = int(self.atk + 0.05*self.atk)
        dmg = random.randint(min_dmg, max_dmg)
        message.append("つうこんの　いちげき！")
        message.append(obj.name + "は " + str(dmg) + "ポイントの ダメージを うけた！")
        return dmg, message
    def set_monster_com(self): # モンスターの戦闘コマンド
        if self.flag_sleep:
            self.act = 28 # 眠っている（不要か？既に28になっている）
        else:
            self.skill_no = random.randint(0, len(self.skill)-1) 
            if get_spell_target(self.skill[self.skill_no]) == 1: # 単体攻撃
                self.act = 13 # 攻撃
            else:
                self.act = 29 # 特技


def get_spell_usemp(str_spell):
    return spell_usemp_dict[str_spell]
def get_spell_explain(str_spell):
    return spell_explain_dict[str_spell]
def get_spell_target(str_spell):
    return spell_target_dict[str_spell]
def get_spell_blink(str_spell):
    return spell_blink_dict[str_spell]
    
def get_mon_area_list():
    return mon_area

# 人物シート
class People():
    def __init__(self):
        self.x = []
        self.y = []
        self.pic = []
        self.talk = []
    def get_posi(self, area):
        self.x.clear()
        self.y.clear()
        self.pic.clear()
        self.talk.clear()
        for i in range(1, len(person_place)): # 1行目はカラムの為、とばす
            if int(person_place[i]) == area:
                self.x.append(int(person_x[i]))
                self.y.append(int(person_y[i]))
                self.pic.append(int(person_pic[i]))
                self.talk.append(person_talk[i])

