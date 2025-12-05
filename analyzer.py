import os
import re
import json
from openai import OpenAI
from dotenv import load_dotenv
from price_fetcher import estimate_component_price

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AntigravityAnalyzer:
    """
    The 'Brain' of the operation. Uses OpenAI to parse unstructured text and estimate value.
    """
    
    def analyze_profitability(self, listing_data):
        """Sends text to the AI Oracle to appraise parts."""
        print("[bold purple]>> Vibing with the data (AI Analysis)...[/bold purple]")
        
        raw_text = listing_data.get('raw_text', '')
        title = listing_data.get('title', '')
        price_str = listing_data.get('price_str', '0')
        
        try:
            listing_price = float(price_str)
        except:
            listing_price = 0.0

        prompt = f"""
        You are an expert PC hardware reseller in France. 
        Analyze the text from this Leboncoin listing.
        
        Listing Title: {title}
        Listing Price (extracted): {listing_price} EUR (If 0, try to find it in the text).
        
        Task:
        1. Identify the specific PC components (CPU, GPU, RAM, SSD/HDD, Motherboard, PSU).
        2. Estimate the current USED market price in France (in EUR) for each part separately. Be CONSERVATIVE (undervalue slightly).
        3. Ignore peripherals (keyboard/mouse) unless they are high-end.
        4. CRITICAL: Value "Cases", "Fans", and "PSUs" at 0 EUR unless they are clearly high-end brands (Corsair, Seasonic, Lian Li, etc) AND models. Standard/Generic = 0.
        5. If the description mentions "HS", "H.S", "Panne", "Broken", "Pour pièces", set verdict to "TRASH".
        
        Return ONLY valid JSON with this structure:
        {{
            "is_gaming_pc": boolean,
            "listing_price": {listing_price if listing_price > 0 else "number found in text"},
            "parts": [
                {{ "component": "Name (e.g. RTX 3060)", "estimated_price": 150, "notes": "optional" }}
            ],
            "total_estimated_value": 0,
            "profit_potential": 0,
            "profit_percentage": 0,
            "verdict": "BUY" or "PASS" or "TRASH",
            "reasoning": "Short explanation of the verdict"
        }}

        Logic for Verdict:
        - TRASH if broken/HS.
        - BUY if (Total Estimated - Listing Price) / Listing Price > 0.50 (50% margin).
        - PASS otherwise.

        Listing Text:
        {raw_text}
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={ "type": "json_object" },
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse model output safely
        try:
            model_text = response.choices[0].message.content
            result = json.loads(model_text)
        except Exception:
            # If parsing fails, return a minimal structure
            result = {
                "is_gaming_pc": False,
                "listing_price": 0,
                "parts": [],
                "total_estimated_value": 0,
                "profit_potential": 0,
                "profit_percentage": 0,
                "verdict": "PASS",
                "reasoning": "Model output could not be parsed."
            }

        # Helper to parse a cleaned numeric price string
        def parse_price_string(s: str) -> float:
            if not s:
                return 0.0
            s2 = s.replace('\u00A0', ' ').replace('\u202F', ' ').replace('\u2009', ' ')
            s2 = s2.replace(' ', '').replace(',', '.')
            m = re.search(r"(\d+\.?\d*)", s2)
            if not m:
                return 0.0
            try:
                return float(m.group(1))
            except Exception:
                return 0.0

        # Ensure parts is a list and compute total estimated value deterministically
        parts = result.get('parts') or []
        
        # Fetch prices from cache or estimate for each part
        enriched_parts = []
        for part in parts:
            component_name = part.get('component', '')
            model_price = part.get('estimated_price', 0)
            
            # Query the price fetcher for cached/estimated used price
            price_info = estimate_component_price(component_name)
            
            # Use cached used price if available and reasonable; otherwise use model's estimate
            cached_used_price = float(price_info.get('estimated_used_price_eur', model_price))
            final_price = cached_used_price if cached_used_price > 0 else model_price
            
            enriched_part = {
                'component': component_name,
                'estimated_price': final_price,
                'estimated_price_new': price_info.get('estimated_new_price_eur', final_price),
                'cached': price_info.get('cached', False),
                'category': price_info.get('category', 'Other'),
                'notes': part.get('notes', '')
            }
            enriched_parts.append(enriched_part)
        
        result['parts'] = enriched_parts
        
        try:
            total_estimated = sum(float(p.get('estimated_price', 0) or 0) for p in enriched_parts)
        except Exception:
            total_estimated = 0
        result['total_estimated_value'] = total_estimated

        # Determine listing price: prefer model value, else try scraped price_str or raw_text
        listing_price = 0.0
        try:
            lp = result.get('listing_price', 0)
            if isinstance(lp, (int, float)) and lp > 0:
                listing_price = float(lp)
            elif isinstance(lp, str) and lp.strip():
                listing_price = parse_price_string(lp)
        except Exception:
            listing_price = 0.0

        # Fallback to scraped price string
        if listing_price == 0.0:
            listing_price = parse_price_string(listing_data.get('price_str', '') )

        # Another fallback: try to find a price in raw_text
        if listing_price == 0.0:
            listing_price = parse_price_string(listing_data.get('raw_text', ''))

        result['listing_price'] = listing_price

        # Compute profit and margin
        profit = round(total_estimated - listing_price, 2)
        result['profit_potential'] = profit
        result['profit_percentage'] = round((profit / listing_price * 100) if listing_price > 0 else 0.0, 2)

        # Derive verdict if model didn't provide one or if it's inconsistent
        model_verdict = (result.get('verdict') or '').upper()
        if 'TRASH' in model_verdict:
            result['verdict'] = 'TRASH'
        else:
            # If model provided BUY/PASS use it, otherwise compute from numbers
            if model_verdict in ('BUY', 'PASS'):
                result['verdict'] = model_verdict
            else:
                if listing_price > 0 and result['profit_percentage'] > 50:
                    result['verdict'] = 'BUY'
                else:
                    result['verdict'] = 'PASS'

        return result
