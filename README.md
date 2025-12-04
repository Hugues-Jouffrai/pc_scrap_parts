# LBC-Arbitrage

A Python tool that finds profitable "part-out" opportunities for gaming PCs on **Leboncoin** (Paris market). It scrapes listings, uses **GPT-4o** to identify components and estimate resale value, then calculates if the profit margin exceeds 50%.

## 🚀 Features

- **Automated Scraping**: Uses Playwright to bypass anti-bot measures (Datadome)
- **AI-Powered Analysis**: GPT-4o parses unstructured listings to extract parts and prices
- **Smart Filtering**: Automatically rejects broken PCs ("HS", "Panne", etc.)
- **Beautiful CLI**: Rich terminal output with color-coded verdicts

## 📋 Requirements

- Python 3.8+
- OpenAI API Key

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd pc_scrap_parts
```

2. **Create a virtual environment**
```bash
py -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
playwright install chromium
```

4. **Set up your OpenAI API Key**
   
   Edit the `.env` file and add:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## 🎯 Usage

Run the tool with a Leboncoin URL:

```bash
python main.py https://www.leboncoin.fr/ad/ordinateurs/YOUR_LISTING_ID
```

Or run interactively:

```bash
python main.py
```

## 📊 How It Works

1. **Scraper** (`scraper.py`): Playwright launches a browser to extract listing data (title, price, description)
2. **Analyzer** (`analyzer.py`): Sends data to GPT-4o to identify PC parts and estimate conservative resale values
3. **Decision Logic**:
   - **BUY**: Profit margin > 50%
   - **PASS**: Profit margin < 50%
   - **TRASH**: Contains keywords like "HS", "Panne", "Broken"

## 🧠 AI Pricing Logic

- Conservative estimates (slightly undervalued)
- Cases, Fans, PSUs valued at €0 unless premium brands (Corsair, Seasonic, etc.)
- Ignores peripherals (keyboard/mouse) unless high-end

## 🎨 Example Output

```
Analysis Results: Gaming PC i7 RTX 3060...
┌───────────────────┬─────────┐
│ Metric            │ Value   │
├───────────────────┼─────────┤
│ Listing Price     │ 450€    │
│ Estimated Value   │ 750€    │
│ Profit            │ 300€    │
│ Margin            │ 66%     │
│ Verdict           │ BUY     │
└───────────────────┴─────────┘

🛠️  PARTS BREAKDOWN:
┌────────────────────────────┬───────────┐
│ Component                  │ Est. Price│
├────────────────────────────┼───────────┤
│ RTX 3060                   │ 250€      │
│ i7-9700K                   │ 180€      │
│ 16GB DDR4 RAM              │ 50€       │
│ 500GB SSD                  │ 40€       │
│ Motherboard (Generic)      │ 30€       │
│ PSU (Generic)              │ 0€        │
│ Case                       │ 0€        │
└────────────────────────────┴───────────┘

📝 Reasoning: Strong profit margin. GPU and CPU are valuable...
```

## ⚠️ Disclaimer

This tool is for educational/research purposes. Always verify listings manually before purchasing. Market prices fluctuate.

## 📝 License

MIT License
