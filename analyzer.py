import os
import json
from openai import OpenAI
from dotenv import load_dotenv

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
        
        return json.loads(response.choices[0].message.content)
