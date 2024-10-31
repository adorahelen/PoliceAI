from apscheduler.schedulers.background import BackgroundScheduler
from utils.db_utils import fetch_new_data

def scheduled_task():
    # 주기적으로 데이터베이스에서 새 데이터를 가져옴
    print("스케줄러가 작동 중입니다.")
    new_data = fetch_new_data()
    print("가져온 데이터:", new_data)

def start_scheduler():
    scheduler = BackgroundScheduler()
    # 매 1시간마다 `scheduled_task` 함수 실행 (주기는 원하는 대로 조정 가능)
    scheduler.add_job(scheduled_task, 'interval', hours=1)
    scheduler.start()

if __name__ == "__main__":
    start_scheduler()