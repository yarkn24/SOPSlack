/**
 * Transaction Analyzer - Frontend Logic
 */

const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000/api'
    : '/api';  // For Vercel serverless functions

function parseTransactions(inputData) {
    /**
     * Parse transaction data from text or CSV format
     * Supports database export format with headers
     */
    const lines = inputData.trim().split('\n');
    const transactions = [];
    
    // Check if first line is a header (contains common column names)
    let headerLine = null;
    let headerMap = {};
    let startIndex = 0;
    
    if (lines.length > 0 && lines[0].toLowerCase().includes('description')) {
        // Detect header row
        headerLine = lines[0];
        const headers = headerLine.split(',').map(h => h.trim().toLowerCase());
        
        // Smart header mapping - find these 6 columns: id, amount, date, payment_method, origination_account_id, description
        headers.forEach((header, index) => {
            const cleanHeader = header.replace(/_/g, '').replace(/\s+/g, '').toLowerCase();
            
            // ID column - exact match or contains 'id' but not 'account'
            if (header === 'id' || (header.includes('id') && !header.includes('account') && !header.includes('customer') && !header.includes('bank'))) {
                if (!headerMap['id']) headerMap['id'] = index;  // Take first match
            }
            // Amount column
            else if (header === 'amount' || header === 'amt' || header === 'value') {
                headerMap['amount'] = index;
            }
            // Date column
            else if (header === 'date' || cleanHeader === 'date' || header === 'created' || header.includes('date')) {
                if (!headerMap['date']) headerMap['date'] = index;
            }
            // Description column - exact match first
            else if (header === 'description') {
                headerMap['description'] = index;
            }
            else if (!headerMap['description'] && (header === 'desc' || cleanHeader.includes('desc'))) {
                headerMap['description'] = index;
            }
            // Payment method column - exact match preferred
            else if (header === 'payment_method' || cleanHeader === 'paymentmethod' || 
                     (header.includes('payment') && (header.includes('method') || header.includes('type')))) {
                headerMap['payment_method'] = index;
            }
            // Origination account ID column - exact match preferred
            else if (header === 'origination_account_id' || cleanHeader === 'originationaccountid' ||
                     header === 'account_id' || cleanHeader === 'accountid' ||
                     (header.includes('origination') && header.includes('account')) ||
                     header === 'account') {
                headerMap['origination_account_id'] = index;
            }
            // Agent/Label column (for validation) - exact match only
            else if (header === 'agent' || header === 'label' || header === 'category') {
                headerMap['agent'] = index;
            }
        });
        
        console.log('CSV with headers detected:', headers);
        console.log('Mapped columns:', headerMap);
        startIndex = 1; // Skip header row
    }
    
    for (let i = startIndex; i < lines.length; i++) {
        const line = lines[i];
        if (!line.trim() || line.startsWith('#')) continue;
        
        // Try different delimiters
        let parts;
        if (line.includes('|')) {
            parts = line.split('|').map(p => p.trim());
        } else if (line.includes('\t')) {
            parts = line.split('\t').map(p => p.trim());
        } else if (line.includes(',')) {
            // CSV format - handle quoted values
            parts = parseCSVLine(line);
        } else {
            continue;
        }
        
        // Remove empty parts from leading/trailing delimiters
        parts = parts.filter(p => p !== '');
        
        if (parts.length < 5) continue;
        
        let transaction;
        
        if (Object.keys(headerMap).length > 0) {
            // Parse using header map (database export format)
            // Only extract 5 essential columns: id, amount, description, payment_method, origination_account_id
            const idIdx = headerMap['id'];
            const amountIdx = headerMap['amount'];
            const descIdx = headerMap['description'];
            const pmIdx = headerMap['payment_method'];
            const accountIdx = headerMap['origination_account_id'];
            const agentIdx = headerMap['agent']; // For validation
            
            // Skip row if essential columns are missing
            if (descIdx === undefined || amountIdx === undefined) {
                console.warn('Skipping row - missing essential columns:', parts);
                continue;
            }
            
            // Skip row if agent already exists (already labeled data)
            if (agentIdx !== undefined && parts[agentIdx] && parts[agentIdx].trim() !== '') {
                console.log(`Skipping row ${parts[idIdx] || 'N/A'} - agent already exists: ${parts[agentIdx]}`);
                continue;
            }
            
            // Payment method: Use directly from CSV (text format like "ach external", "check paid", "wire in")
            const paymentMethod = pmIdx !== undefined ? (parts[pmIdx] || 'wire in') : 'wire in';
            
            transaction = {
                transaction_id: idIdx !== undefined ? (parts[idIdx] || 'N/A') : 'N/A',
                amount: parts[amountIdx] || '0',
                date: '',  // Not needed for prediction
                payment_method: paymentMethod,
                origination_account_id: accountIdx !== undefined ? (parts[accountIdx] || 'Unknown') : 'Unknown',
                description: parts[descIdx] || ''
            };
        } else {
            // Traditional format - check if first field is "claim" (status field)
            let startIdx = 0;
            if (parts[0].toLowerCase() === 'claim') {
                startIdx = 1;  // Skip "claim" field
            }
            
            // Format: [claim?], transaction_id, amount, date, payment_method, account, description
            let transactionId = parts[startIdx].replace(/^claim_/i, '').trim();
            
            transaction = {
                transaction_id: transactionId,
                amount: parts[startIdx + 1],
                date: parts[startIdx + 2],
                payment_method: parts[startIdx + 3] || 'wire in',
                origination_account_id: parts[startIdx + 4] || 'Unknown',
                description: parts.slice(startIdx + 5).join(' ').trim()
            };
        }
        
        // If description is empty, check next line (multi-line format)
        if (!transaction.description && i + 1 < lines.length) {
            const nextLine = lines[i + 1].trim();
            // If next line doesn't have tabs (pure text), it's the description
            if (nextLine && !nextLine.includes('\t')) {
                transaction.description = nextLine;
                i++; // Skip next line since we used it
            }
        }
        
        transactions.push(transaction);
    }
    
    return transactions;
}

