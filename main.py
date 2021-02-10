from datetime import datetime
import time
import os
import random
from datetime import datetime, timedelta
from database import storeDB, flaresDB
from my_scheduler import scheduler
from get_jsoc_data import download_aia_3m, download_aia_12s,  download_hmi_mag_45s


def get_aia_3m():
    if storeDB.aia171_3m.count_documents({}) == 0:
        download_date = str(datetime(2013, 9, 29, 22, 0, 0, 1))
        record = {'download_date' : download_date, 'date': datetime.utcnow()}
        storeDB.aia171_3m.insert_one(record).inserted_id
    else:
        download_date = storeDB.aia171_3m.find_one(sort=[{'_id', -1}])['download_date']
        download_date = str(datetime.strptime(download_date, '%Y-%m-%d %H:%M:%S.%f') + timedelta(minutes=5))
        record = {'download_date': download_date, 'date': datetime.utcnow()}
        storeDB.aia171_3m.insert_one(record).inserted_id

    file_name = download_aia_3m(download_date, 171, 'downloads/test_aia3m')
    # db_schedule.aia171_3m.update_one({'download_date': download_date}, {'$set': {'downloaded': True},
    #                                                                     {'file_name' : file_name}}, upsert=True)


def event_detector():
    if storeDB.aia171_3m.count_documents({}) >= 2:
        pass

def test():
    print('i test task')
    time.sleep(10)

if __name__ == '__main__':
    # max_instances - задание может исполняться в более чем одном экземпляре процесса (7)
    # scheduler.add_job(get_aia_3m, 'interval', minutes=5, max_instances=5,  executor='default')
    # scheduler.add_job(event_detector, 'interval', minutes=5, max_instances=5, executor='default')
    test_job = scheduler.add_job(test, 'interval', seconds=3, max_instances=5, executor='default')
    print(test_job)
    scheduler.start()
    test_job.remove()
    try:
        while True:
            time.sleep(3)

    except KeyboardInterrupt:
        pass


    scheduler.shutdown()
