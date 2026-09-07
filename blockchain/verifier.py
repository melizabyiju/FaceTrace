"""Off-chain verification — compare recomputed hash with on-chain record."""
from .client import BlockchainClient


class Verifier:
    """Wraps a BlockchainClient and performs hash re-verification."""

    def __init__(self, client: BlockchainClient):
        self.client = client

    def verify(self, verification_id: str, recomputed_hash: str) -> dict:
        """
        Retrieve the on-chain record and compare with *recomputed_hash*.

        Returns a dict with:
            verified, on_chain_hash, recomputed_hash, status,
            on_chain_timestamp, submitter
        """
        on_chain = self.client.get_verification(verification_id)

        if not on_chain["exists"]:
            return {
                "verified": False,
                "error": "No record found on-chain for this verification ID.",
                "status": "NOT FOUND",
            }

        on_chain_hash = on_chain["data_hash"]
        match = on_chain_hash == recomputed_hash

        return {
            "verified": match,
            "on_chain_hash": on_chain_hash,
            "recomputed_hash": recomputed_hash,
            "status": "VERIFIED ✓" if match else "MISMATCH ✗",
            "on_chain_timestamp": on_chain["timestamp"],
            "submitter": on_chain["submitter"],
        }
