#!/usr/bin/env python3
"""
🎯 Transaction Predictor - Single or Batch (CSV)
Predict agent labels and provide SOP guidance for transactions.

Usage:
    # Single transaction (interactive)
    python3 transaction_predictor.py --single

    # Batch from CSV
    python3 transaction_predictor.py --csv input.csv

    # Output to CSV
    python3 transaction_predictor.py --csv input.csv --output results.csv
"""

import sys
import argparse
import pandas as pd
from datetime import datetime
from agent_sop_mapping import AGENT_SOP_MAPPING

def simple_rule_prediction(narrative, amount, payment_method, account, date):
    """
    Simple rule-based prediction using common patterns.
    Returns predicted agent label.
    """
    desc = str(narrative).upper()
    amt = float(str(amount).replace('$', '').replace(',', '')) if amount else 0
    pm = str(payment_method).upper()
    acc = str(account).upper()
    
    # Rule-based logic (simplified for demo)
    
    # 1. ZBT transactions
    if 'ZBT' in pm or 'ZBT' in acc or 'ZERO BALANCE' in desc:
        return 'ZBT'
    
    # 2. NIUM transactions
    if 'NIUM' in desc:
        return 'Nium Payment'
    
    # 3. Risk transactions (1TRV pattern)
    if '1TRV' in desc or 'TRVXX' in desc:
        return 'Risk'
    
    # 4. State withholding patterns
    if 'NYS DTF WT' in desc or 'NY DTF WT' in desc:
        return 'NY WH'
    if 'NYS DOL UI' in desc:
        return 'NY UI'
    if '1HIOSDWH' in desc or 'OHSDWHTX' in desc:
        return 'OH SDWH'
    if 'ORIG CO NAME=STATE OF MONTANA' in desc or 'STATE OF MONTANA' in desc:
        return 'MT UI'
    if 'CA EMPLOYMENT' in desc or 'CA EDD' in desc:
        return 'CA WH'
    
    # 5. ICP patterns
    if 'JPMORGAN ACCESS TRANSFER' in desc:
        return 'ICP Funding'
    if 'ICP' in desc or 'INTERCOMPANY' in desc:
        return 'ICP'
    
    # 6. Payroll patterns
    if 'PAYROLL' in desc or 'GUSTO' in desc:
        if 'WIRE' in pm or 'WIRE' in acc:
            return 'Chase Payroll Incoming Wires'
        return 'Payroll'
    
    # 7. Treasury/Money Market
    if 'MONEY MARKET' in desc or 'MM SWEEP' in desc:
        return 'Money Market Transfer'
    if 'TREASURY' in desc or 'SWEEP' in desc:
        return 'Treasury Transfer'
    
    # 8. Check deposits
    if 'CHECK' in pm or 'CHECK' in desc:
        return 'Check'
    
    # 9. ACH patterns
    if 'ACH' in pm or 'ACH' in desc:
        return 'ACH'
    
    # 10. Wire transfers (generic)
    if 'WIRE' in pm or 'WIRE IN' in acc:
        if amt > 100000:
            return 'ICP'  # Large wires likely ICP
        return 'Wire Transfer'
    
    # 11. Returns/Reversals
    if 'RETURN' in desc or 'REVERSAL' in desc or 'REJECT' in desc:
        return 'ICP Return'
    
    # Default: Unable to determine
    return 'Unknown - Manual Review Required'

def get_sop_info(label):
    """Get SOP information for a given label."""
    return AGENT_SOP_MAPPING.get(label)

def predict_single_transaction(narrative, amount, payment_method, account, date):
    """Predict label and get SOP info for a single transaction."""
    
    label = simple_rule_prediction(narrative, amount, payment_method, account, date)
    sop_info = get_sop_info(label)
    
    return {
        'predicted_label': label,
        'sop_info': sop_info,
        'amount': amount,
        'date': date,
        'payment_method': payment_method,
        'account': account,
        'narrative': narrative
    }

