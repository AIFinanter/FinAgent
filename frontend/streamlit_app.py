"""
FinAgent · 金融数据资产治理中心
DIKW 数智流体系 — 追踪每一步客户操作，沉淀为可估值的数据资产
徐心 & 蔡瑶 (2024) 清华管理评论

双主题 · 中英双语 · 无 Emoji
"""

import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from config import config
from finagent.tools.sanitizer import DataSanitizerTool
from finagent.tools.behavior import BehaviorAnalyzerTool
from finagent.tools.compliance import ComplianceSearchTool
from finagent.tools.risk import RiskScorerTool, configure_llm
from finagent.mab import ThompsonBandit, compute_reward
from finagent.lineage import (
    create_lineage, get_all_lineages, lineage_summary,
    DIKWLayer, SpiralType,
)
from finagent.experiment import (
    create_experiment, get_all_experiments,
    vrio_analysis, compute_feature_importance,
)
from finagent.scenarios import get_all_templates, apply_template

# ═══════════════════════════════════════════════════════════════
#  Design Tokens — Dual Theme
# ═══════════════════════════════════════════════════════════════

THEMES = {
    "Dark": {
        "bg":           "#0f1419",
        "bgDeep":       "#090c10",
        "surface":      "#1a1f26",
        "surfaceRaised":"#212730",
        "cardBg":       "rgba(26,31,38,0.70)",
        "border":       "rgba(138,148,158,0.10)",
        "borderFocus":  "rgba(196,162,86,0.28)",
        "brass":        "#c4a256",
        "brassDim":     "#a8883d",
        "brassMuted":   "rgba(196,162,86,0.12)",
        "verdigris":    "#5a9e8b",
        "verdigrisDim": "#4a8a78",
        "verdigrisMuted":"rgba(90,158,139,0.10)",
        "rust":         "#c4563a",
        "rustDim":      "#a8442e",
        "chalk":        "#e6edf3",
        "chalkDim":     "#bcc5cf",
        "stone":        "#8b939c",
        "stoneDim":     "#5c636b",
        "criticalBg":   "rgba(196,86,58,0.08)",
        "info":         "#5aa0b8",
        "chartBlue":    "#4a8aaa",
    },
    "Light": {
        "bg":           "#faf7f2",
        "bgDeep":       "#f3efe8",
        "surface":      "#ffffff",
        "surfaceRaised":"#faf8f4",
        "cardBg":       "#ffffff",
        "border":       "rgba(0,0,0,0.06)",
        "borderFocus":  "rgba(154,123,46,0.30)",
        "brass":        "#9a7b2e",
        "brassDim":     "#7d6222",
        "brassMuted":   "rgba(154,123,46,0.08)",
        "verdigris":    "#1a7a6a",
        "verdigrisDim": "#156658",
        "verdigrisMuted":"rgba(26,122,106,0.08)",
        "rust":         "#b8432e",
        "rustDim":      "#963522",
        "chalk":        "#1a1d23",
        "chalkDim":     "#3a3834",
        "stone":        "#5c5650",
        "stoneDim":     "#8a837a",
        "criticalBg":   "rgba(184,67,46,0.06)",
        "info":         "#3a7a8a",
        "chartBlue":    "#3a7a8a",
    },
}

TYPE_SCALE = {
    "hero":    "2.4rem",
    "h1":      "1.5rem",
    "h2":      "1.15rem",
    "h3":      "0.95rem",
    "body":    "0.88rem",
    "caption": "0.76rem",
    "micro":   "0.70rem",
    "data":    "0.82rem",
}

STRATEGY_COLORS = {"strict": None, "standard": None, "lenient": None}  # resolved per theme

# ═══════════════════════════════════════════════════════════════
#  i18n Dictionary
# ═══════════════════════════════════════════════════════════════

