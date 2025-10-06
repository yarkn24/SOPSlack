#!/bin/bash

PID=25321
LOG_FILE="full_pipeline.log"
LAST_LINE_COUNT=0
STUCK_COUNT=0

echo "🔍 Starting continuous monitoring (every 60 seconds)..."
echo "Target PID: $PID"
echo ""

while true; do
    clear
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  🎯 TRAINING MONITOR - $(date '+%H:%M:%S')"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    
    # Check if process is running
    if ps -p $PID > /dev/null 2>&1; then
        # Get process info
        CPU=$(ps -p $PID -o %cpu= | tr -d ' ')
        MEM=$(ps -p $PID -o %mem= | tr -d ' ')
        TIME=$(ps -p $PID -o etime= | tr -d ' ')
        
        echo "✅ Status: RUNNING"
        echo "⚡ CPU: ${CPU}%"
        echo "💾 Memory: ${MEM}%"
        echo "⏰ Elapsed: ${TIME}"
        echo ""
        
        # Check for stuck (log not growing)
        CURRENT_LINE_COUNT=$(wc -l < "$LOG_FILE" 2>/dev/null || echo "0")
        
        if [ "$CURRENT_LINE_COUNT" -eq "$LAST_LINE_COUNT" ]; then
            STUCK_COUNT=$((STUCK_COUNT + 1))
            if [ $STUCK_COUNT -ge 3 ]; then
                echo "⚠️  WARNING: Log unchanged for ${STUCK_COUNT} minutes - might be stuck!"
            else
                echo "⏳ Log unchanged (${STUCK_COUNT}/3 checks)"
            fi
        else
            STUCK_COUNT=0
            NEW_LINES=$((CURRENT_LINE_COUNT - LAST_LINE_COUNT))
            echo "📝 Log growing: +${NEW_LINES} lines"
        fi
        
        LAST_LINE_COUNT=$CURRENT_LINE_COUNT
        
    else
        echo "❌ Status: STOPPED or COMPLETED"
        echo ""
        echo "📊 Final log (last 30 lines):"
        tail -30 "$LOG_FILE"
        break
    fi
    
    echo ""
    echo "───────────────────────────────────────────────────────────────────"
    echo "📋 Latest Progress:"
    echo "───────────────────────────────────────────────────────────────────"
    tail -12 "$LOG_FILE" | grep -E "\[.*\]|✅|📊|🏆|Phase|Accuracy" | tail -8
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    
    sleep 60
done

echo ""
echo "✅ Monitoring ended."



