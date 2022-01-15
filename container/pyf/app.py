from functools import cache
import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
#from models import BaseModel
from sqlengine.sqlengine import initEngine, initSession
import fastapiapp
import graphqlapp
from fastapi.responses import Response
import fastapi.responses
from IPython.display import SVG
from datetime import datetime
from datetime import timedelta
from typing import Optional

@cache
def getConfig(configFileName='config.json'):
    """Reads config from file
    Parameters
    ----------
    configFileName: str
        name of the file to be readed
    Returns
    -------
    json: dict
        data structure defining parameters describing application and stored externally
    """
    with open(configFileName, 'r') as config:
        return json.load(config)

def initDb(connectionstring, doDropAll=False, doCreateAll=False):
    """Initialize database connection
    Parameters
    ----------
    connectionstring: str
        full connection string defining the connection to database
    doDropAll: boolean=False
        if True, database is dropped
    doCreateAll: boolean=False
        if True, database is redefined, usually used with doDropAll=True
    Returns
    -------
    Session: callable
        used for instatiating a session
    """

    print('initDb started')
    
    print(f'Session with doDropAll={doDropAll} & doCreateAll={doCreateAll}')
    assert not(connectionstring is None), 'Connection string missing'
    #####################
    #initModels()
    #####################

    from models.BaseModel import BaseModel
    
    from models.GroupRelated.GroupModel import GroupModel
    from models.GroupRelated.UserModel import UserModel
    from models.GroupRelated.UserGroupModel import UserGroupModel
    from models.GroupRelated.RoleModel import RoleModel
    from models.GroupRelated.RoleTypeModel import RoleTypeModel
    from models.GroupRelated.GroupTypeModel import GroupTypeModel
    
    from models.EventsRelated.EventModel import EventModel
    from models.EventsRelated.EventUserModel import EventUserModel
    from models.EventsRelated.EventGroupModel import EventGroupModel
    from models.EventsRelated.EventRoomModel import EventRoomModel

    from models.AcreditationRelated.AcrediationUserRole import AcreditationUserRoleModel
    from models.AcreditationRelated.ProgramModel import ProgramModel
    from models.AcreditationRelated.SubjectModel import SubjectModel
    from models.AcreditationRelated.SubjectSemesterModel import SubjectSemesterModel
    from models.AcreditationRelated.SubjectTopic import SubjectTopicModel
    from models.AcreditationRelated.StudyPlan import StudyPlanModel
    from models.AcreditationRelated.StudyPlanItem import StudyPlanItemModel

    from models.FacilitiesRelated.ArealModel import ArealModel
    from models.FacilitiesRelated.BuildingModel import BuildingModel
    from models.FacilitiesRelated.RoomModel import RoomModel

    #from models import GroupModel, UserModel, UserGroupModel, RoleModel, RoleTypeModel
    #from models import EventModel, EventUserModel, EventGroupModel
    #from models import ArealModel, BuildingModel, RoomModel
    #from models import ProgramModel, SubjectModel, SubjectSemesterModel, SubjectTopicModel, AcreditationUserRoleModel

    #all = [GroupModel, UserModel, UserGroupModel, RoleModel, RoleTypeModel, EventModel, EventUserModel, EventGroupModel]
    engine = initEngine(connectionstring) 
    Session = initSession(connectionstring)
    
    if doDropAll:
        BaseModel.metadata.drop_all(engine)
        print('DB Drop Done')
    if doCreateAll:
        BaseModel.metadata.create_all(engine)
        print('DB Create All Done')

    print('table list')
    for item in BaseModel.metadata.tables.keys():
        print('\t', item)
    print('initDb finished')
    return Session



