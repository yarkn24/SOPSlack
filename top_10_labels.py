#!/usr/bin/env python3
"""
Top 10 Most Common Labels - 1 Example Each
"""

from batch_predictor import analyze_batch, format_grouped_output

# Top 10 most common transaction labels (1 example each)
top_10_transactions = [
    # 1. Risk - Chase Wire In
    {
        'id': '59315257',
        'narrative': 'YOUR REF=POH OF 25/10/14,REC FROM=00000000730103207 CHELSEA N SARVER 5605 SCURTICE ST UNIT A LITTLETON CO 80120-1188 US,REMARK=1TRVXX9QP28C DEBIT REF POH OF 25/10/14',
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
    # 3. NY WH (New York Withholding)
    {
        'id': '59319234',
        'narrative': 'NYS DTF WT WITHHOLDING TAX PAYMENT',
        'amount': '$850.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 4. ICP Funding
    {
        'id': '59319890',
        'narrative': 'TRANSFER FROM ACCOUNT000000807737908 REMARK=JPMORGAN ACCESS TRANSFER',
        'amount': '$25,000.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase International Contractor Payment'
    },
    # 5. OH WH (Ohio Withholding)
    {
        'id': '59319567',
        'narrative': 'OH WH TAX WITHHOLDING PAYMENT STATE OF OHIO',
        'amount': '$620.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 6. NY UI (New York Unemployment)
    {
        'id': '59321123',
        'narrative': 'NYS DOL UI UNEMPLOYMENT INSURANCE PAYMENT',
        'amount': '$1,200.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 7. CSC (Child Support Credits)
    {
        'id': '59318890',
        'narrative': 'DESC=CSC123456 CHILD SUPPORT PAYMENT',
        'amount': '$345.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # 8. LOI (Letters of Indemnity)
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
]

print("\n" + "=" * 80)
print("TOP 10 MOST COMMON LABELS - ANALYSIS")
print("=" * 80)
print(f"\n✅ Analyzing {len(top_10_transactions)} transactions\n")

# Analyze batch
grouped = analyze_batch(top_10_transactions)

# Print formatted output
print(format_grouped_output(grouped))

