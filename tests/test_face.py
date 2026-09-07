"""Tests for the face module (require test images to be meaningful)."""
import os
import pytest
from face.detector import validate_image


class TestValidateImage:
    def test_nonexistent_file(self):
        result = validate_image("/nonexistent/path.jpg")
        assert result["valid"] is False
        assert "not found" in result["error"].lower()

    def test_invalid_file(self, tmp_path):
        bad = tmp_path / "bad.jpg"
        bad.write_text("not an image")
        result = validate_image(str(bad))
        assert result["valid"] is False
