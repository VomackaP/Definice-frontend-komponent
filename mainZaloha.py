#uvicorn main:app --reload

from fastapi.responses import Response
import fastapi.responses
from fastapi import FastAPI

import json
from IPython.display import SVG

from datetime import datetime
from datetime import timedelta

def getMonday():
    x = datetime.now()
    if int(x.strftime("%w")) == 0 or int(x.strftime("%w")) == 6:
        y = x + timedelta(days = int(int(x.strftime("%w"))/6 + 1))
    else:
        y = x - timedelta(days = int(x.strftime("%w")) - 1)
    return y

def calendarPositionTime(time):
    if time['hours'] == 8 and time['minutes'] == 0:
        return 0
    elif time['hours'] == 9 and time['minutes'] == 50:
        return 1
    elif time['hours'] == 11 and time['minutes'] == 40:
        return 2
    elif time['hours'] == 14 and time['minutes'] == 30:
        return 4
    else:
        return 5

def calendarPositionDate(date):
    return int(datetime(date['year'], date['month'], date['day']).strftime("%w"))-1

def CompareFF(a, b):
    return lambda item: a(item) and b(item)

def separateData(item):
    less = {'startTime': item['startTime'],'endTime': item['endTime'],
    'date': item['date'],'classroomsNames': item['classroomsNames'],'groupsNames': item['groupsNames'],
    'teachersIds': item['teachersIds'], 'teachersNames': item['teachersNames']}

    if 'subjectName' in item:
        less['subjectName'] = item['subjectName']
    elif 'subtopic' in item:
        less['subjectName'] = item['subtopic']
    else:
        less['subjectName'] = ''
    if 'topic'in item:
        less['topic'] = item['topic']
    else:
        less['topic'] = ''
    return less

def displayItem(item, col, subRow, name1, name2, name3, name4, color='#FF0000', rowNumber=4, widt=230):
    smallRowHeight = 25
    bigRowHeight = rowNumber * 25
    colWidth = widt
    leftUpperX = (col) * (colWidth + 2) + 80
    leftUpperY = smallRowHeight + smallRowHeight + subRow * (bigRowHeight + 2)
    rectangle1 = f'<rect x="{leftUpperX}" y="{leftUpperY}" width="{colWidth}" height="{bigRowHeight}" stroke="#000000" stroke-width="1.33333" stroke-miterlimit="8"/>'
    rectangle2 = (f'<rect x="{leftUpperX}" y="{leftUpperY}" width="{colWidth}" height="{bigRowHeight}" stroke="{color}" stroke-width="1.33333" stroke-miterlimit="8" fill="{color}">'
        #+ '<animate attributeName="rx" values="0;15;0" dur="10s" repeatCount="indefinite" />'
        + '</rect>')
    
    text = f'''<text font-family="Calibri,Calibri_MSFontService,sans-serif" font-weight="600" font-size="18" transform="translate({5+leftUpperX} {20+leftUpperY})">
<a xlink:href="/ui/" target="_blank">{item[name1]}</a>
<tspan font-size="15" font-weight="400" x="-0.0424118" y="23"><a xlink:href="/ui/" target="_blank">{item[name2]}</a></tspan>
<tspan font-size="15" font-weight="400" x="1.04089" y="45"><a xlink:href="/ui/" target="_blank">{item[name3]}</a></tspan>
<tspan font-size="15" font-weight="400" x="1.04089" y="70"><a xlink:href="/ui/" target="_blank">{item[name4]}</a></tspan></text>'''
    return rectangle1 + rectangle2 + text




with open('rozvrh.json', encoding="utf8") as inputFile:
    data = json.load(inputFile)

events = []
for item in data['events']:         #kopie bez jakéhokoliv propojení (jedno změním druhé se nemění)
    events.append({**item})

startDate = getMonday()
#startDate = startDate + timedelta(days = 1)
startDate = datetime(2021, 10, 31)
endDate = startDate + timedelta(days = 6)



filterFunc1 = lambda item: '23-5KB' in item['groupsNames']
filterFunc2 = lambda item: datetime(item['date']['year'], item['date']['month'], item['date']['day']) > startDate and datetime(item['date']['year'], item['date']['month'], item['date']['day']) <= endDate
filteredEvents = filter(CompareFF(filterFunc1,filterFunc2), events)

lessons = []
for index, item in enumerate(filteredEvents):
    lessons.append(separateData(item))



app = FastAPI()

@app.get('/svg')
async def resultGet():
    SVGHeader = '<svg width="3000" height="1400" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden">'
    SVGFooter = '</svg>'

    data = (SVGHeader + '<g>')
    data = data + displayItem({'sbj': '8:00', 'top': '', 'tch': '', 'clsr': ''}, 0, -1, 'sbj', 'top', 'tch', 'clsr', '#FFFFFF',1) 
    data = data + displayItem({'sbj': '9:50', 'top': '', 'tch': '', 'clsr': ''}, 1, -1, 'sbj', 'top', 'tch', 'clsr', '#FFFFFF',1) 
    data = data + displayItem({'sbj': '11:40', 'top': '', 'tch': '', 'clsr': ''}, 2, -1, 'sbj', 'top', 'tch', 'clsr', '#FFFFFF',1)
    data = data + displayItem({'sbj': '', 'top': '', 'tch': '', 'clsr': ''}, 3, -1, 'sbj', 'top', 'tch', 'clsr', '#FFFFFF',1)
    data = data + displayItem({'sbj': '14:30', 'top': '', 'tch': '', 'clsr': ''}, 4, -1, 'sbj', 'top', 'tch', 'clsr', '#FFFFFF',1)
    
    for index, item in enumerate(lessons):
        data = data + displayItem({
            'sbj': str(item['date']['day']) + '.' + str(item['date']['month']) + '.', 'top': '', 'tch': '', 'clsr': ''},
            -1, calendarPositionDate(item['date']), 'sbj', 'top', 'tch', 'clsr', '#FFFFFF',4,60)
        data = data + displayItem({
            'sbj': item['subjectName'], 'top': item['topic'][:34], 'tch': item['teachersNames'][0],'clsr': item['classroomsNames'][0]},
            calendarPositionTime(item['startTime']), calendarPositionDate(item['date']),
            'sbj', 'top', 'tch', 'clsr', '#00FFFF')
    data = data + ('</g>' + SVGFooter)

    return Response(content=data, media_type="image/svg+xml")
