import schedule
import time
from datetime import datetime

def job():
    print("aaisdmasd")

def test():
    print("uhuhuhu")

schedule.every(5).seconds.do(job)
schedule.every(2).seconds.do(test)

while True:
    schedule.run_pending()
    time.sleep(1)