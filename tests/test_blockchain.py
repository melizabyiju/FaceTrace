"""Tests for blockchain client (require a running local node)."""
import os
import pytest
from unittest.mock import MagicMock, patch
from hashing.fingerprint import create_verification_fingerprint


def _blockchain_available():
    """Check if a local blockchain node is running."""
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        return w3.is_connected()
    except Exception:
        return False


@pytest.mark.skipif(
    not _blockchain_available(),
    reason="Local blockchain node not running"
)
class TestBlockchainIntegration:
    """Integration tests — require Hardhat node on localhost:8545."""

    def test_deploy_and_verify(self):
        from blockchain.client import BlockchainClient

        client = BlockchainClient(
            rpc_url="http://127.0.0.1:8545",
            private_key="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
        )
        address = client.deploy_contract()
        assert address is not None
        assert address.startswith("0x")

        # Register a verification
        fp = create_verification_fingerprint(
            "https://example.com/post", b"test image data", "2026-01-01T00:00:00"
        )
        import hashlib
        vid = hashlib.sha256(b"test-verification").hexdigest()

        tx = client.register_verification(vid, fp["data_hash"], "TestPlatform")
        assert tx["status"] == "success"

        # Retrieve and verify
        record = client.get_verification(vid)
        assert record["exists"] is True
        assert record["data_hash"] == fp["data_hash"]

        # On-chain verify
        assert client.verify_hash_onchain(vid, fp["data_hash"]) is True
        assert client.verify_hash_onchain(vid, "00" * 32) is False
