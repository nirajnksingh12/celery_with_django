from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.core.cache import cache
import requests,time, json 
# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celeryapp.settings')

app = Celery('proj')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task()
def add_1(request):
    getcall = cache.get('getcall')
    print('gecall cache value')
    print(getcall)
    if int(getcall) == 6:
        cache.set('getcall',7)
        add_1.retry(exc="test iee", countdown=30) 
    return int(request['x']) + int(request['y'])

@app.task()
def event_prcocess(request):
    print("events process started")
    print(request)
    userId = request['param3']['user_id']
    courseId = request['param3']['course_id']
    #read from cache is any event is in process , if yes then make it in sequence
    cacheName = "eventInProcessList6"
    eventInprocess =  cache.get(cacheName)
    print(eventInprocess)
    runProcess =  True
    deltFlaq = False
    if eventInprocess == None:
        print("no sequence")
    else:
        if userId in eventInprocess:
            print("user found in cache sequence")
            userInfo = eventInprocess[userId]
            if courseId in userInfo:
                print("user course found in cache sequence")
                inprocessEventList = eventInprocess[userId][courseId]
                #pick first process number , FIFO
                processSquence = inprocessEventList[0]
                if processSquence != request['processSquence']:
                    runProcess =  False
                    #if sequency is not in first position then add retry
                    event_prcocess.retry(exc="not in sequence", countdown= 30*inprocessEventList.index(request['processSquence'])) 
                else: 
                    deltFlaq = True   
                    # update list in cache after completetion on curl request
            else:
                print("user course not found in cache sequence")
        else:
            print("user not found in cache sequence")
    try:
        url = 'https://admin.dev-edureka.co/Celery/eventsQueueGet'
        data = request
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        # data = {"name": "Value"}
        r = requests.post(url, verify=False, json=data , headers=headers)
        print(r)
    except Exception as exc:
        print(exc)
        print("error occurred in curl request")

    if deltFlaq:
        del inprocessEventList[0]
        eventInprocess[userId][courseId] = inprocessEventList 
        cache.set(cacheName ,eventInprocess)
    print(eventInprocess)    
    return request['processSquence'] 
    
