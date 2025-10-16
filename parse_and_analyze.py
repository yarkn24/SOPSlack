#!/usr/bin/env python3
"""
Parse tab-separated transaction data and analyze
"""

from batch_predictor import analyze_batch, format_grouped_output

# Parse the input data
raw_data = """	59321936	$3,998.49	10/15/2025 12:00:00am	wire in	Chase Payroll Incoming Wires				
YOUR REF=WIRE_345SC990RKK,REC FROM=COLUMN NATIONAL ASSOCIATION BREX SAN FRANCISCO CA US,FED ID=121145349,B/O CUSTOMER=/868890190533595 1/CONVOI VENTURES MANAGEMENT, LLC 2/336 E UNIVERSITY PKWY 3/US/OREM,84058,UT,B/O BANK=ABA/121145349 COLUMN NATIONAL ASSOCIATION BREX SAN FRANCISCO CA US,REMARK=/URI/GUSTO, OCT 1 - 15 DEBIT REF WMSG_345SCGFDGM+,REC GFP=10150420,MRN SEQ=WMSG_345SCGFDGM+,FED REF=1015 MMQFMP2U 000236 **VIA FED**,TIME=10150023
	claim	59317875	$14,800.00	10/14/2025 12:00:00am	wire in	PNC Wire In	Risk			
DateTime: 1014250603WIRE TRANSFER IN ISO 003YJKORIGINATOR: DETERMINED BY DESIGN LLC AC/9868417016ADDR:712 H ST NE # 1866 WASHINGTON DC 20002 US SNDBNK:MANUFACTURERS & TRADERS TRUST CO ABA:022000046CTY:BUFFALO ST/PR:NY CTRY:US ORG BNK:M&T BankADDR:One M&T Plaza Buffalo NY 14240 USARFB:NOTPROVIDED AMT/CUR: 14800.00 USD STTLMTDATE:10142025 CHG:SHAR OBI:payroll BBI:payrollBENEFICIARY:Gusto Inc AC/1077770489 ADDR:525 20thStreet San Francisco CA 94107 USTRN:25AEA03206VU PARTIALREF:00270 DATE:251014 TIME:0603FULL REFERENCE#:20251014B2Q8921C000270UETR:a9ec344c-0860-4060-8c62-b6bb95e9f126
	claim	59317785	$10.00	10/14/2025 12:00:00am	wire in	PNC Wire In	Risk			
DateTime: 1014251119WIRE TRANSFER IN ISO 0026MSORIGINATOR: 1/ALL TOGATHER WE CAN LLC AC/325207451140ADDR:2/1331 N CAHUENGA BLVD APT 3313 3/US/LOSANGELES, CA 90028 1910 SND BNK:BANK OF AMERICA, N.A.,NY ABA:0959 CTRY:US ORG BNK:ALL TOGATHER WE CAN LLCADDR:1331 N CAHUENGA BLVD APT 3313 LOS ANGELES CA90028-1910 RFB:NOTPROVIDED AMT/CUR: 10.00 USD STTLMTDATE:10142025 CHG:SHAR BENEFICIARY:GUSTO INCAC/1077770489 ADDR:525 20TH ST CTY:SAN FRANCISCOST/PR:CA PSTCD:94107-4345 CTRY:USTRN:PAAEB192686W PARTIALREF:93110 DATE:251014 TIME:1119FULL REFERENCE#:202510140959P0093110UETR:303747e9-9f9a-47ca-a3a3-9616bd14d6f9
	claim	59315257	$5,100.00	10/14/2025 12:00:00am	wire in	Chase Wire In	Risk			
YOUR REF=POH OF 25/10/14,REC FROM=00000000730103207 CHELSEA N SARVER 5605 SCURTICE ST UNIT A LITTLETON CO 80120-1188 US,REMARK=1TRVXX9QP28C DEBIT REF POH OF 25/10/14,REC GFP=10142039,TIME=10141640"""

def parse_transaction_data(raw_text):
    """Parse tab-separated transaction data."""
    lines = raw_text.strip().split('\n')
    transactions = []
    
    i = 0
    while i < len(lines):
        # First line has transaction metadata
        first_line = lines[i]
        parts = first_line.split('\t')
        
        # Filter out empty parts and "claim" keyword
        parts = [p.strip() for p in parts if p.strip() and p.strip().lower() != 'claim']
        
        # Parse: ID, Amount, Date, Payment Method, Account
        # Format can be: [ID, Amount, Date, PaymentMethod, Account, ...]
        # or: [claim, ID, Amount, Date, PaymentMethod, Account, ...]
        if len(parts) >= 5:
            # Find the ID - should be a number
            idx = 0
            for j, part in enumerate(parts):
                if part.replace('$', '').replace(',', '').replace('.', '').isdigit() and '$' not in part:
                    idx = j
                    break
            
            txn_id = parts[idx] if idx < len(parts) else parts[0]
            amount = parts[idx + 1] if idx + 1 < len(parts) else ""
            date = parts[idx + 2] if idx + 2 < len(parts) else ""
            payment_method = parts[idx + 3] if idx + 3 < len(parts) else ""
            account = parts[idx + 4] if idx + 4 < len(parts) else ""
            
            # Next line has narrative
            narrative = ""
            if i + 1 < len(lines):
                narrative = lines[i + 1].strip()
            
            transactions.append({
                'id': txn_id,
                'amount': amount,
                'date': date,
                'payment_method': payment_method,
                'account': account,
                'narrative': narrative
            })
            
            i += 2  # Skip to next transaction (metadata line + narrative line)
        else:
            i += 1
    
    return transactions

# Parse transactions
transactions = parse_transaction_data(raw_data)

print(f"✅ Parsed {len(transactions)} transactions\n")

# Analyze batch
grouped = analyze_batch(transactions)

# Print formatted output
print(format_grouped_output(grouped))

