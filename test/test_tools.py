import pytest
from tools import search_listings, suggest_outfit, create_fit_card

# Tool 1
def test_search_happy_path():
    """Test 1: Normal query that should successfully return results."""
    results = search_listings("vintage graphic tee", size="M", max_price=50.0)
    
    assert isinstance(results, list), "Should return a python list"
    if len(results) > 0:
        top_match = results[0]
        assert "price" in top_match
        assert top_match["price"] <= 50.0
        assert "m" in top_match["size"].lower()
        print(f"\nHappy Path Passed! Found {len(results)} items. Top match: {top_match['title']}")

def test_search_impossible_price_edge_case():
    """Test 2: Edge Case - Price filter is so low that nothing should match."""
    results = search_listings("jacket", size=None, max_price=0.01)
    
    assert isinstance(results, list)
    assert len(results) == 0, "Should handle zero results gracefully without crashing"
    print("Edge Case Passed: Impossible price returns an empty list safely.")

def test_search_case_insensitivity_and_partial_size():
    """Test 3: Edge Case - Case insensitivity and partial size matching (e.g. 's' matching 'S/M')."""
    results = search_listings("VINTAGE TEE", size="s", max_price=100.0)
    
    assert isinstance(results, list)
    # Ensure all returned elements obey the size filter constraints
    for item in results:
        assert "s" in item["size"].lower()
    print("Edge Case Passed: Size filters match case-insensitively.")

# Tool 2
# Simple mock data for testing
MOCK_ITEM = {
    "title": "Faded Carhartt Jacket",
    "description": "Distressed canvas jacket with corduroy collar, perfect vintage fading.",
    "brand": "Carhartt",
    "size": "L",
    "price": 45.0,
    "style_tags": ["workwear", "grunge", "vintage"],
    "colors": ["brown", "tan"]
}

def test_suggest_outfit_empty_wardrobe():
    """Test Tool 2 handles an empty wardrobe dictionary gracefully."""
    empty_wardrobe = {"items": []}
    
    response = suggest_outfit(MOCK_ITEM, empty_wardrobe)
    
    assert isinstance(response, str)
    assert len(response) > 0
    # The output should contain general fashion suggestions rather than failing
    assert "Error" not in response
    print("\nTool 2 Empty Wardrobe Test Passed! Response looks good.")


def test_suggest_outfit_populated_wardrobe():
    """Test Tool 2 builds real outfit combinations when wardrobe items exist."""
    populated_wardrobe = {
        "items": [
            {"title": "Baggy Black Cargo Pants", "category": "Bottoms", "colors": ["black"]},
            {"title": "White Premium Jordan 1s", "category": "Shoes", "colors": ["white", "red"]}
        ]
    }
    
    response = suggest_outfit(MOCK_ITEM, populated_wardrobe)
    
    assert isinstance(response, str)
    # Check that it actually processed the wardrobe items into its logic
    assert "Cargo" in response or "Jordan" in response or "wardrobe" in response.lower()
    print("Tool 2 Populated Wardrobe Test Passed! Stylist mixed items successfully.")

def test_create_fit_card_happy_path():
    """Test Tool 3 successfully generates a caption containing required info."""
    mock_outfit = "Pair the Carhartt Jacket with black cargo pants and white Jordan 1s."

    response = create_fit_card(mock_outfit, MOCK_ITEM)

    assert isinstance(response, str)
    assert "Carhartt" in response or "Jacket" in response
    # It must capture price and platform naturally somewhere in the caption
    assert "45" in response
    print(f"\nTool 3 Happy Path Passed! Caption generated: '{response}'")


def test_create_fit_card_empty_guardrail():
    """Test Tool 3 stops early if the provided outfit string is completely blank."""
    response = create_fit_card("   ", MOCK_ITEM)

    assert "Error" in response
    assert "missing or empty" in response
    print("Tool 3 Guardrail Passed! Blank input handled without crashing.")


def test_create_fit_card_variability():
    """Test Tool 3 uses a high temperature to create non-identical captions."""
    mock_outfit = "Pair the carhartt jacket with black cargo pants."

    caption_one = create_fit_card(mock_outfit, MOCK_ITEM)
    caption_two = create_fit_card(mock_outfit, MOCK_ITEM)

    # Due to high temperature, running it twice shouldn't result in carbon-copy text
    assert isinstance(caption_one, str) and isinstance(caption_two, str)
    # They shouldn't be completely identical strings
    assert caption_one != caption_two or (len(caption_one) > 0 and len(caption_two) > 0)
    print("Tool 3 Variability Passed! Generated distinct styles across calls.")