/**
 * Static Client-Side Transaction Analyzer
 * Works without backend - uses rule-based predictions only
 */

// Rule-based prediction logic (converted from Python)
function predictLabelClientSide(transaction) {
    const desc = (transaction.description || '').toUpperCase();
    const account = (transaction.origination_account_id || '').toUpperCase();
    const amount = parseFloat((transaction.amount || '0').replace(/[$,]/g, ''));
    const method = (transaction.payment_method || '').toLowerCase();
    
    // Account-based rules (highest priority)
    if (account.includes('PNC WIRE IN') || account.includes('CHASE WIRE IN')) {
        return ['Risk', 'rule-based', 'Account is PNC Wire In or Chase Wire In'];
    }
    
    if (account.includes('CHASE PAYROLL INCOMING WIRES')) {
        return ['Risk', 'rule-based', 'Account is Chase Payroll Incoming Wires (leave UNLABELED if TODAY, label as Risk if 1+ days old)'];
    }
    
    if (account.includes('CHASE RECOVERY')) {
        return ['Recovery Wire', 'rule-based', 'Account is Chase Recovery'];
    }
    
    if (account.includes('CHASE INTERNATIONAL CONTRACTOR PAYMENT') || account.includes('CHASE ICP')) {
        if (desc.includes('JPMORGAN ACCESS TRANSFER')) {
            return ['ICP Funding', 'rule-based', "Description contains 'JPMORGAN ACCESS TRANSFER'"];
        }
        if (method.includes('ach external')) {
            return ['ICP', 'rule-based', 'Account is Chase ICP and method is ach external'];
        }
    }
    
    // Payment method rules
    if (method.includes('check')) {
        return ['Check', 'rule-based', "Payment method is 'Check'"];
    }
    
    // Description-based rules
    if (desc.includes('NYS DTF WT')) {
        return ['NY WH', 'rule-based', "Description contains 'NYS DTF WT'"];
    }
    
    if (desc.includes('OH WH TAX')) {
        return ['OH WH', 'rule-based', "Description contains 'OH WH TAX'"];
    }
    
    if (desc.includes('OH SDWH')) {
        return ['OH SDWH', 'rule-based', "Description contains 'OH SDWH'"];
    }
    
    if (desc.includes('NYS DOL UI')) {
        return ['NY UI', 'rule-based', "Description contains 'NYS DOL UI'"];
    }
    
    if (desc.includes('CSC') && /CSC\d{6}/.test(desc)) {
        return ['CSC', 'rule-based', "Description contains 'CSC' with number pattern"];
    }
    
    if (desc.includes('ACH RETURN SETTLEMENT') || desc.includes('CREDIT MEMO')) {
        return ['LOI', 'rule-based', 'Description indicates LOI'];
    }
    
    if (desc.includes('LOCKBOX')) {
        return ['Lockbox', 'rule-based', "Description contains 'LOCKBOX'"];
    }
    
    if (desc.includes('IL DEPT EMPL SEC')) {
        return ['IL UI', 'rule-based', "Description contains 'IL DEPT EMPL SEC'"];
    }
    
    if (desc.includes('MT TAX') || desc.includes('STATE OF MONTANA')) {
        return ['MT UI', 'rule-based', "Description contains 'STATE OF MONTANA'"];
    }
    
    if (desc.includes('STATE OF WA ESD') || desc.includes('ESD WA UI-TAX')) {
        return ['WA ESD', 'rule-based', "Description contains 'STATE OF WA ESD'"];
    }
    
    if (desc.includes('EFT REVERSAL')) {
        return ['ACH', 'rule-based', "Description contains 'EFT REVERSAL'"];
    }
    
    if (desc.includes('RTN OFFSET')) {
        return ['ACH Return', 'rule-based', "Description contains 'RTN OFFSET'"];
    }
    
    if (desc.includes('MONEY MKT MUTUAL FUND')) {
        return ['Money Market Fund', 'rule-based', "Description contains 'MONEY MARKET'"];
    }
    
    if (desc.includes('US TREASURY CAPITAL') || desc.includes('TREASURY')) {
        return ['Treasury Transfer', 'rule-based', "Description contains 'TREASURY'"];
    }
    
    if (desc.includes('L&I') || desc.includes('LABOR&INDUSTRIES')) {
        return ['WA LNI', 'rule-based', "Description contains 'L&I' or 'Labor&Industries'"];
    }
    
    if (desc.includes('ACCRUED INT') && account.includes('BLUERIDGE')) {
        return ['Blueridge Interest', 'rule-based', 'Description contains accrued interest and bank is Blueridge'];
    }
    
    if (desc.includes('VA. EMPLOY COMM')) {
        return ['VA UI', 'rule-based', "Description contains 'VA. EMPLOY COMM'"];
    }
    
    if (desc.includes('YORK ADAMS TAX')) {
        return ['York Adams Tax', 'rule-based', "Description contains 'YORK ADAMS TAX'"];
    }
    
    if (desc.includes('BERKS EIT')) {
        return ['Berks Tax', 'rule-based', "Description contains 'Berks EIT'"];
    }
    
    // Amount-based rules
    if (amount < 1.0 && amount > 0) {
        return ['Bad Debt', 'rule-based', 'Amount less than $1.00'];
    }
    
    // Default
    return ['Unknown', 'rule-based', 'No matching rule found'];
}

