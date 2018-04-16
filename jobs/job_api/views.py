# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import parser_classes
from rest_framework.parsers import JSONParser
from celeryapp.celery import add_1,event_prcocess
from django.core.cache import cache
# Create your views here.

@api_view(['POST'])
# @parser_classes((JSONParser,))
def getcall(request , format=None):
    print("test")
    request_data = request.data
    cache.set("getcall", request_data['x'], timeout=None)
    
    add_1.delay(request_data)
    print(cache.get("getcall"))
    return Response({"message": request_data})

@api_view(['POST'])
def user_events(request , format=None):
    print("events call")
    request_data = request.data['QueueJob']
    userId = request_data['param3']['user_id']
    courseId = request_data['param3']['course_id']
    starttimeinsec = 0
    #read from cache is any event is in process , if yes then make it in sequence
    cacheName = "eventInProcessList6"
    eventInprocess =  cache.get(cacheName)
    processSquence = 1 # number of event in process for same user and same course
    if eventInprocess == None:
        # first time cache will create when cache is empty
        print("inside empty cache")
        inprocessEventList = [] #event list
        inprocessEventList.append(processSquence) #added first event in list
        eventInprocess = {userId : {courseId:inprocessEventList}} # assign to disctionary
        # cache.set(cacheName ,eventInprocess)  # write in cache
    else:
        if userId in eventInprocess: # check if user exist in cache or not
            print("user found in cache")
            userInfo = eventInprocess[userId]
            if courseId in userInfo: # if course exist in user dictionary or not
                print("user course found in cache")
                inprocessEventList = eventInprocess[userId][courseId] # read event sequence list
                totalEvent = len(inprocessEventList)
                if totalEvent >= 1:
                    processSquence = inprocessEventList[len(inprocessEventList) - 1] # read last insert sequence number of event
                    processSquence = processSquence + 1
                #increase sequence number of event and update in list and write in cache
                inprocessEventList.append(processSquence) 
                eventInprocess[userId][courseId] = inprocessEventList
                # cache.set(cacheName ,eventInprocess)
            else:  #if not exist course in user dictionary then create one
                print("user course not found in cache")
                inprocessEventList = []
                inprocessEventList.append(processSquence)
                eventInprocess[userId].update({courseId:inprocessEventList})
                # cache.set(cacheName ,eventInprocess)        
        else: #is user not exit in cache then create dictionary for user and course also
            print("user not found in cache")
            inprocessEventList = []
            inprocessEventList.append(processSquence)
            eventInprocess.update({userId : {courseId:inprocessEventList}})
            # cache.set(cacheName ,eventInprocess)
            
    request_data.update({"processSquence":processSquence})  # register sequnce number and send to queue      
    
    # event_prcocess.signature(request_data , countdown=5) 
    # event_prcocess.apply_async((request_data))
    try:
        cache.set(cacheName ,eventInprocess)  # write in cache
        event_prcocess.delay(request_data)
    except Exception as exc:
        print(exc)
        eventInprocess =  cache.get(cacheName)
        inprocessEventList = eventInprocess[userId][courseId]
        del inprocessEventList[inprocessEventList.index(processSquence)]
        eventInprocess[userId][courseId] = inprocessEventList
        cache.set(cacheName ,eventInprocess)
    # print(res.get())
    # print(res.id)
    print(eventInprocess)
    # print(res.successful())
    return Response(request_data)

    def readCacheTest():
        cacheName = "eventInProcessList"
        eventInprocess =  cache.get(cacheName)
        print(eventInprocess)