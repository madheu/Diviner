# -*- coding: utf-8 -*-
"""
Skill管理器 —— 统一调度所有术数/投资Skill
支持三种Skill来源：
  1. 内置梅花易数（iching_skill.py）
  2. Numerologist Skills（奇门遁甲/紫微斗数/八字）
  3. 巴菲特视角（投资逻辑层）
"""

import json
import os
from datetime import datetime


class SkillRegistry:
    """Skill注册中心"""

    def __init__(self):
        self.skills = {}
        self.active_skills = {}

    def register(self, name, skill_instance, category="general"):
        """注册一个Skill"""
        self.skills[name] = {
            "instance": skill_instance,
            "category": category,
            "enabled": True,
            "registered_at": datetime.now().isoformat(),
        }
        return self

    def enable(self, name):
        if name in self.skills:
            self.skills[name]["enabled"] = True

    def disable(self, name):
        if name in self.skills:
            self.skills[name]["enabled"] = False

    def get(self, name):
        skill = self.skills.get(name)
        if skill and skill["enabled"]:
            return skill["instance"]
        return None

    def list_all(self):
        return [
            {"name": k, "category": v["category"], "enabled": v["enabled"]}
            for k, v in self.skills.items()
        ]

    def get_by_category(self, category):
        return [
            v["instance"]
            for k, v in self.skills.items()
            if v["category"] == category and v["enabled"]
        ]


class SkillManager:
    """
    统一Skill调度器
    负责协调所有术数Skill和投资Skill，输出统一格式的分析结果
    """

    def __init__(self):
        self.registry = SkillRegistry()
        self._init_skills()

    def _init_skills(self):
        """初始化所有Skill"""
        from iching_skill import IChingSkillInterface
        from qimen_skill import QimenDunjiaAdapter
        from buffett_skill import BuffettSkill

        # 注册内置Skill
        self.registry.register("梅花易数", IChingSkillInterface(), "术数")
        self.registry.register("奇门遁甲", QimenDunjiaAdapter(), "术数")
        self.registry.register("巴菲特视角", BuffettSkill(), "投资")

    def divine(self, question, method="梅花易数", dt=None, external_event=None):
        """
        执行术数预测
        method: "梅花易数" | "奇门遁甲" | "紫微斗数"
        """
        skill = self.registry.get(method)
        if skill is None:
            # 回退到梅花易数
            skill = self.registry.get("梅花易数")

        if hasattr(skill, "divine"):
            return skill.divine(question, dt, external_event)
        elif hasattr(skill, "analyze"):
            return skill.analyze(question, dt, external_event)
        else:
            raise ValueError(f"Skill {method} 不支持预测接口")

    def analyze_investment(self, question, real_data, news_analysis):
        """执行投资分析（巴菲特视角）"""
        buffett = self.registry.get("巴菲特视角")
        if buffett:
            return buffett.analyze(question, real_data, news_analysis)
        return None

    def get_skill_info(self):
        """获取所有Skill信息"""
        return self.registry.list_all()

    def set_active_method(self, method):
        """设置当前活跃的术数方法"""
        valid_methods = ["梅花易数", "奇门遁甲", "紫微斗数"]
        if method not in valid_methods:
            return False
        # 禁用其他术数，启用选中的
        for m in valid_methods:
            if m == method:
                self.registry.enable(m)
            else:
                self.registry.disable(m)
        return True


# 全局单例
_skill_manager = None


def get_skill_manager():
    global _skill_manager
    if _skill_manager is None:
        _skill_manager = SkillManager()
    return _skill_manager