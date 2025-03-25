import json
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataIngestionAgent:
    """
    Processes raw transaction data into a standardized format using Python code.
    - Converts timestamps to ISO 8601 format (UTC).
    - Removes duplicate transactions based on transaction_id and timestamp.
    - Maps known fields and places others into metadata.
    """
    def __init__(self):
        """Initialize the data ingestion agent."""
        # No client needed as this agent does not use an LLM
        self.processed_transactions: List[Dict[str, Any]] = []
        self.seen_transactions: Set[Tuple[str, str]] = set()
        # Define core fields expected in the output transaction object
        # Optional core fields will be included if present, others go to metadata
        self.core_fields = {"transaction_id", "timestamp", "amount", "currency", "sender", "receiver"}
        self.optional_core_fields = {"transaction_type", "source_system"}

    def _standardize_timestamp(self, timestamp_str: Optional[str]) -> Optional[str]:
        """Converts a timestamp string to ISO 8601 format in UTC."""
        if not timestamp_str:
            return None
        try:
            # Attempt to parse the timestamp, assuming it might be ISO 8601 compatible
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            # Ensure it's timezone-aware and convert to UTC
            if dt.tzinfo is None:
                # If naive, assume UTC (or configure a default timezone if needed)
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            # Return in ISO 8601 format with 'Z' for UTC
            return dt.isoformat(timespec='seconds').replace('+00:00', 'Z')
        except ValueError:
            logging.warning(f"Could not parse timestamp: {timestamp_str}. Skipping conversion.")
            # Return original or None if parsing fails, depending on requirements
            # Returning None might be safer if ISO format is strictly required downstream
            return None
        except Exception as e:
            logging.error(f"Error processing timestamp '{timestamp_str}': {e}")
            return None

    def _process_transaction(self, transaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processes a single transaction for standardization and deduplication."""
        tx_id = transaction.get("transaction_id")
        raw_timestamp = transaction.get("timestamp")

        if not tx_id or not raw_timestamp:
            logging.warning(f"Skipping transaction due to missing ID or timestamp: {transaction.get('transaction_id', 'N/A')}")
            return None

        # Standardize timestamp first for deduplication key
        standardized_ts = self._standardize_timestamp(raw_timestamp)
        if not standardized_ts:
            logging.warning(f"Skipping transaction {tx_id} due to invalid timestamp: {raw_timestamp}")
            return None

        # Check for duplicates
        transaction_key = (str(tx_id), standardized_ts)
        if transaction_key in self.seen_transactions:
            logging.info(f"Duplicate transaction found, skipping: {tx_id} at {standardized_ts}")
            return None
        self.seen_transactions.add(transaction_key)

        # Create standardized transaction object
        standardized_tx = {}
        metadata = {}

        for key, value in transaction.items():
            if key in self.core_fields:
                standardized_tx[key] = value
            elif key in self.optional_core_fields:
                standardized_tx[key] = value
            # Special handling for timestamp - use the standardized one
            elif key == "timestamp":
                standardized_tx[key] = standardized_ts
            # Put all other fields into metadata
            else:
                metadata[key] = value

        # Ensure all mandatory core fields are present (handle if needed, e.g., raise error or default)
        # For now, assume they exist if tx_id and timestamp were present
        if not all(field in standardized_tx for field in self.core_fields):
            logging.warning(f"Transaction {tx_id} is missing some core fields after processing. Raw: {transaction}")
            # Decide if you want to skip or proceed with missing fields
            # return None # Option to skip

        # Add metadata if it's not empty
        if metadata:
            standardized_tx["metadata"] = metadata
            
        # Specific type checks/conversions (example for amount)
        if 'amount' in standardized_tx:
            try:
                standardized_tx['amount'] = float(standardized_tx['amount'])
            except (ValueError, TypeError):
                logging.warning(f"Could not convert amount '{standardized_tx['amount']}' to float for tx {tx_id}. Keeping original.")

        return standardized_tx

    def run(self, raw_transaction_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Transforms raw transaction data into a standardized format using Python code.

        Args:
            raw_transaction_data: Dictionary containing a list of transactions,
                                typically loaded from a JSON structure like
                                {"transactions": [...]}.

        Returns:
            dict: Standardized data containing a "transactions" list, conforming to
                  the target schema.
        """
        self.processed_transactions = []
        self.seen_transactions = set()

        if not isinstance(raw_transaction_data, dict) or "transactions" not in raw_transaction_data:
            logging.error("Input data is not a dictionary or missing 'transactions' key.")
            return {"transactions": []}

        input_transactions = raw_transaction_data["transactions"]
        if not isinstance(input_transactions, list):
            logging.error("'transactions' key does not contain a list.")
            return {"transactions": []}

        for transaction in input_transactions:
            if not isinstance(transaction, dict):
                logging.warning(f"Skipping item in transaction list as it's not a dictionary: {transaction}")
                continue

            processed_tx = self._process_transaction(transaction)
            if processed_tx:
                self.processed_transactions.append(processed_tx)

        logging.info(f"Data ingestion complete. Processed {len(self.processed_transactions)} unique transactions.")
        return {"transactions": self.processed_transactions}
