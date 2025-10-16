#!/usr/bin/env python3
"""
Demo: Common transaction labels with examples
"""

from batch_predictor import analyze_batch, format_grouped_output

# Sample transactions for most common labels
demo_transactions = [
    # Risk - Chase Wire In
    {
        'id': '59315257',
        'narrative': 'YOUR REF=POH OF 25/10/14,REC FROM=00000000730103207 CHELSEA N SARVER 5605 SCURTICE ST UNIT A LITTLETON CO 80120-1188 US,REMARK=1TRVXX9QP28C DEBIT REF POH OF 25/10/14',
        'amount': '$5,100.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'wire in',
        'account': 'Chase Wire In'
    },
    # Risk - PNC Wire In
    {
        'id': '59317875',
        'narrative': 'DateTime: 1014250603WIRE TRANSFER IN ISO 003YJKORIGINATOR: DETERMINED BY DESIGN LLC AC/9868417016ADDR:712 H ST NE # 1866 WASHINGTON DC 20002 US',
        'amount': '$14,800.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'wire in',
        'account': 'PNC Wire In'
    },
    # Risk - Chase Payroll Incoming Wires
    {
        'id': '59321936',
        'narrative': 'YOUR REF=WIRE_345SC990RKK,REC FROM=COLUMN NATIONAL ASSOCIATION BREX SAN FRANCISCO CA US,FED ID=121145349,B/O CUSTOMER=/868890190533595',
        'amount': '$3,998.49',
        'date': '10/15/2025 12:00:00am',
        'payment_method': 'wire in',
        'account': 'Chase Payroll Incoming Wires'
    },
    # Recovery Wire
    {
        'id': '59320123',
        'narrative': 'WIRE TRANSFER IN FROM COMPANY ABC FOR RECOVERY',
        'amount': '$2,500.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'wire in',
        'account': 'Chase Recovery'
    },
    # Check
    {
        'id': '59318456',
        'narrative': 'CHECK PAID 00123456789 PAYEE: ABC COMPANY',
        'amount': '$1,250.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'check paid',
        'account': 'Chase Operations'
    },
    # NY WH
    {
        'id': '59319234',
        'narrative': 'NYS DTF WT WITHHOLDING TAX PAYMENT',
        'amount': '$850.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # OH WH
    {
        'id': '59319567',
        'narrative': 'OH WH TAX WITHHOLDING PAYMENT STATE OF OHIO',
        'amount': '$620.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # CSC (Child Support Credits)
    {
        'id': '59318890',
        'narrative': 'DESC=CSC123456 CHILD SUPPORT PAYMENT',
        'amount': '$345.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # ICP Funding
    {
        'id': '59319890',
        'narrative': 'TRANSFER FROM ACCOUNT000000807737908 REMARK=JPMORGAN ACCESS TRANSFER',
        'amount': '$25,000.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase International Contractor Payment'
    },
    # Lockbox
    {
        'id': '59320456',
        'narrative': 'LOCKBOX PAYMENT PROCESSING FEE',
        'amount': '$15.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # OH SDWH
    {
        'id': '59320789',
        'narrative': 'OH SDWH STATE TAX PAYMENT OHIO',
        'amount': '$430.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # NY UI
    {
        'id': '59321123',
        'narrative': 'NYS DOL UI UNEMPLOYMENT INSURANCE PAYMENT',
        'amount': '$1,200.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # MT UI
    {
        'id': '59321456',
        'narrative': 'STATE OF MONTANA UNEMPLOYMENT INSURANCE',
        'amount': '$550.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # LOI
    {
        'id': '59321789',
        'narrative': 'REMARK=ACH RETURN SETTLEMENT',
        'amount': '$100.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # Money Market Fund
    {
        'id': '59322123',
        'narrative': 'MONEY MKT MUTUAL FUND TRANSFER',
        'amount': '$50,000.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'ach external',
        'account': 'Chase Operations'
    },
    # Treasury Transfer
    {
        'id': '59322456',
        'narrative': 'US TREASURY CAPITAL TRANSFER',
        'amount': '$100,000.00',
        'date': '10/14/2025 12:00:00am',
        'payment_method': 'wire in',
        'account': 'Chase Operations'
    },
]

print("=" * 80)
print("DEMO: COMMON TRANSACTION LABELS")
print("=" * 80)
print(f"\n✅ Analyzing {len(demo_transactions)} sample transactions\n")

# Analyze batch
grouped = analyze_batch(demo_transactions)

# Print formatted output
print(format_grouped_output(grouped))