T = {
    "zh": {
        "app_title": "FinAgent · 数据资产治理",
        "app_icon": "",
        "sidebar_brand": "FinAgent",
        "sidebar_subtitle": "数据资产治理",
        "sidebar_infra": "基础设施",
        "sidebar_key_label": "已配置",
        "sidebar_demo_label": "Demo 模式",
        "sidebar_manage": "管理",
        "sidebar_update_key": "更新密钥",
        "sidebar_save": "保存",
        "sidebar_clear": "清除",
        "sidebar_save_enable": "加密保存并启用",
        "sidebar_tracking": "追踪参数",
        "sidebar_scenario": "业务场景",
        "sidebar_scenarios": ["保险客服质检", "银行风险偏好", "反欺诈交易", "AI投顾合规", "跨境数据", "自定义"],
        "sidebar_sensitivity": "DIKW 敏感度",
        "sidebar_sensitivity_help": "越高则从信息到知识的跃迁条件越严格",
        "sidebar_strategy": "策略资产",
        "sidebar_strategies": {"strict": "严格", "standard": "标准", "lenient": "宽松"},
        "sidebar_decisions": "次决策",
        "sidebar_theme": "主题",
        "sidebar_lang": "语言",
        "hero_title": "数据资产治理",
        "hero_desc": "追踪每一步客户操作、每一条信息流、每一个Agent行为。通过 <span>{highlight}</span> 方法论将原始行为数据转化为可估值的数据资产。",
        "hero_tag_active": "资产化运行中",
        "hero_tag_paper": "徐心 & 蔡瑶, 2024",
        "tab_intake": "行为接入",
        "tab_dashboard": "资产仪表盘",
        "tab_strategy": "策略资产",
        "tab_attribution": "归因追溯",
        "tab_lineage": "数据血缘",
        "tab_step": "STEP 框架",
        "tab_compliance": "合规知识库",
        "intake_title": "接入行为数据",
        "intake_caption": "DIKW 流水线的数据源头——每一次客户操作、每一条Agent输出、每一笔金融信息流",
        "intake_template_expander": "场景模板（徐心 & 蔡瑶, 2024）",
        "intake_apply_template": "应用模板",
        "intake_text_label": "行为内容",
        "intake_run": "启动 DIKW 资产化",
        "intake_clear": "清空",
        "intake_meta_title": "行为元数据",
        "intake_meta_caption": "行为基础模型的七维特征向量输入",
        "intake_geo": "地理跳变 (km)",
        "intake_freq": "操作频率 (次/分)",
        "intake_amount": "金额偏离度",
        "intake_sensitive": "敏感词占比",
        "intake_device": "设备指纹重复度",
        "intake_history": "历史失败次数",
        "pipeline_spinner": "DIKW 资产化流水线运行中 — 原始数据 → 行为特征 → 知识发现 → 策略资产",
        "pipeline_mode_llm": "DeepSeek LLM",
        "pipeline_mode_rule": "规则引擎 (配置 API Key 以启用 LLM)",
        "pipeline_toast": "资产化完成 · 数据资产评分",
        "result_title": "最新资产化结果",
        "result_score": "数据资产评分",
        "result_anomaly": "行为异常度",
        "result_anomaly_normal": "正常",
        "result_anomaly_abnormal": "异常",
        "result_strategy": "推荐策略",
        "result_intervention": "干预层级",
        "result_intervention_sub": "DIKW 自动定位",
        "result_expander": "脱敏对比 & 合规报告",
        "result_original": "原始文本",
        "result_sanitized": "脱敏文本",
        "result_compliance": "合规检查明细",
        "result_llm_output": "LLM 分析输出",
        "tag_high": "高风险",
        "tag_medium": "中风险",
        "tag_low": "低风险",
        "dashboard_title": "数据资产仪表盘",
        "dashboard_caption": "DIKW 各层资产质量的实时快照与演化趋势",
        "dashboard_gauge": "当前资产质量",
        "dashboard_pie": "行为模式分布",
        "dashboard_history_title": "资产质量演化",
        "dashboard_history_caption": "最近 30 条记录的资产质量变化趋势",
        "dashboard_x_axis": "记录编号",
        "dashboard_empty_title": "尚未追踪客户行为",
        "dashboard_empty_desc": "在「行为接入」面板接入第一条客户操作或金融信息流后，资产质量变化趋势将在此呈现。",
        "strategy_title": "策略资产 · 自适应决策",
        "strategy_caption": "Thompson Sampling · 每条客户行为自动匹配最优治理策略 · 策略本身沉淀为可估值资产",
        "strategy_bandit_label": "多臂老虎机",
        "strategy_bandit_sub": "探索与利用的平衡",
        "strategy_bandit_sub2": "自动收敛至最优策略",
        "strategy_sim_rounds": "模拟轮数",
        "strategy_run_test": "运行收敛验证",
        "strategy_y_axis": "期望成功率",
        "strategy_x_axis": "试验次数",
        "strategy_current": "当前各策略期望成功率",
        "strategy_expected": "期望成功率",
        "attribution_title": "归因追溯 · 行为到资产的因果链",
        "attribution_caption": "DIKW 每一层跃迁的因果关系可追溯——徐心方法论: 从数据到智慧的每一步都有理论依据",
        "attribution_chain": "决策归因链",
        "attribution_layer": "干预层级",
        "attribution_strategy": "建议策略",
        "attribution_cycle": "重评估周期",
        "attribution_cycle_sub": "滚动窗口 · 自适应",
        "attribution_triggers": "阻断触发器",
        "attribution_triggers_caption": "满足任一条件触发干预",
        "attribution_features": "七维行为特征向量",
        "attribution_features_caption": "行为基础模型的特征提取结果",
        "attribution_feature_names": ["时间异常", "地理跳变", "操作频率", "金额偏离", "敏感词占比", "设备重复", "历史失败"],
        "attribution_empty_title": "接入行为后查看归因分析",
        "attribution_empty_desc": "在「行为接入」面板追踪一条客户操作或Agent行为后，DIKW各层跃迁的因果链将在此呈现。",
        "lineage_title": "DIKW 数据血缘",
        "lineage_caption": "双螺旋结构——数据螺旋与知识螺旋，端到端的数据资产演化路径",
        "lineage_select": "选择行为记录查看血缘",
        "lineage_data_spiral": "数据螺旋",
        "lineage_data_spiral_sub": "单点数据 → 全局信息 → 跨领域知识 → 预测未来",
        "lineage_knowledge_spiral": "知识螺旋",
        "lineage_knowledge_spiral_sub": "业务场景 → 理论指导 → 创造引领",
        "lineage_transitions": "层间跃迁记录",
        "lineage_layer_status": "DIKW 四层资产状态",
        "lineage_transition_count": "次转换",
        "lineage_empty_title": "接入行为后追踪数据血缘",
        "lineage_empty_desc": "在「行为接入」面板追踪一条客户操作后，DIKW四层中从原始数据到策略智慧的完整演化路径将在此呈现。",
        "lineage_global": "全局血缘概览",
        "lineage_total": "累计追踪记录",
        "lineage_avg": "平均跃迁步数",
        "lineage_top": "最多场景",
        "step_title": "STEP 数智链评估",
        "step_caption": "徐心 & 蔡瑶 (2024): Structure(组织结构) · Tool(手段工具) · Economic(经济机制) · Process(方式流程)",
        "step_tab1": "Structure 数智价值链",
        "step_tab2": "Tool 数据资产平台",
        "step_tab3": "Economic 经济机制",
        "step_tab4": "Process A/B 实验",
        "step_s1_title": "数智价值链 — Porter价值链 + 数智活动",
        "step_s1_caption": "在经典价值链基础上增加数智活动，包含数据、计算、评估三个职能",
        "step_s1_data_title": "数据职能 (Data → Information)",
        "step_s1_data_desc": "从价值链各活动采集整合数据资源，完成数据加工和特征工程。",
        "step_s1_data_sub": "DIKW对应: 数据整合 + 内部流通 + 隐私保护",
        "step_s1_comp_title": "计算职能 (Knowledge)",
        "step_s1_comp_desc": "基于机器学习等算法，以业务需求为导向，从大数据中挖掘商务智能。",
        "step_s1_comp_sub": "DIKW对应: 科学建模 + 理论指导 + 规律发现",
        "step_s1_eval_title": "评估职能 (Wisdom)",
        "step_s1_eval_desc": "科学衡量数智化项目产生的经济价值——构建科学的资产估值体系。",
        "step_s2_title": "数据资产管理平台 — 采 · 存 · 管 · 用",
        "step_s2_caption": "建立覆盖数据全生命周期的管理规范，支持以价值创造为导向的数据资产应用开发",
        "step_s2_stages": ["采集", "加工", "建模", "应用"],
        "step_s2_layers": ["Data Layer", "Info Layer", "Knowledge Layer", "Wisdom Layer"],
        "step_s2_descs": ["原始文本 + 元数据", "脱敏处理 + 特征提取", "合规检索 + LLM评分", "策略决策 + 归因"],
        "step_s2_lineage": "端到端数据血缘分析",
        "step_s2_lineage_caption": "构建面向企业数据资产的知识图谱，实现端到端的数据血缘分析",
        "step_s2_lineage_empty": "接入行为后生成数据血缘瀑布图",
        "step_s3_title": "经济机制 — 特征贡献度 & VRIO 分析",
        "step_s3_caption": "内部市场化 + 按贡献分配 + 构建可持续竞争优势",
        "step_s3_fi_title": "特征重要性归因",
        "step_s3_fi_caption": "各行为特征对数据资产评分的贡献度",
        "step_s3_fi_driver": "最大驱动因子",
        "step_s3_vrio_title": "VRIO 竞争力评估",
        "step_s3_vrio_caption": "Valuable · Rare · Inimitable · Organized",
        "step_s3_empty_title": "接入行为后查看经济机制分析",
        "step_s3_empty_desc": "追踪一条客户操作后，特征重要性归因和VRIO竞争力评估将在此呈现。",
        "step_s4_title": "A/B 对照实验 — 科学评估治理策略价值",
        "step_s4_caption": "因果推断方法评估数字化运营的经济价值和投资回报率",
        "step_s4_mgmt": "实验管理",
        "step_s4_name": "实验名称",
        "step_s4_desc": "实验描述",
        "step_s4_create": "创建新实验",
        "step_s4_options_title": "实物期权评估",
        "step_s4_options_caption": "分步分层投资，每阶段有选择权价值",
        "step_s4_results": "实验结果",
        "step_s4_empty_title": "创建实验开始对照测试",
        "step_s4_empty_desc": "点击「创建新实验」运行 A/B 对照测试，比较不同治理策略的效果。",
        "compliance_title": "合规知识库 · 数据资产的法律底座",
        "compliance_caption": "25 条监管条文 · DIKW体系Knowledge层的理论依据 · 每条资产化决策均有法可依",
        "compliance_filter": "按领域筛选",
        "compliance_filter_all": "全部领域",
        "compliance_not_found": "法规文件未找到，请运行初始化脚本。",
        "footer": "FinAgent v3.0 · 金融数据资产治理中心 · DIKW 数智流体系 (徐心 & 蔡瑶, 2024) · 每一步客户操作 → 可估值的数据资产",
        "vrio_verdicts": {0: "竞争劣势", 1: "竞争劣势", 2: "竞争均势", 3: "临时竞争优势", 4: "可持续竞争优势"},
        "vrio_pass": "满足",
        "vrio_fail": "未满足",
        "vrio_dim_labels": {
            "V_valuable": "有价值",
            "R_rarity": "稀缺性",
            "I_inimitability": "不可模仿",
            "O_organization": "组织有效",
        },
    },
    "en": {
        "app_title": "FinAgent · Data Asset Governance",
        "app_icon": "",
        "sidebar_brand": "FinAgent",
        "sidebar_subtitle": "Data Asset Governance",
        "sidebar_infra": "Infrastructure",
        "sidebar_key_label": "Configured",
        "sidebar_demo_label": "Demo mode",
        "sidebar_manage": "Manage",
        "sidebar_update_key": "Update key",
        "sidebar_save": "Save",
        "sidebar_clear": "Clear",
        "sidebar_save_enable": "Save & Enable",
        "sidebar_tracking": "Tracking",
        "sidebar_scenario": "Scenario",
        "sidebar_scenarios": ["Insurance Voice QA", "Bank Risk Preference", "Anti-fraud", "AI Advisor Compliance", "Cross-border Data", "Custom"],
        "sidebar_sensitivity": "DIKW Sensitivity",
        "sidebar_sensitivity_help": "Higher = stricter transition requirements from Information to Knowledge",
        "sidebar_strategy": "Strategy Assets",
        "sidebar_strategies": {"strict": "Strict", "standard": "Standard", "lenient": "Lenient"},
        "sidebar_decisions": "decisions",
        "sidebar_theme": "Theme",
        "sidebar_lang": "Language",
        "hero_title": "Data Asset Governance",
        "hero_desc": "Track every customer operation, every information flow, every Agent action. Transform raw behavioral data into measurable data assets through the <span>{highlight}</span> methodology.",
        "hero_tag_active": "Asset Pipeline Active",
        "hero_tag_paper": "Xu Xin & Cai Yao, 2024",
        "tab_intake": "Behavior Intake",
        "tab_dashboard": "Asset Dashboard",
        "tab_strategy": "Strategy Assets",
        "tab_attribution": "Attribution",
        "tab_lineage": "Data Lineage",
        "tab_step": "STEP Framework",
        "tab_compliance": "Compliance Base",
        "intake_title": "Ingest Behavior Data",
        "intake_caption": "The source of the DIKW pipeline — every customer action, Agent output, or financial information flow",
        "intake_template_expander": "Scenario templates (Xu Xin & Cai Yao, 2024)",
        "intake_apply_template": "Apply template",
        "intake_text_label": "Behavior content",
        "intake_run": "Run DIKW Pipeline",
        "intake_clear": "Clear",
        "intake_meta_title": "Behavioral Metadata",
        "intake_meta_caption": "Seven-dimension feature vector for the behavioral foundation model",
        "intake_geo": "Geo distance (km)",
        "intake_freq": "Action frequency (/min)",
        "intake_amount": "Amount deviation",
        "intake_sensitive": "Sensitive word ratio",
        "intake_device": "Device fingerprint repeat",
        "intake_history": "Historical failures",
        "pipeline_spinner": "DIKW Pipeline — Raw data → Behavioral features → Knowledge discovery → Strategy assets",
        "pipeline_mode_llm": "DeepSeek LLM",
        "pipeline_mode_rule": "Rule engine (configure API Key for LLM)",
        "pipeline_toast": "Pipeline complete · Asset score",
        "result_title": "Latest Result",
        "result_score": "Asset Score",
        "result_anomaly": "Behavioral Anomaly",
        "result_anomaly_normal": "Normal",
        "result_anomaly_abnormal": "Anomalous",
        "result_strategy": "Recommended Strategy",
        "result_intervention": "Intervention Layer",
        "result_intervention_sub": "DIKW auto-positioning",
        "result_expander": "Sanitization comparison & Compliance",
        "result_original": "Original text",
        "result_sanitized": "Sanitized text",
        "result_compliance": "Compliance check",
        "result_llm_output": "LLM analysis output",
        "tag_high": "High",
        "tag_medium": "Medium",
        "tag_low": "Low",
        "dashboard_title": "Asset Dashboard",
        "dashboard_caption": "Real-time snapshot and evolution of DIKW-layer data asset quality",
        "dashboard_gauge": "Current asset quality",
        "dashboard_pie": "Behavioral pattern distribution",
        "dashboard_history_title": "Quality Evolution",
        "dashboard_history_caption": "Asset quality trends across the 30 most recent records",
        "dashboard_x_axis": "Record",
        "dashboard_empty_title": "No behavior tracked yet",
        "dashboard_empty_desc": "Submit a customer action or financial information flow from the Behavior Intake tab to begin building asset quality history.",
        "strategy_title": "Strategy Assets · Adaptive Decision",
        "strategy_caption": "Thompson Sampling · Each customer behavior automatically matched to optimal governance strategy · Strategy itself accumulates as a measurable asset",
        "strategy_bandit_label": "Multi-Armed Bandit",
        "strategy_bandit_sub": "Exploration vs. exploitation",
        "strategy_bandit_sub2": "Auto-converges to optimal strategy",
        "strategy_sim_rounds": "Simulation rounds",
        "strategy_run_test": "Run convergence test",
        "strategy_y_axis": "Expected success rate",
        "strategy_x_axis": "Trials",
        "strategy_current": "Current expected success rate per strategy",
        "strategy_expected": "Expected Rate",
        "attribution_title": "Causal Attribution · Behavior to Asset Chain",
        "attribution_caption": "Every DIKW layer transition is causally traceable — per the Xu Xin methodology: every step from Data to Wisdom has a theoretical basis",
        "attribution_chain": "Decision Chain",
        "attribution_layer": "Intervention Layer",
        "attribution_strategy": "Strategy",
        "attribution_cycle": "Re-evaluation Cycle",
        "attribution_cycle_sub": "Rolling window · Adaptive",
        "attribution_triggers": "Block Triggers",
        "attribution_triggers_caption": "Any condition met triggers intervention",
        "attribution_features": "Seven-Dimensional Feature Vector",
        "attribution_features_caption": "Behavioral foundation model feature extraction",
        "attribution_feature_names": ["Temporal", "Geo Jump", "Action Freq", "Amount Dev", "Sensitive Ratio", "Device Repeat", "Hist Failures"],
        "attribution_empty_title": "Attribute analysis after first behavior intake",
        "attribution_empty_desc": "After tracking a customer action or Agent behavior in the Behavior Intake tab, the causal chain of DIKW layer transitions will appear here.",
        "lineage_title": "DIKW Lineage",
        "lineage_caption": "Dual Helix — Data Spiral and Knowledge Spiral, tracking the end-to-end evolution of data into assets",
        "lineage_select": "Select record to view lineage",
        "lineage_data_spiral": "Data Spiral",
        "lineage_data_spiral_sub": "Point data → Global → Cross-domain → Prediction",
        "lineage_knowledge_spiral": "Knowledge Spiral",
        "lineage_knowledge_spiral_sub": "Scenario → Theory → Creative Leadership",
        "lineage_transitions": "Layer Transitions",
        "lineage_layer_status": "DIKW Layer Status",
        "lineage_transition_count": "transitions",
        "lineage_empty_title": "Lineage tracking after first behavior intake",
        "lineage_empty_desc": "After tracking a customer action in the Behavior Intake tab, the complete DIKW evolution path — Data Spiral and Knowledge Spiral — will appear here.",
        "lineage_global": "Global Lineage Summary",
        "lineage_total": "Total Records",
        "lineage_avg": "Avg Transitions",
        "lineage_top": "Top Scenario",
        "step_title": "STEP Framework",
        "step_caption": "Xu Xin & Cai Yao (2024): Structure · Tool · Economic mechanism · Process",
        "step_tab1": "Structure",
        "step_tab2": "Tool",
        "step_tab3": "Economic",
        "step_tab4": "Process",
        "step_s1_title": "Digital-Intelligence Value Chain",
        "step_s1_caption": "Porter's value chain + digital-intelligence activities: Data, Computation, Evaluation",
        "step_s1_data_title": "Data Function (Data → Information)",
        "step_s1_data_desc": "Collect and integrate data from across the value chain. Complete data processing and feature engineering.",
        "step_s1_data_sub": "DIKW: Data integration + privacy protection",
        "step_s1_comp_title": "Computation Function (Knowledge)",
        "step_s1_comp_desc": "Apply machine learning algorithms guided by business needs and theory to mine business intelligence.",
        "step_s1_comp_sub": "DIKW: Scientific modeling + theory guidance",
        "step_s1_eval_title": "Evaluation Function (Wisdom)",
        "step_s1_eval_desc": "Scientifically measure the economic value created by digital-intelligence initiatives.",
        "step_s2_title": "Data Asset Management Platform — Collect · Store · Manage · Use",
        "step_s2_caption": "Full lifecycle data asset management supporting value-creation-oriented application development",
        "step_s2_stages": ["Collect", "Process", "Model", "Apply"],
        "step_s2_layers": ["Data Layer", "Info Layer", "Knowledge Layer", "Wisdom Layer"],
        "step_s2_descs": ["Raw text + metadata", "Sanitization + features", "Compliance + LLM scoring", "Strategy + attribution"],
        "step_s2_lineage": "End-to-End Data Lineage",
        "step_s2_lineage_caption": "Knowledge graph of data assets — from raw data to strategic wisdom",
        "step_s2_lineage_empty": "Data lineage waterfall will appear after first behavior intake",
        "step_s3_title": "Economic Mechanism: Feature Contribution & VRIO",
        "step_s3_caption": "Internal market mechanisms + Contribution-based allocation + Sustainable competitive advantage",
        "step_s3_fi_title": "Feature Importance",
        "step_s3_fi_caption": "Contribution of each behavioral feature to the asset score",
        "step_s3_fi_driver": "Primary driver",
        "step_s3_vrio_title": "VRIO Assessment",
        "step_s3_vrio_caption": "Valuable · Rare · Inimitable · Organized",
        "step_s3_empty_title": "Economic analysis after first behavior intake",
        "step_s3_empty_desc": "After tracking a customer action, feature importance attribution and VRIO competitive assessment will appear here.",
        "step_s4_title": "A/B Experiment — Scientific strategy evaluation",
        "step_s4_caption": "Causal inference methods for measuring economic value and ROI of digital operations",
        "step_s4_mgmt": "Experiment Management",
        "step_s4_name": "Experiment name",
        "step_s4_desc": "Description",
        "step_s4_create": "Create experiment",
        "step_s4_options_title": "Real Options Valuation",
        "step_s4_options_caption": "Step-wise investment with option value at each stage",
        "step_s4_results": "Experiment Results",
        "step_s4_empty_title": "Create an experiment to begin",
        "step_s4_empty_desc": "Click 'Create experiment' to run an A/B test comparing governance strategies.",
        "compliance_title": "Compliance Base · Legal foundation of data assets",
        "compliance_caption": "25 regulatory articles · Theoretical foundation for the Knowledge layer · Every asset governance decision is legally grounded",
        "compliance_filter": "Filter by domain",
        "compliance_filter_all": "All domains",
        "compliance_not_found": "Regulation file not found. Run the initialization script.",
        "footer": "FinAgent v3.0 · Financial Data Asset Governance · DIKW Methodology (Xu Xin & Cai Yao, 2024) · Every customer action → a measurable data asset",
        "vrio_verdicts": {0: "Competitive disadvantage", 1: "Competitive disadvantage", 2: "Competitive parity", 3: "Temporary advantage", 4: "Sustained advantage"},
        "vrio_pass": "Pass",
        "vrio_fail": "Fail",
        "vrio_dim_labels": {
            "V_valuable": "Valuable",
            "R_rarity": "Rare",
            "I_inimitability": "Inimitable",
            "O_organization": "Organized",
        },
    },
}


