from app.services.tax_calculator import calculate_income_tax

# Sample tax slabs matching default rules
SAMPLE_TAX_RULES = [
    type("Rule", (), {"rule_type": "income_tax", "min_income": 0, "max_income": 250000, "rate": 0})(),
    type("Rule", (), {"rule_type": "income_tax", "min_income": 250000, "max_income": 500000, "rate": 5})(),
    type("Rule", (), {"rule_type": "income_tax", "min_income": 500000, "max_income": 1000000, "rate": 20})(),
    type("Rule", (), {"rule_type": "income_tax", "min_income": 1000000, "max_income": None, "rate": 30})(),
]


def test_tax_below_threshold():
    tax = calculate_income_tax(240000, SAMPLE_TAX_RULES)
    assert tax == 0.0


def test_tax_first_slab():
    tax = calculate_income_tax(300000, SAMPLE_TAX_RULES)
    # 2.5L-3L: 50000 * 5% = 2500
    assert tax == 2500.0


def test_tax_second_slab():
    tax = calculate_income_tax(600000, SAMPLE_TAX_RULES)
    # 2.5L-5L: 250000 * 5% = 12500
    # 5L-6L: 100000 * 20% = 20000
    # Total = 32500
    assert tax == 32500.0


def test_tax_highest_slab():
    tax = calculate_income_tax(1500000, SAMPLE_TAX_RULES)
    # 2.5L-5L: 250000 * 5% = 12500
    # 5L-10L: 500000 * 20% = 100000
    # 10L-15L: 500000 * 30% = 150000
    # Total = 262500
    assert tax == 262500.0


def test_tax_no_rules():
    tax = calculate_income_tax(500000, [])
    assert tax == 0.0
