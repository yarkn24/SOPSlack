#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/yarkin.akcil/Documents/GitHub/SOPSlack')

from clean_wiki_predictor import format_output

print(format_output(
    narrative="YOUR REF=WIRE_345SC990RKK,REC FROM=COLUMN NATIONAL ASSOCIATION BREX SAN FRANCISCO CA US,FED ID=121145349,B/O CUSTOMER=/868890190533595 1/CONVOI VENTURES MANAGEMENT, LLC 2/336 E UNIVERSITY PKWY 3/US/OREM,84058,UT,B/O BANK=ABA/121145349 COLUMN NATIONAL ASSOCIATION BREX SAN FRANCISCO CA US,REMARK=/URI/GUSTO, OCT 1 - 15 DEBIT REF WMSG_345SCGFDGM+",
    amount="$3,998.49",
    date="10/15/2025 12:00:00am",
    payment_method="wire in",
    account="Chase Payroll Incoming Wires"
))

