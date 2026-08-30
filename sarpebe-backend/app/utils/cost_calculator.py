from decimal import Decimal

# Pricing per token
PRICING = {
    "gemini-2.5-flash-lite": {
        "input": Decimal("0.000075"),
        "output": Decimal("0.0003")
    },
    "gemini-embedding-2": {
        "input": Decimal("0.00001"),
        "output": Decimal("0.0")
    },
}

def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculates the total fiat cost of an LLM operation based on token usage.
    Returns a float for easy database insertion.
    """
    model_pricing = PRICING.get(model_name)
    if not model_pricing:
        return 0.0
    
    input_cost = Decimal(prompt_tokens) * model_pricing["input"]
    output_cost = Decimal(completion_tokens) * model_pricing["output"]
    total_cost = input_cost + output_cost
    
    return float(total_cost)
