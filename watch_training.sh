#!/bin/bash

PID=1935
LOG="efficient_training.log"
LAST_SIZE=0
STUCK=0

clear
echo "🔍 Monitoring PID: $PID (CTRL+C to stop monitoring)"
echo ""

while true; do
    echo "════════════════════════════════════════════════════════════════"
    echo "  ⏰ $(date '+%H:%M:%S') - Training Monitor"
    echo "════════════════════════════════════════════════════════════════"
    
    if ps -p $PID > /dev/null 2>&1; then
        CPU=$(ps -p $PID -o %cpu= | tr -d ' ')
        MEM=$(ps -p $PID -o %mem= | tr -d ' ')
        TIME=$(ps -p $PID -o etime= | tr -d ' ')
        
        echo "✅ Status: RUNNING"
        echo "⚡ CPU: ${CPU}% | 💾 Memory: ${MEM}% | ⏰ Elapsed: ${TIME}"
        
        # Check if stuck
        CURRENT_SIZE=$(wc -l < "$LOG" 2>/dev/null || echo "0")
        if [ "$CURRENT_SIZE" -eq "$LAST_SIZE" ]; then
            STUCK=$((STUCK + 1))
            if [ $STUCK -ge 3 ]; then
                echo "⚠️  WARNING: Log unchanged for ${STUCK} minutes - might be stuck!"
            else
                echo "⏸️  Log paused (${STUCK}/3 checks)"
            fi
        else
            STUCK=0
            GROWTH=$((CURRENT_SIZE - LAST_SIZE))
            echo "📝 Log growing: +${GROWTH} lines"
        fi
        LAST_SIZE=$CURRENT_SIZE
        
        echo ""
        echo "📋 Latest progress:"
        tail -8 "$LOG" | grep -E "✅|🏃|\[.*\]|Accuracy" || tail -3 "$LOG"
        
    else
        echo "❌ Status: STOPPED"
        echo ""
        echo "📊 Final results:"
        tail -40 "$LOG"
        break
    fi
    
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    sleep 60
done
