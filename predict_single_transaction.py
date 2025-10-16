#!/usr/bin/env python3
"""
Single Transaction Predictor
Predict agent label, SOP link, and relevant reconciliation steps for a single transaction.
"""

import sys
from predict_with_rules import apply_rules
from agent_sop_mapping import AGENT_SOP_MAPPING

def predict_transaction(amount, date, payment_method, account, narrative):
    """
    Predict label and provide SOP guidance for a single transaction.
    
    Args:
        amount: Transaction amount (float or string with $)
        date: Transaction date (string)
        payment_method: Payment method (string)
        account: Account name (string)
        narrative: Transaction narrative/description (string)
    
    Returns:
        dict with prediction, SOP link, and reconciliation steps
    """
    # Clean amount
    if isinstance(amount, str):
        amount = float(amount.replace('$', '').replace(',', ''))
    
    # Create transaction dict for prediction
    transaction = {
        'amount': amount,
        'date': date,
        'payment_method': payment_method,
        'org_account': account,
        'transaction_narrative': narrative,
        'description': narrative  # Some functions use 'description'
    }
    
    # Predict using rules
    predicted_label = apply_rules(transaction)
    
    if not predicted_label:
        predicted_label = "Unable to determine (needs manual review)"
        sop_info = None
    else:
        # Get SOP mapping
        sop_info = AGENT_SOP_MAPPING.get(predicted_label)
    
    return {
        'label': predicted_label,
        'sop_info': sop_info,
        'transaction': transaction
    }

def format_output(result):
    """Format the prediction result for display."""
    output = []
    output.append("\n" + "="*80)
    output.append("🎯 TRANSACTION PREDICTION RESULT")
    output.append("="*80)
    
    # Transaction details
    output.append("\n📋 TRANSACTION DETAILS:")
    output.append(f"   Amount: ${result['transaction']['amount']:,.2f}")
    output.append(f"   Date: {result['transaction']['date']}")
    output.append(f"   Payment Method: {result['transaction']['payment_method']}")
    output.append(f"   Account: {result['transaction']['org_account']}")
    output.append(f"   Narrative: {result['transaction']['transaction_narrative'][:100]}...")
    
    # Prediction
    output.append("\n🤖 PREDICTED LABEL:")
    output.append(f"   → {result['label']}")
    
    if result['sop_info']:
        sop = result['sop_info']
        
        # SOP Link
        output.append("\n📚 RELEVANT SOP:")
        if sop.get('confluence_links'):
            for link in sop['confluence_links']:
                output.append(f"   🔗 {link}")
        
        # Labeling Rules
        output.append("\n📝 LABELING RULES:")
        if sop.get('labeling_rules'):
            for rule in sop['labeling_rules']:
                output.append(f"   • {rule}")
        
        # Reconciliation Steps
        output.append("\n✅ RECONCILIATION STEPS:")
        if sop.get('reconciliation_steps'):
            for i, step in enumerate(sop['reconciliation_steps'], 1):
                output.append(f"   {i}. {step}")
        
        # Additional Info
        if sop.get('frequency'):
            output.append(f"\n⏰ Frequency: {sop['frequency']}")
        if sop.get('criticality'):
            output.append(f"⚠️  Criticality: {sop['criticality']}")
        if sop.get('notes'):
            output.append(f"\n💡 Note: {sop['notes']}")
    else:
        output.append("\n⚠️  No SOP mapping found for this label.")
        output.append("   This transaction may require manual review or escalation.")
    
    output.append("\n" + "="*80 + "\n")
    
    return "\n".join(output)

def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 6:
        print("Usage: python predict_single_transaction.py <amount> <date> <payment_method> <account> <narrative>")
        print("\nExample:")
        print('python predict_single_transaction.py "$5,100.00" "10/14/2025" "wire in" "Chase Wire In" "YOUR REF=POH OF 25/10/14..."')
        sys.exit(1)
    
    amount = sys.argv[1]
    date = sys.argv[2]
    payment_method = sys.argv[3]
    account = sys.argv[4]
    narrative = " ".join(sys.argv[5:])  # Rest of args is narrative
    
    result = predict_transaction(amount, date, payment_method, account, narrative)
    print(format_output(result))

if __name__ == "__main__":
    # Test with the provided example
    print("\n🧪 TESTING WITH PROVIDED EXAMPLE:")
    
    result = predict_transaction(
        amount="$5,100.00",
        date="10/14/2025 12:00:00am",
        payment_method="wire in",
        account="Chase Wire In",
        narrative="YOUR REF=POH OF 25/10/14,REC FROM=00000000730103207 CHELSEA N SARVER 5605 SCURTICE ST UNIT A LITTLETON CO 80120-1188 US,REMARK=1TRVXX9QP28C DEBIT REF POH OF"
    )
    
    print(format_output(result))