def format_single_output(result):
    """Format output for a single transaction."""
    output = []
    output.append("\n" + "="*80)
    output.append("🎯 TRANSACTION PREDICTION RESULT")
    output.append("="*80)
    
    # Transaction details
    output.append("\n📋 TRANSACTION DETAILS:")
    output.append(f"   Amount: {result['amount']}")
    output.append(f"   Date: {result['date']}")
    output.append(f"   Payment Method: {result['payment_method']}")
    output.append(f"   Account: {result['account']}")
    output.append(f"   Narrative: {result['narrative'][:150]}...")
    
    # Prediction
    output.append("\n🤖 PREDICTED LABEL:")
    output.append(f"   → {result['predicted_label']}")
    
    sop = result['sop_info']
    if sop:
        # Get main SOP link (Daily Bank Transaction Reconciliation)
        main_sop = None
        escalation_sop = None
        if sop.get('confluence_links'):
            for link in sop['confluence_links']:
                if 'Daily+Bank' in link or '169411126' in link:
                    main_sop = link
                elif 'Escalating' in link or '460194134' in link:
                    escalation_sop = link
        
        # SOP Section
        if sop.get('sop_section'):
            output.append(f"\n📖 SOP SECTION WHERE THIS IS DOCUMENTED:")
            output.append(f"   → {sop['sop_section']}")
            if main_sop:
                output.append(f"   📄 Source: Daily Bank Transaction Reconciliation by Bank Transaction Type")
                output.append(f"   🔗 {main_sop}")
        
        # SOP Quote (exact text from SOP)
        if sop.get('sop_quote'):
            output.append(f"\n💬 EXACT TEXT FROM SOP:")
            output.append(f'   "{sop["sop_quote"]}"')
            if main_sop:
                output.append(f"   📄 Source: Daily Bank Transaction Reconciliation by Bank Transaction Type")
                output.append(f"   🔗 {main_sop}")
        
        # Labeling Rules
        output.append("\n📝 HOW TO IDENTIFY THIS TRANSACTION:")
        if sop.get('labeling_rules'):
            for rule in sop['labeling_rules']:
                output.append(f"   • {rule}")
            if main_sop:
                output.append(f"\n   📄 Source: Daily Bank Transaction Reconciliation by Bank Transaction Type")
                output.append(f"   🔗 {main_sop}")
        else:
            output.append("   • No specific labeling rules documented")
        
        # Reconciliation Steps
        output.append("\n✅ RECONCILIATION STEPS TO FOLLOW:")
        if sop.get('reconciliation_steps'):
            for i, step in enumerate(sop['reconciliation_steps'], 1):
                output.append(f"\n   Step {i}: {step}")
            if main_sop:
                output.append(f"\n   📄 Source: Daily Bank Transaction Reconciliation by Bank Transaction Type")
                output.append(f"   🔗 {main_sop}")
        else:
            output.append("   • No specific reconciliation steps documented")
        
        # Escalation Info
        if escalation_sop and (sop.get('escalation_threshold') or sop.get('criticality') == 'CRITICAL'):
            output.append("\n⚠️  WHEN TO ESCALATE:")
            if sop.get('escalation_threshold'):
                output.append(f"   • Threshold: {sop['escalation_threshold']}")
            output.append(f"   📄 Escalation Process: Escalating Reconciliation Issues to Cross-Functional Stakeholders")
            output.append(f"   🔗 {escalation_sop}")
        
        # Additional Info
        output.append("\n📊 TRANSACTION METADATA:")
        if sop.get('frequency'):
            output.append(f"   • Frequency: {sop['frequency']}")
        if sop.get('criticality'):
            output.append(f"   • Criticality: {sop['criticality']}")
        if sop.get('typical_amount_range'):
            output.append(f"   • Typical Amount Range: {sop['typical_amount_range']}")
        if sop.get('escalation_threshold'):
            output.append(f"   • ⚠️  Escalation Threshold: {sop['escalation_threshold']}")
        
        if sop.get('notes'):
            output.append(f"\n💡 SPECIAL NOTES:")
            output.append(f"   {sop['notes']}")
    else:
        output.append("\n⚠️  NO SOP MAPPING FOUND")
        output.append("   This label may be new or require manual SOP documentation.")
        output.append("   Please escalate to RE team for guidance.")
    
    output.append("\n" + "="*80 + "\n")
    
    return "\n".join(output)