function parseCSVLine(line) {
    /**
     * Parse CSV line handling quoted values with commas
     */
    const parts = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            parts.push(current.trim());
            current = '';
        } else {
            current += char;
        }
    }
    
    parts.push(current.trim());
    return parts;
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
     * Step 2: Send parsed transactions to prediction API in batches
     * Process 5 transactions at a time to avoid Vercel timeout (10s limit)
     */
    const BATCH_SIZE = 5;
    const allResults = [];
    
    // Split into batches
    const batches = [];
    for (let i = 0; i < transactions.length; i += BATCH_SIZE) {
        batches.push(transactions.slice(i, i + BATCH_SIZE));
    }
    
    console.log(`Processing ${transactions.length} transactions in ${batches.length} batches...`);
    
    // Process each batch
    for (let i = 0; i < batches.length; i++) {
        const batch = batches[i];
        console.log(`Processing batch ${i + 1}/${batches.length} (${batch.length} transactions)...`);
        
        try {
            const response = await fetch(`${API_URL}/predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    transactions: batch,
                    ai_provider: document.getElementById('ai-provider')?.value || 'gemini'
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            allResults.push(...data.results);
            
            // Show progress
            const loadingDiv = document.getElementById('loading');
            if (loadingDiv) {
                const progressText = loadingDiv.querySelector('p');
                if (progressText) {
                    progressText.textContent = `Analyzing transactions... (${allResults.length}/${transactions.length} completed)`;
                }
            }
            
        } catch (error) {
            console.error(`Error processing batch ${i + 1}:`, error);
            throw new Error(`Failed to analyze batch ${i + 1}. ${error.message}`);
        }
    }
    
    console.log(`✅ Successfully analyzed ${allResults.length} transactions`);
    return allResults;
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
    
    // No validation mode - agent column is skipped if exists
    
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
                <strong>📊 How we found this:</strong> ${firstResult.reason}${firstResult.method.includes('ML') ? ' (found via ML)' : ''}
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
                    <h4>📚 SOP INFORMATION</h4>
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
                
                // Gemini Summary (if available)
                if (firstResult.gemini_summary) {
                    html += `
                        <div class="gemini-summary">
                            <strong>🤖 Gemini Summary:</strong>
                            <div style="background: #f0f9ff; padding: 12px; border-radius: 8px; margin-top: 8px; font-size: 0.95em;">
                                ${firstResult.gemini_summary.split('\n').join('<br>')}
                            </div>
                        </div>
                    `;
                }
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

