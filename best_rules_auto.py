
def apply_rules(row, icp_funding_amounts=None):
    desc = str(row['description']).upper()
    acc = int(row['origination_account_id']) if pd.notna(row['origination_account_id']) else 0
    amt = float(row['amount'])
    pm = int(row['payment_method']) if pd.notna(row['payment_method']) else -1
    
    if pm == 12:
        return 'ZBT'
    elif 'NIUM' in desc:
        return 'Nium Payment'
    elif acc == 21 and 'REMARK=JPMORGAN ACCESS TRANSFER FROM' in desc:
        return 'ICP Funding'
    elif icp_funding_amounts and amt in icp_funding_amounts and 'REMARK=JPMORGAN ACCESS TRANSFER' in desc:
        return 'ICP Funding'
    elif '1TRV' in desc:
        return 'Risk'
    elif 'ORIG CO NAME=STATE OF MONTANA' in desc or 'STATE OF MONTANA' in desc:
        return 'MT UI'
    elif '1HIOSDWH' in desc or 'OHSDWHTX' in desc:
        return 'OH SDWH'
    elif 'NYS DTF WT' in desc or 'NY DTF WT' in desc:
        return 'NY WH'
    elif 'NYS DOL UI' in desc:
        return 'NY UI'
    elif pm == 4 and ('ACH CREDIT SETTLEMENT' in desc or 'ACH DEBIT SETTLEMENT' in desc):
        if 'REVERSAL' in desc:
            return 'ACH Reversal'
        else:
            return 'ACH Transaction'
    elif 'WA' in desc and ('L&I' in desc or 'LNI' in desc or 'LABOR' in desc or 'INDUSTRIES' in desc):
        return 'WA LNI'
    elif 'ENTRY DESCR=ITL' in desc and 'GUSTO PAYROLL' in desc:
        return 'Company Balance Transfers'
    elif acc == 16 and 'CREDIT MEMO' in desc:
        return 'LOI'
    elif '100% US TREASURY CAPITAL 3163' in desc or 'MONEY MKT MUTUAL FUND' in desc:
        return 'Money Market Transfer'
    elif 'JPMORGAN ACCESS TRANSFER' in desc:
        return 'Treasury Transfer'
    elif 'INTEREST ADJUSTMENT' in desc:
        return 'Interest Adjustment'
    elif 'KEYSTONE' in desc:
        return 'PA UI'
    elif pm == 2:
        return 'Check'
    elif acc in [7, 28]:
        if 'INTEREST' in desc:
            return 'Interest Payment'
        else:
            return 'Recovery Wire'
    elif acc in [6, 9, 18] and pm == 0:
        return 'Risk'
    elif acc == 26:
        if amt < 0.5:
            return 'Bad Debt'
        else:
            return 'BRB'
    elif amt < 0.5 and amt > 0:
        return 'Bad Debt'
    elif 'LOCKBOX' in desc:
        return 'Lockbox'
    elif 'TS FX ACCOUNTS RECEIVABLE' in desc or 'JPV' in desc:
        return 'ICP Return'
    elif 'REMARK=WISE' in desc and amt < 50000:
        return 'ICP Refund'
    elif 'WISE' in desc and amt < 50000:
        return 'ICP Refund'
    elif acc == 21 and 'REFUND' in desc:
        return 'ICP Return'
    elif 'OHEMWHTX' in desc or 'OH WH TAX' in desc or '8011OHIO-TAXOEWH' in desc:
        return 'OH WH'
    elif 'CHECK' in desc and ('REFERENCE' in desc or 'ITEM' in desc or 'POSTED' in desc):
        return 'Check Adjustment'
    elif 'YORK ADAMS' in desc:
        return 'York Adams'
    elif 'IRS' in desc:
        return 'IRS Wire'
    
    return None
