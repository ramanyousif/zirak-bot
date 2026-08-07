#!/bin/bash
cd ~/zirak-bot
pkill -f main_bot.py 2>/dev/null
sleep 2
nohup python3 main_bot.py > bot.log 2>&1 &
echo "Bot started with PID $!"
