"""Scheduled tasks for email ingestion."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import logging
import subprocess
import sys
from pathlib import Path

from app.config import config
from app.notification_service import check_for_new_emails

logger = logging.getLogger(__name__)


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
                    logger.info(f"New school emails detected: {new_count}")
                    try:
                        from app.notification_sender import send_new_email_alert
                        send_new_email_alert(new_count)
                    except Exception as notify_err:
                        logger.warning(f"Notification send failed: {notify_err}")
            except Exception as e:
                logger.error(f"Error in periodic email check: {e}")
        
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
                    logger.info("Scheduled ingestion completed successfully")
                    # After a full ingest, check for new emails and notify
                    try:
                        check_result = check_for_new_emails(manual=False)
                        if check_result.get('has_new'):
                            from app.notification_sender import send_new_email_alert
                            send_new_email_alert(check_result.get('new_count', 0))
                    except Exception as notify_err:
                        logger.warning(f"Post-ingestion notification failed: {notify_err}")
                else:
                    logger.error(f"Scheduled ingestion failed: {result.stderr}")

            except Exception as e:
                logger.error(f"Error in scheduled ingestion: {e}")
        
        # Schedule the job
        self.scheduler.add_job(
            func=run_ingestion,
            trigger=CronTrigger(hour=hour, minute=minute),
            id='daily_email_ingestion',
            name='Daily Email Ingestion',
            replace_existing=True
        )
        
        logger.info(f"Scheduled daily email ingestion at {hour:02d}:{minute:02d}")

    def schedule_weekly_digest(self, hour: int = 8, minute: int = 0, day_of_week: str = "sun"):
        """
        Schedule the weekly school digest email (default: Sunday 8am).
        Only runs if PARENT_EMAIL and RESEND_API_KEY are configured.
        """
        from app.config import config
        if not config.PARENT_EMAIL or not config.RESEND_API_KEY:
            logger.info("Weekly digest skipped (PARENT_EMAIL or RESEND_API_KEY not set)")
            return

        def run_digest():
            try:
                from app.digest_generator import send_weekly_digest
                send_weekly_digest()
            except Exception as e:
                logger.error(f"Weekly digest error: {e}")

        self.scheduler.add_job(
            func=run_digest,
            trigger=CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
            id='weekly_digest',
            name='Weekly School Digest',
            replace_existing=True,
        )
        logger.info(f"Scheduled weekly digest every {day_of_week} at {hour:02d}:{minute:02d}")

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

