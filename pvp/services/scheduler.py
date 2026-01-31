from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django_apscheduler.models import DjangoJobExecution
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging
import atexit

logger = logging.getLogger(__name__)

class MatchScheduler:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_scheduler()
        return cls._instance
    
    def _init_scheduler(self):
        """Инициализация планировщика"""
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_jobstore(DjangoJobStore(), "default")
        
        self.scheduler.configure(
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 30,
            }
        )
        
        self._cleanup_old_jobs()
        register_events(self.scheduler)
        self.scheduler.start()
        logger.info("Match scheduler started")
        atexit.register(self.shutdown)
    
    def _cleanup_old_jobs(self):
        """Очистка старых записей о задачах"""
        try:
            DjangoJobExecution.objects.delete_old_job_executions(7 * 86400)
        except Exception as e:
            logger.warning(f"Failed to cleanup old jobs: {e}")
    
    def schedule_match_finish(self, match_id, duration_minutes, func):
        """
        Планирует завершение матча через указанное время
        
        Returns:
            str: ID задачи или None в случае ошибки
        """
        try:
            job_id = f"match_finish_{str(match_id)}"
            run_time = timezone.now() + timedelta(minutes=duration_minutes)
            
            self.scheduler.add_job(
                func,
                trigger='date',
                run_date=run_time,
                args=[],
                id=job_id,
                name=f"Finish match {str(match_id)}",
                replace_existing=True,
                misfire_grace_time=60,
            )
            
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to schedule match finish: {e}")
            return None
    
    def cancel_match_schedule(self, match_id):
        """
        Отменяет запланированное завершение матча
        
        Returns:
            bool: Успешно ли отменена задача
        """
        try:
            job_id = f"match_finish_{str(match_id)}"
            
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"Cancelled scheduled finish for match {str(match_id)}")
                return True
            else:
                logger.debug(f"No scheduled job found for match {match_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to cancel match schedule: {e}")
            return False
    
    def reschedule_match_finish(self, match_id, duration_minutes):
        """
        Перепланирует завершение матча (отменяет старую, создает новую)
        """
        self.cancel_match_schedule(match_id)
        return self.schedule_match_finish(match_id, duration_minutes)
    
    def get_scheduled_time(self, match_id):
        """Возвращает время запланированного завершения матча"""
        try:
            job_id = f"match_finish_{match_id}"
            job = self.scheduler.get_job(job_id)
            return job.next_run_time if job else None
        except:
            return None
    
    def shutdown(self):
        """Аккуратная остановка планировщика"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Match scheduler stopped")
    
    def get_all_scheduled_matches(self):
        """Возвращает все запланированные матчи (для админки)"""
        jobs = self.scheduler.get_jobs()
        match_jobs = []
        
        for job in jobs:
            if job.id.startswith('match_finish_'):
                match_id = job.id.replace('match_finish_', '')
                match_jobs.append({
                    'match_id': match_id,
                    'scheduled_time': job.next_run_time,
                    'job_id': job.id
                })
        
        return match_jobs