// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title VerificationRegistry
/// @notice Stores SHA-256 fingerprints of verified social-media discoveries.
///         Only hashes are stored on-chain — never raw images, text, or PII.
contract VerificationRegistry {

    struct Verification {
        bytes32 dataHash;      // SHA-256 fingerprint of discovered data
        string  source;        // e.g. "Instagram", "Web"
        uint256 timestamp;     // block.timestamp at registration
        address submitter;     // msg.sender
        bool    exists;        // guard against re-registration
    }

    mapping(bytes32 => Verification) public records;
    uint256 public recordCount;

    event VerificationRegistered(
        bytes32 indexed verificationId,
        bytes32 dataHash,
        string  source,
        uint256 timestamp,
        address submitter
    );

    /// @notice Register a new verification record.
    function registerVerification(
        bytes32 verificationId,
        bytes32 dataHash,
        string calldata source
    ) external {
        require(!records[verificationId].exists, "ID already registered");

        records[verificationId] = Verification({
            dataHash:  dataHash,
            source:    source,
            timestamp: block.timestamp,
            submitter: msg.sender,
            exists:    true
        });
        recordCount++;

        emit VerificationRegistered(
            verificationId, dataHash, source, block.timestamp, msg.sender
        );
    }

    /// @notice Retrieve a stored verification record.
    function getVerification(bytes32 verificationId)
        external view
        returns (
            bytes32 dataHash,
            string memory source,
            uint256 timestamp,
            address submitter,
            bool    exists_
        )
    {
        Verification storage v = records[verificationId];
        return (v.dataHash, v.source, v.timestamp, v.submitter, v.exists);
    }

    /// @notice Check whether a given hash matches the on-chain record.
    function verifyHash(bytes32 verificationId, bytes32 expectedHash)
        external view
        returns (bool)
    {
        if (!records[verificationId].exists) return false;
        return records[verificationId].dataHash == expectedHash;
    }
}
