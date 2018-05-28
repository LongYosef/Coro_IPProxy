# coding:utf-8
import datetime
from sqlalchemy import Column, Integer, DateTime, Numeric, create_engine, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from DIYIPProxy.baseconfig import DB_CONFIG, DEFAULT_SCORE
'''
sql操作的基类
包括ip，端口，types类型(0高匿名，1透明)，protocol(0 http,1 https http),country(国家),area(省市),updatetime(更新时间)
 speed(连接速度)
'''

BaseModel = declarative_base()


class Proxy(BaseModel):
    __tablename__ = 'site_proxys'
    id = Column(Integer, primary_key=True, autoincrement=True)
    flag = Column(Integer, default=2)
    ip = Column(VARCHAR(16), nullable=False)
    port = Column(Integer, nullable=False)
    proxytypes = Column(Integer, nullable=False,default=0)
    protocol = Column(Integer, nullable=False, default=0)
    updatetime = Column(DateTime(), default=datetime.datetime.utcnow)
    speed = Column(Numeric(5, 2), nullable=False)
    score = Column(Integer, nullable=False, default=DEFAULT_SCORE)


class Sqlhandler():
    params = {'ip': Proxy.ip, 'port': Proxy.port, 'types': Proxy.proxytypes, 
              'protocol': Proxy.protocol,'score': Proxy.score}

    def __init__(self):
        self.engine = create_engine(DB_CONFIG['DB_CONNECT_STRING'],pool_size=10,max_overflow=20,echo = False)
        DB_Session = sessionmaker(bind=self.engine)
        self.sessions=scoped_session(DB_Session)

    def init_db(self):
        BaseModel.metadata.create_all(self.engine)

    def drop_db(self):
        BaseModel.metadata.drop_all(self.engine)


    def insert(self, value):
        insertsession=self.sessions()
        proxy = Proxy(ip=value['ip'], port=value['port'], proxytypes=value['proxytypes'],protocol=value['protocol'], speed=value['speed'])
        insertsession.add(proxy)
        insertsession.commit()
        self.sessions.remove()
        
    def insertall(self, valuelist):
        insertallsession=self.sessions()
        proxy = [Proxy(ip=value['ip'], port=value['port'],proxytypes=value['proxytypes'],protocol=value['protocol'],speed=value['speed']) for value in valuelist]
        insertallsession.add_all(proxy)
        insertallsession.commit()
        self.sessions.remove()


    def delete(self, conditions=None):
        
        '''
        conditions的格式是个字典。eg:{'ip':'192.18.1.1','port':8080}
        '''
        
        deletesession=self.sessions()
        if conditions:
            condition_list = []
            for key in list(conditions.keys()):
                if self.params.get(key, None):
                    condition_list.append(self.params.get(key) == conditions.get(key))
            conditions = condition_list
            query = deletesession.query(Proxy)
            for condition in conditions:
                query = query.filter(condition)
            deleteNum = query.delete()
            deletesession.commit()
            self.sessions.remove()
        else:
            deleteNum = 0
            return deleteNum


    def update(self, conditions=None, value=None):
        '''
        conditions的格式是个字典。eg:{'ip':'192.18.1.1','port':8080}
        value:也是个字典，eg：{'ip':'192.168.0.1'}
        return 返回更新数量
        '''
        updatesession=self.sessions()
        if conditions and value:
            condition_list = []
            for key in list(conditions.keys()):
                if self.params.get(key, None):
                    condition_list.append(self.params.get(key) == conditions.get(key))
            conditions = condition_list
            query = updatesession.query(Proxy)
            for condition in conditions:
                query = query.filter(condition)
            updatevalue = {}
            for key in list(value.keys()):
                if self.params.get(key, None):
                    updatevalue[self.params.get(key, None)] = value.get(key)
            updateNum = query.update(updatevalue)
            updatesession.commit()
            self.sessions.remove()
        else:
            updateNum = 0
        return updateNum


    def select(self, count=None, conditions=None):
        '''
        conditions的格式是个字典。eg:{'ip':'192.18.1.1','port':8080}
        count是提取数量，整数
        return 返回值是代理IP全信息
        '''
        selectsession=self.sessions()
        if conditions:
            condition_list = []
            for key in list(conditions.keys()):
                if self.params.get(key, None):
                    condition_list.append(self.params.get(key) == conditions.get(key))
            conditions = condition_list
        else:
            conditions = []

        query = selectsession.query(Proxy.ip, Proxy.port, Proxy.speed)
        if len(conditions) > 0 and count:
            for condition in conditions:
                query = query.filter(condition)
            result=query.order_by(Proxy.speed).limit(count).all()
            selectsession.commit()
            self.sessions.remove()
            return result
        elif count:
            result=query.order_by(Proxy.speed).limit(count).all()
            selectsession.commit()
            self.sessions.remove()
            return result
        elif len(conditions) > 0:
            for condition in conditions:
                query = query.filter(condition)
            result=query.order_by(Proxy.speed).all()
            selectsession.commit()
            self.sessions.remove()
            return result
        else:
            result=query.order_by(Proxy.speed).all()
            selectsession.commit()
            self.sessions.remove()
            return result



if __name__ == '__main__':
    sqlhelper = Sqlhandler()
    sqlhelper.init_db()
    t=sqlhelper.select()
    print(t)
