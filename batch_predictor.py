#!/usr/bin/env python3
"""
Batch Transaction Predictor - Groups similar transactions
"""

from final_predictor import predict_label, get_real_sop_content, get_business_rules

def analyze_batch(transactions):
    """
    Analyze multiple transactions and group by label + context
    
    Args:
        transactions: List of dicts with keys: id, narrative, amount, payment_method, account, date
    
    Returns:
        Grouped results
    """
    
    # Analyze each transaction
    results = []
    for txn in transactions:
        # Clean ID - remove "claim_" prefix if exists
        clean_id = str(txn['id']).replace('claim_', '').replace('claim', '').strip()
        label, method, reason = predict_label(
            txn['narrative'], 
            txn['amount'], 
            txn['payment_method'], 
            txn['account'],
            txn['date']
        )
        
        # Get SOP content - for Chase Payroll, use special SOP content
        if 'Chase Payroll' in txn['account']:
            sop_content = get_real_sop_content("Risk (Chase Payroll)")
        else:
            sop_content = get_real_sop_content(label)
        
        business_rules = get_business_rules(label)
        
        # Create a grouping key based on label + reason (to separate different contexts)
        context_key = f"{label}|{reason}"
        
        results.append({
            'id': clean_id,
            'label': label,
            'method': method,
            'reason': reason,
            'sop_content': sop_content,
            'business_rules': business_rules,
            'context_key': context_key,
            'transaction': txn
        })
    
    # Group by context_key
    grouped = {}
    for result in results:
        key = result['context_key']
        if key not in grouped:
            grouped[key] = {
                'ids': [],
                'label': result['label'],
                'method': result['method'],
                'reason': result['reason'],
                'sop_content': result['sop_content'],
                'business_rules': result['business_rules'],
                'transactions': []
            }
        grouped[key]['ids'].append(result['id'])
        grouped[key]['transactions'].append(result['transaction'])
    
    return grouped

def format_grouped_output(grouped_results):
    """Format grouped results."""
    
    output = []
    output.append("\n" + "="*80)
    output.append("BATCH TRANSACTION ANALYSIS")
    output.append("="*80)
    
    for i, (context_key, group) in enumerate(grouped_results.items(), 1):
        output.append(f"\n{'='*80}")
        output.append(f"GROUP {i}: {group['label']}")
        output.append(f"{'='*80}")
        
        # Transaction IDs
        output.append(f"\n🔢 Transaction IDs: {', '.join(group['ids'])}")
        
        # Label with explanation
        output.append(f"\n🏷️  Label: {group['label']}")
        
        # Show method only if ML-based
        if group['method'] == 'ml-based':
            output.append(f"📊 How we found this: {group['reason']} (ML ile buldum)")
        else:
            output.append(f"📊 How we found this: {group['reason']}")
        
        # Show sample transactions
        output.append(f"\n📋 Sample Transactions ({len(group['transactions'])} total):")
        for j, (txn, txn_id) in enumerate(zip(group['transactions'][:3], group['ids'][:3]), 1):  # Show max 3 samples
            output.append(f"\n   {j}. ID: {txn_id} | {txn['amount']} | {txn['account']}")
            output.append(f"      {txn['narrative'][:60]}...")
        
        if len(group['transactions']) > 3:
            output.append(f"\n   ... and {len(group['transactions']) - 3} more")
        
        # SOP INFORMATION
        sop_content = group['sop_content']
        if sop_content:
            output.append(f"\n{'─'*80}")
            output.append(f"📚 SOP BİLGİLERİ (ONLY FROM SOP):")
            output.append(f"{'─'*80}")
            
            # Labeling from SOP
            if 'labeling' in sop_content and sop_content['labeling']:
                output.append(f"\n📝 How to Label (from SOP):")
                output.append(f'   "{sop_content["labeling"]}"')
                if 'sop_page' in sop_content:
                    output.append(f"\n   Source: {sop_content['sop_page']}")
                    output.append(f"   Link: {sop_content['sop_link']}")
            
            # Reconciliation from SOP
            if 'reconciliation' in sop_content and sop_content['reconciliation']:
                output.append(f"\n📖 How to Reconcile (from SOP):")
                output.append(f'   "{sop_content["reconciliation"]}"')
                if 'sop_page' in sop_content:
                    output.append(f"\n   Source: {sop_content['sop_page']}")
                    output.append(f"   Link: {sop_content['sop_link']}")
            
            # Additional SOPs
            if 'additional_sops' in sop_content and sop_content['additional_sops']:
                output.append(f"\n📚 Additional Reference SOPs:")
                for add_sop in sop_content['additional_sops']:
                    output.append(f"\n   • {add_sop['title']}")
                    output.append(f"     {add_sop['link']}")
                    if 'note' in add_sop:
                        output.append(f"     Note: {add_sop['note']}")
        
        # Business Rules - kept internal, not displayed to user
    
    output.append("\n" + "="*80 + "\n")
    
    return "\n".join(output)

if __name__ == "__main__":
    print("\n🎯 BATCH DEMO MODE\n")
    
    # Test with multiple transactions
    test_transactions = [
        {
            'id': 'claim_59321936',
            'narrative': 'YOUR REF=WIRE_345SC990RKK,REC FROM=COLUMN NATIONAL ASSOCIATION BREX SAN FRANCISCO CA US',
            'amount': '$3,998.49',
            'date': '10/15/2025 12:00:00am',
            'payment_method': 'wire in',
            'account': 'Chase Payroll Incoming Wires'
        },
        {
            'id': 'claim_59317875',
            'narrative': 'DateTime: 1014250603WIRE TRANSFER IN ISO 003YJKORIGINATOR: DETERMINED BY DESIGN LLC',
            'amount': '$14,800.00',
            'date': '10/14/2025 12:00:00am',
            'payment_method': 'wire in',
            'account': 'PNC Wire In'
        },
        {
            'id': 'claim_59317785',
            'narrative': 'DateTime: 1014251119WIRE TRANSFER IN ISO 0026MSORIGINATOR: ALL TOGATHER WE CAN LLC',
            'amount': '$10.00',
            'date': '10/14/2025 12:00:00am',
            'payment_method': 'wire in',
            'account': 'PNC Wire In'
        },
        {
            'id': 'claim_59321999',
            'narrative': 'YOUR REF=POH OF 25/10/14,REC FROM=00000000730103207 CHELSEA N SARVER,REMARK=1TRVXX9QP28C',
            'amount': '$5,100.00',
            'date': '10/14/2025 12:00:00am',
            'payment_method': 'wire in',
            'account': 'Chase Wire In'
        }
    ]
    
    grouped = analyze_batch(test_transactions)
    print(format_grouped_output(grouped))