# ═══════════════════════════════════════════════════════════════
#  CSS Injection — Theme-aware
# ═══════════════════════════════════════════════════════════════

def inject_css(p):
    """Inject CSS using the given palette `p`."""
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@300;400;450;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    .stApp {{
        background: {p['bg']};
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: {p['chalk']};
    }}

    h1 {{
        font-family: 'Crimson Text', 'Georgia', serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.005em !important;
        color: {p['chalk']} !important;
    }}
    h2 {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        color: {p['chalk']} !important;
    }}
    h3 {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 550 !important;
        color: {p['chalkDim']} !important;
        font-size: {TYPE_SCALE['h3']} !important;
    }}

    .type-display {{
        font-family: 'Crimson Text', 'Georgia', serif;
        font-weight: 600;
    }}
    .type-mono {{
        font-family: 'JetBrains Mono', 'Consolas', monospace;
        font-weight: 400;
    }}
    .type-caption {{
        font-family: 'Inter', sans-serif;
        font-weight: 450;
        letter-spacing: 0.03em;
        font-size: {TYPE_SCALE['micro']};
        color: {p['stone']};
    }}

    [data-testid="stSidebar"] {{
        background: {p['bgDeep']} !important;
        border-right: 1px solid {p['border']} !important;
    }}
    [data-testid="stSidebar"] .stMarkdown {{ color: {p['chalk']} !important; }}
    [data-testid="stSidebar"] label {{
        color: {p['stone']} !important;
        font-size: {TYPE_SCALE['caption']} !important;
        font-weight: 500 !important;
        letter-spacing: 0.04em !important;
    }}

    .card {{
        background: {p['cardBg']};
        border: 1px solid {p['border']};
        border-radius: 6px;
        padding: 24px;
    }}

    .metric-card {{
        background: {p['cardBg']};
        border: 1px solid {p['border']};
        border-radius: 6px;
        padding: 20px 18px;
        text-align: center;
    }}
    .metric-value {{
        font-size: 2.2rem;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        color: {p['chalk']};
        line-height: 1.1;
    }}
    .metric-label {{
        font-size: {TYPE_SCALE['micro']};
        color: {p['stone']};
        letter-spacing: 0.06em;
        margin-top: 8px;
        font-weight: 500;
    }}

    .hero {{
        position: relative;
        padding: 32px 0 28px 0;
        margin-bottom: 24px;
        border-bottom: 1px solid {p['brassMuted']};
    }}
    .hero-rule {{
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 80px;
        height: 2px;
        background: {p['brass']};
    }}

    .dot {{
        display: inline-block;
        width: 7px; height: 7px;
        border-radius: 50%;
        margin-right: 8px;
        vertical-align: middle;
    }}
    .dot-active {{ background: {p['verdigris']}; box-shadow: 0 0 6px {p['verdigris']}44; }}
    .dot-warning {{ background: {p['brass']}; }}
    .dot-critical {{ background: {p['rust']}; }}
    @keyframes pulse-dot {{
        0%, 100% {{ box-shadow: 0 0 6px {p['verdigris']}44; }}
        50% {{ box-shadow: 0 0 12px {p['verdigris']}88; }}
    }}
    .dot-pulse {{ animation: pulse-dot 3s ease-in-out infinite; }}

    .tag {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: {TYPE_SCALE['micro']};
        font-weight: 550;
        letter-spacing: 0.03em;
        border: 1px solid transparent;
    }}
    .tag-brass   {{ color: {p['brass']}; border-color: {p['brassMuted']}; background: {p['brassMuted']}; }}
    .tag-verdigris {{ color: {p['verdigris']}; border-color: {p['verdigrisMuted']}; background: {p['verdigrisMuted']}; }}
    .tag-rust    {{ color: {p['rust']}; border-color: {p['criticalBg']}; background: {p['criticalBg']}; }}

    .stButton > button {{
        border-radius: 6px !important;
        font-weight: 550 !important;
        font-size: {TYPE_SCALE['body']} !important;
        letter-spacing: 0.01em !important;
        transition: all 0.15s ease !important;
        border: 1px solid transparent !important;
    }}
    .stButton > button[kind="primary"] {{
        background: {p['verdigris']} !important;
        border: none !important;
        color: white !important;
    }}
    .stButton > button:hover {{ filter: brightness(1.1); }}
    .stButton > button:focus-visible {{
        outline: 2px solid {p['verdigris']} !important;
        outline-offset: 2px !important;
    }}

    .stTextArea textarea, .stTextInput input, .stSelectbox > div > div {{
        border-radius: 6px !important;
        border: 1px solid {p['border']} !important;
        background: {p['surface']} !important;
        color: {p['chalk']} !important;
        font-size: {TYPE_SCALE['body']} !important;
    }}
    .stTextArea textarea:focus, .stTextInput input:focus {{
        border-color: {p['verdigris']} !important;
        box-shadow: 0 0 0 2px {p['verdigrisMuted']} !important;
    }}
    .stTextArea textarea::placeholder, .stTextInput input::placeholder {{
        color: {p['stoneDim']} !important;
    }}

    .stNumberInput > div > div {{
        border-radius: 6px !important;
        border: 1px solid {p['border']} !important;
        background: {p['surface']} !important;
    }}

    [data-testid="stTabs"] {{ background: transparent !important; }}
    .stTabs [role="tablist"] {{
        background: transparent;
        border-bottom: 1px solid {p['border']};
        padding: 0; gap: 0; border-radius: 0;
    }}
    .stTabs [role="tab"] {{
        border-radius: 0 !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        font-size: {TYPE_SCALE['body']} !important;
        color: {p['stone']} !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.15s ease !important;
        margin-bottom: -1px;
        background: transparent !important;
    }}
    .stTabs [role="tab"]:hover {{ color: {p['chalkDim']} !important; }}
    .stTabs [role="tab"]:focus-visible {{
        outline: 2px solid {p['verdigris']} !important;
        outline-offset: -2px !important;
    }}
    .stTabs [role="tab"][aria-selected="true"] {{
        color: {p['chalk']} !important;
        border-bottom-color: {p['brass']} !important;
        background: transparent !important;
    }}

    .streamlit-expanderHeader {{
        border-radius: 6px !important;
        background: {p['surface']} !important;
        border: 1px solid {p['border']} !important;
        color: {p['chalk']} !important;
    }}
    .streamlit-expanderHeader:focus-visible {{
        outline: 2px solid {p['verdigris']} !important;
        outline-offset: 2px !important;
    }}

    .rule {{
        height: 1px;
        background: {p['border']};
        margin: 28px 0;
    }}

    .footer {{
        text-align: center;
        padding: 28px 24px;
        color: {p['stoneDim']};
        font-size: {TYPE_SCALE['micro']};
        border-top: 1px solid {p['border']};
        margin-top: 48px;
        letter-spacing: 0.02em;
    }}

    ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(138,148,158,0.18);
        border-radius: 3px;
    }}

    @keyframes cardReveal {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .reveal-1 {{ animation: cardReveal 0.35s ease-out both; animation-delay: 0.03s; }}
    .reveal-2 {{ animation: cardReveal 0.35s ease-out both; animation-delay: 0.08s; }}
    .reveal-3 {{ animation: cardReveal 0.35s ease-out both; animation-delay: 0.13s; }}
    .reveal-4 {{ animation: cardReveal 0.35s ease-out both; animation-delay: 0.18s; }}

    .empty-state {{
        text-align: center;
        padding: 40px 24px;
        border: 1px dashed {p['border']};
        border-radius: 6px;
        background: {p['cardBg']};
    }}
    .empty-state-title {{
        font-weight: 600;
        font-size: {TYPE_SCALE['h3']};
        color: {p['chalkDim']};
        margin-bottom: 8px;
    }}
    .empty-state-desc {{
        font-size: {TYPE_SCALE['body']};
        color: {p['stone']};
        max-width: 440px;
        margin: 0 auto;
        line-height: 1.6;
    }}

    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }}
    }}

    .stAlert {{ border-radius: 6px !important; border: 1px solid {p['border']} !important; }}
    [data-testid="stDataFrame"] {{ border: 1px solid {p['border']} !important; border-radius: 6px; }}
    </style>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════

