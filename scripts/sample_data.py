"""
样例数据 — 覆盖 5 种金融场景

用于验证端到端 DIKW 流水线
"""

# 场景 1: 钓鱼邮件检测
SAMPLE_PHISHING = {
    "id": "SAMPLE-001",
    "scenario": "phishing",
    "raw_text": (
        "尊敬的用户您好，检测到您的银行账户存在异常登录行为。"
        "请立即点击以下链接验证身份信息：http://fake-bank.com/verify\n"
        "登录IP: 192.168.1.100\n"
        "姓名：王小明\n"
        "身份证330102198512345678\n"
        "卡号6222021234567890\n"
        "联系电话13800138000\n"
        "若未在24小时内验证，账户将被冻结！"
    ),
    "metadata": {
        "geo_distance_km": 5000,
        "action_freq_per_min": 15,
        "amount_deviation": 0,
        "sensitive_word_ratio": 0.3,
        "device_fingerprint_repeat": 0.1,
        "history_failures": 3,
    },
}

# 场景 2: 异常登录 (凌晨)
SAMPLE_ANOMALOUS_LOGIN = {
    "id": "SAMPLE-002",
    "scenario": "login",
    "raw_text": (
        "您的账户于凌晨03:15在异地登录，设备型号UnknownDevice。"
        "登录IP: 10.0.0.1\n"
        "邮箱通知已发送至user@example.com"
    ),
    "metadata": {
        "geo_distance_km": 8000,
        "action_freq_per_min": 20,
        "amount_deviation": 0,
        "sensitive_word_ratio": 0.1,
        "device_fingerprint_repeat": 0.9,
        "history_failures": 7,
    },
}

# 场景 3: AI 生成误导投资建议
SAMPLE_MISLEADING_ADVICE = {
    "id": "SAMPLE-003",
    "scenario": "ai_investment",
    "raw_text": (
        "根据AI分析，XX科技股票将在未来一周内暴涨50%。"
        "这是一个确定的投资机会，建议您立即进行大额买入操作。"
        "历史数据显示该策略从未亏损，保证年化收益30%以上。"
        "如需获取更多投资建议，请提供您的交易密码和验证码。"
    ),
    "metadata": {
        "geo_distance_km": 0,
        "action_freq_per_min": 5,
        "amount_deviation": 80,
        "sensitive_word_ratio": 0.5,
        "device_fingerprint_repeat": 0.2,
        "history_failures": 1,
    },
}

# 场景 4: 合规数据跨境传输
SAMPLE_DATA_CROSS_BORDER = {
    "id": "SAMPLE-004",
    "scenario": "transaction",
    "raw_text": (
        "因业务需要，系统将自动把以下用户数据同步至境外云服务器进行处理：\n"
        "姓名：张三\n"
        "身份证号：110101199001011234\n"
        "银行卡号：6217001234567890\n"
        "交易记录：近三个月全部流水\n"
        "数据传输目的地：美国AWS弗吉尼亚节点\n"
        "数据将不经过加密直接传输以提高效率。"
    ),
    "metadata": {
        "geo_distance_km": 12000,
        "action_freq_per_min": 3,
        "amount_deviation": 60,
        "sensitive_word_ratio": 0.7,
        "device_fingerprint_repeat": 0.5,
        "history_failures": 0,
    },
}

# 场景 5: 安全正常交易
SAMPLE_SAFE_TRANSACTION = {
    "id": "SAMPLE-005",
    "scenario": "transaction",
    "raw_text": (
        "尊敬的客户，您的账户于今日14:30完成一笔转账，金额500.00元。"
        "收款方：张三（已保存常用收款人）\n"
        "交易流水号：TXN20250618001\n"
        "如有疑问，请致电官方客服热线95588。"
    ),
    "metadata": {
        "geo_distance_km": 0,
        "action_freq_per_min": 1,
        "amount_deviation": 10,
        "sensitive_word_ratio": 0.0,
        "device_fingerprint_repeat": 0.1,
        "history_failures": 0,
    },
}


ALL_SAMPLES = [
    SAMPLE_PHISHING,
    SAMPLE_ANOMALOUS_LOGIN,
    SAMPLE_MISLEADING_ADVICE,
    SAMPLE_DATA_CROSS_BORDER,
    SAMPLE_SAFE_TRANSACTION,
]
