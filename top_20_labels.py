#!/usr/bin/env python3
"""
Top 20 Most Common Labels - 1 Example Each
Complete SOP Analysis
"""

from batch_predictor import analyze_batch, format_grouped_output

# Top 20 most common transaction labels (1 example each)
top_20_transactions = [
    # 1. Risk - Chase Wire In
    {
        'id': '59315257',
        'narrative': 'YOUR REF=POH OF 25/10/14,REC FROM=00000000730103207 CHELSEA N SARVER,REMARK=1TRVXX9QP28C',
        'amount': '$5,100.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'wire in',
        'account': 'Chase Wire In'
    },
    # 2. Check
    {
        'id': '59318456',
        'narrative': 'CHECK PAID 00123456789 PAYEE: ABC COMPANY',
        'amount': '$1,250.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'check paid',
        'account': 'Chase Operations'
    },
    # 3. NY WH
    {
        'id': '59319234',
        'narrative': 'NYS DTF WT WITHHOLDING TAX PAYMENT',
        'amount': '$850.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 4. OH WH
    {
        'id': '59319567',
        'narrative': 'OH WH TAX WITHHOLDING PAYMENT STATE OF OHIO',
        'amount': '$620.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 5. NY UI
    {
        'id': '59321123',
        'narrative': 'NYS DOL UI UNEMPLOYMENT INSURANCE PAYMENT',
        'amount': '$1,200.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 6. CSC
    {
        'id': '59318890',
        'narrative': 'DESC=CSC123456 CHILD SUPPORT PAYMENT',
        'amount': '$345.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 7. ICP Funding
    {
        'id': '59319890',
        'narrative': 'TRANSFER FROM ACCOUNT000000807737908 REMARK=JPMORGAN ACCESS TRANSFER',
        'amount': '$25,000.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase International Contractor Payment'
    },
    # 8. LOI
    {
        'id': '59321789',
        'narrative': 'REMARK=ACH RETURN SETTLEMENT',
        'amount': '$100.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 9. Lockbox
    {
        'id': '59320456',
        'narrative': 'LOCKBOX PAYMENT PROCESSING FEE',
        'amount': '$15.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 10. OH SDWH
    {
        'id': '59320789',
        'narrative': 'OH SDWH STATE TAX PAYMENT OHIO',
        'amount': '$430.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 11. MT UI
    {
        'id': '59321456',
        'narrative': 'STATE OF MONTANA UNEMPLOYMENT TAX',
        'amount': '$550.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 12. IL UI
    {
        'id': '59322100',
        'narrative': 'IL DEPT EMPL SEC UNEMPLOYMENT INSURANCE',
        'amount': '$780.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 13. WA ESD
    {
        'id': '59322200',
        'narrative': 'STATE OF WA ESD UNEMPLOYMENT TAX',
        'amount': '$920.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 14. ACH
    {
        'id': '59322300',
        'narrative': 'REMARK=EFT REVERSAL PAYMENT RETURN',
        'amount': '$250.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 15. ACH Return
    {
        'id': '59322400',
        'narrative': 'RTN OFFSET RETURN PAYMENT',
        'amount': '$180.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 16. Money Market Fund
    {
        'id': '59322123',
        'narrative': 'MONEY MKT MUTUAL FUND TRANSFER',
        'amount': '$50,000.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 17. Treasury Transfer
    {
        'id': '59322456',
        'narrative': 'US TREASURY CAPITAL TRANSFER',
        'amount': '$100,000.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'wire in',
        'account': 'Chase Operations'
    },
    # 18. WA LNI
    {
        'id': '59322500',
        'narrative': 'L&I LABOR&INDUSTRIES TAX PAYMENT',
        'amount': '$340.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 19. Bad Debt
    {
        'id': '59322600',
        'narrative': 'MICROVARIANCE ADJUSTMENT',
        'amount': '$0.03',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 20. VA UI
    {
        'id': '59322700',
        'narrative': 'VA. EMPLOY COMM UNEMPLOYMENT INSURANCE',
        'amount': '$690.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
]

print("\n" + "=" * 80)
print("TOP 20 MOST COMMON LABELS - COMPLETE SOP ANALYSIS")
print("=" * 80)
print(f"\n✅ Analyzing {len(top_20_transactions)} transactions\n")

# Analyze batch
grouped = analyze_batch(top_20_transactions)

# Print formatted output
print(format_grouped_output(grouped))

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nTotal Labels Analyzed: {len(grouped)}")
print("\nLabels WITH SOP Reconciliation Info:")
with_recon = []
without_recon = []
for group_key, group in grouped.items():
    if group['sop_content'].get('reconciliation'):
        with_recon.append(group['label'])
    else:
        without_recon.append(group['label'])

for label in with_recon:
    print(f"  ✅ {label}")

print("\nLabels WITHOUT SOP Reconciliation Info:")
for label in without_recon:
    print(f"  ⚠️  {label}")

