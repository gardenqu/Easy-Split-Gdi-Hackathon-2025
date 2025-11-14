import pytest
from bill_splitting_logic import BillSplitter, calculate_even_split, split_receipt_items


def test_equal_split_one_item_two_people():
    """Item split equally between 2 participants."""
    splitter = BillSplitter()
    p1 = splitter.add_participant("Alice")
    p2 = splitter.add_participant("Bob")

    splitter.add_item("Burger", 20.00, participants=[p1, p2])

    result = splitter.calculate_split()

    alice = result["participants"][0]
    bob = result["participants"][1]

    assert alice["subtotal"] == 10.00
    assert bob["subtotal"] == 10.00
    assert result["summary"]["total_subtotal"] == 20.00


def test_custom_shares_split():
    """Item split using custom share percentages."""
    splitter = BillSplitter()
    p1 = splitter.add_participant("Alice")
    p2 = splitter.add_participant("Bob")

    # Alice pays 70%, Bob pays 30%
    splitter.add_item(
        "Pizza", 
        30.00,
        participants=[p1, p2],
        custom_shares={p1: 0.7, p2: 0.3}
    )

    result = splitter.calculate_split()
    alice = result["participants"][0]
    bob = result["participants"][1]

    assert alice["subtotal"] == 21.00   # 70% of 30
    assert bob["subtotal"] == 9.00      # 30% of 30


def test_tax_and_tip_distribution():
    """Ensure tax and tip are distributed proportionally."""
    splitter = BillSplitter()
    p1 = splitter.add_participant("Alice")
    p2 = splitter.add_participant("Bob")

    splitter.add_item("Steak", 50, participants=[p1])
    splitter.add_item("Drink", 50, participants=[p2])

    splitter.set_tax_and_tip(tax_rate=10, tip_percentage=20)  # 10% tax, 20% tip

    result = splitter.calculate_split()

    alice = result["participants"][0]
    bob = result["participants"][1]

    # Each should pay 50 subtotal
    assert alice["subtotal"] == 50.00
    assert bob["subtotal"] == 50.00

    # Total subtotal = 100 → tax = 10, tip = 20
    assert result["summary"]["total_tax"] == 10.00
    assert result["summary"]["total_tip"] == 20.00

    # Each pays 50% of tax/tip
    assert alice["tax_share"] == 5.00
    assert bob["tax_share"] == 5.00

    assert alice["tip_share"] == 10.00
    assert bob["tip_share"] == 10.00


def test_split_even_function():
    """Test the separate calculate_even_split utility."""
    result = calculate_even_split(100, 3)

    assert result["per_person"] == pytest.approx(33.33)
    assert result["allocated_total"] == pytest.approx(99.99)
    assert result["rounding_difference"] == pytest.approx(0.01)
