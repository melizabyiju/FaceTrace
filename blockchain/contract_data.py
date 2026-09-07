"""Pre-compiled ABI and bytecode for VerificationRegistry.

Generated from contracts/VerificationRegistry.sol (Solidity 0.8.19).
Keep this in sync if the contract source changes — or let
BlockchainClient.compile_contract() recompile at runtime with py-solc-x.
"""

CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "verificationId", "type": "bytes32"},
            {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
            {"internalType": "string", "name": "source", "type": "string"}
        ],
        "name": "registerVerification",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "verificationId", "type": "bytes32"}
        ],
        "name": "getVerification",
        "outputs": [
            {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
            {"internalType": "string", "name": "source", "type": "string"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "address", "name": "submitter", "type": "address"},
            {"internalType": "bool", "name": "exists_", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "verificationId", "type": "bytes32"},
            {"internalType": "bytes32", "name": "expectedHash", "type": "bytes32"}
        ],
        "name": "verifyHash",
        "outputs": [
            {"internalType": "bool", "name": "", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "", "type": "bytes32"}
        ],
        "name": "records",
        "outputs": [
            {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
            {"internalType": "string", "name": "source", "type": "string"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "address", "name": "submitter", "type": "address"},
            {"internalType": "bool", "name": "exists", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "recordCount",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "verificationId", "type": "bytes32"},
            {"indexed": False, "internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
            {"indexed": False, "internalType": "string", "name": "source", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "submitter", "type": "address"}
        ],
        "name": "VerificationRegistered",
        "type": "event"
    }
]

# -----------------------------------------------------------------------
# Bytecode placeholder — will be filled by compile_contract() at runtime
# if py-solc-x is installed, otherwise an error is raised at deploy time.
# -----------------------------------------------------------------------
CONTRACT_BYTECODE = ""