def mask_key(key: str, visible: int = 7) -> str:
    if not key: return "Not configured"
    if len(key) <= visible + 4: return key[:3] + "***"
    return f"{key[:visible]}...{key[-4:]}"

def load_api_key_status() -> dict:
    try:
        from finguard.crypto_utils import has_stored_key, decrypt_api_key
        k = decrypt_api_key()
        return {"configured": bool(k), "masked_key": mask_key(k), "has_stored": has_stored_key()}
    except Exception:
        return {"configured": False, "masked_key": "", "has_stored": False}

def metric_card(label: str, value: str, sub: str = "", reveal_delay: int = 0, accent: str = "") -> str:
    delay_class = f"reveal-{reveal_delay}" if reveal_delay > 0 else ""
    accent_style = f"border-top: 2px solid {accent};" if accent else ""
    return f"""
    <div class="metric-card {delay_class}" style="{accent_style}">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {f'<div style="font-size:0.7rem;padding-top:6px;">{sub}</div>' if sub else ''}
    </div>"""

def empty_state(title: str, description: str) -> str:
    return f"""
    <div class="empty-state">
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-desc">{description}</div>
    </div>"""

def score_tag(score: float, p, t) -> str:
    if score > 0.55: return f'<span class="tag tag-rust">{t["tag_high"]} {score:.2f}</span>'
    elif score > 0.25: return f'<span class="tag tag-brass">{t["tag_medium"]} {score:.2f}</span>'
    else: return f'<span class="tag tag-verdigris">{t["tag_low"]} {score:.2f}</span>'

def score_color(score: float, p) -> str:
    if score > 0.55: return p['rust']
    if score > 0.25: return p['brass']
    return p['verdigris']

def card(inner_html: str, reveal_delay: int = 0) -> str:
    delay_class = f"reveal-{reveal_delay}" if reveal_delay > 0 else ""
    return f'<div class="card {delay_class}">{inner_html}</div>'

# ═══════════════════════════════════════════════════════════════
#  Session State
# ═══════════════════════════════════════════════════════════════

if "bandit" not in st.session_state:
    st.session_state.bandit = ThompsonBandit(config.mab.arms)
if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "api_key_loaded" not in st.session_state:
    try:
        from finguard.crypto_utils import decrypt_api_key
        s = decrypt_api_key()
        st.session_state.api_key_loaded = bool(s)
        if s: config.llm.api_key = s
    except Exception:
        st.session_state.api_key_loaded = False
if "lineage_store" not in st.session_state:
    st.session_state.lineage_store = {}
if "active_experiment" not in st.session_state:
    st.session_state.active_experiment = None
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"
if "lang" not in st.session_state:
    st.session_state.lang = "zh"
if "intake_text" not in st.session_state:
    st.session_state.intake_text = ""

bandit = st.session_state.bandit

# ═══════════════════════════════════════════════════════════════
#  Resolve theme & language for initial page config
# ═══════════════════════════════════════════════════════════════

_init_p = THEMES[st.session_state.theme]
_init_t = T[st.session_state.lang]

# ═══════════════════════════════════════════════════════════════
#  Page Config — MUST be first Streamlit command
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title=_init_t["app_title"],
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css(_init_p)

# ═══════════════════════════════════════════════════════════════
#  Sidebar — inline, no function wrapper
# ═══════════════════════════════════════════════════════════════

