#!/usr/bin/env python3
"""
Rule-based Bank Transaction Labeling Engine
Based on Reconciliation SOP rules
"""
import json
import re


class BankTransactionLabeler:
    """Apply labeling rules to bank transactions"""
    
    def __init__(self):
        self.rules = []
        self._setup_rules()
    
    def _setup_rules(self):
        """Setup labeling rules based on SOP"""
        
        # Rule 1: NY WH - "NYS DTF WT" in description
        self.rules.append({
            'name': 'NY WH',
            'check': lambda row: self._check_description_contains(row, 'NYS DTF WT')
        })
        
        # Rule 2: OH WH - "OH WH TAX" in description
        self.rules.append({
            'name': 'OH WH',
            'check': lambda row: self._check_description_contains(row, 'OH WH TAX')
        })
        
        # Rule 3: CSC - "CSCXXXXXX" pattern in description
        self.rules.append({
            'name': 'CSC',
            'check': lambda row: self._check_csc_pattern(row)
        })
        
        # Rule 4: Check - payment_method = "check paid"
        self.rules.append({
            'name': 'Check',
            'check': lambda row: str(row.get('payment_method', '')).lower() == 'check paid'
        })
        
        # Rule 4.5: DEFINITIVE RISK - "1TRV" pattern in description
        # ANY transaction with "1TRV" in description is ALWAYS Risk
        # This overrides all other rules (including account-based rules)
        self.rules.insert(0, {
            'name': 'Risk',
            'check': lambda row: '1TRV' in self._get_description_text(row).upper()
        })
        
        # Rule 5a: Recovery Wire → BUT if amount > $25K, it's likely Risk (wrong account)
        # Large amounts ($20-30K+) in Recovery account are usually Risk transactions
        self.rules.append({
            'name': 'Risk',
            'check': lambda row: (
                'chase recovery' in str(row.get('origination_account_id', '')).lower() and
                float(row.get('amount', 0)) > 25000
            )
        })
        
        # Rule 5b: Recovery Wire - Chase Recovery account (normal case)
        # Note: Old label was "collections", now it's "Recovery Wire"
        # Excludes large amounts (>$25K) which are handled above
        self.rules.append({
            'name': 'Recovery Wire',
            'check': lambda row: (
                'chase recovery' in str(row.get('origination_account_id', '')).lower() and
                float(row.get('amount', 0)) <= 25000
            )
        })
        
        # Rule 6a: Risk → BUT if amount < $3.5K, it's likely Recovery Wire (wrong account)
        # Small amounts (<$3-4K) in Risk accounts are usually Recovery Wire transactions
        self.rules.append({
            'name': 'Recovery Wire',
            'check': lambda row: (
                (
                    'chase wire in' in str(row.get('origination_account_id', '')).lower() or
                    'pnc wire in' in str(row.get('origination_account_id', '')).lower() or
                    'chase payroll incoming wires' in str(row.get('origination_account_id', '')).lower()
                ) and
                float(row.get('amount', 0)) < 3500 and
                float(row.get('amount', 0)) > 0
            )
        })
        
        # Rule 6b: Risk - Wire accounts (normal case, 90% probability)
        # Chase Wire-in, PNC Wire in, Chase Payroll Incoming Wires → mostly Risk
        # Excludes small amounts (<$3.5K) which are handled above
        self.rules.append({
            'name': 'Risk',
            'check': lambda row: (
                (
                    'chase wire in' in str(row.get('origination_account_id', '')).lower() or
                    'pnc wire in' in str(row.get('origination_account_id', '')).lower() or
                    'chase payroll incoming wires' in str(row.get('origination_account_id', '')).lower()
                ) and
                float(row.get('amount', 0)) >= 3500
            )
        })
        
        # Rule 7: Bad Debt - amount < $1.00
        self.rules.append({
            'name': 'Bad Debt',
            'check': lambda row: float(row.get('amount', 0)) < 1.00 and float(row.get('amount', 0)) > 0
        })
        
        # Rule 8: Lockbox - "Lockbox" in description
        self.rules.append({
            'name': 'Lockbox',
            'check': lambda row: self._check_description_contains(row, 'Lockbox')
        })
        
        # Rule 9: OH SDWH - "OH SDWH" in description
        self.rules.append({
            'name': 'OH SDWH',
            'check': lambda row: self._check_description_contains(row, 'OH SDWH')
        })
    
    def _check_description_contains(self, row, text):
        """Check if description contains text (case insensitive)"""
        desc = self._get_description_text(row)
        return text.upper() in desc.upper()
    
    def _check_csc_pattern(self, row):
        """Check for CSC pattern: CSCXXXXXX"""
        desc = self._get_description_text(row)
        # Pattern: CSC followed by digits
        return bool(re.search(r'CSC\d+', desc, re.IGNORECASE))
    
    def _get_description_text(self, row):
        """Extract text from description field"""
        desc = row.get('description', '')
        if not desc:
            return ''
        
        # Try to parse JSON
        try:
            desc_dict = json.loads(desc)
            text_parts = []
            for key, value in desc_dict.items():
                if value and isinstance(value, str):
                    text_parts.append(value)
            return ' '.join(text_parts)
        except:
            return str(desc)
    
    def label(self, row):
        """
        Apply rules to a transaction row
        Returns: agent label or None
        """
        for rule in self.rules:
            try:
                if rule['check'](row):
                    return rule['name']
            except Exception as e:
                # Skip rule if error
                continue
        
        return None
    
    def label_dataframe(self, df):
        """
        Apply rules to entire dataframe
        Returns: Series of labels
        """
        import pandas as pd
        
        # Convert to dict for faster access
        records = df.to_dict('records')
        
        labels = []
        for record in records:
            label = self.label(record)
            labels.append(label)
        
        return pd.Series(labels, index=df.index)


if __name__ == '__main__':
    # Test
    labeler = BankTransactionLabeler()
    
    test_cases = [
        {'description': '{"vendor_description": "NYS DTF WT payment"}', 'amount': 100},
        {'description': 'OH WH TAX payment', 'amount': 50},
        {'description': 'CSC123456 child support', 'amount': 200},
        {'payment_method': 'check paid', 'amount': 75},
        {'amount': 0.50},
        {'description': 'Lockbox payment', 'amount': 100},
        {'description': 'OH SDWH payment', 'amount': 80}
    ]
    
    print("Testing labeling rules:")
    for i, test in enumerate(test_cases, 1):
        label = labeler.label(test)
        print(f"{i}. {test} -> {label}")
