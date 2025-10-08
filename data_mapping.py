"""
Data Mapping Configuration
===========================
Maps Redash column names/values to ML model format.

Redash uses text names (e.g., "ach_external", "Chase Wire In")
ML model uses numeric codes (e.g., 4, 21)
"""

# Payment Method Mapping: Text (Redash) → Number (Training Data)
PAYMENT_METHOD_MAPPING = {
    0: 'wire_in',
    1: 'wire_out',
    2: 'check_paid',
    3: 'ach_return',
    4: 'ach_transaction',
    5: 'check_returned',
    7: 'known_unknown',
    8: 'unknown_method',
    9: 'transfer',
    10: 'ach_external',
    11: 'wire_return',
    12: 'zero_balance_transfer',
    13: 'interest_and_charges',
    14: 'unknown',
}

# Reverse mapping: Text → Number
PAYMENT_METHOD_REVERSE = {v: k for k, v in PAYMENT_METHOD_MAPPING.items()}

# Account Mapping: Number (ID) → Text (Name) - FROM REDASH QUERY
ACCOUNT_MAPPING = {
    1: 'SVB Operations',
    3: 'Chase Operations',
    6: 'Chase Incoming Wires',
    7: 'Chase Recovery',
    8: 'Chase Flex Pay',
    9: 'Chase Wire In',
    10: 'SVB Wire In',
    11: 'Sunrise',
    13: 'Chase Flex Pay Revenue',
    14: 'Sunrise',
    15: 'Sunrise',
    16: 'PNC Operations',
    17: 'PNC Corporate Cash',
    18: 'PNC Customer Wire Ins',
    19: 'BRB Customer Operations Old',
    20: 'BRB Corporate Cash',
    21: 'Chase International Contractor Payments',
    22: 'Brex Operations',
    26: 'BRB Customer Operations',
    31: 'Grasshopper Operations',
}

# Reverse mapping: Text → Number
ACCOUNT_REVERSE = {v: k for k, v in ACCOUNT_MAPPING.items()}


def map_payment_method(pm_text: str) -> int:
    """
    Convert payment method text to numeric code.
    
    Args:
        pm_text: Payment method text (e.g., "ach_external")
    
    Returns:
        Numeric code (e.g., 10)
    """
    pm_text = str(pm_text).lower().strip()
    return PAYMENT_METHOD_REVERSE.get(pm_text, 8)  # Default: 8 (unknown)


def is_corporate_account(account_text: str) -> bool:
    """
    Check if account is corporate (out of scope).
    Any account with "Corporate" in the name is ignored.
    
    Args:
        account_text: Account text
    
    Returns:
        True if corporate account (should be ignored)
    """
    account_text = str(account_text).strip()
    return 'corporate' in account_text.lower()


def map_account(account_text: str) -> int:
    """
    Convert account text to numeric code.
    
    Args:
        account_text: Account text (e.g., "Chase Wire In")
    
    Returns:
        Numeric code (e.g., 9), or -1 if corporate account
    """
    account_text = str(account_text).strip()
    
    # Check if corporate (out of scope)
    if is_corporate_account(account_text):
        return -1  # Special code for corporate accounts
    
    return ACCOUNT_REVERSE.get(account_text, 0)  # Default: 0 (unknown)


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