with st.sidebar:
    # Theme & Language toggles — on_change callback updates session_state
    def on_theme_change():
        st.session_state.theme = st.session_state._tw
    def on_lang_change():
        st.session_state.lang = st.session_state._lw

    col_theme, col_lang = st.columns(2)
    with col_theme:
        st.selectbox(
            _init_t["sidebar_theme"], ["Dark", "Light"],
            index=0 if st.session_state.theme == "Dark" else 1,
            key="_tw",
            on_change=on_theme_change,
        )
    with col_lang:
        st.selectbox(
            _init_t["sidebar_lang"], ["中文", "English"],
            index=0 if st.session_state.lang == "zh" else 1,
            key="_lw",
            on_change=on_lang_change,
        )

    # Re-resolve after potential on_change (for the rest of sidebar + main)
    p = THEMES[st.session_state.theme]
    t = T[st.session_state.lang]
    STRATEGY_COLORS["strict"] = p['rust']
    STRATEGY_COLORS["standard"] = p['brass']
    STRATEGY_COLORS["lenient"] = p['verdigris']

    # Brand
    st.markdown(f"""
    <div style="padding:12px 0 16px 0;">
        <div class="type-display" style="font-size:1.5rem;color:{p['chalk']};">
            {t["sidebar_brand"]}
        </div>
        <div class="type-caption" style="margin-top:3px;">{t["sidebar_subtitle"]}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="rule"></div>', unsafe_allow_html=True)

    # Infrastructure
    st.markdown(t["sidebar_infra"])
    ks = load_api_key_status()
    if ks["configured"]:
        st.markdown(f'<div class="tag tag-verdigris" style="margin-bottom:8px;"><span class="dot dot-active dot-pulse"></span>{t["sidebar_key_label"]} {ks["masked_key"]}</div>', unsafe_allow_html=True)
        with st.expander(t["sidebar_manage"]):
            nk = st.text_input(t["sidebar_update_key"], type="password", placeholder="sk-xxx", key="update_key")
            c1, c2 = st.columns(2)
            with c1:
                if st.button(t["sidebar_save"], use_container_width=True, key="btn_save"):
                    if nk and nk.startswith("sk-"):
                        from finguard.crypto_utils import encrypt_api_key
                        encrypt_api_key(nk.strip(), persist=True)
                        config.llm.api_key = nk.strip()
                        st.session_state.api_key_loaded = True
                        st.rerun()
            with c2:
                if st.button(t["sidebar_clear"], use_container_width=True, key="btn_clear"):
                    from finguard.crypto_utils import clear_api_key
                    clear_api_key()
                    config.llm.api_key = ""
                    st.session_state.api_key_loaded = False
                    st.rerun()
    else:
        st.markdown(f'<div class="tag tag-brass" style="margin-bottom:8px;"><span class="dot dot-warning"></span>{t["sidebar_demo_label"]}</div>', unsafe_allow_html=True)
        nk = st.text_input("API Key", type="password", placeholder="sk-xxx...", key="new_key")
        if st.button(t["sidebar_save_enable"], type="primary", use_container_width=True, key="btn_set"):
            if nk and nk.startswith("sk-"):
                from finguard.crypto_utils import encrypt_api_key
                encrypt_api_key(nk.strip(), persist=True)
                config.llm.api_key = nk.strip()
                st.session_state.api_key_loaded = True
                st.rerun()

    st.markdown(f'<div class="rule"></div>', unsafe_allow_html=True)

    # Tracking params
    st.markdown(t["sidebar_tracking"])
    scenario_labels = t["sidebar_scenarios"]
    scenario = st.selectbox(t["sidebar_scenario"], scenario_labels)
    context_level = st.slider(t["sidebar_sensitivity"], 0.0, 1.0, 0.5, 0.05, help=t["sidebar_sensitivity_help"])

    st.markdown(f'<div class="rule"></div>', unsafe_allow_html=True)

    # Strategy assets
    st.markdown(t["sidebar_strategy"])
    ev = bandit.expected_values()
    strategy_labels = t["sidebar_strategies"]
    for s in bandit.arms:
        color = STRATEGY_COLORS.get(s, p['stone'])
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;">'
            f'<span style="color:{p["stone"]};font-size:{TYPE_SCALE["caption"]};">{strategy_labels.get(s, s)}</span>'
            f'<span style="font-weight:650;font-size:0.95rem;color:{color};">{ev[s]:.1%}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    st.caption(f"{bandit.total_trials} {t['sidebar_decisions']} · Thompson Sampling")

# After sidebar, resolve p/t for main content (read from session_state)
p = THEMES[st.session_state.theme]
t = T[st.session_state.lang]
STRATEGY_COLORS["strict"] = p['rust']
STRATEGY_COLORS["standard"] = p['brass']
STRATEGY_COLORS["lenient"] = p['verdigris']

# ═══════════════════════════════════════════════════════════════
#  Page Config & CSS
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title=t["app_title"],
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css(p)

# ═══════════════════════════════════════════════════════════════
#  Hero
# ═══════════════════════════════════════════════════════════════

st.markdown(f"""
<div class="hero">
    <div class="hero-rule"></div>
    <h1 style="font-size:{TYPE_SCALE['hero']};margin:24px 0 0 0;line-height:1.15;">
        {t['hero_title']}
    </h1>
    <p style="margin:10px 0 0 0;color:{p['stone']};font-size:{TYPE_SCALE['body']};line-height:1.6;max-width:680px;">
        {t['hero_desc'].format(highlight='<span style="color:' + p['chalkDim'] + ';">DIKW</span>')}
    </p>
    <div style="margin-top:14px;display:flex;gap:12px;">
        <span class="tag tag-verdigris"><span class="dot dot-active"></span>{t['hero_tag_active']}</span>
        <span class="tag tag-brass">{t['hero_tag_paper']}</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  Tabs
# ═══════════════════════════════════════════════════════════════

tabs = st.tabs([
    t["tab_intake"], t["tab_dashboard"], t["tab_strategy"],
    t["tab_attribution"], t["tab_lineage"], t["tab_step"],
    t["tab_compliance"],
])


# ─── Tab 1: Behavior Intake ──────────────────

with tabs[0]:
    col_input, col_meta = st.columns([2, 1])

    with col_input:
        st.markdown(f"### {t['intake_title']}")
        st.caption(t["intake_caption"])

        with st.expander(t["intake_template_expander"]):
            templates = get_all_templates()
            template_id = st.selectbox(
                "Scenario",
                list(templates.keys()),
                format_func=lambda k: f"{templates[k]['industry'].title()} · {templates[k]['name']}",
                label_visibility="collapsed",
                key="template_sel",
            )
            if st.button(t["intake_apply_template"], use_container_width=True, key="apply_tmpl"):
                tmpl = apply_template(template_id)
                if tmpl:
                    st.session_state.intake_text = tmpl.get("sample_input", "")
                    st.rerun()

        # Use session_state to make template application work
        text_val = st.session_state.intake_text or (
            "尊敬的客户，您的账户存在异常登录行为，请立即点击链接验证身份信息。\n登录IP: 192.168.1.100\n验证链接: http://fake-bank.com/verify"
            if st.session_state.lang == "zh" else
            "Dear customer, your account shows an unusual login pattern. Please verify your identity immediately.\nLogin IP: 192.168.1.100\nVerification link: http://fake-bank.com/verify"
        )
        input_text = st.text_area(
            t["intake_text_label"],
            value=text_val,
            height=176,
            label_visibility="collapsed",
            key="intake_text",
        )

        b1, b2 = st.columns([3, 1])
        with b1:
            evaluate_btn = st.button(t["intake_run"], type="primary", use_container_width=True)
        with b2:
            if st.button(t["intake_clear"], use_container_width=True, key="clear_input"):
                st.session_state.intake_text = ""
                st.rerun()

    with col_meta:
        st.markdown(f"### {t['intake_meta_title']}")
        st.caption(t["intake_meta_caption"])
        geo_distance   = st.number_input(t["intake_geo"], 0, 10000, 0, 100)
        freq           = st.number_input(t["intake_freq"], 0, 100, 1)
        amount_dev     = st.number_input(t["intake_amount"], 0.0, 200.0, 0.0, 10.0)
        sensitive_ratio = st.slider(t["intake_sensitive"], 0.0, 1.0, 0.1, 0.05)
        device_repeat   = st.slider(t["intake_device"], 0.0, 1.0, 0.0, 0.05)
        history_fail    = st.slider(t["intake_history"], 0, 20, 0)

    if evaluate_btn and input_text:
        with st.spinner(t["pipeline_spinner"]):
            sanitizer_tool = DataSanitizerTool()
            sanitize_result = sanitizer_tool.call({"text": input_text})
            sanitized = sanitize_result["sanitized_text"]
            compliance = sanitize_result["report"]

            behavior_tool = BehaviorAnalyzerTool()
            meta = {
                "timestamp": datetime.now(), "geo_distance_km": geo_distance,
                "action_freq_per_min": freq, "amount_deviation": amount_dev,
                "sensitive_word_ratio": sensitive_ratio, "device_fingerprint_repeat": device_repeat,
                "history_failures": history_fail,
            }
            behavior_result = behavior_tool.call({"meta": meta})
            anomaly = behavior_result["anomaly_score"]
            features = list(behavior_result["features"].values())

            compliance_tool = ComplianceSearchTool()
            compliance_result = compliance_tool.call({"query": sanitized[:500], "top_k": 5})
            rag_evidence = compliance_result["results"]

            risk_tool = RiskScorerTool()
            if config.llm.api_key:
                configure_llm(model=config.llm.model, base_url=config.llm.model_server, api_key=config.llm.api_key)
            risk_result = risk_tool.call({
                "scenario": scenario, "content": sanitized,
                "behavior_anomaly": anomaly, "rag_evidence": rag_evidence,
                "history_summary": "No prior incidents", "context_level": context_level,
            })
            risk_score = risk_result["risk_score"]
            risk_type = risk_result["primary_risk_type"]
            indicators_data = risk_result["key_indicators"]
            indicators = [i["indicator"] if isinstance(i, dict) else str(i) for i in indicators_data[:5]]
            llm_raw = risk_result.get("raw_response", "")
            mode = t["pipeline_mode_llm"] if config.llm.api_key else t["pipeline_mode_rule"]

            strategy_name, mab_samples = bandit.pull()

            audit_id = f"eval_{len(st.session_state.history)+1:04d}"
            lineage = create_lineage(audit_id, scenario)
            lineage.record_transition(
                from_layer=DIKWLayer.DATA, to_layer=DIKWLayer.INFORMATION,
                spiral_type=SpiralType.DATA_SPIRAL,
                input_summary=f"Raw text ({len(input_text)} chars)",
                output_summary=f"Sanitized + 7-dim feature vector",
                transformation=f"DataSanitizer ({sanitize_result['masked_count']} types) + BehaviorAnalyzer (anomaly={anomaly:.2f})",
                context=f"Scenario: {scenario}",
                tool_used="data_sanitizer, behavior_analyzer",
            )
            lineage.record_transition(
                from_layer=DIKWLayer.DATA, to_layer=DIKWLayer.INFORMATION,
                spiral_type=SpiralType.KNOWLEDGE_SPIRAL,
                input_summary=f"Raw text ({len(input_text)} chars)",
                output_summary=f"Sanitized text + anomaly score {anomaly:.2f}",
                transformation=f"Processing raw data within business scenario '{scenario}'",
                context=scenario, tool_used="data_sanitizer",
            )
            lineage.record_transition(
                from_layer=DIKWLayer.INFORMATION, to_layer=DIKWLayer.KNOWLEDGE,
                spiral_type=SpiralType.DATA_SPIRAL,
                input_summary="Behavioral features + sanitized text",
                output_summary=f"Asset score {risk_score:.2f} + {len(rag_evidence)} regulations",
                transformation=f"ComplianceSearch ({len(rag_evidence)} refs) + RiskScorer (score={risk_score:.2f})",
                context="Regulatory compliance + LLM semantic analysis",
                tool_used="compliance_search, risk_scorer",
            )
            lineage.record_transition(
                from_layer=DIKWLayer.INFORMATION, to_layer=DIKWLayer.KNOWLEDGE,
                spiral_type=SpiralType.KNOWLEDGE_SPIRAL,
                input_summary=f"Anomaly {anomaly:.2f} + sanitized text",
                output_summary=f"Risk type: {risk_type}",
                transformation="Financial regulations + risk assessment theory guiding pattern discovery",
                context="Financial regulation + behavioral decision theory",
                tool_used="risk_scorer",
            )
            lineage.record_transition(
                from_layer=DIKWLayer.KNOWLEDGE, to_layer=DIKWLayer.WISDOM,
                spiral_type=SpiralType.DATA_SPIRAL,
                input_summary=f"Asset score {risk_score:.2f} + MAB samples",
                output_summary=f"Strategy={strategy_name} (MAB confidence={max(mab_samples.values()):.1%})",
                transformation=f"Thompson Sampling to select {strategy_name}",
                context="From known risk to predicted optimal strategy",
                tool_used="mab_bandit",
            )
            lineage.record_transition(
                from_layer=DIKWLayer.KNOWLEDGE, to_layer=DIKWLayer.WISDOM,
                spiral_type=SpiralType.KNOWLEDGE_SPIRAL,
                input_summary=f"Asset score {risk_score:.2f}",
                output_summary=f"Strategy={strategy_name}, layer={'Knowledge' if risk_score > 0.5 else 'Information'}",
                transformation="Creative application of MAB + explainable attribution",
                context="Creative leadership: adaptive governance strategy",
                tool_used="mab_bandit, explainable_selector",
            )
            st.session_state.lineage_store[audit_id] = lineage

            st.session_state.last_result = {
                "id": audit_id, "sanitized_text": sanitized,
                "compliance_report": compliance, "anomaly_score": anomaly,
                "features": features, "risk_score": risk_score,
                "risk_type": risk_type, "indicators": indicators,
                "rag_evidence": rag_evidence, "mab_samples": mab_samples,
                "recommended_strategy": strategy_name,
                "mab_confidence": max(mab_samples.values()) if mab_samples else 0.0,
                "causal_attribution": f"MAB sampling: strict={mab_samples.get('strict',0):.2f} standard={mab_samples.get('standard',0):.2f} lenient={mab_samples.get('lenient',0):.2f} -> {strategy_name}",
                "intervention_layer": "Knowledge" if risk_score > 0.5 else "Information",
                "block_triggers": [
                    f"Asset score exceeds threshold ({0.3 if strategy_name=='strict' else 0.6})",
                    f"Behavioral anomaly exceeds threshold ({0.3 if strategy_name=='strict' else 0.7})"
                ],
                "actions": [
                    "Flag for human review" if strategy_name == "strict"
                    else "Secondary review" if strategy_name == "standard"
                    else "Auto-approve"
                ],
                "recommendations": [
                    "Re-evaluate within 24 hours" if risk_score < 0.3
                    else "Increase review frequency"
                ],
                "mode": mode, "llm_raw": llm_raw,
            }
            st.session_state.history.append(st.session_state.last_result)
            st.toast(f"{t['pipeline_toast']} {risk_score:.2f}")

    if st.session_state.last_result:
        r = st.session_state.last_result
        st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
        st.markdown(f"### {t['result_title']} `{r.get('mode', '')}`")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(metric_card(t["result_score"], f'{r["risk_score"]:.3f}',
                                    score_tag(r["risk_score"], p, t), reveal_delay=1), unsafe_allow_html=True)
        with c2:
            st.markdown(metric_card(t["result_anomaly"], f'{r["anomaly_score"]:.3f}',
                                    t["result_anomaly_abnormal"] if r["anomaly_score"] > 0.5 else t["result_anomaly_normal"],
                                    reveal_delay=2), unsafe_allow_html=True)
        with c3:
            st.markdown(metric_card(t["result_strategy"], r["recommended_strategy"].upper(),
                                    f"MAB confidence {r['mab_confidence']:.0%}", reveal_delay=3), unsafe_allow_html=True)
        with c4:
            st.markdown(metric_card(t["result_intervention"], r["intervention_layer"],
                                    t["result_intervention_sub"], reveal_delay=4), unsafe_allow_html=True)

        with st.expander(t["result_expander"]):
            cr1, cr2 = st.columns(2)
            with cr1:
                st.caption(t["result_original"])
                st.text_area("raw", input_text, height=120, disabled=True, label_visibility="collapsed")
            with cr2:
                st.caption(t["result_sanitized"])
                st.text_area("san", r["sanitized_text"], height=120, disabled=True, label_visibility="collapsed")
            st.caption(t["result_compliance"])
            st.json(r["compliance_report"])
            if r.get("llm_raw"):
                with st.expander(t["result_llm_output"]):
                    st.code(r["llm_raw"], language="json")


# ═══════════════════════════════════════════════════════════════
# ─── Tab 2: Asset Dashboard ───────────────────

with tabs[1]:
    st.markdown(f"### {t['dashboard_title']}")
    st.caption(t["dashboard_caption"])

    if st.session_state.last_result:
        r = st.session_state.last_result
        col_gauge, col_pie = st.columns([1, 1])
        with col_gauge:
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=r["risk_score"],
                number={"font": {"size": 48, "color": p['chalk'], "family": "Inter"}},
                title={"text": t["dashboard_gauge"], "font": {"size": 13, "color": p['stone']}},
                gauge={
                    "axis": {"range": [0, 1], "tickcolor": p['stone'], "tickfont": {"size": 10}},
                    "bar": {"color": score_color(r["risk_score"], p), "thickness": 0.18},
                    "bgcolor": p['surface'],
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0, 0.3], "color": p['verdigrisMuted']},
                        {"range": [0.3, 0.7], "color": p['brassMuted']},
                        {"range": [0.7, 1.0], "color": p['criticalBg']},
                    ],
                },
            ))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=320, margin=dict(t=40, b=0), font_color=p['stone'])
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with col_pie:
            if st.session_state.history:
                type_counts = {}
                for h in st.session_state.history:
                    rt = h.get("risk_type", "safe")
                    type_counts[rt] = type_counts.get(rt, 0) + 1
                labels, values = list(type_counts.keys()), list(type_counts.values())
                pie_map = {"phishing": p['rust'], "compliance": p['brass'], "data_leak": p['info'], "misleading": p['verdigris'], "safe": p['verdigrisDim']}
                marker_colors = [pie_map.get(l, p['stoneDim']) for l in labels]
            else:
                labels, values = ["Compliance", "Data Leak", "Misleading", "Hallucination", "Safe"], [20, 15, 25, 10, 30]
                marker_colors = [p['brass'], p['info'], p['verdigris'], "#8b7aa0", p['verdigrisDim']]
            fig = go.Figure([go.Pie(labels=labels, values=values, hole=0.58, marker_colors=marker_colors, textinfo="label+percent", textfont_color=p['chalkDim'], textfont_size=12)])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=320, margin=dict(t=20, b=0), showlegend=False, title={"text": t["dashboard_pie"], "font": {"size": 13, "color": p['stone']}})
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if st.session_state.history:
        st.markdown(f"### {t['dashboard_history_title']}")
        st.caption(t["dashboard_history_caption"])
        df = pd.DataFrame([{t["dashboard_x_axis"]: h["id"][-4:], "Asset Score": h["risk_score"], "Anomaly": h["anomaly_score"], "Strategy": h["recommended_strategy"]} for h in st.session_state.history[-30:]])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df[t["dashboard_x_axis"]], y=df["Asset Score"], mode="lines+markers", name="Asset Score", line=dict(color=p['verdigris'], width=2.5), fill="tozeroy", fillcolor=p['verdigrisMuted'], marker=dict(size=6)))
        fig.add_trace(go.Scatter(x=df[t["dashboard_x_axis"]], y=df["Anomaly"], mode="lines+markers", name="Anomaly", line=dict(color=p['brass'], width=2), marker=dict(size=5)))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=360, yaxis_range=[0, 1], yaxis_title="Score", xaxis_title="Record", font_color=p['stone'], hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02))
        fig.update_xaxes(showgrid=False); fig.update_yaxes(showgrid=True, gridcolor=p['border'])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown(empty_state(t["dashboard_empty_title"], t["dashboard_empty_desc"]), unsafe_allow_html=True)

