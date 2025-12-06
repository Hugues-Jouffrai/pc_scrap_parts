"""
test_analyzer.py
Unit tests for analyzer.py price parsing and calculation logic.
"""

import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from analyzer import AntigravityAnalyzer


class TestAnalyzerPriceParsing(unittest.TestCase):
    """Test suite for analyzer price parsing and calculation."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = AntigravityAnalyzer()

    def test_parse_price_string_basic(self):
        """Test parsing basic price strings."""
        # Test the internal parse function
        listing_data = {
            'title': 'Gaming PC',
            'price_str': '1000',
            'raw_text': 'Price: 1000€'
        }
        
        result = self.analyzer.analyze_profitability(listing_data)
        self.assertEqual(result['listing_price'], 1000.0)

    def test_parse_price_with_euro_symbol(self):
        """Test parsing prices with euro symbol."""
        listing_data = {
            'title': 'Gaming PC',
            'price_str': '1500€',
            'raw_text': 'Price: 1500€'
        }
        
        result = self.analyzer.analyze_profitability(listing_data)
        self.assertEqual(result['listing_price'], 1500.0)

    def test_parse_price_with_nbsp(self):
        """Test parsing prices with non-breaking spaces."""
        listing_data = {
            'title': 'Gaming PC',
            'price_str': '1\u00A0000',  # Non-breaking space
            'raw_text': 'Price: 1\u00A0000 €'
        }
        
        result = self.analyzer.analyze_profitability(listing_data)
        self.assertEqual(result['listing_price'], 1000.0)

    def test_parse_price_with_thin_space(self):
        """Test parsing prices with thin spaces (Unicode 202F)."""
        listing_data = {
            'title': 'Gaming PC',
            'price_str': '2\u202F500',  # Thin space
            'raw_text': 'Price: 2\u202F500€'
        }
        
        result = self.analyzer.analyze_profitability(listing_data)
        self.assertEqual(result['listing_price'], 2500.0)

    def test_parse_price_with_comma_decimal(self):
        """Test parsing prices with comma as decimal separator."""
        listing_data = {
            'title': 'Gaming PC',
            'price_str': '1000,50',
            'raw_text': 'Price: 1000,50€'
        }
        
        result = self.analyzer.analyze_profitability(listing_data)
        self.assertEqual(result['listing_price'], 1000.50)

    @patch('analyzer.client')
    def test_parts_list_processing(self, mock_client):
        """Test that parts are processed correctly."""
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "is_gaming_pc": True,
            "listing_price": 1000,
            "parts": [
                {"component": "RTX 3060", "estimated_price": 250, "notes": "Good condition"},
                {"component": "i7-10700k", "estimated_price": 300, "notes": ""},
                {"component": "16GB DDR4", "estimated_price": 80, "notes": ""}
            ],
            "total_estimated_value": 0,
            "profit_potential": 0,
            "profit_percentage": 0,
            "verdict": "PASS",
            "reasoning": "Test reasoning"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        listing_data = {
            'title': 'Test PC',
            'price_str': '1000',
            'raw_text': 'Test description'
        }
        
        result = self.analyzer.analyze_profitability(listing_data)
        
        # Check parts are enriched
        self.assertEqual(len(result['parts']), 3)
        self.assertTrue(all('category' in p for p in result['parts']))
        self.assertTrue(all('cached' in p for p in result['parts']))
        
        # Check total is calculated
        self.assertEqual(result['total_estimated_value'], 630)  # 250 + 300 + 80

    @patch('analyzer.client')
    def test_profit_calculation(self, mock_client):
        """Test profit and margin calculation."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "is_gaming_pc": True,
            "listing_price": 500,
            "parts": [
                {"component": "GPU", "estimated_price": 300, "notes": ""},
                {"component": "CPU", "estimated_price": 250, "notes": ""}
            ],
            "total_estimated_value": 0,
            "profit_potential": 0,
            "profit_percentage": 0,
            "verdict": "PASS",
            "reasoning": "Test"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        listing_data = {
            'title': 'Test PC',
            'price_str': '500',
            'raw_text': 'Test'
        }
        
        result = self.analyzer.analyze_profitability(listing_data)
        
        # Total: 550, Profit: 50, Margin: 10%
        self.assertEqual(result['total_estimated_value'], 550)
        self.assertEqual(result['profit_potential'], 50)
        self.assertEqual(result['profit_percentage'], 10.0)

    @patch('analyzer.client')
    def test_verdict_buy_threshold(self, mock_client):
        """Test that verdict is BUY when margin > 50%."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "is_gaming_pc": True,
            "listing_price": 100,
            "parts": [
                {"component": "Component", "estimated_price": 160, "notes": ""}
            ],
            "total_estimated_value": 0,
            "profit_potential": 0,
            "profit_percentage": 0,
            "verdict": "PASS",
            "reasoning": "Test"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        listing_data = {
            'title': 'Test PC',
            'price_str': '100',
            'raw_text': 'Test'
        }
        
        result = self.analyzer.analyze_profitability(listing_data)
        
        # Profit: 60, Margin: 60% > 50% threshold -> BUY
        self.assertEqual(result['verdict'], 'BUY')

    @patch('analyzer.client')
    def test_verdict_trash_detection(self, mock_client):
        """Test that TRASH verdict is preserved."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "is_gaming_pc": False,
            "listing_price": 100,
            "parts": [],
            "total_estimated_value": 0,
            "profit_potential": 0,
            "profit_percentage": 0,
            "verdict": "TRASH",
            "reasoning": "Broken parts detected"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        listing_data = {
            'title': 'Broken PC',
            'price_str': '100',
            'raw_text': 'HS, Broken, Not working'
        }
        
        result = self.analyzer.analyze_profitability(listing_data)
        self.assertEqual(result['verdict'], 'TRASH')

    @patch('analyzer.client')
    def test_listing_price_zero_fallback(self, mock_client):
        """Test fallback when listing price cannot be determined."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "is_gaming_pc": True,
            "listing_price": 0,
            "parts": [
                {"component": "Component", "estimated_price": 100, "notes": ""}
            ],
            "total_estimated_value": 0,
            "profit_potential": 0,
            "profit_percentage": 0,
            "verdict": "PASS",
            "reasoning": "Test"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        listing_data = {
            'title': 'Test PC',
            'price_str': '',  # Empty price_str
            'raw_text': 'Description without price'
        }
        
        result = self.analyzer.analyze_profitability(listing_data)
        self.assertEqual(result['listing_price'], 0.0)
        self.assertEqual(result['profit_percentage'], 0.0)  # No margin calc when price is 0


class TestAnalyzerRobustness(unittest.TestCase):
    """Test suite for analyzer robustness and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = AntigravityAnalyzer()

    @patch('analyzer.client')
    def test_malformed_json_response_handling(self, mock_client):
        """Test that analyzer handles malformed JSON gracefully."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Not valid JSON"
        mock_client.chat.completions.create.return_value = mock_response
        
        listing_data = {
            'title': 'Test PC',
            'price_str': '500',
            'raw_text': 'Test'
        }
        
        # Should not raise an exception
        result = self.analyzer.analyze_profitability(listing_data)
        self.assertIsNotNone(result)
        self.assertEqual(result['verdict'], 'PASS')
        self.assertEqual(result['total_estimated_value'], 0)

    @patch('analyzer.client')
    def test_missing_parts_list(self, mock_client):
        """Test that analyzer handles missing parts list."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "is_gaming_pc": True,
            "listing_price": 500,
            "parts": None,  # Missing parts
            "total_estimated_value": 0,
            "profit_potential": 0,
            "profit_percentage": 0,
            "verdict": "PASS",
            "reasoning": "Test"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        listing_data = {
            'title': 'Test PC',
            'price_str': '500',
            'raw_text': 'Test'
        }
        
        result = self.analyzer.analyze_profitability(listing_data)
        self.assertEqual(result['total_estimated_value'], 0)

    @patch('analyzer.client')
    def test_negative_profit_margin(self, mock_client):
        """Test that analyzer correctly handles negative profit margins."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "is_gaming_pc": True,
            "listing_price": 1000,
            "parts": [
                {"component": "Component", "estimated_price": 500, "notes": ""}
            ],
            "total_estimated_value": 0,
            "profit_potential": 0,
            "profit_percentage": 0,
            "verdict": "PASS",
            "reasoning": "Test"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        listing_data = {
            'title': 'Test PC',
            'price_str': '1000',
            'raw_text': 'Test'
        }
        
        result = self.analyzer.analyze_profitability(listing_data)
        self.assertEqual(result['profit_potential'], -500)
        self.assertEqual(result['profit_percentage'], -50.0)
        self.assertEqual(result['verdict'], 'PASS')


if __name__ == "__main__":
    unittest.main()
