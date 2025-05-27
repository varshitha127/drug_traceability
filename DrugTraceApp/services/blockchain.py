import os
import json
import logging
from web3 import Web3, HTTPProvider
from django.conf import settings
from django.core.cache import cache
from typing import Dict, Any, Optional
import hashlib

logger = logging.getLogger(__name__)

class BlockchainService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BlockchainService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._web3 = None
            self._contract = None
            self._contract_address = None
            self._contract_abi = None
            self._initialize_blockchain()

    def _initialize_blockchain(self):
        """Initialize blockchain connection and contract"""
        try:
            # Get configuration from settings
            blockchain_address = getattr(settings, 'BLOCKCHAIN_ADDRESS', 'http://127.0.0.1:9545')
            contract_path = getattr(settings, 'CONTRACT_PATH', 'Drug.json')
            contract_address = getattr(settings, 'CONTRACT_ADDRESS', '0x152C98B8d6B3b6B983ba6bE52A1b0AcEf132e86D')

            # Initialize Web3
            self._web3 = Web3(HTTPProvider(blockchain_address))
            if not self._web3.is_connected():
                raise ConnectionError("Failed to connect to blockchain node")

            # Set default account
            if self._web3.eth.accounts:
                self._web3.eth.default_account = self._web3.eth.accounts[0]

            # Load contract
            try:
                with open(contract_path) as file:
                    contract_json = json.load(file)
                    self._contract_abi = contract_json['abi']
                self._contract_address = contract_address
                self._contract = self._web3.eth.contract(
                    address=self._contract_address,
                    abi=self._contract_abi
                )
            except Exception as e:
                logger.error(f"Error loading contract: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"Blockchain initialization error: {str(e)}")
            raise

    @property
    def web3(self) -> Web3:
        """Get Web3 instance"""
        if not self._web3:
            self._initialize_blockchain()
        return self._web3

    @property
    def contract(self):
        """Get contract instance"""
        if not self._contract:
            self._initialize_blockchain()
        return self._contract

    def get_user_data(self) -> str:
        """Get user data from blockchain"""
        try:
            return self.contract.functions.getUser().call()
        except Exception as e:
            logger.error(f"Error getting user data: {str(e)}")
            raise

    def get_tracing_data(self) -> str:
        """Get tracing data from blockchain"""
        try:
            return self.contract.functions.getTracingData().call()
        except Exception as e:
            logger.error(f"Error getting tracing data: {str(e)}")
            raise

    def add_user_data(self, data: str) -> str:
        """Add user data to blockchain"""
        try:
            tx_hash = self.contract.functions.addUser(data).transact()
            return self.web3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            logger.error(f"Error adding user data: {str(e)}")
            raise

    def add_tracing_data(self, data: str) -> str:
        """Add tracing data to blockchain"""
        try:
            tx_hash = self.contract.functions.setTracingData(data).transact()
            return self.web3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            logger.error(f"Error adding tracing data: {str(e)}")
            raise

    def update_tracing_data(self, data: str) -> str:
        """Update tracing data in blockchain"""
        try:
            tx_hash = self.contract.functions.setTracingData(data).transact()
            return self.web3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            logger.error(f"Error updating tracing data: {str(e)}")
            raise

    def add_drug_trace(self, data: Dict[str, Any]) -> str:
        """Add drug trace to blockchain"""
        try:
            # Convert data to string format expected by contract
            data_str = json.dumps(data)
            tx_hash = self.contract.functions.setTracingData(data_str).transact()
            return self.web3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            logger.error(f"Error adding drug trace: {str(e)}")
            raise

    def verify_drug_trace(self, tx_hash: str, data: Dict[str, Any]) -> bool:
        """Verify drug trace in blockchain"""
        try:
            # Get transaction receipt
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            if not receipt:
                return False

            # Get transaction data
            tx = self.web3.eth.get_transaction(tx_hash)
            if not tx:
                return False

            # Verify transaction was successful
            if receipt['status'] != 1:
                return False

            # Get stored data from blockchain
            stored_data = self.get_drug_trace(tx_hash)
            if not stored_data:
                return False
            
            # Compare data hashes
            current_hash = hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest()
            
            stored_hash = hashlib.sha256(
                json.dumps(stored_data, sort_keys=True).encode()
            ).hexdigest()
            
            return current_hash == stored_hash
            
        except Exception as e:
            logger.error(f"Error verifying drug trace: {str(e)}")
            return False

    def _get_nonce(self) -> int:
        """Get the current nonce for the default account"""
        return self.web3.eth.get_transaction_count(self.web3.eth.default_account)
    
    def _sign_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Sign a transaction with the private key"""
        private_key = os.getenv('BLOCKCHAIN_PRIVATE_KEY')
        if not private_key:
            raise ValueError("Private key not found")
        
        signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key)
        return signed_txn
    
    def _wait_for_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Wait for a transaction to be mined and return receipt"""
        try:
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt['status'] != 1:
                raise Exception(f"Transaction failed: {receipt}")
            return receipt
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            raise
    
    def get_drug_trace(self, trace_hash: str) -> Optional[Dict[str, Any]]:
        """Get drug trace from blockchain"""
        try:
            # Check cache first
            cache_key = f"drug_trace_{trace_hash}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            
            # Get data from blockchain
            trace_data = self.contract.functions.getDrugTrace(trace_hash).call()
            if not trace_data:
                return None
            
            # Parse and cache the data
            parsed_data = json.loads(trace_data)
            cache.set(cache_key, parsed_data, timeout=3600)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Failed to get drug trace: {str(e)}")
            raise 