# ─── Tab 3: Strategy Assets ───────────────────

with tabs[2]:
    st.markdown(f"### {t['strategy_title']}")
    st.caption(t["strategy_caption"])
    col_plot, col_ctrl = st.columns([3, 1])
    with col_ctrl:
        st.markdown(card(f"""<div style="text-align:center;"><div style="font-weight:700;font-size:1rem;">{t['strategy_bandit_label']}</div><div style="font-size:0.82rem;margin-top:4px;">{t['strategy_bandit_sub']}</div><div style="font-size:0.72rem;margin-top:4px;">{t['strategy_bandit_sub2']}</div></div>"""), unsafe_allow_html=True)
        sim_rounds = st.number_input(t["strategy_sim_rounds"], 10, 500, 100, 10)
        if st.button(t["strategy_run_test"], type="primary", use_container_width=True):
            random.seed(42); test_b = ThompsonBandit(config.mab.arms)
            true_rates = {"strict": 0.8, "standard": 0.5, "lenient": 0.3}
            for _ in range(sim_rounds):
                chosen, _ = test_b.pull()
                test_b.update(chosen, 0.9 if random.random() < true_rates[chosen] else 0.3)
            st.session_state.bandit = test_b; bandit = test_b
            st.rerun()
    with col_plot:
        fig = go.Figure()
        hist = bandit.convergence_data()
        for s in bandit.arms:
            if hist["trials"]:
                fig.add_trace(go.Scatter(x=hist["trials"], y=hist[s], mode="lines", name=s, line=dict(color=STRATEGY_COLORS.get(s, p['verdigris']), width=2.5)))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=420, yaxis_range=[0, 1], yaxis_title=t["strategy_y_axis"], xaxis_title=t["strategy_x_axis"], font_color=p['stone'], hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02))
        fig.update_xaxes(showgrid=False); fig.update_yaxes(showgrid=True, gridcolor=p['border'])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    st.caption(t["strategy_current"])
    cols = st.columns(len(bandit.arms))
    ev = bandit.expected_values()
    for i, (col, (s, v)) in enumerate(zip(cols, ev.items())):
        with col:
            color = STRATEGY_COLORS.get(s, p['verdigris'])
            st.markdown(f"""<div class="metric-card reveal-{i+1}" style="border-left:3px solid {color};"><div style="font-size:0.9rem;font-weight:600;">{s}</div><div style="font-size:1.8rem;font-weight:700;color:{color};margin:8px 0;">{v:.2%}</div><div class="metric-label">{t['strategy_expected']}</div></div>""", unsafe_allow_html=True)

