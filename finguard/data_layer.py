"""
Data Layer — 金融数据脱敏引擎

DIKW 层级: Data (原始数据 → 脱敏数据)
"""

import re
from typing import Tuple


class DataSanitizer:
    """金融数据脱敏引擎"""

    PATTERNS: list = [
        # 注意：顺序敏感！长数字优先且按特征区分：
        #   银行卡: 62开头（银联）16-19位
        #   身份证: 15位 或 17位+校验码(0-9Xx) = 15/18位
        ("person_name", r'(?<=姓名[：:])[一-鿿]{2,4}', "[PERSON]"),
        ("bank_card", r'62\d{14,17}', "[CARD_NUM]"),
        ("id_number", r'\d{15}(?:\d{2}[\dXx])?', "[ID_NUM]"),
        ("phone", r'1[3-9]\d{9}', "[PHONE]"),
        ("ip_addr", r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', "[IP_ADDR]"),
        ("email", r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "[EMAIL]"),
    ]

    def sanitize(self, text: str) -> Tuple[str, dict]:
        """
        输入: 原始金融文本
        输出: (脱敏文本, 合规检查报告)
        """
        sanitized = text
        compliance_report = {"passed": [], "failed": []}

        for field_name, pattern, replacement in self.PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                already_masked = all(replacement in sanitized for _ in matches)
                if already_masked:
                    compliance_report["passed"].append(field_name)
                else:
                    sanitized = re.sub(pattern, replacement, sanitized)
                    compliance_report["passed"].append(
                        f"{field_name}({len(matches)}条)"
                    )
            else:
                compliance_report["failed"].append(f"{field_name}: 未检测到")

        return sanitized, compliance_report
