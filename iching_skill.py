# -*- coding: utf-8 -*-
"""
术数易学Skill接口
这是一个插槽模块，你可以用自己提供的Skill替换此文件的实现。

接口约定：
- 输入：divine(question, dt, external_event) 
- 输出：dict，必须包含以下字段：
  {
    "本卦": {"name": str, "upper": str, "lower": str, "judgment": str, "ji_xiong": int},
    "变卦": {"name": str, "upper": str, "lower": str, "judgment": str, "ji_xiong": int},
    "互卦": {"name": str, "upper": str, "lower": str},
    "体卦": {"name": str, "element": str, "nature": str},
    "用卦": {"name": str, "element": str, "nature": str},
    "体用生克": {"关系": str, "含义": str, "评分": int},
    "动爻": int,
    "解读": {"趋势定性": str, "行动建议": str, "综合评分": float},
    "时辰": str,
    "起卦时间": str,
  }

如果你有自己的Skill，只需替换 divine() 方法即可。
"""

import math
import random
import hashlib
from datetime import datetime

# ============================================================
# 八卦与64卦数据（内置，Skill无需关心此部分）
# ============================================================

BAGUA = {
    "乾": {"name": "乾", "element": "金", "nature": "天", "num": 1, "symbol": "☰"},
    "兑": {"name": "兑", "element": "金", "nature": "泽", "num": 2, "symbol": "☱"},
    "离": {"name": "离", "element": "火", "nature": "火", "num": 3, "symbol": "☲"},
    "震": {"name": "震", "element": "木", "nature": "雷", "num": 4, "symbol": "☳"},
    "巽": {"name": "巽", "element": "木", "nature": "风", "num": 5, "symbol": "☴"},
    "坎": {"name": "坎", "element": "水", "nature": "水", "num": 6, "symbol": "☵"},
    "艮": {"name": "艮", "element": "土", "nature": "山", "num": 7, "symbol": "☶"},
    "坤": {"name": "坤", "element": "土", "nature": "地", "num": 8, "symbol": "☷"},
}

NUM_TO_GUA = {1: "乾", 2: "兑", 3: "离", 4: "震", 5: "巽", 6: "坎", 7: "艮", 8: "坤"}

WUXING = {
    "金": {"生": "水", "克": "木", "被生": "土", "被克": "火"},
    "木": {"生": "火", "克": "土", "被生": "水", "被克": "金"},
    "水": {"生": "木", "克": "火", "被生": "金", "被克": "土"},
    "火": {"生": "土", "克": "金", "被生": "木", "被克": "水"},
    "土": {"生": "金", "克": "水", "被生": "火", "被克": "木"},
}