# ─── Tab 4: Attribution ───────────────────────

with tabs[3]:
    st.markdown(f"### {t['attribution_title']}")
    st.caption(t["attribution_caption"])
    if st.session_state.last_result:
        r = st.session_state.last_result
        st.markdown(card(f"""<div style="display:flex;align-items:flex-start;gap:16px;"><div style="font-weight:700;font-size:0.95rem;">{t['attribution_chain']}</div><div style="line-height:1.65;">{r['causal_attribution']}</div></div>"""), unsafe_allow_html=True)
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1: st.markdown(metric_card(t["attribution_layer"], r["intervention_layer"], t["result_intervention_sub"], reveal_delay=1), unsafe_allow_html=True)
        with col_d2: st.markdown(metric_card(t["attribution_strategy"], r["recommended_strategy"].upper(), f"MAB confidence {r['mab_confidence']:.0%}", reveal_delay=2), unsafe_allow_html=True)
        with col_d3: st.markdown(metric_card(t["attribution_cycle"], "24h", t["attribution_cycle_sub"], reveal_delay=3), unsafe_allow_html=True)
        st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
        col_trig, col_feat = st.columns([1, 1.5])
        with col_trig:
            st.markdown(f"**{t['attribution_triggers']}**")
            st.caption(t["attribution_triggers_caption"])
            for tr in r.get("block_triggers", []):
                st.markdown(f'<div class="tag tag-rust" style="margin:4px 0;">{tr}</div>', unsafe_allow_html=True)
        with col_feat:
            st.markdown(f"**{t['attribution_features']}**")
            st.caption(t["attribution_features_caption"])
            if r.get("features"):
                fnames = t["attribution_feature_names"]
                fvals = r["features"]
                fcolors = [p['rust'] if v > 0.6 else p['brass'] if v > 0.3 else p['verdigris'] for v in fvals]
                fig = go.Figure(go.Bar(x=fnames, y=fvals, marker_color=fcolors, text=[f"{v:.2f}" for v in fvals], textposition="outside", textfont_color=p['chalkDim'], textfont_size=11))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=320, yaxis_range=[0, 1.05], yaxis_title="Feature value", font_color=p['stone'])
                fig.update_xaxes(showgrid=False); fig.update_yaxes(showgrid=True, gridcolor=p['border'])
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown(empty_state(t["attribution_empty_title"], t["attribution_empty_desc"]), unsafe_allow_html=True)

# ─── Tab 5: Lineage ───────────────────────────

with tabs[4]:
    st.markdown(f"### {t['lineage_title']}")
    st.caption(t["lineage_caption"])
    if st.session_state.lineage_store:
        lineage_id = st.selectbox(t["lineage_select"], list(st.session_state.lineage_store.keys()))
        if lineage_id:
            lin = st.session_state.lineage_store[lineage_id]; helix = lin.dual_helix_view()
            col_data, col_know = st.columns(2)
            with col_data:
                st.markdown(f"""<div class="card" style="border-left:2px solid {p['verdigris']};"><div style="font-weight:650;color:{p['verdigris']};margin-bottom:8px;">{t['lineage_data_spiral']}</div><div style="font-size:{TYPE_SCALE['caption']};margin-bottom:8px;">{t['lineage_data_spiral_sub']}</div>{"".join(f'<div style="padding:5px 0;font-size:{TYPE_SCALE["body"]};">{s["stage"]}: {s["desc"]}</div>' for s in helix["data_spiral"]["steps"])}</div>""", unsafe_allow_html=True)
            with col_know:
                st.markdown(f"""<div class="card" style="border-left:2px solid {p['brass']};"><div style="font-weight:650;color:{p['brass']};margin-bottom:8px;">{t['lineage_knowledge_spiral']}</div><div style="font-size:{TYPE_SCALE['caption']};margin-bottom:8px;">{t['lineage_knowledge_spiral_sub']}</div>{"".join(f'<div style="padding:5px 0;font-size:{TYPE_SCALE["body"]};">{s["stage"]}: {s["desc"]}<br><span style="font-size:{TYPE_SCALE["caption"]};">{s["context"]}</span></div>' for s in helix["knowledge_spiral"]["steps"])}</div>""", unsafe_allow_html=True)
            st.markdown(f"#### {t['lineage_transitions']}")
            transitions = lin.to_dict()["transitions"]
            if transitions:
                df_trans = pd.DataFrame([{"Transition": f"{tr['from']} -> {tr['to']}", "Spiral": tr['spiral'], "Method": tr['transformation'][:64], "Context": tr['context'][:40], "Tool": tr['tool']} for tr in transitions])
                st.dataframe(df_trans, use_container_width=True, hide_index=True)
            st.markdown(f"#### {t['lineage_layer_status']}")
            summary = lin.summarize()
            lcolors = {"Data": p['info'], "Information": p['verdigris'], "Knowledge": p['brass'], "Wisdom": p['rust']}
            cols_layer = st.columns(4)
            for col, (ln, li) in zip(cols_layer, summary.items()):
                with col:
                    st.markdown(f"""<div class="metric-card" style="border-top:2px solid {lcolors[ln]};"><div style="font-weight:650;color:{lcolors[ln]};font-size:0.9rem;">{ln}</div><div style="font-size:0.72rem;margin-top:4px;">{li['description']}</div><div style="font-size:1.4rem;font-weight:700;color:{lcolors[ln]};margin-top:8px;">{li['transformations']}</div><div class="metric-label">{t['lineage_transition_count']}</div><div style="font-size:0.66rem;margin-top:4px;">{', '.join(li['tools']) if li['tools'] else 'none'}</div></div>""", unsafe_allow_html=True)
    else:
        st.markdown(empty_state(t["lineage_empty_title"], t["lineage_empty_desc"]), unsafe_allow_html=True)
    if st.session_state.lineage_store:
        st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
        st.markdown(f"#### {t['lineage_global']}")
        ls = lineage_summary()
        c1, c2, c3 = st.columns(3)
        with c1: st.metric(t["lineage_total"], ls["total"])
        with c2: st.metric(t["lineage_avg"], f"{ls['avg_transitions']:.1f}")
        with c3: st.metric(t["lineage_top"], max(ls["by_scenario"].items(), key=lambda x: x[1])[0] if ls["by_scenario"] else "N/A")

# ─── Tab 6: STEP Framework ────────────────────

