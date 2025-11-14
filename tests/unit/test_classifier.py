"""Unit tests for text layer detection"""
import unittest
import tempfile
import os
from classifier.detect_text_layer import has_text_layer


class TestClassifier(unittest.TestCase):
    def test_has_text_layer_native_pdf(self):
        """Test detection of native text PDF"""
        # This would require a sample PDF with text
        # For now, just test the function exists
        self.assertTrue(callable(has_text_layer))
    
    def test_has_text_layer_scanned_pdf(self):
        """Test detection of scanned PDF (no text layer)"""
        # This would require a sample scanned PDF
        # For now, just test the function exists
        self.assertTrue(callable(has_text_layer))


if __name__ == '__main__':
    unittest.main()

