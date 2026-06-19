"""
金融内容风险分析器 — 基于规则的多维度风险检测

覆盖 6 大金融风险领域:
  1. 洗钱 (Money Laundering)
  2. 诈骗 (Fraud)
  3. 非法集资 (Illegal Fundraising)
  4. 数据泄露 (Data Leak)
  5. 市场操纵 (Market Manipulation)
  6. 合规违规 (Compliance Violation)

基于关键词 + 模式匹配的轻量级检测，作为 Demo 模式和 LLM 的前置过滤器。
"""

import re
from typing import List, Tuple


# ═══════════════════════════════════════════════════════
#  风险词库 (6 领域 × N 模式)
# ═══════════════════════════════════════════════════════

RISK_PATTERNS: List[Tuple[str, str, float, List[str]]] = [
    # ── 1. 洗钱 ──
    ("money_laundering", "洗钱", 0.40, [
        "洗钱", "洗黑钱", "黑钱", "赃款", "非法资金", "资金转移", "地下钱庄",
        "匿名账户", "虚假交易", "壳公司", "空壳公司", "离岸账户", "跨境转移",
        "大额现金", "分拆交易", "结构化交易", "可疑交易", "资金来源不明",
        "掩饰隐瞒犯罪所得", "帮助转移资金", "跑分", "跑分平台", "虚拟货币洗钱",
        "USDT洗钱", "比特币洗钱", "加密货币转移", "分散转移",
        "匿名", "不可追踪", "无记录", "隐蔽", "掩护",
        "化名", "代持", "人头账户", "地下", "暗网",
    ]),
    # ── 2. 诈骗 ──
    ("fraud", "诈骗", 0.35, [
        "诈骗", "欺诈", "骗局", "杀猪盘", "庞氏骗局", "传销", "非法集资",
        "高回报", "稳赚不赔", "保本保息", "零风险", "保证收益", "包赚",
        "内幕消息", "必涨", "稳赢", "百分百盈利", "日收益", "月收益.*%",
        "冒充公检法", "冒充客服", "安全账户", "保证金", "解冻费", "手续费",
        "验证码", "短信验证", "需要提供密码",
        "已经赚了", "跟单", "老师带单", "稳赚", "躺赚",
    ]),
    # ── 3. 非法集资 ──
    ("illegal_fundraising", "非法集资", 0.30, [
        "非法集资", "众筹", "私募", "股权投资", "原始股", "虚拟币", "数字货币投资",
        "区块链项目", "挖矿收益", "年化收益.*%", "月化.*%", "分红",
        "拉人头", "下线", "团队计酬", "层级返利", "静态收益", "动态收益",
    ]),
    # ── 4. 数据泄露 ──
    ("data_leak", "数据泄露", 0.30, [
        "身份证号", "银行卡号", "密码", "明文", "不加密", "裸数据",
        "个人隐私", "用户数据.*出售", "数据交易", "信息贩卖", "社工库",
        "拖库", "撞库", "数据外泄", "未授权访问", "越权",
        "姓名.*身份证.*银行卡.*手机",
        "数据同步.*境外", "传输.*不加密", "未加密传输", "明文传输",
        "无保护", "开放访问", "公开可查", "任意访问",
        "用户隐私", "泄露", "外泄", "流出",
        "境外.*服务器", "跨境数据", "出国.*数据",
        "数据.*出国", "数据.*出境", "数据.*跨境",
    ]),
    # ── 5. 市场操纵 ──
    ("market_manipulation", "市场操纵", 0.25, [
        "操纵市场", "坐庄", "对敲", "对倒", "拉抬", "打压", "出货",
        "老鼠仓", "抢先交易", "幌骗", "虚假申报", "市场操纵",
        "建议立即买入", "建议立即卖出", "马上买入", "清仓",
    ]),
    # ── 6. 合规违规 ──
    ("compliance", "合规违规", 0.30, [
        "绕过监管", "规避审查", "未经批准", "不合规", "灰色地带",
        "境外.*传输.*未评估", "未脱敏", "未加密传输", "无资质",
        "无牌照", "超范围经营", "未经授权", "伪造资质",
        "绕过.*评估", "规避.*监管", "不经过.*审批", "跳过了",
        "没报备", "私下", "隐蔽操作", "打擦边球", "钻空子",
        "安全评估.*跳过", "跳过.*安全", "不经过.*评估",
    ]),
    # ── 7. 钓鱼/社工 ──
    ("phishing", "钓鱼攻击", 0.25, [
        "立即点击", "请点击链接", "点击验证", "登录验证", "重新认证",
        "账户冻结", "账户异常", "系统升级.*验证", "重新激活",
        "http://(?!localhost)[^/]*\\.(com|cn|net|top|xyz|tk|ml|ga)",
        "bit\\.ly", "tinyurl", "short\\.link",
        "点击.*链接.*验证", "扫码.*验证",
    ]),
    # ── 8. AI 幻觉/误导 ──
    ("ai_hallucination", "AI幻觉", 0.20, [
        "根据AI分析.*必涨", "AI预测.*保证", "AI模型.*确定性",
        "从未亏损", "绝对准确", "100%准确", "零失误",
        "AI.*内幕", "人工智能.*预测.*涨跌",
    ]),
]


