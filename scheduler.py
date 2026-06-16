#!/usr/bin/env python3
import time
import datetime
import logging
import sys
import os
import yaml

# Import main logic
import main

# Setup logger for scheduler
logger = logging.getLogger("STEMNewsScheduler")

def get_next_run_delay(target_time_str, tz_hours=8):
    """
    Calculate the number of seconds to sleep until the next target time (e.g., "08:00")
    in the specified timezone (default Beijing Time UTC+8).
    """
    tz_offset = datetime.timezone(datetime.timedelta(hours=tz_hours))
    now = datetime.datetime.now(tz_offset)
    
    try:
        parts = target_time_str.split(":")
        target_hour = int(parts[0])
        target_minute = int(parts[1])
    except Exception as e:
        logger.error(f"Invalid schedule time format '{target_time_str}': {e}. Defaulting to 08:00.")
        target_hour, target_minute = 8, 0
        
    target_dt = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    
    if target_dt <= now:
        # If the target time has already passed today, schedule for tomorrow
        target_dt += datetime.timedelta(days=1)
        
    delay = (target_dt - now).total_seconds()
    return delay, target_dt

def run_scheduler():
    logger.info("=== Starting AI STEM Education Bot Scheduler ===")
    
    # Verify config file exists
    config = main.load_config()
    target_time = config.get("schedule", {}).get("time", "08:00")
    logger.info(f"Scheduler configured to run daily at: {target_time} (Beijing Time UTC+8)")
    
    while True:
        # Reload configuration on each iteration in case keywords/webhook changes
        try:
            config = main.load_config()
            target_time = config.get("schedule", {}).get("time", "08:00")
        except Exception as e:
            logger.warning(f"Failed to reload config: {e}. Using previous setting: {target_time}")
            
        delay, next_run = get_next_run_delay(target_time, tz_hours=8)
        
        logger.info(f"Next scheduled run at: {next_run.strftime('%Y-%m-%d %H:%M:%S')} (Beijing Time)")
        logger.info(f"Sleeping for {int(delay // 3600)}h {int((delay % 3600) // 60)}m {int(delay % 60)}s...")
        
        try:
            # We sleep in smaller increments to allow clean KeyboardInterrupt termination
            sleep_remaining = delay
            while sleep_remaining > 0:
                sleep_chunk = min(sleep_remaining, 10.0)
                time.sleep(sleep_chunk)
                sleep_remaining -= sleep_chunk
                
            logger.info("Scheduler waking up... Starting daily execution.")
            # Run the daily brief task
            main.main()
            logger.info("Daily execution finished. Re-scheduling for next day.")
            
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user request. Exiting.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Unexpected error in scheduler loop: {e}. Retrying in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    run_scheduler()