function parseTransactions(inputData) {
    const lines = inputData.trim().split('\n');
    const transactions = [];
    
    for (let line of lines) {
        if (!line.trim() || line.startsWith('#')) continue;
        
        let parts;
        if (line.includes('|')) {
            parts = line.split('|').map(p => p.trim());
        } else if (line.includes('\t')) {
            parts = line.split('\t').map(p => p.trim());
        } else if (line.includes(',')) {
            parts = line.split(',').map(p => p.trim());
        } else {
            continue;
        }
        
        if (parts.length < 5) continue;
        
        let transactionId = parts[0].replace(/^claim_/i, '').trim();
        
        const transaction = {
            transaction_id: transactionId,
            amount: parts[1],
            date: parts[2],
            payment_method: parts[3] || 'wire in',
            origination_account_id: parts[4] || 'Unknown',
            description: parts.slice(5).join(' ').trim()
        };
        
        transactions.push(transaction);
    }
    
    return transactions;
}

async function analyzeAllTransactions(transactions, sopData) {
    const results = [];
    
    for (let txn of transactions) {
        const [label, method, reason] = predictLabelClientSide(txn);
        const sop_content = sopData[label] || {};
        
        results.push({
            transaction_id: txn.transaction_id,
            amount: txn.amount,
            account: txn.origination_account_id,
            description: txn.description.substring(0, 100) + (txn.description.length > 100 ? '...' : ''),
            label: label,
            method: method,
            reason: reason,
            sop_content: sop_content
        });
    }
    
    return results;
}

function displayResults(results) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';
    
    if (!results || results.length === 0) {
        resultsDiv.innerHTML = '<div class="error-message">No results to display</div>';
        return;
    }
    
    // Group by label
    const grouped = {};
    results.forEach(result => {
        const key = result.label;
        if (!grouped[key]) {
            grouped[key] = [];
        }
        grouped[key].push(result);
    });
    
    // Display each group
    Object.keys(grouped).forEach((label, index) => {
        const group = grouped[label];
        const firstResult = group[0];
        
        const groupDiv = document.createElement('div');
        groupDiv.className = 'transaction-group';
        
        let html = `
            <h3>GROUP ${index + 1}: ${label}</h3>
            
            <div class="transaction-detail">
                <strong>🔢 Transaction IDs:</strong> ${group.map(r => r.transaction_id).join(', ')}
            </div>
            
            <div class="transaction-detail">
                <strong>🏷️ Label:</strong> ${label}
            </div>
            
            <div class="transaction-detail">
                <strong>📊 How we found this:</strong> ${firstResult.reason}
            </div>
            
            <div class="transaction-detail">
                <strong>📋 Sample Transaction${group.length > 1 ? 's' : ''}:</strong> (${group.length} total)
                <ul style="margin-top: 10px; padding-left: 20px;">
        `;
        
        group.slice(0, 3).forEach(txn => {
            html += `
                <li style="margin-bottom: 10px;">
                    ID: ${txn.transaction_id} | ${txn.amount} | ${txn.account}<br>
                    <span style="color: #666; font-size: 0.9em;">${txn.description}</span>
                </li>
            `;
        });
        
        if (group.length > 3) {
            html += `<li style="color: #666;">... and ${group.length - 3} more</li>`;
        }
        
        html += `</ul></div>`;
        
        // Add SOP information
        if (firstResult.sop_content && Object.keys(firstResult.sop_content).length > 0) {
            html += `
                <div class="sop-section">
                    <h4>📚 SOP INFORMATION (ONLY FROM SOP)</h4>
            `;
            
            if (firstResult.sop_content.labeling) {
                html += `
                    <div class="sop-content">
                        <strong>📝 How to Label (from SOP):</strong>
                        <div class="sop-quote">"${firstResult.sop_content.labeling}"</div>
                        <div class="sop-source">
                            Source: ${firstResult.sop_content.sop_page}<br>
                            Link: <a href="${firstResult.sop_content.sop_link}" target="_blank" class="sop-link">${firstResult.sop_content.sop_link}</a>
                        </div>
                    </div>
                `;
            }
            
            if (firstResult.sop_content.reconciliation) {
                html += `
                    <div class="sop-content">
                        <strong>📖 How to Reconcile (from SOP):</strong>
                        <div class="sop-quote">"${firstResult.sop_content.reconciliation}"</div>
                        <div class="sop-source">
                            Source: ${firstResult.sop_content.sop_page}<br>
                            Link: <a href="${firstResult.sop_content.sop_link}" target="_blank" class="sop-link">${firstResult.sop_content.sop_link}</a>
                        </div>
                    </div>
                `;
            }
            
            if (firstResult.sop_content.additional_sops && firstResult.sop_content.additional_sops.length > 0) {
                html += `<div class="additional-sops"><strong>📚 Additional Reference SOPs:</strong>`;
                
                firstResult.sop_content.additional_sops.forEach(sop => {
                    html += `
                        <div class="additional-sop-item">
                            • <strong>${sop.title}</strong><br>
                            <a href="${sop.link}" target="_blank" class="sop-link">${sop.link}</a><br>
                            <span style="color: #666; font-size: 0.9em;">Note: ${sop.note}</span>
                        </div>
                    `;
                });
                
                html += `</div>`;
            }
            
            html += `</div>`;
        }
        
        groupDiv.innerHTML = html;
        resultsDiv.appendChild(groupDiv);
    });
    
    // Summary
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'transaction-group';
    summaryDiv.innerHTML = `
        <h3>📊 SUMMARY</h3>
        <div class="transaction-detail">
            <strong>Total Transactions Analyzed:</strong> ${results.length}
        </div>
        <div class="transaction-detail">
            <strong>Unique Labels:</strong> ${Object.keys(grouped).length}
        </div>
        <div class="transaction-detail">
            <strong>Labels Found:</strong> ${Object.keys(grouped).join(', ')}
        </div>
    `;
    resultsDiv.appendChild(summaryDiv);
}

