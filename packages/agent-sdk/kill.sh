#!/bin/bash

# Find all Python processes running main.py
echo "Looking for Python processes running main.py or server.py..."
PIDS=$(ps -ef | grep "python.*main.py" | grep -v grep | awk '{print $2}')
PIDS+=$(ps -ef | grep "python.*server.py" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
  echo "No Python processes running main.py or server.py found."
  exit 0
fi

# Kill each process with SIGKILL (kill -9)
echo "Found the following processes to kill:"
for PID in $PIDS; do
  CMDLINE=$(cat /proc/$PID/cmdline | tr '\0' ' ')
  echo "  PID $PID: $CMDLINE"
done

echo -e "\nKilling processes..."
for PID in $PIDS; do
  echo "  Killing PID $PID..."
  kill -9 $PID
  if [ $? -eq 0 ]; then
    echo "    ✓ Successfully killed"
  else
    echo "    ✗ Failed to kill"
  fi
done

# Check if any processes remain
REMAINING=$(ps -ef | grep "python.*main.py" | grep -v grep | awk '{print $2}')
if [ -z "$REMAINING" ]; then
  echo -e "\n🔥 All processes successfully killed."
  spd-say "All dead, just like my dreams"
else
  echo -e "\n⚠️ Some processes still running: $REMAINING"
  spd-say "Failed to kill everything, try harder"
fi 