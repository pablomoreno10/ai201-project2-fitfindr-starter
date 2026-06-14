"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()
    filtered = listings

    if max_price is not None:
        filtered = [l for l in filtered if l.get('price', 0.0) <= max_price]
        
    if size is not None:
        size_lower = size.lower()
        filtered = [l for l in filtered if l.get('size', '') and size_lower in l['size'].lower()]

    keywords = description.lower().split()
    if not keywords:
        return []  

    scored = []
    for listing in filtered:
        searchable_text = f"{listing.get('title', '')} {listing.get('description', '')} {' '.join(listing.get('style_tags', []))}".lower()

        score = sum(1 for kw in keywords if kw in searchable_text)
        
        if score > 0:
            scored.append((score, listing))

    scored.sort(key=lambda x: x[0], reverse=True)
    
    return [listing for score, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """

    client = _get_groq_client()
    item_title = new_item.get('title', 'Unknown Item')
    item_desc = new_item.get('description', '')
    item_brand = new_item.get('brand', 'Generic')
    item_size = new_item.get('size', 'N/A')
    item_price = new_item.get('price', 'N/A')
    item_tags = ", ".join(new_item.get('style_tags', []))
    item_colors = ", ".join(new_item.get('colors', []))

    item_summary = (
        f"Item: {item_title}\n"
        f"Description: {item_desc}\n"
        f"Brand: {item_brand} | Size: {item_size} | Price: ${item_price}\n"
        f"Colors: {item_colors} | Style Tags: {item_tags}"
    )
    wardrobe_items = wardrobe.get('items', [])

    if not wardrobe_items:
        system_prompt = (
            "You are an expert personal stylist specializing in streetwear, sustainable fashion, and vintage trends. "
            "The user wants styling ideas for a secondhand item they found, but their digital wardrobe is empty. "
            "Provide creative, general styling advice. Suggest what types of garments, silhouettes, textures, and footwear "
            "would complement this piece. Keep the tone conversational, helpful, and concise (1-2 short paragraphs)."
        )
        user_prompt = f"Here is the item I found:\n\n{item_summary}"
    else:
        wardrobe_lines = []
        for item in wardrobe_items:
            w_title = item.get('title', 'Untitled Piece')
            w_cat = item.get('category', 'Clothing')
            w_colors = ", ".join(item.get('colors', [])) if isinstance(item.get('colors'), list) else "N/A"
            wardrobe_lines.append(f"- {w_title} ({w_cat}, Color: {w_colors})")
        
        wardrobe_summary = "\n".join(wardrobe_lines)

        system_prompt = (
            "You are an expert personal stylist. Create 1-2 distinct, complete outfit combinations "
            "by pairing the new item explicitly with named pieces from the user's wardrobe. "
            "Explain the overall aesthetic vibe of the look (e.g., 90s grunge, retro athletic, minimal chic). "
            "Be highly specific and practical. Use the exact names of items from their wardrobe."
        )
        user_prompt = (
            f"Here is the new item I want to buy:\n\n{item_summary}\n\n"
            f"Here is my current wardrobe:\n{wardrobe_summary}"
        )

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        # Catch errors gracefully as requested by the spec
        return f"Styling service temporarily unavailable. (Error: {str(e)})"


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """

    if not outfit or not outfit.strip():
        return "Error: Cannot generate a fit card because the outfit suggestion is missing or empty."
    
    client = _get_groq_client()

    item_title = new_item.get('title', 'this piece')
    item_price = new_item.get('price', 'unpriced')
    item_platform = new_item.get('platform', 'thrift shop')

    if isinstance(item_price, (int, float)):
        price_str = f"${item_price:.2f}" if item_price % 1 != 0 else f"${int(item_price)}"
    else:
        price_str = str(item_price)

    system_prompt = (
        "You are a trendy social media manager writing a casual, authentic outfit caption for Instagram/TikTok. "
        "Keep it to exactly 2-4 sentences. Avoid sounding like a dry product description or corporate advertisement. "
        "Use modern, casual syntax (lowercase styling, minimal punctuation, or an emoji is fine, but don't overdo it). "
        "CRITICAL RULES:\n"
        f"1. You MUST mention the item name ('{item_title}') exactly once.\n"
        f"2. You MUST mention the price ('{price_str}') exactly once.\n"
        f"3. You MUST mention the platform it was found on ('{item_platform}') exactly once.\n"
        "Do not include any introductory meta-text like 'Here is your caption:'—return ONLY the final caption."
    )

    user_prompt = (
        f"The outfit combination is:\n{outfit}\n\n"
        f"The main item details are:\nItem: {item_title} | Price: {price_str} | Platform: {item_platform}"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.9,  
            max_tokens=150
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Caption generator temporarily unavailable. (Error: {str(e)})"