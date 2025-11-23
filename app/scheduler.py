"""Scheduled tasks for email ingestion."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import subprocess
import sys
from pathlib import Path

from app.config import config
from app.notification_service import check_for_new_emails


class EmailScheduler:
    """Manages scheduled email ingestion tasks."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        atexit.register(lambda: self.scheduler.shutdown())
    
    def schedule_periodic_checks(self, interval_minutes: int = 30):
        """
        Schedule periodic email checks for notifications.
        
        Args:
            interval_minutes: How often to check (default: 30 minutes)
        """
        def run_check():
            try:
                result = check_for_new_emails(manual=False)
                if result.get('has_new'):
                    new_count = result.get('new_count', 0)
                    from_lobeda = result.get('from_lobeda', False)
                    if from_lobeda:
                        print(f"🎯 ALERT: New email from Miss Lobeda! ({new_count} new email(s) total)")
                    else:
                        print(f"📧 New emails detected: {new_count} new email(s)")
            except Exception as e:
                print(f"Error in periodic email check: {e}")
        
        # Schedule periodic checks
        self.scheduler.add_job(
            run_check,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='periodic_email_check',
            replace_existing=True
        )
        print(f"✅ Scheduled periodic email checks every {interval_minutes} minutes")
    
    def schedule_daily_ingestion(self, hour: int = 18, minute: int = 0):
        """
        Schedule daily email ingestion.
        
        Args:
            hour: Hour of day (0-23), default 18 (6pm)
            minute: Minute of hour (0-59), default 0
        """
        def run_ingestion():
            """Run email ingestion and upload."""
            print(f"\n{'='*80}")
            print(f"Scheduled email ingestion started at {hour:02d}:{minute:02d}")
            print(f"{'='*80}\n")
            
            try:
                # Run ingestion script
                project_root = Path(__file__).parent.parent
                script_path = project_root / "scripts" / "backfill_emails.py"
                
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=str(project_root),
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"\n✅ Scheduled ingestion completed successfully")
                    print(result.stdout)
                else:
                    print(f"\n❌ Scheduled ingestion failed:")
                    print(result.stderr)
            
            except Exception as e:
                print(f"\n❌ Error in scheduled ingestion: {e}")
        
        # Schedule the job
        self.scheduler.add_job(
            func=run_ingestion,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_email_ingestion',
            name='Daily Email Ingestion',
            replace_existing=True
        )
        
        print(f"✅ Scheduled daily email ingestion at {hour:02d}:{minute:02d}")
    
    def get_next_run_time(self) -> str:
        """Get the next scheduled run time."""
        job = self.scheduler.get_job('daily_email_ingestion')
        if job:
            next_run = job.next_run_time
            if next_run:
                return next_run.strftime("%Y-%m-%d %H:%M:%S")
        return "Not scheduled"


# Global scheduler instance
scheduler = EmailScheduler()