HEXAGRAMS = [
    (1, "乾为天", "乾", "乾", "元亨利贞。自强不息，创始通达。", 1),
    (2, "坤为地", "坤", "坤", "元亨，利牝马之贞。厚德载物，柔顺守成。", 0),
    (3, "水雷屯", "坎", "震", "屯，刚柔始交而难生。万事开头难，需耐心。", 0),
    (4, "山水蒙", "艮", "坎", "蒙，亨。童蒙求我，启蒙待时。", 0),
    (5, "水天需", "坎", "乾", "需，有孚，光亨。等待时机，不可冒进。", 0),
    (6, "天水讼", "乾", "坎", "讼，有孚窒惕。争讼不利，宜和解。", -1),
    (7, "地水师", "坤", "坎", "师，贞，丈人吉。统兵出征，需名正言顺。", 0),
    (8, "水地比", "坎", "坤", "比，吉。亲附团结，吉。", 1),
    (9, "风天小畜", "巽", "乾", "小畜，亨。密云不雨，小有积蓄。", 0),
    (10, "天泽履", "乾", "兑", "履虎尾，不咥人，亨。如履薄冰，谨慎行事。", 0),
    (11, "地天泰", "坤", "乾", "泰，小往大来，吉亨。天地交泰，通顺。", 1),
    (12, "天地否", "乾", "坤", "否之匪人，不利君子贞。闭塞不通，退守。", -1),
    (13, "天火同人", "乾", "离", "同人于野，亨。志同道合，利合作。", 1),
    (14, "火天大有", "离", "乾", "大有，元亨。大丰收，收获满满。", 1),
    (15, "地山谦", "坤", "艮", "谦，亨，君子有终。谦虚受益，吉。", 1),
    (16, "雷地豫", "震", "坤", "豫，利建侯行师。愉悦安乐，顺势而动。", 1),
    (17, "泽雷随", "兑", "震", "随，元亨利贞，无咎。随顺时势，灵活应变。", 1),
    (18, "山风蛊", "艮", "巽", "蛊，元亨。积弊需整治，拨乱反正。", 0),
    (19, "地泽临", "坤", "兑", "临，元亨利贞。居高临下，亲临督导。", 1),
    (20, "风地观", "巽", "坤", "观，盥而不荐。观察形势，审时度势。", 0),
    (21, "火雷噬嗑", "离", "震", "噬嗑，亨。咬合决断，利用狱。", 0),
    (22, "山火贲", "艮", "离", "贲，亨。文饰之美，不可过度。", 0),
    (23, "山地剥", "艮", "坤", "剥，不利有攸往。剥落衰败，宜守。", -1),
    (24, "地雷复", "坤", "震", "复，亨。一阳来复，转机将至。", 1),
    (25, "天雷无妄", "乾", "震", "无妄，元亨利贞。不妄为，守正得吉。", 1),
    (26, "山天大畜", "艮", "乾", "大畜，利贞。厚积薄发，蓄势待时。", 1),
    (27, "山雷颐", "艮", "震", "颐，贞吉。养正待时，自食其力。", 0),
    (28, "泽风大过", "兑", "巽", "大过，栋桡。过度失衡，非常之时。", -1),
    (29, "坎为水", "坎", "坎", "习坎，有孚维心亨。重重险阻，守心待援。", -1),
    (30, "离为火", "离", "离", "离，利贞，亨。依附光明，柔顺中正。", 1),
    (31, "泽山咸", "兑", "艮", "咸，亨利贞。感应互通，男女相感。", 1),
    (32, "雷风恒", "震", "巽", "恒，亨，无咎。持之以恒，坚守正道。", 1),
    (33, "天山遁", "乾", "艮", "遁，亨。退避隐忍，以退为进。", 0),
    (34, "雷天大壮", "震", "乾", "大壮，利贞。强盛壮大，不可恃强。", 1),
    (35, "火地晋", "离", "坤", "晋，康侯用锡马蕃庶。进步上升，光明。", 1),
    (36, "地火明夷", "坤", "离", "明夷，利艰贞。光明受损，韬光养晦。", -1),
    (37, "风火家人", "巽", "离", "家人，利女贞。家庭和睦，各守其位。", 1),
    (38, "火泽睽", "离", "兑", "睽，小事吉。乖离不合，小事可成。", 0),
    (39, "水山蹇", "坎", "艮", "蹇，利西南不利东北。艰难险阻，待援。", -1),
    (40, "雷水解", "震", "坎", "解，利西南。困难解除，转危为安。", 1),
    (41, "山泽损", "艮", "兑", "损，有孚，元吉。减损有道，损下益上。", 0),
    (42, "风雷益", "巽", "震", "益，利有攸往。增益有利，损上益下。", 1),
    (43, "泽天夬", "兑", "乾", "夬，扬于王庭。决断果断，去除小人。", 0),
    (44, "天风姤", "乾", "巽", "姤，女壮，勿用取女。不期而遇，防微杜渐。", 0),
    (45, "泽地萃", "兑", "坤", "萃，亨。聚集荟萃，人才汇聚。", 1),
    (46, "地风升", "坤", "巽", "升，元亨。上升渐进，积小成大。", 1),
    (47, "泽水困", "兑", "坎", "困，亨，贞大人吉。困顿受挫，守正待时。", -1),
    (48, "水风井", "坎", "巽", "井，改邑不改井。井养不穷，守常不变。", 0),
    (49, "泽火革", "兑", "离", "革，巳日乃孚。变革之时，顺势而变。", 0),
    (50, "火风鼎", "离", "巽", "鼎，元吉，亨。鼎新革故，稳固根基。", 1),
    (51, "震为雷", "震", "震", "震，亨。震惊百里，临危不乱。", 0),
    (52, "艮为山", "艮", "艮", "艮其背，不获其身。止于当止，知止不殆。", 0),
    (53, "风山渐", "巽", "艮", "渐，女归吉。循序渐进，不可急躁。", 1),
    (54, "雷泽归妹", "震", "兑", "归妹，征凶，无攸利。名不正则言不顺。", -1),
    (55, "雷火丰", "震", "离", "丰，亨。盛大丰盈，日中则昃。", 1),
    (56, "火山旅", "离", "艮", "旅，小亨。旅途漂泊，谨慎行事。", 0),
    (57, "巽为风", "巽", "巽", "巽，小亨。柔顺入微，顺势渗透。", 0),
    (58, "兑为泽", "兑", "兑", "兑，亨利贞。喜悦和乐，以诚待人。", 1),
    (59, "风水涣", "巽", "坎", "涣，亨。涣散分离，需凝聚人心。", 0),
    (60, "水泽节", "坎", "兑", "节，亨。节制有度，过犹不及。", 0),
    (61, "风泽中孚", "巽", "兑", "中孚，豚鱼吉。诚信感召，信及豚鱼。", 1),
    (62, "雷山小过", "震", "艮", "小过，亨利贞。小有过越，宜下不宜上。", 0),
    (63, "水火既济", "坎", "离", "既济，亨小。事已成，守成不易。", 0),
    (64, "火水未济", "离", "坎", "未济，亨。事未成，革命尚未成功。", 0),
]

