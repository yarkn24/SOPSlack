#!/bin/bash

# Training Monitor - Her dakika update verir
LOG_FILE="training_fast_output.log"
START_TIME=$(date +%s)

echo "🔍 Training Monitor Başladı"
echo "⏱️  Her dakika update verilecek..."
echo ""

while true; do
    # Process çalışıyor mu kontrol et
    PID=$(ps aux | grep "fast_iterative_training.py" | grep -v grep | awk '{print $2}')
    
    if [ -z "$PID" ]; then
        echo "⚠️  Training durdu veya bitti!"
        echo ""
        echo "📊 SON DURUM:"
        tail -30 "$LOG_FILE"
        break
    fi
    
    # Geçen süreyi hesapla
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    MINUTES=$((ELAPSED / 60))
    SECONDS=$((ELAPSED % 60))
    
    # CPU ve Memory kullanımı
    CPU=$(ps aux | grep "$PID" | grep -v grep | awk '{print $3}')
    MEM=$(ps aux | grep "$PID" | grep -v grep | awk '{print $4}')
    
    # Son satırları göster
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⏰ $(date '+%H:%M:%S') | ⏱️  ${MINUTES}m ${SECONDS}s | CPU: ${CPU}% | Mem: ${MEM}%"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Son accuracy veya phase bilgisi
    LAST_ACCURACY=$(tail -20 "$LOG_FILE" | grep "Accuracy:" | tail -1)
    LAST_PHASE=$(tail -20 "$LOG_FILE" | grep "PHASE\|Testing\|\[" | tail -1)
    
    if [ ! -z "$LAST_ACCURACY" ]; then
        echo "📊 $LAST_ACCURACY"
    fi
    
    if [ ! -z "$LAST_PHASE" ]; then
        echo "🏃 $LAST_PHASE"
    fi
    
    echo ""
    
    # 60 saniye bekle
    sleep 60
done



