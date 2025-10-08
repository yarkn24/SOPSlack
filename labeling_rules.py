"""
Labeling Rules for Agent Assignment
=====================================
Rules that prevent labeling in specific conditions.
"""

from datetime import datetime, date

def should_skip_labeling(row, today_date=None):
    """
    Check if a transaction should be skipped from labeling.
    
    Args:
        row: DataFrame row with transaction data
        today_date: Today's date (for testing), defaults to datetime.now().date()
    
    Returns:
        tuple: (should_skip: bool, reason: str or None)
    """
    if today_date is None:
        today_date = datetime.now().date()
    
    # Get transaction details
    account_id = row.get('origination_account_id_num', 0)
    account_name = row.get('account', '')
    payment_method_name = row.get('payment_method', '')
    predicted_agent = row.get('predicted_agent', '')
    transaction_date = row.get('date', '')
    
    # Parse transaction date
    try:
        if isinstance(transaction_date, str):
            trans_date = datetime.strptime(transaction_date, '%Y-%m-%d').date()
        else:
            trans_date = transaction_date.date() if hasattr(transaction_date, 'date') else transaction_date
    except:
        trans_date = None
    
    # RULE 1: Never label ZBT (Zero Balance Transfer)
    if predicted_agent == 'ZBT' or payment_method_name == 'zero_balance_transfer':
        return (True, "ZBT transactions are never labeled (business rule)")
    
    # RULE 2: Chase Payroll Incoming Wires (Account 6 ONLY) - TODAY only
    # Only skip if transaction date is TODAY
    # NOTE: Account 6 and Account 9 are DIFFERENT accounts - never combine them!
    if account_id == 6 and trans_date == today_date:
        return (True, f"Account 6 (Chase Payroll Incoming Wires) - same-day transactions not labeled (Risk, needs T+1)")
    
    # No skip needed
    return (False, None)


def get_unlabeled_summary(df):
    """
    Generate summary of unlabeled transactions.
    
    Args:
        df: DataFrame with 'skip_labeling' and 'skip_reason' columns
    
    Returns:
        str: Summary text for Slack message, or None if no unlabeled transactions
    """
    if 'skip_labeling' not in df.columns:
        return None
    
    unlabeled = df[df['skip_labeling'] == True]
    
    if len(unlabeled) == 0:
        return None
    
    # Group by reason
    reason_counts = unlabeled['skip_reason'].value_counts()
    
    summary = "⚠️ *Unlabeled Transactions*\n"
    summary += f"Total: {len(unlabeled)} transaction(s) not labeled\n\n"
    
    for reason, count in reason_counts.items():
        summary += f"• {count} transaction(s): {reason}\n"
    
    return summary