with tabs[5]:
    st.markdown(f"### {t['step_title']}")
    st.caption(t["step_caption"])
    s1, s2, s3, s4 = st.tabs([t["step_tab1"], t["step_tab2"], t["step_tab3"], t["step_tab4"]])
    with s1:
        st.markdown(f"#### {t['step_s1_title']}"); st.caption(t["step_s1_caption"])
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""<div class="card"><div style="font-weight:650;color:{p['verdigris']};margin-bottom:10px;">{t['step_s1_data_title']}</div><div style="font-size:{TYPE_SCALE['body']};line-height:1.6;">{t['step_s1_data_desc']}<br><span style="font-size:{TYPE_SCALE['caption']};">{t['step_s1_data_sub']}</span></div><div style="margin-top:10px;"><span class="tag tag-verdigris">data_sanitizer</span> <span class="tag tag-verdigris">behavior_analyzer</span></div></div>""", unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""<div class="card"><div style="font-weight:650;color:{p['brass']};margin-bottom:10px;">{t['step_s1_comp_title']}</div><div style="font-size:{TYPE_SCALE['body']};line-height:1.6;">{t['step_s1_comp_desc']}<br><span style="font-size:{TYPE_SCALE['caption']};">{t['step_s1_comp_sub']}</span></div><div style="margin-top:10px;"><span class="tag tag-brass">compliance_search</span> <span class="tag tag-brass">risk_scorer</span></div></div>""", unsafe_allow_html=True)
        st.markdown(f"""<div class="card" style="margin-top:12px;"><div style="font-weight:650;color:{p['rust']};margin-bottom:10px;">{t['step_s1_eval_title']}</div><div style="font-size:{TYPE_SCALE['body']};line-height:1.6;">{t['step_s1_eval_desc']}</div><div style="margin-top:10px;"><span class="tag tag-rust">MAB strategy</span> <span class="tag tag-verdigris">Explainable attribution</span></div></div>""", unsafe_allow_html=True)
    with s2:
        st.markdown(f"#### {t['step_s2_title']}"); st.caption(t["step_s2_caption"])
        stages = t["step_s2_stages"]; layers_s2 = t["step_s2_layers"]; descs_s2 = t["step_s2_descs"]
        stage_colors = [p['brass'], p['verdigris'], p['brass'], p['rust']]
        cols_lc = st.columns(4)
        for i, (sg, ly, ds, sc) in enumerate(zip(stages, layers_s2, descs_s2, stage_colors)):
            with cols_lc[i]:
                st.markdown(f"""<div class="metric-card" style="border-top:2px solid {sc};"><div style="font-weight:650;color:{sc};font-size:1rem;">{sg}</div><div style="font-size:0.7rem;margin-top:2px;">{ly}</div><div style="font-size:0.68rem;margin-top:6px;">{ds}</div></div>""", unsafe_allow_html=True)
        st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
        st.markdown(f"**{t['step_s2_lineage']}**"); st.caption(t["step_s2_lineage_caption"])
        if st.session_state.lineage_store:
            fig = go.Figure(go.Bar(
                x=[100, 80, 60, 40],
                y=["Raw Data", "Information", "Knowledge", "Wisdom"],
                orientation='h',
                marker_color=[p['brass'], p['verdigris'], p['brass'], p['rust']],
                text=[100, 80, 60, 40],
                textposition="outside",
                textfont_color=p['chalkDim'],
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=250, margin=dict(l=40, r=40), font_color=p['stone'],
                xaxis_title="Assets retained through each layer (%)",
            )
            fig.update_xaxes(range=[0, 110], showgrid=True, gridcolor=p['border'])
            fig.update_yaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info(t["step_s2_lineage_empty"])
    with s3:
        st.markdown(f"#### {t['step_s3_title']}"); st.caption(t["step_s3_caption"])
        if st.session_state.last_result:
            r = st.session_state.last_result
            col_fi, col_vrio = st.columns([1, 1])
            with col_fi:
                st.markdown(f"**{t['step_s3_fi_title']}**"); st.caption(t["step_s3_fi_caption"])
                fd = {k: (r.get("features", [0]*7)[i] if len(r.get("features", [])) > i else 0) for i, k in enumerate(["temporal","geo_distance","action_freq","amount_dev","sensitive_ratio","device_repeat","hist_failures"])}
                fi = compute_feature_importance(fd, r["risk_score"])
                if fi["features"]:
                    fig = go.Figure(go.Bar(x=[v["percentage"] for v in fi["features"].values()], y=[v["label"] for v in fi["features"].values()], orientation='h', marker_color=[p['rust'] if float(v["percentage"].rstrip('%'))>30 else p['brass'] if float(v["percentage"].rstrip('%'))>15 else p['verdigris'] for v in fi["features"].values()], text=[f"{v['contribution']:.4f}" for v in fi["features"].values()], textposition="outside"))
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=280, margin=dict(l=120, r=60), font_color=p['stone'], xaxis_title="Contribution %")
                    fig.update_xaxes(showgrid=True, gridcolor=p['border']); st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                    st.markdown(f"""<div class="card" style="text-align:center;margin-top:8px;"><span>{t['step_s3_fi_driver']}: </span><span style="color:{p['brass']};font-weight:650;">{fi['top_driver_label']}</span><span style="font-size:0.8rem;margin-left:8px;">({fi['features'][fi['top_driver']]['percentage']})</span></div>""", unsafe_allow_html=True)
            with col_vrio:
                st.markdown(f"**{t['step_s3_vrio_title']}**"); st.caption(t["step_s3_vrio_caption"])
                vrio = vrio_analysis({"risk_score": r["risk_score"], "uses_llm": bool(config.llm.api_key), "rag_evidence_count": len(r.get("rag_evidence", [])), "mab_trials": bandit.total_trials, "feedback_count": len(st.session_state.history)})
                vc_map = {0: p['rust'], 1: p['rust'], 2: p['brass'], 3: p['brass'], 4: p['verdigris']}
                vc = vc_map.get(vrio["pass_count"], p['stone'])
                st.markdown(f"""<div class="card" style="text-align:center;margin-bottom:12px;border:2px solid {vc};"><div style="font-weight:650;color:{vc};font-size:1.1rem;">{t['vrio_verdicts'].get(vrio['pass_count'], 'Unknown')}</div><div style="font-size:0.78rem;margin-top:4px;">{vrio['pass_count']}/4</div></div>""", unsafe_allow_html=True)
                for dim, info in vrio["dimensions"].items():
                    mark = t["vrio_pass"] if info['score'] else t["vrio_fail"]
                    color = p['verdigris'] if info['score'] else p['stoneDim']
                    st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid {p['border']};"><span style="font-size:{TYPE_SCALE['caption']};">{info['label']}</span><span style="color:{color};font-size:{TYPE_SCALE['caption']};font-weight:550;">{mark}</span></div>""", unsafe_allow_html=True)
        else:
            st.markdown(empty_state(t["step_s3_empty_title"], t["step_s3_empty_desc"]), unsafe_allow_html=True)
    with s4:
        st.markdown(f"#### {t['step_s4_title']}"); st.caption(t["step_s4_caption"])
        col_ab1, col_ab2 = st.columns([1, 1])
        with col_ab1:
            st.markdown(f"**{t['step_s4_mgmt']}**")
            en = st.text_input(t["step_s4_name"], "strategy_comparison_v1"); ed = st.text_area(t["step_s4_desc"], "Compare strict vs standard vs lenient")
            if st.button(t["step_s4_create"], type="primary", use_container_width=True):
                exp = create_experiment(en, ed); st.session_state.active_experiment = en
                import random; random.seed(42)
                for _ in range(100): exp.control.record("pass" if random.random()<0.5 else "block", random.randint(300,1200))
                for tr in exp.treatments:
                    rate = 0.8 if tr.strategy=="strict" else (0.3 if tr.strategy=="lenient" else 0.5)
                    for _ in range(100): tr.record("pass" if random.random()<rate else "block", random.randint(100,1000))
                st.rerun()
            st.markdown(f"**{t['step_s4_options_title']}**"); st.caption(t["step_s4_options_caption"])
            st.markdown(f"""<div class="card"><div style="font-size:{TYPE_SCALE['caption']};line-height:1.8;"><b>Stage 1</b> (Data→Info) — Data integration option<br><span>Cost: Data cleaning + platform</span><br><b>Stage 2</b> (Info→Knowledge) — Model development option<br><span>Cost: Algorithm R&D + theory validation</span><br><b>Stage 3</b> (Knowledge→Wisdom) — Strategy deployment option<br><span>Cost: A/B testing + business integration</span><br><div style="margin-top:8px;color:{p['brass']};font-weight:550;">Each completed stage grants an option to proceed to the next</div></div></div>""", unsafe_allow_html=True)
        with col_ab2:
            st.markdown(f"**{t['step_s4_results']}**")
            experiments = get_all_experiments()
            if experiments:
                evn = st.selectbox("Select", list(experiments.keys()))
                if evn and experiments[evn]:
                    ed2 = experiments[evn]
                    if isinstance(ed2, dict):
                        st.markdown(f"Total: {ed2['total_samples']} · Best: **{ed2['best_group']}**")
                        for g in ed2.get("groups", []):
                            bc = p['verdigris'] if g['name']==ed2['best_group'] else p['stone']
                            st.markdown(f"""<div class="card" style="margin-bottom:8px;border-left:2px solid {bc};"><div style="display:flex;justify-content:space-between;"><span style="font-weight:600;">{g['name']}</span><span>{g['strategy']}</span></div><div style="display:flex;gap:24px;margin-top:8px;font-size:{TYPE_SCALE['caption']};"><span>Success: <b style="color:{bc};">{g['success_rate']:.1%}</b></span><span>Samples: {g['sample_size']}</span><span>Latency: {g['avg_latency_ms']:.0f}ms</span></div></div>""", unsafe_allow_html=True)
                        if ed2.get("lift_analysis"):
                            st.markdown("**Significance**")
                            for la in ed2["lift_analysis"]:
                                sc = p['verdigris'] if la['significant'] else p['stone']
                                st.markdown(f"""<div style="font-size:{TYPE_SCALE['caption']};padding:3px 0;">{la['treatment']} vs control: lift {la['lift']} (z={la['z_score']}) <span style="color:{sc};">{la['verdict']}</span></div>""", unsafe_allow_html=True)
            else:
                st.markdown(empty_state(t["step_s4_empty_title"], t["step_s4_empty_desc"]), unsafe_allow_html=True)

# ─── Tab 7: Compliance Base ───────────────────

with tabs[6]:
    st.markdown(f"### {t['compliance_title']}")
    st.caption(t["compliance_caption"])
    reg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base", "regulations", "finance_regulations.json")
    try:
        with open(reg_path, "r", encoding="utf-8") as f: regs = json.load(f)
        categories = sorted(set(r["category"] for r in regs))
        cat_labels = {'data_privacy':'Data Privacy','data_security':'Data Security','data_cross_border':'Cross-border','ai_governance':'AI Governance','aml':'AML','consumer_protection':'Consumer Protection'}
        selected_cats = st.multiselect(t["compliance_filter"], categories, default=[], placeholder=t["compliance_filter_all"], format_func=lambda c: cat_labels.get(c, c))
        filtered = regs if not selected_cats else [r for r in regs if r["category"] in selected_cats]
        cols = st.columns(2)
        for i, reg in enumerate(filtered):
            with cols[i%2]:
                bc_map = {'data_privacy':'tag-verdigris','data_security':'tag-brass','data_cross_border':'tag-rust','ai_governance':'tag-verdigris','aml':'tag-rust','consumer_protection':'tag-verdigris'}
                bc = bc_map.get(reg['category'], 'tag-verdigris')
                cl = cat_labels.get(reg['category'], reg['category']); cf = reg.get('penalty', '')
                st.markdown(f"""<div class="card" style="margin-bottom:12px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;"><span style="font-weight:600;font-size:{TYPE_SCALE['body']};">{reg['source']} {reg['article']}</span><span class="tag {bc}">{cl}</span></div><p style="font-size:{TYPE_SCALE['caption']};line-height:1.6;margin:0;">{reg['content']}</p><div style="margin-top:8px;font-size:{TYPE_SCALE['micro']};display:flex;gap:16px;"><span>Penalty: {cf if cf else 'Per regulation'}</span><span class="type-mono">{reg['id']}</span></div></div>""", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(t["compliance_not_found"])

# ═══════════════════════════════════════════════════════════════
#  Footer
# ═══════════════════════════════════════════════════════════════

st.markdown(f"""
<div class="footer">
    {t['footer']}
</div>
""", unsafe_allow_html=True)