# ═══════════════════════════════════════════════════════
#  敏感信息正则 (与 data_layer 互补)
# ═══════════════════════════════════════════════════════

SENSITIVE_REGEX = [
    (r'\d{17}[\dXx]', '身份证号(18位)', 0.15),
    (r'\d{15}(?:\d{2}[\dXx])?', '身份证号', 0.10),
    (r'62\d{14,17}', '银行卡号(银联)', 0.10),
    (r'1[3-9]\d{9}', '手机号', 0.05),
    (r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 'IP地址', 0.03),
    (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '邮箱', 0.03),
    (r'密码[：:]\s*[\w\d]+', '明文密码', 0.20),
    (r'验证码[：:]\s*\d{4,6}', '明文验证码', 0.15),
]


# ═══════════════════════════════════════════════════════

def analyze_content(text: str, anomaly_score: float = 0.0) -> dict:
    """
    对金融文本进行多维度风险分析

    Args:
        text: 待检测文本
        anomaly_score: 行为模型异常分 (0-1)

    Returns:
        {
            "risk_score": float,      # 综合风险评分 0-1
            "risk_type": str,         # 主风险类型
            "indicators": [str],      # 检出的风险指示器
            "categories": {str: float}, # 各领域风险得分
        }
    """
    text_lower = text.lower()
    category_scores = {}
    all_indicators = []

    # 1. 关键词匹配
    for category, label, base_weight, keywords in RISK_PATTERNS:
        score = 0.0
        matched = []
        for kw in keywords:
            # 支持简单正则
            matches = re.findall(kw, text, re.IGNORECASE)
            if matches:
                match_count = len(matches)
                # 每个匹配词加分，但同类词有上限
                score += min(match_count * base_weight, base_weight * 3)
                if kw not in matched:
                    matched.append(kw)

        if score > 0:
            category_scores[category] = min(score, 0.9)
            all_indicators.append(f"[{label}] {', '.join(matched[:4])}")

    # 2. 敏感信息正则检测
    sensitive_score = 0.0
    for pattern, label, weight in SENSITIVE_REGEX:
        matches = re.findall(pattern, text)
        if matches:
            sensitive_score += min(len(matches) * weight, weight * 5)
            all_indicators.append(f"检测到{label}({len(matches)}处)")

    if sensitive_score > 0:
        category_scores["data_leak"] = max(category_scores.get("data_leak", 0), min(sensitive_score, 0.9))

    # 3. 综合风险评分
    max_cat_score = max(category_scores.values()) if category_scores else 0.0
    # 多领域命中加分
    bonus = min(0.2, len(category_scores) * 0.05)
    # 基础: 最高领域分 + 多领域加成 + 行为异常分
    risk_score = max_cat_score * 0.55 + anomaly_score * 0.30 + bonus
    risk_score = min(1.0, risk_score)

    # 4. 确定主风险类型
    if category_scores:
        primary_category = max(category_scores, key=category_scores.get)
        # 映射到系统风险类型
        type_map = {
            "money_laundering": "compliance",
            "fraud": "misleading",
            "illegal_fundraising": "compliance",
            "data_leak": "data_leak",
            "market_manipulation": "misleading",
            "compliance": "compliance",
            "phishing": "misleading",
            "ai_hallucination": "hallucination",
        }
        risk_type = type_map.get(primary_category, "compliance")
    elif risk_score > 0.3:
        risk_type = "misleading"
    else:
        risk_type = "safe"

    return {
        "risk_score": risk_score,
        "risk_type": risk_type,
        "indicators": all_indicators[:8],  # 最多 8 个指示器
        "categories": {k: round(v, 3) for k, v in sorted(category_scores.items(), key=lambda x: -x[1])},
    }
