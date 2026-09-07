#!/usr/bin/env python3
"""
Deploy the VerificationRegistry contract to the configured blockchain.

Usage:
    python scripts/deploy_contract.py

The contract address is printed to stdout so you can paste it into .env.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.config import Config
from blockchain.client import BlockchainClient


def main():
    print("╔══════════════════════════════════════╗")
    print("║  Deploy VerificationRegistry         ║")
    print("╚══════════════════════════════════════╝\n")

    print(f"  RPC URL:  {Config.BLOCKCHAIN_RPC_URL}")
    print(f"  Chain ID: {Config.CHAIN_ID}\n")

    client = BlockchainClient(
        rpc_url=Config.BLOCKCHAIN_RPC_URL,
        private_key=Config.PRIVATE_KEY,
    )

    address = client.deploy_contract()

    print(f"\n  ✅  Contract deployed successfully!")
    print(f"  Address: {address}")
    print(f"\n  Add this to your .env file:")
    print(f"  CONTRACT_ADDRESS={address}\n")


if __name__ == "__main__":
    main()
