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
    """Service class for handling blockchain operations"""
    
    def __init__(self):
        self.web3 = None
        self.contract = None
        self._initialize_web3()
    
    def _initialize_web3(self) -> None:
        """Initialize Web3 connection and contract"""
        try:
            # Get blockchain configuration from environment variables
            blockchain_url = os.getenv('BLOCKCHAIN_URL', 'http://127.0.0.1:9545')
            contract_address = os.getenv('CONTRACT_ADDRESS')
            contract_abi_path = os.path.join(settings.BASE_DIR, 'contracts', 'Drug.json')
            
            if not all([blockchain_url, contract_address, contract_abi_path]):
                raise ValueError("Missing blockchain configuration")
            
            # Initialize Web3
            self.web3 = Web3(HTTPProvider(blockchain_url))
            if not self.web3.is_connected():
                raise ConnectionError("Failed to connect to blockchain network")
            
            # Load contract ABI
            with open(contract_abi_path) as f:
                contract_json = json.load(f)
                contract_abi = contract_json['abi']
            
            # Initialize contract
            self.contract = self.web3.eth.contract(
                address=contract_address,
                abi=contract_abi
            )
            
            # Set default account
            self.web3.eth.default_account = os.getenv('BLOCKCHAIN_ACCOUNT')
            
        except Exception as e:
            logger.error(f"Failed to initialize blockchain service: {str(e)}")
            raise
    
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
    
    def add_drug_trace(self, drug_data: Dict[str, Any]) -> str:
        """Add drug trace to blockchain"""
        try:
            # Generate unique hash for the drug data
            data_hash = hashlib.sha256(
                json.dumps(drug_data, sort_keys=True).encode()
            ).hexdigest()
            
            # Prepare transaction
            nonce = self._get_nonce()
            transaction = self.contract.functions.addDrugTrace(
                data_hash,
                json.dumps(drug_data)
            ).build_transaction({
                'nonce': nonce,
                'gas': 2000000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_txn = self._sign_transaction(transaction)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            receipt = self._wait_for_transaction(tx_hash)
            
            # Cache the transaction hash
            cache_key = f"drug_trace_{data_hash}"
            cache.set(cache_key, receipt['transactionHash'].hex(), timeout=3600)
            
            return receipt['transactionHash'].hex()
            
        except Exception as e:
            logger.error(f"Failed to add drug trace: {str(e)}")
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
    
    def verify_drug_trace(self, trace_hash: str, drug_data: Dict[str, Any]) -> bool:
        """Verify drug trace data against blockchain"""
        try:
            # Get stored data
            stored_data = self.get_drug_trace(trace_hash)
            if not stored_data:
                return False
            
            # Compare data hashes
            current_hash = hashlib.sha256(
                json.dumps(drug_data, sort_keys=True).encode()
            ).hexdigest()
            
            stored_hash = hashlib.sha256(
                json.dumps(stored_data, sort_keys=True).encode()
            ).hexdigest()
            
            return current_hash == stored_hash
            
        except Exception as e:
            logger.error(f"Failed to verify drug trace: {str(e)}")
            return False 