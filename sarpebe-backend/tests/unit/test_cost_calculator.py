from decimal import Decimal
from app.utils.cost_calculator import calculate_cost

def test_calculate_cost_gemini_flash_lite():
    cost = calculate_cost("gemini-2.5-flash-lite", 1000000, 1000000)
    assert cost == 375.0

def test_calculate_cost_gemini_embedding():
    cost = calculate_cost("gemini-embedding-2", 1000000, 0)
    assert cost == 10.0 # 0.00001 * 1M

def test_calculate_cost_zero_tokens():
    cost = calculate_cost("gemini-2.5-flash-lite", 0, 0)
    assert cost == 0.0

def test_calculate_cost_unknown_model():
    cost = calculate_cost("unknown-model", 100, 100)
    assert cost == 0.0
