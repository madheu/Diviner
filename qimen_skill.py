# -*- coding: utf-8 -*-
"""
奇门遁甲Skill适配器
基于 Numerologist_skills/qimen-dunjia 的Skill规范
来源：https://github.com/FANzR-arch/Numerologist_skills

核心能力：
- 结构化访谈（先问清再排盘）
- 排盘计算（简化版，完整版需运行 qimen_cli.py）
- 用神取用与解读
- 方位/时机/行动建议
"""

import hashlib
import random
from datetime import datetime


class QimenDunjiaSkill:
    """
    奇门遁甲Skill适配器

    遵循原Skill的5步工作流：
    1. 先访谈 → 2. 确认信息 → 3. 排盘(简化) → 4. 读盘 → 5. 解读输出
    """

    # 九宫方位
    PALACES = {
        1: {"name": "坎一宫", "direction": "北", "element": "水"},
        2: {"name": "坤二宫", "direction": "西南", "element": "土"},
        3: {"name": "震三宫", "direction": "东", "element": "木"},
        4: {"name": "巽四宫", "direction": "东南", "element": "木"},
        5: {"name": "中五宫", "direction": "中", "element": "土"},
        6: {"name": "乾六宫", "direction": "西北", "element": "金"},
        7: {"name": "兑七宫", "direction": "西", "element": "金"},
        8: {"name": "艮八宫", "direction": "东北", "element": "土"},
        9: {"name": "离九宫", "direction": "南", "element": "火"},
    }

    # 八门
    DOORS = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]
    DOOR_MEANINGS = {
        "休门": "休息、等待、养精蓄锐——吉",
        "生门": "生机、利润、成长——大吉",
        "伤门": "伤害、损失、竞争——凶",
        "杜门": "堵塞、隐蔽、技术——平",
        "景门": "表面、宣传、文书——平",
        "死门": "终结、停滞、保守——大凶",
        "惊门": "惊恐、口舌、纠纷——凶",
        "开门": "开创、公开、事业——大吉",
    }

    # 九星
    STARS = ["天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"]
    STAR_MEANINGS = {
        "天蓬": "大胆冒险，但易出格",
        "天芮": "问题暴露，需修补",
        "天冲": "快速行动，有冲劲",
        "天辅": "辅助支持，文教",
        "天禽": "中正稳健，居中调度",
        "天心": "谋划策划，领导力",
        "天柱": "支撑但易崩塌",
        "天任": "担当责任，负重前行",
        "天英": "表面光鲜，注意虚火",
    }

    # 八神
    GODS = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
    GOD_MEANINGS = {
        "值符": "领袖气场，权威加持",
        "螣蛇": "虚惊怪异，变化无常",
        "太阴": "暗中谋划，阴柔之力",
        "六合": "合作联盟，姻缘媒介",
        "白虎": "威猛凶险，快速突破",
        "玄武": "暗中捣鬼，防小人",
        "九地": "沉稳坚固，宜守不宜攻",
        "九天": "高远扬名，主动出击",
    }

    def __init__(self):
        self.last_result = None

    def analyze(self, question, dt=None, external_event=None):
        """
        奇门遁甲分析（简化版）
        完整版需安装 lunar_python 并运行 qimen_cli.py

        当前简化版基于时间+问题哈希生成模拟盘面，
        但保留了完整的解读框架。
        """
        if dt is None:
            dt = datetime.now()

        # 用问题+时间生成确定性种子
        seed = hashlib.md5(f"{question}{dt.isoformat()}".encode()).hexdigest()
        rng = random.Random(int(seed[:8], 16))

        # 模拟排盘
        chart = self._generate_chart(dt, rng, question)

        # 用神取用
        yongshen = self._get_yongshen(question, chart)

        # 解读
        interpretation = self._interpret(chart, yongshen, question)

        self.last_result = {
            "chart": chart,
            "yongshen": yongshen,
            "interpretation": interpretation,
            "method": "奇门遁甲（简化排盘）",
            "warning": "当前为简化版排盘，正式决策请运行完整版 qimen_cli.py",
        }
        return self.last_result

    def _generate_chart(self, dt, rng, question):
        """生成模拟奇门盘"""
        dun_type = "阳遁" if dt.month in [1, 2, 3, 4, 5, 6] else "阴遁"
        ju_number = rng.randint(1, 9)

        # 模拟值符值使
        zhifu_star = rng.choice(self.STARS)
        zhishi_door = rng.choice(self.DOORS)

        # 时干（用户代表）
        time_stem = rng.choice(["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"])

        # 模拟9宫
        palaces = []
        for i in range(1, 10):
            palace_info = self.PALACES[i]
            palaces.append({
                "palace": i,
                "name": palace_info["name"],
                "direction": palace_info["direction"],
                "element": palace_info["element"],
                "star": rng.choice(self.STARS),
                "door": rng.choice(self.DOORS),
                "god": rng.choice(self.GODS),
                "earth_stem": rng.choice(["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]),
                "sky_stem": rng.choice(["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]),
            })

        return {
            "dun_type": dun_type,
            "ju_number": ju_number,
            "zhifu": {"star": zhifu_star, "palace": rng.randint(1, 9)},
            "zhishi": {"door": zhishi_door, "palace": rng.randint(1, 9)},
            "time_stem_visible": time_stem,
            "palaces": palaces,
            "is_simulated": True,
        }

    def _get_yongshen(self, question, chart):
        """根据问题类型取用神"""
        question_lower = question.lower()

        # 用神分类
        if any(w in question for w in ["涨", "跌", "买", "卖", "投资", "仓位", "行情"]):
            yongshen_type = "生门（利润）"
            primary = "生门"
        elif any(w in question for w in ["合作", "合伙", "签约", "合同"]):
            yongshen_type = "六合（合作）"
            primary = "六合"
        elif any(w in question for w in ["工作", "事业", "职业", "跳槽"]):
            yongshen_type = "开门（事业）"
            primary = "开门"
        elif any(w in question for w in ["风险", "危险", "亏损", "止损"]):
            yongshen_type = "白虎（凶险）"
            primary = "白虎"
        else:
            yongshen_type = "时干（当前状态）"
            primary = "时干"

        # 在盘中定位用神
        target_palace = None
        for p in chart["palaces"]:
            if primary == "时干":
                if p["sky_stem"] == chart["time_stem_visible"]:
                    target_palace = p
                    break
            elif primary == "生门":
                if p["door"] == "生门":
                    target_palace = p
                    break
            elif primary == "开门":
                if p["door"] == "开门":
                    target_palace = p
                    break
            elif primary in ["六合", "白虎"]:
                if p["god"] == primary:
                    target_palace = p
                    break

        if target_palace is None:
            target_palace = chart["palaces"][0]

        return {
            "type": yongshen_type,
            "primary": primary,
            "palace": target_palace,
        }

    def _interpret(self, chart, yongshen, question):
        """解读奇门盘"""
        p = yongshen["palace"]
        door = p["door"]
        star = p["star"]
        god = p["god"]

        door_meaning = self.DOOR_MEANINGS.get(door, "平")
        star_meaning = self.STAR_MEANINGS.get(star, "")
        god_meaning = self.GOD_MEANINGS.get(god, "")

        # 吉凶判断
        ji_doors = ["休门", "生门", "开门"]
        xiong_doors = ["伤门", "死门", "惊门"]
        if door in ji_doors:
            base_judgment = "吉"
            score = 2
        elif door in xiong_doors:
            base_judgment = "凶"
            score = -1
        else:
            base_judgment = "平"
            score = 0

        # 星的影响
        if star in ["天心", "天辅", "天禽", "天任"]:
            score += 1
        elif star in ["天蓬", "天芮", "天柱"]:
            score -= 1

        # 神的影响
        if god in ["值符", "六合", "九天", "九地"]:
            score += 1
        elif god in ["白虎", "玄武", "螣蛇"]:
            score -= 1

        # 方位建议
        direction = p["direction"]
        element = p["element"]

        if score >= 3:
            advice = "盘面信号积极，可以行动"
            action = "适合推进"
        elif score >= 1:
            advice = "盘面有助力但也有阻力，小步试探"
            action = "谨慎推进"
        elif score >= -1:
            advice = "信号模糊，观望为主"
            action = "暂不行动"
        else:
            advice = "盘面阻力较大，建议等待"
            action = "建议回避"

        return {
            "用神落宫": f"{p['name']}（{direction}方，{element}）",
            "门": f"{door}——{door_meaning}",
            "星": f"{star}——{star_meaning}",
            "神": f"{god}——{god_meaning}",
            "吉凶判断": base_judgment,
            "综合评分": score,
            "行动建议": advice,
            "行动指令": action,
            "有利方位": direction,
            "避让方位": self._opposite_direction(direction),
            "趋势定性": f"奇门：{advice}",
            "风险提示": self._risk_warning(door, god),
        }

    def _opposite_direction(self, direction):
        opposite = {"北": "南", "南": "北", "东": "西", "西": "东",
                    "东北": "西南", "西南": "东北", "西北": "东南", "东南": "西北", "中": "中"}
        return opposite.get(direction, "中")

    def _risk_warning(self, door, god):
        warnings = []
        if door == "死门":
            warnings.append("死门当值，重大决策需三思")
        if god == "白虎":
            warnings.append("白虎临宫，注意突发风险")
        if god == "玄武":
            warnings.append("玄武暗藏，防小人或信息不透明")
        if god == "螣蛇":
            warnings.append("螣蛇缠绕，事情可能有反复或虚假信息")
        return "；".join(warnings) if warnings else "无明显风险信号"


# 转换为与梅花易数兼容的接口
class QimenDunjiaAdapter:
    """将奇门遁甲结果转为决策系统兼容格式"""

    def __init__(self):
        self.skill = QimenDunjiaSkill()

    def divine(self, question, dt=None, external_event=None):
        """对外提供与梅花易数相同的divine接口"""
        result = self.skill.analyze(question, dt, external_event)
        interp = result["interpretation"]
        chart = result["chart"]

        # 转换为决策系统需要的格式
        return {
            "本卦": {
                "name": f"奇门·{chart['dun_type']}{chart['ju_number']}局",
                "upper": f"值符{chart['zhifu']['star']}",
                "lower": f"值使{chart['zhishi']['door']}",
                "judgment": f"时干{chart['time_stem_visible']}，{interp['用神落宫']}",
                "ji_xiong": 1 if interp["综合评分"] > 0 else (-1 if interp["综合评分"] < 0 else 0),
            },
            "变卦": {
                "name": "趋避指引",
                "upper": interp["有利方位"],
                "lower": interp["避让方位"],
                "judgment": interp["风险提示"],
                "ji_xiong": 0,
            },
            "互卦": {"name": "用神", "upper": interp["门"], "lower": interp["星"]},
            "体卦": {"name": "我方", "element": "用神", "nature": interp["用神落宫"]},
            "用卦": {"name": "外势", "element": interp["神"], "nature": f"{interp['吉凶判断']}"},
            "体用生克": {
                "关系": interp["吉凶判断"],
                "含义": interp["行动建议"],
                "评分": interp["综合评分"],
            },
            "动爻": 0,
            "解读": {
                "趋势定性": interp["趋势定性"],
                "行动建议": interp["行动建议"],
                "综合评分": interp["综合评分"],
                "体用关系": f"{interp['门']} | {interp['星']} | {interp['神']}",
            },
            "时辰": datetime.now().strftime("%H时"),
            "起卦时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "method": "奇门遁甲",
            "warning": result["warning"],
        }