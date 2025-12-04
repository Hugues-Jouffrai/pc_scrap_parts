# GitHub Setup Guide

## Pushing to GitHub

1. Create a new repository on GitHub (don't initialize with README)
2. Run these commands:

```bash
git remote add origin https://github.com/Hugues-Jouffrai/pc_scrap_parts.git
git branch -M main
git push -u origin main
```

## Testing the Tool

Before using the tool, make sure you've added your OpenAI API key to `.env`:

```
OPENAI_API_KEY=sk-...your_key_here
```

Then test with:

```bash
.\venv\Scripts\python.exe main.py
```

Paste a Leboncoin URL when prompted!
