"""Unit tests for image preprocessing"""
import unittest
import numpy as np
import cv2
from preprocess.image_prep import deskew, denoise, resize_to_dpi, binarize


class TestPreprocess(unittest.TestCase):
    def test_deskew(self):
        """Test deskew function"""
        # Create a test image
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        result = deskew(img)
        self.assertEqual(result.shape, img.shape)
    
    def test_denoise(self):
        """Test denoise function"""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        result = denoise(img)
        self.assertEqual(result.shape, img.shape)
    
    def test_resize_to_dpi(self):
        """Test DPI resize function"""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        result = resize_to_dpi(img, target_dpi=300, current_dpi=72)
        # Should be larger
        self.assertGreater(result.shape[0], img.shape[0])
    
    def test_binarize(self):
        """Test binarize function"""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        result = binarize(img)
        # Should be grayscale (2D)
        self.assertEqual(len(result.shape), 2)


if __name__ == '__main__':
    unittest.main()

