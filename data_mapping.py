"""
Data Mapping Configuration
===========================
Maps Redash column names/values to ML model format.

Redash uses text names (e.g., "ach_external", "Chase Wire In")
ML model uses numeric codes (e.g., 4, 21)
"""

# Payment Method Mapping: Text (Redash) → Number (Training Data)
PAYMENT_METHOD_MAPPING = {
    'wire_in': 0,
    'wire_out': 1,
    'check_paid': 2,
    'ach_return': 3,
    'ach_transaction': 4,
    'check_returned': 5,
    'known_unknown': 7,
    'unknown_method': 8,
    'transfer': 9,
    'ach_external': 10,
    'wire_return': 11,
    'zero_balance_transfer': 12,
    'interest_and_charges': 13,
    'unknown': 14,
}

# Account Mapping: Text (Redash) → Number (Training Data)
ACCOUNT_MAPPING = {
    'SVB Operations': 1,
    'Chase Operations': 3,
    'Chase Incoming Wires': 6,
    'Chase Recovery': 7,
    'Chase Flex Pay': 8,
    'Chase Wire In': 9,
    'SVB Wire In': 10,
    'Sunrise': 11,  # Also 14, 15
    'Chase Flex Pay Revenue': 13,
    'PNC Operations': 16,
    'PNC Corporate Cash': 17,
    'PNC Customer Wire Ins': 18,
    'BRB Customer Operations Old': 19,
    'BRB Corporate Cash': 20,
    'Chase International Contractor Payments': 21,
    'Brex Operations': 22,
    'BRB Customer Operations': 26,
    'Grasshopper Operations': 31,
}

# Reverse mapping for display
PAYMENT_METHOD_REVERSE = {v: k for k, v in PAYMENT_METHOD_MAPPING.items()}
ACCOUNT_REVERSE = {v: k for k, v in ACCOUNT_MAPPING.items()}


def map_payment_method(pm_text: str) -> int:
    """
    Convert payment method text to numeric code.
    
    Args:
        pm_text: Payment method text (e.g., "ach_external")
    
    Returns:
        Numeric code (e.g., 4)
    """
    pm_text = str(pm_text).lower().strip()
    return PAYMENT_METHOD_MAPPING.get(pm_text, 8)  # Default: 8 (unknown)


def map_account(account_text: str) -> int:
    """
    Convert account text to numeric code.
    
    Args:
        account_text: Account text (e.g., "Chase Wire In")
    
    Returns:
        Numeric code (e.g., 7)
    """
    account_text = str(account_text).strip()
    return ACCOUNT_MAPPING.get(account_text, 0)  # Default: 0 (unknown)


def normalize_amount(amount: float) -> float:
    """
    Normalize amount to match training data format.
    
    Redash query amounts are already in correct dollar format.
    Training data uses the same format.
    No conversion needed!
    
    Args:
        amount: Amount from Redash (e.g., 1993819.11)
    
    Returns:
        Same amount (e.g., 1993819.11)
    """
    return amount  # No conversion needed!


def prepare_for_prediction(redash_row: dict) -> dict:
    """
    Convert Redash data row to ML model format.
    
    Args:
        redash_row: Dictionary with Redash column names
    
    Returns:
        Dictionary with ML model column names and formats
    """
    return {
        'id': redash_row['id'],
        'description': redash_row['description'],
        'amount': normalize_amount(float(redash_row['amount'])),
        'payment_method': map_payment_method(redash_row['payment_method']),
        'origination_account': map_account(redash_row['account']),
    }


# Test the mappings
if __name__ == "__main__":
    print("=" * 80)
    print("DATA MAPPING TEST")
    print("=" * 80)
    print()
    
    # Example Redash row
    redash_row = {
        'id': 58947234,
        'description': 'ORIG CO NAME=NIUM INC,ORIG ID=0514672353...',
        'amount': 1993819.11,
        'payment_method': 'ach_external',
        'account': 'Chase International Contractor Payments',
        'agent': 'Nium Payment',
    }
    
    print("📥 REDASH DATA:")
    for key, value in redash_row.items():
        if key == 'description':
            print(f"   {key}: {value[:50]}...")
        else:
            print(f"   {key}: {value}")
    
    print()
    print("🔄 MAPPED FOR ML MODEL:")
    ml_row = prepare_for_prediction(redash_row)
    for key, value in ml_row.items():
        if key == 'description':
            print(f"   {key}: {value[:50]}...")
        else:
            print(f"   {key}: {value}")
    
    print()
    print("=" * 80)
    print("MAPPING TABLES")
    print("=" * 80)
    print()
    
    print("📊 Payment Method Mapping:")
    for text, code in sorted(PAYMENT_METHOD_MAPPING.items()):
        print(f"   '{text}' → {code}")
    
    print()
    print("🏦 Account Mapping:")
    for text, code in sorted(ACCOUNT_MAPPING.items()):
        print(f"   '{text}' → {code}")