def buildApp():
    """builds a FastAPI application object with binded Swagger and GraphQL endpoints
    Returns
    -------
    app
        FastAPI instance with binded endpoints
    """
    print('Load config')
    #print('Load config')
    connectionstring = 'postgresql://postgres:example@postgres:5432/postgres'  #getConfig()['connectionstring']

    print('Init Session')
    Session = initSession(connectionstring)
    def prepareSession():#Session=Session): # default parameters are not allowed here
        """generator for creating db session encapsulated with try/except block and followed session.commit() / session.rollback()
        Returns
        -------
        generator
            contains just one item which is instance of Session (SQLAlchemy)
        """
        session = Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()    

    #app = FastAPI(root_path="/apif")
    
    initDb(connectionstring, doDropAll=True, doCreateAll=True)
    #initDb(connectionstring)

    app = FastAPI()
    @app.get('/svg/')
    async def resultGet(type: str, filterID: int, start: Optional[datetime] = None):
        if start != None:
            startDate = start
        else:
            startDate = getMonday()
            startDate = startDate - timedelta(days = 1)     #posun na neděli protože datatime má někdy problém s rovností v >= 
        endDate = startDate + timedelta(days = 6)
        filteringID = filterID

        if type == 'S':
            filteringGroup = 'groupsNames'      #pak upravit na groupsId - nějaký velký programátor který mě nechce potkat nechápe že věci mají mít ID
            filteringID = '23-5KB'
        elif type == 'T':
            filteringGroup = 'teachersIds'      #občas chyba - učitele někdy nemají ID
        elif type == 'C':
            filteringGroup = 'classroomsIds'    #nefunguje - proč asi, ne všechny učebny mají ID

        filteringText = filteringID             #pak předělat na hledání názvu filtrované věci podle filteringGroupe a filteringID

        filterFunc1 = lambda item: filteringID in item[filteringGroup]
        filterFunc2 = lambda item: datetime(item['date']['year'], item['date']['month'], item['date']['day']) >= startDate and datetime(item['date']['year'], item['date']['month'], item['date']['day']) <= endDate
        filteredEvents = filter(CompareFF(filterFunc1,filterFunc2), events)
        
        lessons = []
        for index, item in enumerate(filteredEvents):
            lessons.append(separateData(item))

        if (filteringID == '23-5KB'):           #pak odstranit jen dočasný fix protože učební skupiny nemají ID
            filteringID = 10

        SVGHeader = '<svg width="3000" height="1400" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden">'
        SVGFooter = '</svg>'

        data = (SVGHeader + '<g>')
        data = data + displayItem({'sbj': '8:00', 'top': '', 'tch': '', 'clsr': ''}, 0, -1, 'sbj', 'top', 'tch', 'clsr', '#FFFFFF',1) 
        data = data + displayItem({'sbj': '9:50', 'top': '', 'tch': '', 'clsr': ''}, 1, -1, 'sbj', 'top', 'tch', 'clsr', '#FFFFFF',1) 
        data = data + displayItem({'sbj': '11:40', 'top': '', 'tch': '', 'clsr': ''}, 2, -1, 'sbj', 'top', 'tch', 'clsr', '#FFFFFF',1)
        data = data + displayItem({'sbj': '', 'top': '', 'tch': '', 'clsr': ''}, 3, -1, 'sbj', 'top', 'tch', 'clsr', '#FFFFFF',1)
        data = data + displayItem({'sbj': '14:30', 'top': '', 'tch': '', 'clsr': ''}, 4, -1, 'sbj', 'top', 'tch', 'clsr', '#FFFFFF',1)
        data = data + displayItem({'sbj': '16:20', 'top': '', 'tch': '', 'clsr': ''}, 5, -1, 'sbj', 'top', 'tch', 'clsr', '#FFFFFF',1)

        data = data + displayItem({'sbj': filteringText, 'top': '', 'tch': '', 'clsr': ''}, 2, 20, 'sbj', 'top', 'tch', 'clsr', '#00BBFF',1)
        data = data + displayItem({'sbj': 'Předchozí týden', 'top': '', 'tch': '', 'clsr': ''}, 1, 20, 'sbj', 'top', 'tch', 'clsr', '#00DFFF',
        1,220,"./?type="+type+"&amp;filterID="+str(filteringID)+"&amp;start=" + str(startDate - timedelta(days = 7)))

        data = data + displayItem({'sbj': 'Příští týden', 'top': '', 'tch': '', 'clsr': ''}, 3, 20, 'sbj', 'top', 'tch', 'clsr', '#00DFFF',
        1,220,"./?type="+type+"&amp;filterID="+str(filteringID)+"&amp;start=" + str(startDate + timedelta(days = 7)))
        
        datumForName = startDate
        dayList = ['Po', 'Út', 'St', 'Čt', 'Pá']
        for i in range(5):
            datumForName = datumForName + timedelta(days = 1)
            data = data + displayItem({
                'sbj': str(datumForName.day) + '.' + str(datumForName.month) + '.', 'top': dayList[datumForName.weekday()], 'tch': '', 'clsr': ''},
                -1, i, 'sbj', 'top', 'tch', 'clsr', '#FFFFFF',4,60)

        for index, item in enumerate(lessons):
            data = data + displayItem({
                'sbj': item['subjectName'][:27], 'top': item['topic'][:32], 'tch': item['teachersNames'][0],'clsr': item['classroomsNames'][0]},
                calendarPositionTime(item['startTime']), calendarPositionDate(item['date']),
                'sbj', 'top', 'tch', 'clsr', '', 4, 220, "","","/teacher/?id="+str(item['teachersIds'][0]),"")
        data = data + ('</g>' + SVGFooter)
        
        return Response(content=data, media_type="image/svg+xml")
    @app.get('/svgs/')
    async def resultGet(start: Optional[datetime] = None):
        if start != None:
            startDate = start
        else:
            startDate = datetime(2021, 9, 1)
            startDate = startDate - timedelta(days = 1)
        endDate = datetime(2022, 3, 7)
        filteringGroup = 'groupsNames'
        filteringText = '23-5KB'

        filterFunc1 = lambda item: filteringText in item[filteringGroup]
        filterFunc2 = lambda item: datetime(item['date']['year'], item['date']['month'], item['date']['day']) >= startDate and datetime(item['date']['year'], item['date']['month'], item['date']['day']) <= endDate
        filteredEvents = filter(CompareFF(filterFunc1,filterFunc2), events)

        lessons = []
        for index, item in enumerate(filteredEvents):
            lessons.append(separateData(item))

        SVGHeader = '<svg width="3000" height="1400" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" overflow="hidden">'
        SVGFooter = '</svg>'

        data = (SVGHeader + '<g>')

        for i in range(4):
            data = data + displayItemS({'sbj': '8:00', 'tch': '', 'clsr': ''}, 1, 2 + i*16, 'sbj', 'tch', 'clsr', 3,'#AACCFF')
            data = data + displayItemS({'sbj': '9:50', 'tch': '', 'clsr': ''}, 1, 5 + i*16, 'sbj', 'tch', 'clsr', 3,'#AACCFF') 
            data = data + displayItemS({'sbj': '11:40', 'tch': '', 'clsr': ''}, 1, 8 + i*16, 'sbj', 'tch', 'clsr', 3,'#AACCFF')
            data = data + displayItemS({'sbj': '14:30', 'tch': '', 'clsr': ''}, 1, 11 + i*16, 'sbj', 'tch', 'clsr', 3,'#AACCFF')
            data = data + displayItemS({'sbj': '16:20', 'tch': '', 'clsr': ''}, 1, 14 + i*16, 'sbj', 'tch', 'clsr', 3,'#AACCFF')
        data = data + displayItemS({'sbj': '8:00', 'tch': '', 'clsr': ''}, 1, 2 + 64, 'sbj', 'tch', 'clsr', 3,'#AACCFF')
        data = data + displayItemS({'sbj': '9:50', 'tch': '', 'clsr': ''}, 1, 5 + 64, 'sbj', 'tch', 'clsr', 3,'#AACCFF') 
        data = data + displayItemS({'sbj': '11:40', 'tch': '', 'clsr': ''}, 1, 8 + 64, 'sbj', 'tch', 'clsr', 3,'#AACCFF')
        
        dayList = ['Po', 'Út', 'St', 'Čt', 'Pá']
        for i in range(4):
            data = data + displayItemS({
                'sbj': dayList[i], 'tch': '', 'clsr': ''},
                0, i * 16 + 2, 'sbj', 'tch', 'clsr', 15,'#00FFAA')
        data = data + displayItemS({
                'sbj': dayList[4], 'tch': '', 'clsr': ''},
                0, 4 * 16 + 2, 'sbj', 'tch', 'clsr', 9,'#00FFAA')

        datumColumn = {}
        sloupcePrvnichMesicu = []
        datumForSemestr = startDate + timedelta(days = 1)
        sloupec = 2
        while(datumForSemestr <= endDate):
            if datumForSemestr.day == 1 or sloupec == 2:
                if int(datumForSemestr.strftime("%w")) == 1:
                    data = data + displayItemS({'sbj': str(datumForSemestr.month) + '/' + str(datumForSemestr.year)[2:], 'tch': '', 'clsr': ''},
                        sloupec, 0, 'sbj', 'tch', 'clsr', 1,'#FFAA00')
                    sloupcePrvnichMesicu.append(sloupec)
                else:
                    data = data + displayItemS({'sbj': str(datumForSemestr.month) + '/' + str(datumForSemestr.year)[2:], 'tch': '', 'clsr': ''},
                        sloupec+1, 0, 'sbj', 'tch', 'clsr', 1,'#FFAA00')
                    sloupcePrvnichMesicu.append(sloupec+1)
            if int(datumForSemestr.strftime("%w")) == 6:
                datumForSemestr = datumForSemestr + timedelta(days = 1)
                continue
            elif int(datumForSemestr.strftime("%w")) == 0:
                datumForSemestr = datumForSemestr + timedelta(days = 1)
                sloupec = sloupec + 1
                continue
            data = data + displayItemS({'sbj': datumForSemestr.day, 'tch': '', 'clsr': ''},
                sloupec, (int(datumForSemestr.strftime("%w"))-1) * 16 + 1, 'sbj', 'tch', 'clsr', 1,'#FFFF00')
            datumColumn[datumForSemestr] = sloupec
            hours = 0
            if int(datumForSemestr.strftime("%w")) == 5:
                hours = 3
            else:
                hours = 5
            for i in range(hours):
                if(sloupec in sloupcePrvnichMesicu):
                    color = '#FFCCAA'
                else:
                    color = '#FFFFFF'
                data = data + displayItemS({'sbj': '', 'tch': '', 'clsr': ''},
                    sloupec, (int(datumForSemestr.strftime("%w"))-1) * 16 + i*3 + 2, 'sbj', 'tch', 'clsr', 3, color)

            datumForSemestr = datumForSemestr + timedelta(days = 1)
        
        inicials = {}
        shortcuts = {}
        for index, item in enumerate(lessons):
            date = item['date']
            
            column = datumColumn[datetime(date['year'], date['month'], date['day'])]
            row = calendarPositionDate(item['date']) * 16 + SemestrPositionTime(item['startTime']) * 3 + 2
            teachInicials = str(getInicials(item['teachersNames'][0]))
            subjectShortcut = str(subShortcut(item['subjectName']))
            if(teachInicials != ""):
                inicials[teachInicials] = item['teachersNames'][0]          #ošetřit duplicitní iniciály
            if(subjectShortcut != ""):
                shortcuts[subjectShortcut] = item['subjectName']
            if(column in sloupcePrvnichMesicu):
                color = '#FFCCAA'
            else:
                color = '#FFFFFF'

            data = data + displayItemS({
                'sbj': subjectShortcut, 'tch': teachInicials,'clsr': item['classroomsNames'][0][:4]},
                column , row, 'sbj', 'tch', 'clsr', 3, color)
        
        rowOfLegend = 76
        for item in shortcuts:
            data = data + displayItemS({'sbj': item, 'tch': '', 'clsr': ''},
                0, rowOfLegend, 'sbj', 'tch', 'clsr', 1,'#A0DAFF')
            data = data + displayItemS({'sbj': shortcuts[item], 'tch': '', 'clsr': ''},
                1, rowOfLegend, 'sbj', 'tch', 'clsr', 1,'#B0FFFF', link1 = "", link2 = "", link3 = "", widt = 231)
            rowOfLegend += 1

        rowOfLegend = 76
        for item in inicials:
            data = data + displayItemS({'sbj': item, 'tch': '', 'clsr': ''},
                9, rowOfLegend, 'sbj', 'tch', 'clsr', 1,'#55FFAA')
            data = data + displayItemS({'sbj': inicials[item], 'tch': '', 'clsr': ''},
                10, rowOfLegend, 'sbj', 'tch', 'clsr', 1,'#AAFF00', link1 = "", link2 = "", link3 = "", widt = 231)
            rowOfLegend += 1

        data = data + ('</g>' + SVGFooter)
        
        return Response(content=data, media_type="image/svg+xml")
    origins = ["http://localhost:3000", "http://localhost:50003",]

    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=[""], allow_headers=[""],)

    print('init Db')
    fastapiapp.attachFastApi(app, prepareSession)
    graphqlapp.attachGraphQL(app, prepareSession)
    return app

app = buildApp()




 
