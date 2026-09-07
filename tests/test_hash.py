"""Tests for the hashing / fingerprint module."""
import pytest
from hashing.fingerprint import (
    calculate_sha256_bytes,
    calculate_sha256_string,
    calculate_sha256_file,
    create_verification_fingerprint,
    reverify_fingerprint,
)


class TestSHA256:
    def test_same_bytes_same_hash(self):
        data = b"hello world"
        assert calculate_sha256_bytes(data) == calculate_sha256_bytes(data)

    def test_different_bytes_different_hash(self):
        assert calculate_sha256_bytes(b"a") != calculate_sha256_bytes(b"b")

    def test_known_hash(self):
        # SHA-256 of empty string is well-known
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert calculate_sha256_bytes(b"") == expected

    def test_string_hash(self):
        h = calculate_sha256_string("test")
        assert len(h) == 64  # 256 bits = 64 hex chars


class TestFingerprint:
    def test_deterministic(self):
        fp1 = create_verification_fingerprint(
            post_url="https://example.com/post/1",
            image_data=b"fake image bytes",
            discovery_timestamp="2026-01-01T00:00:00+00:00",
        )
        fp2 = create_verification_fingerprint(
            post_url="https://example.com/post/1",
            image_data=b"fake image bytes",
            discovery_timestamp="2026-01-01T00:00:00+00:00",
        )
        assert fp1["data_hash"] == fp2["data_hash"]

    def test_different_url_different_hash(self):
        fp1 = create_verification_fingerprint(
            "https://a.com", b"img", "2026-01-01T00:00:00"
        )
        fp2 = create_verification_fingerprint(
            "https://b.com", b"img", "2026-01-01T00:00:00"
        )
        assert fp1["data_hash"] != fp2["data_hash"]

    def test_different_image_different_hash(self):
        fp1 = create_verification_fingerprint(
            "https://a.com", b"img1", "2026-01-01T00:00:00"
        )
        fp2 = create_verification_fingerprint(
            "https://a.com", b"img2", "2026-01-01T00:00:00"
        )
        assert fp1["data_hash"] != fp2["data_hash"]


class TestReverify:
    def test_matching_hash(self):
        fp = create_verification_fingerprint(
            "https://example.com", b"data", "2026-06-01T12:00:00"
        )
        result = reverify_fingerprint(
            "https://example.com", b"data", "2026-06-01T12:00:00",
            on_chain_hash=fp["data_hash"],
        )
        assert result["verified"] is True
        assert "VERIFIED" in result["match"]

    def test_tampered_data(self):
        fp = create_verification_fingerprint(
            "https://example.com", b"original", "2026-06-01T12:00:00"
        )
        result = reverify_fingerprint(
            "https://example.com", b"tampered", "2026-06-01T12:00:00",
            on_chain_hash=fp["data_hash"],
        )
        assert result["verified"] is False
        assert "MISMATCH" in result["match"]