HEXAGRAM_MAP = {}
for h in HEXAGRAMS:
    HEXAGRAM_MAP[(h[2], h[3])] = h
    HEXAGRAM_MAP[h[1]] = h

DIZHI_NUM = {"子": 1, "丑": 2, "寅": 3, "卯": 4, "辰": 5, "巳": 6,
             "午": 7, "未": 8, "申": 9, "酉": 10, "戌": 11, "亥": 12}


# ============================================================
# Skill接口类 —— 替换此类即可接入你的术数Skill
# ============================================================

class IChingSkillInterface:
    """
    术数Skill接口

    如果你有自己的Skill，只需替换这个类。
    必须保持 divine() 方法的输入输出格式不变。
    """

    def divine(self, question, dt=None, external_event=None):
        """
        梅花易数起卦（内置实现）

        参数:
            question: str - 用户问题
            dt: datetime - 起卦时间，默认当前时间
            external_event: str - 外应事件（可选）

        返回:
            dict - 卦象分析结果
        """
        if dt is None:
            dt = datetime.now()

        # 外应扰动
        if external_event:
            q_hash = int(hashlib.md5(external_event.encode()).hexdigest()[:8], 16)
        else:
            q_hash = int(hashlib.md5(question.encode()).hexdigest()[:8], 16)

        year, month, day = dt.year, dt.month, dt.day
        hour_num, dizhi_name = self._get_dizhi_num(dt)

        upper_num = self._calc_gua_num(year + month + day + (q_hash % 100))
        lower_num = self._calc_gua_num(year + month + day + hour_num + (q_hash % 50))
        dong_yao = self._calc_dong_yao(year + month + day + hour_num + (q_hash % 30))

        upper_gua = NUM_TO_GUA[upper_num]
        lower_gua = NUM_TO_GUA[lower_num]

        ben_gua = HEXAGRAM_MAP.get((upper_gua, lower_gua))
        if ben_gua is None:
            ben_gua = HEXAGRAM_MAP.get((lower_gua, upper_gua), HEXAGRAMS[0])

        if dong_yao <= 3:
            ti_gua, yong_gua = upper_gua, lower_gua
        else:
            ti_gua, yong_gua = lower_gua, upper_gua

        if dong_yao <= 3:
            new_lower_num = ((lower_num + 3) % 8) + 1
            if new_lower_num > 8:
                new_lower_num = new_lower_num % 8 or 8
            bian_upper, bian_lower = upper_gua, NUM_TO_GUA[new_lower_num]
        else:
            new_upper_num = ((upper_num + 3) % 8) + 1
            if new_upper_num > 8:
                new_upper_num = new_upper_num % 8 or 8
            bian_upper, bian_lower = NUM_TO_GUA[new_upper_num], lower_gua

        bian_gua = HEXAGRAM_MAP.get((bian_upper, bian_lower))
        if bian_gua is None:
            bian_gua = HEXAGRAM_MAP.get((bian_lower, bian_upper), HEXAGRAMS[0])

        hu_gua = HEXAGRAMS[(ben_gua[0] + dong_yao * 3) % 64]

        ti_element = BAGUA[ti_gua]["element"]
        yong_element = BAGUA[yong_gua]["element"]
        shengke = self._analyze_shengke(ti_element, yong_element)
        interpretation = self._interpret(ben_gua, bian_gua, shengke, dong_yao)

        return {
            "本卦": {"name": ben_gua[1], "upper": ben_gua[2], "lower": ben_gua[3],
                    "judgment": ben_gua[4], "ji_xiong": ben_gua[5]},
            "变卦": {"name": bian_gua[1], "upper": bian_upper, "lower": bian_lower,
                    "judgment": bian_gua[4], "ji_xiong": bian_gua[5]},
            "互卦": {"name": hu_gua[1], "upper": hu_gua[2], "lower": hu_gua[3]},
            "体卦": {"name": ti_gua, "element": ti_element, "nature": BAGUA[ti_gua]["nature"]},
            "用卦": {"name": yong_gua, "element": yong_element, "nature": BAGUA[yong_gua]["nature"]},
            "体用生克": shengke,
            "动爻": dong_yao,
            "解读": interpretation,
            "时辰": dizhi_name,
            "起卦时间": dt.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _get_dizhi_num(self, dt):
        hour = dt.hour
        dizhi_hour_map = [
            (23, 0, "子"), (1, 2, "丑"), (3, 4, "寅"), (5, 6, "卯"),
            (7, 8, "辰"), (9, 10, "巳"), (11, 12, "午"), (13, 14, "未"),
            (15, 16, "申"), (17, 18, "酉"), (19, 20, "戌"), (21, 22, "亥"),
        ]
        for start, end, name in dizhi_hour_map:
            if start <= hour <= end or (start == 23 and hour <= 0):
                return DIZHI_NUM[name], name
        return 1, "子"

    def _calc_gua_num(self, num):
        n = num % 8
        return 8 if n == 0 else n

    def _calc_dong_yao(self, num):
        n = num % 6
        return 6 if n == 0 else n

    def _analyze_shengke(self, ti_element, yong_element):
        wx = WUXING[ti_element]
        if yong_element == wx["生"]:
            return {"关系": "体生用", "含义": "我方泄气于外，消耗较大，需量力而行", "评分": -1}
        elif yong_element == wx["克"]:
            return {"关系": "体克用", "含义": "我方克制外势，事可成但费力", "评分": 1}
        elif yong_element == wx["被生"]:
            return {"关系": "用生体", "含义": "外部助益我方，大吉之象", "评分": 2}
        elif yong_element == wx["被克"]:
            return {"关系": "用克体", "含义": "外部压制我方，凶险，宜退守", "评分": -2}
        elif ti_element == yong_element:
            return {"关系": "体用比和", "含义": "内外和谐一致，顺遂", "评分": 2}
        return {"关系": "未知", "含义": "无法判断", "评分": 0}

    def _interpret(self, ben_gua, bian_gua, shengke, dong_yao):
        ji_xiong = ben_gua[5]
        shengke_score = shengke["评分"]
        total_score = ji_xiong * 1 + shengke_score * 0.5

        if total_score >= 2:
            trend, advice = "趋势向好，积极可为", "建议积极参与，把握时机"
        elif total_score >= 0.5:
            trend, advice = "趋势平稳，小步试探", "可以尝试，但控制投入规模"
        elif total_score >= -0.5:
            trend, advice = "趋势不明，观望为主", "暂不行动，等待更明确的信号"
        elif total_score >= -1.5:
            trend, advice = "趋势不利，谨慎为上", "建议减仓或暂停，防守优先"
        else:
            trend, advice = "趋势凶险，立即退守", "强烈建议停止行动，保全实力"

        if ben_gua[5] != bian_gua[5]:
            if ben_gua[5] < bian_gua[5]:
                trend += "；变卦转吉，有拐点向上的可能"
            else:
                trend += "；变卦转凶，注意拐点向下的风险"

        return {
            "趋势定性": trend,
            "行动建议": advice,
            "综合评分": round(total_score, 2),
            "体用关系": shengke["含义"],
        }