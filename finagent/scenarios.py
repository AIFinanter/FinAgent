"""
Business Scenario Templates — 基于论文案例的预配置场景

论文案例:
  1. 保险公司: 客服语音质检 — 情绪检测 → 服务质量预测 (10x 效率)
  2. 商业银行: 客户风险偏好 — 行为大数据 → 投资组合调整 (10x 转化率)

将这些案例抽象为可复用的审计场景模板，加速部署。
"""

from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class ScenarioTemplate:
    """业务场景模板"""
    id: str
    name: str
    industry: str          # insurance | banking | fintech | general
    description: str
    typical_risks: List[str]
    sample_input: str
    metadata_defaults: dict
    rag_search_query: str
    paper_reference: str = ""


# ── 论文案例场景模板 ──────────────────────────

SCENARIO_TEMPLATES = {
    "insurance_voice_qa": ScenarioTemplate(
        id="insurance_voice_qa",
        name="保险客服语音质检",
        industry="insurance",
        description=(
            "参照论文案例: 保险公司2022年客服中心投入4071亿元，积攒海量语音通话数据。"
            "传统人工质检只能覆盖2%的通话记录，通过DIKW数智流改造后质检效率提高10倍。"
        ),
        typical_risks=[
            "误导性保险条款解释",
            "承诺保证收益 (违反保险法)",
            "未经授权收集个人健康信息",
            "AI坐席幻觉——编造不存在的保险产品",
        ],
        sample_input=(
            "尊敬的客户您好，根据我们的AI分析系统，您目前的健康状况完全符合我们的"
            "'终身无忧'保险计划。这款产品保证年化收益不低于5%，而且您的所有医疗记录"
            "我们已经从医院系统获取了，不需要您额外提供。建议您立即签约，锁定收益。"
        ),
        metadata_defaults={
            "sensitive_word_ratio": 0.4,
            "device_fingerprint_repeat": 0.9,
            "history_failures": 0,
        },
        rag_search_query="保险销售合规 误导性宣传 个人信息收集 保证收益",
        paper_reference="数智流论文: 从数据到智慧——情绪计算平台案例",
    ),
    "bank_risk_preference": ScenarioTemplate(
        id="bank_risk_preference",
        name="银行客户风险偏好分析",
        industry="banking",
        description=(
            "参照论文案例: 商业银行整合借记卡、理财、网银、营销等多部门数据，"
            "通过数据驱动的风险偏好测量方法，相比高频浏览推荐策略，"
            "基于风险偏好的推荐使购买转化率提高10倍。"
        ),
        typical_risks=[
            "未经客户授权的风险偏好画像",
            "误导性理财产品推荐 (夸大收益)",
            "客户交易数据泄露风险",
            "跨境数据传输未评估",
        ],
        sample_input=(
            "根据您的交易记录和浏览行为，系统判定您为高风险偏好型投资者。"
            "我们为您推荐这款'激进增长'私募产品，历史年化收益20%以上，"
            "最大回撤仅5%。目前已有3000+位高端客户参与，建议您配置至少50万。"
            "您的账户经理将在一小时内联系您确认申购。"
        ),
        metadata_defaults={
            "amount_deviation": 80.0,
            "action_freq_per_min": 5,
            "sensitive_word_ratio": 0.3,
        },
        rag_search_query="理财产品销售适当性 风险测评 KYC 私募合格投资者",
        paper_reference="数智流论文: 从信息到知识——投资组合风险调整规律",
    ),
    "antifraud_transaction": ScenarioTemplate(
        id="antifraud_transaction",
        name="反欺诈交易监测",
        industry="banking",
        description=(
            "金融交易反欺诈场景: 监测异常交易模式、洗钱嫌疑、"
            "账户盗用等风险。关联DIKW数据螺旋——从单笔交易数据到全局欺诈模式识别。"
        ),
        typical_risks=[
            "洗钱结构性交易 (分拆大额)",
            "账户盗用——异常设备/地理位置",
            "电信诈骗诱导转账",
            "虚拟货币非法资金转移",
        ],
        sample_input=(
            "尊敬的客户，您的账户于2024年6月18日凌晨3:15在境外登录，"
            "并尝试向未知账户转账50,000美元。系统已暂时冻结您的账户，"
            "请立即拨打400-888-8888进行身份验证以解冻账户。"
            "为加快处理，请提供您的身份证号和银行卡密码。"
        ),
        metadata_defaults={
            "geo_distance_km": 8000,
            "action_freq_per_min": 12,
            "amount_deviation": 150.0,
            "sensitive_word_ratio": 0.5,
            "device_fingerprint_repeat": 0.1,
            "history_failures": 5,
        },
        rag_search_query="反洗钱 可疑交易报告 大额交易 客户身份识别",
        paper_reference="论文: 反洗钱法 + 金融机构大额交易和可疑交易报告管理办法",
    ),
    "ai_investment_advice": ScenarioTemplate(
        id="ai_investment_advice",
        name="AI 投资顾问合规审计",
        industry="fintech",
        description=(
            "针对AI投顾/智能投顾输出内容的合规审计。参照论文STEP框架——"
            "需要将数字技术与业务模式紧密结合，以推动业务增长、"
            "再造核心业务模式作为数字战略的核心目标。"
        ),
        typical_risks=[
            "AI幻觉——编造不存在的金融产品和收益率",
            "未披露AI身份 (应告知用户正在与AI交互)",
            "超出执业牌照范围的投资建议",
            "未做适当性匹配即推荐高风险产品",
        ],
        sample_input=(
            "我是您的AI投资顾问小财。经过对全球市场的深度学习分析，"
            "我发现了一只即将爆发的AI概念股——'星辰科技'(代码600888)。"
            "根据我的神经网络模型预测，该股票在未来30天内将有至少40%的涨幅。"
            "这个预测的准确率在我的历史记录中是100%。建议您立即满仓买入。"
        ),
        metadata_defaults={
            "sensitive_word_ratio": 0.15,
            "action_freq_per_min": 8,
        },
        rag_search_query="AI投顾合规 投资咨询牌照 适当性管理 禁止预测承诺",
        paper_reference="数智流论文: STEP框架 + 生成式人工智能服务管理暂行办法",
    ),
    "data_cross_border": ScenarioTemplate(
        id="data_cross_border",
        name="数据跨境传输合规",
        industry="general",
        description=(
            "金融数据跨境传输合规审计。涉及个人信息保护法第38条、"
            "数据安全法、数据出境安全评估等法规。"
            "对应论文中DIKW Data层的'数据整合及内部流通涉及用户隐私保护问题'。"
        ),
        typical_risks=[
            "未通过安全评估即向境外传输金融数据",
            "用户未被告知数据跨境传输",
            "跨境传输范围超出业务必要性",
            "未与境外接收方签订标准合同",
        ],
        sample_input=(
            "项目需求: 将2024年Q1的全部客户交易数据(包括姓名、身份证号、"
            "银行卡号、交易金额、交易时间、IP地址)上传至AWS新加坡节点"
            "(ap-southeast-1)进行AI模型训练。数据传输使用HTTP协议，"
            "不加密。目前项目已启动，数据正在上传中。"
        ),
        metadata_defaults={
            "sensitive_word_ratio": 0.8,
            "geo_distance_km": 4500,
            "amount_deviation": 0,
        },
        rag_search_query="数据出境安全评估 个人信息保护法第38条 跨境数据传输标准合同",
        paper_reference="数智流论文: 数据安全法 + 个人信息保护法 + 数据出境安全评估办法",
    ),
}


def get_all_templates() -> dict:
    """获取所有场景模板"""
    return {k: {
        "id": t.id,
        "name": t.name,
        "industry": t.industry,
        "description": t.description,
        "typical_risks": t.typical_risks,
        "paper_reference": t.paper_reference,
    } for k, t in SCENARIO_TEMPLATES.items()}


def get_template(template_id: str) -> ScenarioTemplate:
    """获取指定场景模板"""
    return SCENARIO_TEMPLATES.get(template_id)


def apply_template(template_id: str) -> dict:
    """
    应用场景模板 — 返回预设的输入文本、元数据和检索查询。

    用于 Streamlit UI 的"快速填充"功能。
    """
    t = get_template(template_id)
    if not t:
        return {}

    return {
        "scenario": t.name,
        "sample_input": t.sample_input,
        "metadata_defaults": t.metadata_defaults,
        "rag_query": t.rag_search_query,
        "industry": t.industry,
        "description": t.description,
    }
