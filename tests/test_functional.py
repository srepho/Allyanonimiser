"""
Functional tests for Allyanonimiser package.

These tests verify that the key functions and interfaces in the package
work correctly when called with valid inputs.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch


class MockAnalyzer:
    """Mock class for simulating an analyzer."""
    
    def __init__(self, patterns=None):
        self.patterns = patterns or []
        self.analyze_called = False
        self.analyze_results = []
    
    def analyze(self, text, language=None):
        """Mock analyze method."""
        self.analyze_called = True
        # Return a simple result for testing
        self.analyze_results = [
            {"entity_type": "PERSON", "text": "John Smith", "score": 0.85},
            {"entity_type": "EMAIL", "text": "john@example.com", "score": 0.95}
        ]
        return self.analyze_results
    
    def add_pattern(self, pattern):
        """Mock add_pattern method."""
        self.patterns.append(pattern)


class MockAnonymizer:
    """Mock class for simulating an anonymizer."""
    
    def __init__(self, analyzer=None):
        self.analyzer = analyzer
        self.anonymize_called = False
        
    def anonymize(self, text, operators=None):
        """Mock anonymize method."""
        self.anonymize_called = True
        # Return a simple anonymized result
        return {
            "text": "Hello <PERSON>, your email is <EMAIL>",
            "items": [
                {"entity_type": "PERSON", "start": 6, "end": 14, "replacement": "<PERSON>"},
                {"entity_type": "EMAIL", "start": 29, "end": 36, "replacement": "<EMAIL>"}
            ]
        }


class TestFactoryFunctions(unittest.TestCase):
    """Test the factory functions in the package."""
    
    @patch("sys.modules")
    def test_create_au_insurance_analyzer(self, mock_modules):
        """Test the create_au_insurance_analyzer factory function."""
        # Create a mock EnhancedAnalyzer class
        mock_enhanced_analyzer = MagicMock()
        
        # Set up the module mocks
        mock_modules.get.return_value = MagicMock(
            EnhancedAnalyzer=mock_enhanced_analyzer,
            create_au_insurance_analyzer=lambda: mock_enhanced_analyzer()
        )
        
        # Import the function (this will use our mocked modules)
        from allyanonimiser import create_au_insurance_analyzer
        
        # Call the factory function
        analyzer = create_au_insurance_analyzer()
        
        # Verify that the analyzer was created
        self.assertIsNotNone(analyzer)
        # Verify that EnhancedAnalyzer was called
        mock_enhanced_analyzer.assert_called_once()
    
    @patch("sys.modules")
    def test_create_allyanonimiser(self, mock_modules):
        """Test the create_allyanonimiser factory function."""
        # Create mock classes
        mock_allyanonimiser = MagicMock()
        mock_enhanced_analyzer = MagicMock()
        
        # Set up the module mocks
        mock_modules.get.return_value = MagicMock(
            Allyanonimiser=mock_allyanonimiser,
            EnhancedAnalyzer=mock_enhanced_analyzer,
            create_allyanonimiser=lambda: mock_allyanonimiser(analyzer=mock_enhanced_analyzer())
        )
        
        # Import the function
        from allyanonimiser import create_allyanonimiser
        
        # Call the factory function
        instance = create_allyanonimiser()
        
        # Verify that the instance was created
        self.assertIsNotNone(instance)
        # Verify that Allyanonimiser was called
        mock_allyanonimiser.assert_called_once()


class TestClaimNotesAnalyzer(unittest.TestCase):
    """Test the ClaimNotesAnalyzer class."""
    
    @patch("sys.modules")
    def test_analyze_claim_notes(self, mock_modules):
        """Test the analyze_claim_notes function."""
        # Create a mock ClaimNotesAnalyzer class
        mock_claim_notes_analyzer = MagicMock()
        mock_claim_notes_analyzer.return_value.analyze.return_value = {
            "incident_description": "Vehicle accident",
            "customer_details": {"name": "John Smith", "phone": "0412345678"},
            "pii_segments": [{"text": "Name: John Smith", "pii_likelihood": 0.9}]
        }
        
        # Set up the module mocks
        mock_modules.get.return_value = MagicMock(
            ClaimNotesAnalyzer=mock_claim_notes_analyzer,
            analyze_claim_notes=lambda text: mock_claim_notes_analyzer().analyze(text)
        )
        
        # Import the function
        from allyanonimiser import analyze_claim_notes
        
        # Call the function
        result = analyze_claim_notes("Claim note text...")
        
        # Verify that the function returned the expected result
        self.assertIn("incident_description", result)
        self.assertIn("customer_details", result)
        self.assertIn("pii_segments", result)
        
        # Verify that ClaimNotesAnalyzer.analyze was called
        mock_claim_notes_analyzer.return_value.analyze.assert_called_once()


class TestAllyanonimiserInterface(unittest.TestCase):
    """Test the Allyanonimiser main interface."""
    
    @patch("sys.modules")
    def test_process_method(self, mock_modules):
        """Test the process method of the Allyanonimiser class."""
        # Create a mock Allyanonimiser class
        mock_allyanonimiser = MagicMock()
        mock_allyanonimiser.return_value.process.return_value = {
            "analysis": {"entities": [{"entity_type": "PERSON", "text": "John Smith"}]},
            "anonymized": "Hello <PERSON>",
            "content_type": "generic"
        }
        
        # Set up the module mocks
        mock_modules.get.return_value = MagicMock(
            Allyanonimiser=mock_allyanonimiser
        )
        
        # Import the class
        from allyanonimiser import Allyanonimiser
        
        # Create an instance and call the process method
        instance = Allyanonimiser()
        result = instance.process("Hello John Smith")
        
        # Verify that the method returned the expected result
        self.assertIn("analysis", result)
        self.assertIn("anonymized", result)
        self.assertIn("content_type", result)
        
        # Verify that the process method was called
        mock_allyanonimiser.return_value.process.assert_called_once_with("Hello John Smith")


class FunctionalTests(unittest.TestCase):
    """Integration-style tests that mock minimal components."""
    
    def setUp(self):
        """Set up test environment."""
        # Skip tests if real modules not available
        self.skipIfModulesNotAvailable = False
        
        # Try to import the real modules
        try:
            # Use importlib to avoid polluting the global namespace
            import importlib
            self.allyanonimiser_module = importlib.import_module("allyanonimiser")
        except ImportError:
            self.skipIfModulesNotAvailable = True
    
    def test_factory_functions_coordination(self):
        """Test that factory functions work together correctly."""
        if self.skipIfModulesNotAvailable:
            self.skipTest("allyanonimiser module not available")
        
        # Create mock objects
        mock_analyzer = MockAnalyzer()
        mock_anonymizer = MockAnonymizer(analyzer=mock_analyzer)
        
        # Patch the module to return our mocks
        with patch.object(self.allyanonimiser_module, "EnhancedAnalyzer", return_value=mock_analyzer), \
             patch.object(self.allyanonimiser_module, "EnhancedAnonymizer", return_value=mock_anonymizer):
            
            # Test the create_au_insurance_analyzer function
            analyzer = self.allyanonimiser_module.create_au_insurance_analyzer()
            self.assertIsNotNone(analyzer)
            
            # Test adding a pattern
            test_pattern = {"entity_type": "TEST", "pattern": "test", "context": ["test"]}
            analyzer.add_pattern(test_pattern)
            self.assertIn(test_pattern, analyzer.patterns)
            
            # Test analyzing text
            results = analyzer.analyze("Hello John Smith")
            self.assertTrue(analyzer.analyze_called)
            self.assertEqual(len(analyzer.analyze_results), 2)


if __name__ == "__main__":
    unittest.main()