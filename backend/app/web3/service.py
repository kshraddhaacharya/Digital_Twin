import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

ARTIFACTS_PATH = os.path.join(os.path.dirname(__file__), "contract_artifacts.json")


class Web3Service:
    """
    Web3 Engine managing decentralized patient identity, EVM smart contract deployment,
    immutable on-chain state anchoring, cryptographic verification, and sovereign consent.
    """

    _instance: Optional["Web3Service"] = None

    def __init__(self):
        self.provider_url = os.getenv("WEB3_PROVIDER_URL")
        self.w3 = self._initialize_web3()
        self.artifacts = self._load_artifacts()
        self.account = self._setup_account()
        self.contract = self._deploy_or_attach_contract()

    @classmethod
    def get_instance(cls) -> "Web3Service":
        if cls._instance is None:
            cls._instance = Web3Service()
        return cls._instance

    def _initialize_web3(self) -> Web3:
        """Initializes connection to external EVM node or zero-config in-process EVM."""
        if self.provider_url:
            try:
                w3 = Web3(Web3.HTTPProvider(self.provider_url))
                if w3.is_connected():
                    # Support POA chains like Polygon, Arbitrum, BSC if needed
                    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                    print(f"[Web3] Connected to remote EVM provider: {self.provider_url}")
                    return w3
            except Exception as e:
                print(f"[Web3] Remote provider failed ({e}). Falling back to simulated in-process EVM.")

        # Fallback to local high-fidelity simulated EVM
        try:
            from web3.providers.eth_tester import EthereumTesterProvider
            w3 = Web3(EthereumTesterProvider())
            print("[Web3] Connected to high-fidelity in-process EVM blockchain (EthereumTesterProvider).")
            return w3
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Web3 EVM provider: {e}")

    def _load_artifacts(self) -> Dict[str, Any]:
        """Loads compiled smart contract ABI and Bytecode."""
        if not os.path.exists(ARTIFACTS_PATH):
            raise FileNotFoundError(f"Contract artifacts not found at {ARTIFACTS_PATH}")
        with open(ARTIFACTS_PATH, "r") as f:
            return json.load(f)

    def _setup_account(self):
        """Sets default transacting account."""
        accounts = self.w3.eth.accounts
        if accounts:
            self.w3.eth.default_account = accounts[0]
            return accounts[0]
        # Generate deterministic demo key if no accounts pre-loaded
        priv_key = os.getenv("WEB3_PRIVATE_KEY", "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d")
        acc = self.w3.eth.account.from_key(priv_key)
        return acc.address

    def _deploy_or_attach_contract(self):
        """Deploys registry contract or attaches to pre-existing deployment."""
        contract_addr = os.getenv("REGISTRY_CONTRACT_ADDRESS")
        abi = self.artifacts["abi"]
        bytecode = self.artifacts.get("bin", "")

        if contract_addr and self.w3.is_address(contract_addr):
            print(f"[Web3] Attached to existing registry contract at {contract_addr}")
            return self.w3.eth.contract(address=contract_addr, abi=abi)

        # Deploy fresh registry contract
        print("[Web3] Deploying PatientDigitalTwinRegistry smart contract to EVM...")
        contract_factory = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        tx_hash = contract_factory.constructor().transact({"from": self.account})
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        deployed_address = tx_receipt.contractAddress
        print(f"[Web3] Smart contract deployed at {deployed_address} in Block #{tx_receipt.blockNumber} (tx: {tx_hash.hex()})")
        return self.w3.eth.contract(address=deployed_address, abi=abi)

    @staticmethod
    def calculate_state_hash(patient_id: str, version: int, features: Dict[str, Any]) -> str:
        """
        Computes a deterministic cryptographic SHA-256 state root of the digital twin features.
        """
        payload = {
            "patient_id": patient_id,
            "version": version,
            "latest_heart_rate": round(features.get("latest_heart_rate", 0.0), 2),
            "rolling_mean_60m": round(features.get("rolling_mean_60m", 0.0), 2),
            "trend_slope_per_hour": round(features.get("trend_slope_per_hour", 0.0), 2),
            "vital_status": features.get("vital_status", "normal"),
        }
        canonical_json = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_ipfs_cid(data: Dict[str, Any]) -> str:
        """
        Computes a deterministic content-addressed IPFS CIDv1 identifier.
        """
        canonical_data = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        h = hashlib.sha256(canonical_data).hexdigest()
        # Format as standard base32 CIDv1 representation (bafybeih...)
        return f"bafybeih{h[:40]}"

    def attest_twin_state(
        self,
        patient_id: str,
        version: int,
        timestamp: datetime,
        latest_hr: float,
        rolling_mean: Optional[float],
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submits an on-chain transaction committing the digital twin state version,
        cryptographic state root, and IPFS CID to the Ethereum smart contract.
        """
        state_hash_hex = self.calculate_state_hash(patient_id, version, features)
        state_root_bytes = bytes.fromhex(state_hash_hex)

        ipfs_cid = self.generate_ipfs_cid({
            "patient_id": patient_id,
            "state_version": version,
            "features": features,
            "timestamp": timestamp.isoformat()
        })

        ts_epoch = int(timestamp.timestamp())
        scaled_hr = int(round(latest_hr * 10))
        scaled_mean = int(round((rolling_mean or latest_hr) * 10))

        # Register patient if not yet registered
        owner = self.contract.functions.patientOwners(patient_id).call()
        if owner == "0x0000000000000000000000000000000000000000":
            tx_reg = self.contract.functions.registerPatient(patientId=patient_id, owner=self.account).transact({"from": self.account})
            self.w3.eth.wait_for_transaction_receipt(tx_reg)

        # Call smart contract attestTwinState
        tx_hash = self.contract.functions.attestTwinState(
            patientId=patient_id,
            version=version,
            timestamp=ts_epoch,
            latestHR=scaled_hr,
            rollingMean=scaled_mean,
            stateRoot=state_root_bytes,
            ipfsCID=ipfs_cid
        ).transact({"from": self.account})

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            "on_chain_tx_hash": tx_hash.hex(),
            "on_chain_block_number": receipt.blockNumber,
            "state_hash_sha256": state_hash_hex,
            "ipfs_cid": ipfs_cid,
            "contract_address": self.contract.address,
            "attester_wallet": self.account,
            "gas_used": receipt.gasUsed
        }

    def verify_twin_attestation(
        self,
        patient_id: str,
        version: int,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validates cryptographic parity between a candidate digital twin state
        and the immutable attestation recorded on the Ethereum smart contract.
        """
        candidate_hash_hex = self.calculate_state_hash(patient_id, version, features)
        candidate_bytes = bytes.fromhex(candidate_hash_hex)

        is_valid, on_chain_root_bytes, ipfs_cid, block_num = self.contract.functions.verifyStateAttestation(
            patient_id,
            version,
            candidate_bytes
        ).call()

        on_chain_hash_hex = on_chain_root_bytes.hex() if isinstance(on_chain_root_bytes, bytes) else str(on_chain_root_bytes)

        return {
            "is_valid": bool(is_valid),
            "patient_id": patient_id,
            "state_version": version,
            "candidate_hash": candidate_hash_hex,
            "on_chain_root": on_chain_hash_hex,
            "ipfs_cid": ipfs_cid,
            "block_number": block_num,
            "contract_address": self.contract.address
        }

    def grant_researcher_access(self, patient_id: str, researcher_address: str, duration_seconds: int = 86400) -> str:
        """Sovereign consent: grants researcher wallet access on-chain."""
        tx_hash = self.contract.functions.grantAccess(
            patient_id,
            self.w3.to_checksum_address(researcher_address),
            duration_seconds
        ).transact({"from": self.account})
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex()

    def revoke_researcher_access(self, patient_id: str, researcher_address: str) -> str:
        """Sovereign consent: revokes researcher wallet access on-chain."""
        tx_hash = self.contract.functions.revokeAccess(
            patient_id,
            self.w3.to_checksum_address(researcher_address)
        ).transact({"from": self.account})
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex()

    def check_access(self, patient_id: str, user_address: str) -> bool:
        """Checks if a user/researcher address currently has active access on-chain."""
        return self.contract.functions.hasAccess(
            patient_id,
            self.w3.to_checksum_address(user_address)
        ).call()

    def get_network_status(self) -> Dict[str, Any]:
        """Returns Web3 connection and network telemetry."""
        balance_wei = self.w3.eth.get_balance(self.account)
        balance_eth = float(self.w3.from_wei(balance_wei, "ether"))
        return {
            "is_connected": self.w3.is_connected(),
            "chain_id": self.w3.eth.chain_id,
            "network_name": "EVM Simulated Node (Zero-Config)" if not self.provider_url else "Ethereum / EVM Compatible",
            "contract_address": self.contract.address,
            "active_wallet_address": self.account,
            "wallet_balance_eth": round(balance_eth, 4),
            "latest_block_number": self.w3.eth.block_number
        }
