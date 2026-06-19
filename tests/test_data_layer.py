"""Tests for Data Layer — 脱敏引擎"""

import pytest
from finguard.data_layer import DataSanitizer


@pytest.fixture
def sanitizer():
    return DataSanitizer()


def test_person_name_detection(sanitizer):
    text = "姓名：张三向您转账10000元"
    sanitized, report = sanitizer.sanitize(text)
    assert "[PERSON]" in sanitized
    assert "张三" not in sanitized


def test_id_number_masking(sanitizer):
    text = "身份证号110101199001011234请核实"
    sanitized, report = sanitizer.sanitize(text)
    assert "[ID_NUM]" in sanitized


def test_bank_card_masking(sanitizer):
    text = "卡号6222021234567890123交易成功"
    sanitized, report = sanitizer.sanitize(text)
    assert "[CARD_NUM]" in sanitized


def test_phone_masking(sanitizer):
    text = "联系电话13800138000已记录"
    sanitized, report = sanitizer.sanitize(text)
    assert "[PHONE]" in sanitized


def test_ip_masking(sanitizer):
    text = "登录IP: 192.168.1.100 来源未知"
    sanitized, report = sanitizer.sanitize(text)
    assert "[IP_ADDR]" in sanitized


def test_email_masking(sanitizer):
    text = "发送至user@example.com请查收"
    sanitized, report = sanitizer.sanitize(text)
    assert "[EMAIL]" in sanitized


def test_multi_field_text(sanitizer):
    """复合场景: 同时包含多种敏感信息"""
    text = "姓名：李四，身份证330102198512345678，卡号6217001234567890，电话13900001111"
    sanitized, report = sanitizer.sanitize(text)
    assert "[PERSON]" in sanitized
    assert "[ID_NUM]" in sanitized
    assert "[CARD_NUM]" in sanitized
    assert "[PHONE]" in sanitized


def test_clean_text_passes(sanitizer):
    text = "尊敬的用户，您的账户一切正常，请放心使用。"
    sanitized, report = sanitizer.sanitize(text)
    assert sanitized == text


def test_compliance_report_structure(sanitizer):
    text = "姓名：王五，电话13800138000"
    _, report = sanitizer.sanitize(text)
    assert "passed" in report
    assert "failed" in report
    assert any("person_name" in p for p in report["passed"])
    assert any("phone" in p for p in report["passed"])