def process_csv(input_file, output_file=None):
    """Process a CSV file with multiple transactions."""
    
    print(f"\n📂 Reading CSV file: {input_file}")
    
    try:
        df = pd.read_csv(input_file)
        print(f"✅ Found {len(df)} transactions\n")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return
    
    # Detect column names (flexible)
    col_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'amount' in col_lower:
            col_map['amount'] = col
        elif 'date' in col_lower:
            col_map['date'] = col
        elif 'payment' in col_lower or 'method' in col_lower:
            col_map['payment_method'] = col
        elif 'account' in col_lower:
            col_map['account'] = col
        elif 'narrative' in col_lower or 'description' in col_lower or 'desc' in col_lower:
            col_map['narrative'] = col
    
    # Check if we have required columns
    if 'narrative' not in col_map:
        print("❌ Could not find narrative/description column in CSV")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # Set defaults for missing columns
    if 'amount' not in col_map:
        df['amount'] = 0
        col_map['amount'] = 'amount'
    if 'date' not in col_map:
        df['date'] = datetime.now().strftime('%Y-%m-%d')
        col_map['date'] = 'date'
    if 'payment_method' not in col_map:
        df['payment_method'] = 'Unknown'
        col_map['payment_method'] = 'payment_method'
    if 'account' not in col_map:
        df['account'] = 'Unknown'
        col_map['account'] = 'account'
    
    # Process each transaction
    results = []
    for idx, row in df.iterrows():
        narrative = row[col_map['narrative']]
        amount = row[col_map['amount']]
        date = row[col_map['date']]
        payment_method = row[col_map['payment_method']]
        account = row[col_map['account']]
        
        label = simple_rule_prediction(narrative, amount, payment_method, account, date)
        sop_info = get_sop_info(label)
        
        # Build result row
        result_row = {
            'original_index': idx + 1,
            'amount': amount,
            'date': date,
            'payment_method': payment_method,
            'account': account,
            'narrative': narrative,
            'predicted_label': label,
            'sop_link': ', '.join(sop_info['confluence_links']) if sop_info and sop_info.get('confluence_links') else 'No SOP',
            'frequency': sop_info.get('frequency', 'N/A') if sop_info else 'N/A',
            'criticality': sop_info.get('criticality', 'N/A') if sop_info else 'N/A'
        }
        
        results.append(result_row)
        
        # Print progress
        print(f"✅ [{idx+1}/{len(df)}] {label} - ${amount}")
    
    # Create results dataframe
    results_df = pd.DataFrame(results)
    
    # Save to CSV if output file specified
    if output_file:
        results_df.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")
    
    # Print summary
    print("\n" + "="*80)
    print("📊 BATCH PREDICTION SUMMARY")
    print("="*80)
    print(f"\nTotal Transactions: {len(results_df)}")
    print(f"\nLabel Distribution:")
    label_counts = results_df['predicted_label'].value_counts()
    for label, count in label_counts.items():
        print(f"   • {label}: {count}")
    
    unknown_count = len(results_df[results_df['predicted_label'].str.contains('Unknown|Manual', case=False, na=False)])
    if unknown_count > 0:
        print(f"\n⚠️  {unknown_count} transactions need manual review")
    
    print("\n" + "="*80 + "\n")
    
    return results_df

def interactive_single():
    """Interactive mode for single transaction prediction."""
    print("\n" + "="*80)
    print("🎯 SINGLE TRANSACTION PREDICTOR")
    print("="*80)
    print("\nEnter transaction details (or press Ctrl+C to exit):\n")
    
    try:
        amount = input("Amount (e.g., $5,100.00): ").strip()
        date = input("Date (e.g., 10/14/2025): ").strip()
        payment_method = input("Payment Method (e.g., wire in): ").strip()
        account = input("Account (e.g., Chase Wire In): ").strip()
        print("\nNarrative (paste full description, then press Enter twice):")
        
        narrative_lines = []
        while True:
            line = input()
            if line == "":
                break
            narrative_lines.append(line)
        narrative = " ".join(narrative_lines)
        
        # Predict
        result = predict_single_transaction(narrative, amount, payment_method, account, date)
        
        # Display result
        print(format_single_output(result))
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description='Transaction Predictor - Predict agent labels and provide SOP guidance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single transaction (interactive)
  python3 transaction_predictor.py --single

  # Batch from CSV
  python3 transaction_predictor.py --csv transactions.csv

  # Save results to CSV
  python3 transaction_predictor.py --csv transactions.csv --output results.csv
        """
    )
    
    parser.add_argument('--single', action='store_true', help='Interactive single transaction mode')
    parser.add_argument('--csv', type=str, help='Input CSV file with transactions')
    parser.add_argument('--output', '-o', type=str, help='Output CSV file for results')
    
    args = parser.parse_args()
    
    if args.single:
        interactive_single()
    elif args.csv:
        process_csv(args.csv, args.output)
    else:
        # Default: test with example
        print("\n🧪 TESTING WITH EXAMPLE TRANSACTION:")
        result = predict_single_transaction(
            narrative="YOUR REF=POH OF 25/10/14,REC FROM=00000000730103207 CHELSEA N SARVER 5605 SCURTICE ST UNIT A LITTLETON CO 80120-1188 US,REMARK=1TRVXX9QP28C DEBIT REF POH OF",
            amount="$5,100.00",
            date="10/14/2025 12:00:00am",
            payment_method="wire in",
            account="Chase Wire In"
        )
        print(format_single_output(result))
        
        print("\n💡 TIP: Use --single for interactive mode or --csv for batch processing")
        print("   Example: python3 transaction_predictor.py --single")

if __name__ == "__main__":
    main()

