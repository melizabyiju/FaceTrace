"""Blockchain client — deploy and interact with VerificationRegistry."""
import os
import json
from web3 import Web3
from eth_account import Account

from .contract_data import CONTRACT_ABI, CONTRACT_BYTECODE

_CONTRACT_SOL = os.path.join(
    os.path.dirname(__file__), os.pardir, "contracts", "VerificationRegistry.sol"
)


def compile_contract():
    """Compile VerificationRegistry.sol with py-solc-x and return (abi, bin)."""
    try:
        import solcx
    except ImportError:
        raise ImportError(
            "py-solc-x is required to compile the contract. "
            "Install it with: pip install py-solc-x"
        )

    target = "0.8.19"
    installed = [str(v) for v in solcx.get_installed_solc_versions()]
    if target not in installed:
        print(f"[Blockchain] Installing Solidity compiler v{target}...")
        solcx.install_solc(target)

    with open(_CONTRACT_SOL, "r", encoding="utf-8") as f:
        source = f.read()

    compiled = solcx.compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version=target,
    )
    contract_id = "<stdin>:VerificationRegistry"
    return compiled[contract_id]["abi"], compiled[contract_id]["bin"]


class BlockchainClient:
    """High-level wrapper around web3.py for the VerificationRegistry."""

    def __init__(self, rpc_url: str, private_key: str,
                 contract_address: str = None):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(
                f"Cannot connect to blockchain node at {rpc_url}. "
                "Make sure Hardhat/Ganache is running."
            )
        self.account = Account.from_key(private_key)
        self.contract_address = contract_address
        self.contract = None
        self.abi = CONTRACT_ABI

        if contract_address:
            self._load_contract(contract_address)

    # ------------------------------------------------------------------ #
    #  Contract helpers                                                    #
    # ------------------------------------------------------------------ #
    def _load_contract(self, address: str):
        """Attach to an already-deployed contract."""
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=self.abi,
        )

    def deploy_contract(self) -> str:
        """
        Compile (if needed) and deploy VerificationRegistry.
        Returns the deployed contract address.
        """
        # Try runtime compilation first
        bytecode = CONTRACT_BYTECODE
        abi = self.abi
        if not bytecode:
            print("[Blockchain] Compiling contract with py-solc-x...")
            abi, bytecode = compile_contract()
            self.abi = abi

        print("[Blockchain] Deploying VerificationRegistry...")
        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)

        tx = contract.constructor().build_transaction({
            "from": self.account.address,
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            "gas": 3_000_000,
            "gasPrice": self.w3.eth.gas_price or self.w3.to_wei("1", "gwei"),
        })
        signed = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        self.contract_address = receipt.contractAddress
        self._load_contract(self.contract_address)

        print(f"[Blockchain] Contract deployed at : {self.contract_address}")
        print(f"[Blockchain] Deploy tx            : 0x{tx_hash.hex()}")
        return self.contract_address

    # ------------------------------------------------------------------ #
    #  Write / Read                                                        #
    # ------------------------------------------------------------------ #
    def register_verification(self, verification_id: str,
                              data_hash: str, source: str) -> dict:
        """
        Write a verification fingerprint on-chain.

        Args:
            verification_id: 64-char hex string (will be converted to bytes32).
            data_hash:       64-char hex SHA-256 digest.
            source:          Platform name, e.g. "Instagram".
        """
        vid_bytes  = bytes.fromhex(verification_id[:64])
        hash_bytes = bytes.fromhex(data_hash[:64])

        tx = self.contract.functions.registerVerification(
            vid_bytes, hash_bytes, source
        ).build_transaction({
            "from": self.account.address,
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            "gas": 500_000,
            "gasPrice": self.w3.eth.gas_price or self.w3.to_wei("1", "gwei"),
        })
        signed = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        return {
            "tx_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "status": "success" if receipt.status == 1 else "failed",
            "contract_address": self.contract_address,
        }

    def get_verification(self, verification_id: str) -> dict:
        """Read a verification record from the chain."""
        vid_bytes = bytes.fromhex(verification_id[:64])
        result = self.contract.functions.getVerification(vid_bytes).call()
        return {
            "data_hash": result[0].hex(),
            "source": result[1],
            "timestamp": result[2],
            "submitter": result[3],
            "exists": result[4],
        }

    def verify_hash_onchain(self, verification_id: str,
                            expected_hash: str) -> bool:
        """Call the contract's verifyHash and return True/False."""
        vid_bytes  = bytes.fromhex(verification_id[:64])
        hash_bytes = bytes.fromhex(expected_hash[:64])
        return self.contract.functions.verifyHash(vid_bytes, hash_bytes).call()
