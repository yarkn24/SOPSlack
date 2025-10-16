/**
 * Transaction Analyzer - Frontend Logic
 */

const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000/api'
    : '/api';  // For Vercel serverless functions

function parseTransactions(inputData) {
    /**
     * Parse transaction data from text or CSV format
     */
    const lines = inputData.trim().split('\n');
    const transactions = [];
    
    for (let line of lines) {
        if (!line.trim() || line.startsWith('#')) continue;
        
        // Try different delimiters
        let parts;
        if (line.includes('|')) {
            parts = line.split('|').map(p => p.trim());
        } else if (line.includes('\t')) {
            parts = line.split('\t').map(p => p.trim());
        } else if (line.includes(',')) {
            // CSV format
            parts = line.split(',').map(p => p.trim());
        } else {
            continue;
        }
        
        if (parts.length < 5) continue;
        
        // Clean transaction ID (remove "claim_" prefix if exists)
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

async function parseTransactionsWithAI(rawText) {
    /**
     * Step 1: Parse raw text with Gemini AI
     */
    try {
        const response = await fetch(`${API_URL}/parse`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                raw_text: rawText,
                use_gemini: true
            })
        });
        
        if (!response.ok) {
            throw new Error(`Parse error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.transactions;
        
    } catch (error) {
        console.error('Error parsing transactions:', error);
        // Fallback to traditional parsing
        return parseTransactions(rawText);
    }
}

async function analyzeAllTransactions(transactions, sopData) {
    /**
     * Step 2: Send parsed transactions to prediction API
     */
    try {
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transactions: transactions,
                ai_provider: document.getElementById('ai-provider')?.value || 'gemini'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.results;
        
    } catch (error) {
        console.error('Error calling API:', error);
        throw new Error('Failed to analyze transactions. Make sure the backend server is running.');
    }
}

function displayResults(results) {
    /**
     * Display analysis results in the UI
     */
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
                <strong>📊 How we found this:</strong> ${firstResult.reason}${firstResult.method.includes('ML') ? ' (ML ile buldum)' : ''}
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
                    <h4>📚 SOP BİLGİLERİ (ONLY FROM SOP)</h4>
            `;
            
            // Labeling section
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
            
            // Reconciliation section
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
            
            // Additional SOPs
            if (firstResult.sop_content.additional_sops && firstResult.sop_content.additional_sops.length > 0) {
                html += `
                    <div class="additional-sops">
                        <strong>📚 Additional Reference SOPs:</strong>
                `;
                
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
    
    // Add summary
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

