# coding:utf-8
import random
from DIYIPProxy.baseconfig import get_header
from DIYIPProxy.sqlhelper import Sqlhandler
from DIYIPProxy.baseconfig import parserList
from DIYIPProxy.baseconfig import VALID_URL,TEST_HTTP_URL,TEST_HTTPS_URL
from DIYIPProxy.logger import proxylog,handler_remove

import aiohttp
import async_timeout
import asyncio

from lxml import etree
import time
import json


class ProxyCrawling:
    def __init__(self,url_list=None,valid_url=None,headers=None,loop=None,max_tasks=50,retry_times=5,timeout=10):
        self.headers=headers #请求头设置
        self.timeout=timeout #超时设置
        self.max_tasks=max_tasks #最大任务数设置
        self.start=time.time() #创建实例时间
        self.urllist=url_list #代理网站url及解析信息
        self.valid_url=valid_url #代理检测目标url
        self.proxyq=asyncio.Queue() #协程队列
        self.seen_proxy=set() #去重
        self.retry=retry_times #代理url访问失败最大重试请求数
        self.loop=loop or asyncio.get_event_loop() #时间循环
        self.session=aiohttp.ClientSession(loop=self.loop) #aiohttp会话设置
        self.total_proxy_num=0 #代理数量统计
        self.sucess_proxy_num=0 #成功代理数量统计
        self.lock=asyncio.Lock() #协程锁
        self.http_url=TEST_HTTP_URL #http代理检验url
        self.https_url=TEST_HTTPS_URL #https代理检测url
        self.sqlhelper = Sqlhandler() #数据库操作相关
        self.sqlhelper.init_db() #数据库初始化
        self.proxy_filter() #过滤器初始化
        for ulpxy in self.urllist: #初始化将代理网址url入协程队列
            self.url_into_queue(ulpxy)
            
    #获取user-agent
    def get_headers(self):
        return (get_header() if not self.headers else self.headers)
    
    #统计所有代理ip数量
    async def total_proxy_count(self):
        with await self.lock:
            self.total_proxy_num+=1
            if self.total_proxy_num%50==0:
                proxylog.info('Now Total Proxy Number is {} '.format(self.total_proxy_num))
                
    #统计所有成功代理ip数量            
    async def sucess_proxy_count(self):
        with await self.lock:
            self.sucess_proxy_num+=1 
            proxylog.info('Now Sucess Proxy Number is {}'.format(self.sucess_proxy_num))
            
    #代理url及解析推入协程队列      
    def url_into_queue(self,proxy_url,single_url=None):
        if single_url is None:
            single_url={}
        for url in proxy_url['urls']:
            single_url['flag']=1
            single_url['url']=url
            single_url['pattern']=proxy_url['pattern']
            single_url['position']=proxy_url['position']
            self.proxyq.put_nowait(single_url)
            single_url={}
            
    #将数据库已有代理ip推入协程队列，用于检测代理是否失效，flag=3意味着需要做失效检查        
    def database_into_queue(self,queue_proxy_ip,queue_proxy_port):
        queue_proxy={'flag':3,'ip': queue_proxy_ip, 'port': int(queue_proxy_port),'speed': 100}
        self.proxyq.put_nowait(queue_proxy)
    
    #将已有代理ip加入去重set，并将其推入协程队列，用以检测是否失效   
    def proxy_filter(self):
        valided_proxy=self.sqlhelper.select()
        if valided_proxy:
            for valid_pxy in valided_proxy:
                filter_ip=valid_pxy[0]
                filter_port=valid_pxy[1]
                seen_pxy='http://{}:{}'.format(filter_ip,filter_port)
                self.seen_proxy.add(seen_pxy)
                self.database_into_queue(filter_ip,filter_port)
            
    #页面解析，flag=2意味着需要做ip校验   
    def page_parser(self,response, parser):
        root = etree.HTML(response)
        proxys_list = root.xpath(parser['pattern'])
        for proxy in proxys_list:
            try:
                ip = proxy.xpath(parser['position']['ip'])[0].text
                port = proxy.xpath(parser['position']['port'])[0].text
                proxy_info = {'flag':2,'ip': ip, 'port': int(port),'speed': 100}
                prxy='http://%s:%s'%(ip,port)
                if prxy not in self.seen_proxy:
                    self.seen_proxy.add(prxy)
                    self.proxyq.put_nowait(proxy_info)
                else:
                    pass
            except Exception:
                continue
    #爬取页面        
    async def fetch(self,url,proxys=None):
        with await self.lock:
            proxylog.info('start fetch: {}'.format(url))
        try:    
            with async_timeout.timeout(self.timeout):
                async with self.session.get(url,headers=self.get_headers(),proxy=proxys) as response:
                    assert response.status==200
                    content=await response.text()
                    return content
        except Exception as e:
            with await self.lock:
                proxylog.info('pagedown Failed:{}'.format(url))
            return None
        
    #代理类型检测，0表示高匿，1表示匿名，2表示透明，5代表检测失败    
    async def typecheck(self,check_url,proxys):
        with await self.lock:
            proxylog.debug('start typecheck')
        response=await self.fetch(check_url,proxys)
        if response:
            content=json.loads(response)
            headers=content['headers']
            ip=content['origin']
            proxy_connection=headers.get('proxy-connection',None)
            if ',' in ip:
                checked_types=2
            elif proxy_connection:
                checked_types=1
            else:
                checked_types=0
            return (True,checked_types)
        else:
            return (False,5)
        
    #检查代理类型，0代表http和https都可以，1代表https，2代表http，5代表检查失败    
    async def protocolcheck(self,proxys):
        with await self.lock:
            proxylog.debug('start protocol and type check')
        proxy_http,http_types=await self.typecheck(self.http_url,proxys)
        proxy_https,https_types=await self.typecheck(self.https_url,proxys)
        if proxy_http and proxy_https:
            protocol=0
            proxy_types=http_types
        elif proxy_https:
            protocol=1
            proxy_types=https_types
        elif proxy_http:
            protocol=2
            proxy_types=http_types
        else:
            protocol=5
            proxy_types=5
        return (protocol,proxy_types)
    
    #代理url下载流程，将下载解析结果入队列，下载失败默认会重试，重试次数可设定    
    async def page_download(self,url,parser):
        content=await self.fetch(url)
        if content:
            self.page_parser(content,parser)
            return None
        else:
            count=0
            proxy_list=Sqlhandler.select(10)
            if not proxy_list:
                return None
            while count < self.retry:
                try:
                    random_proxy=random.choice(proxy_list)
                    ip=random_proxy['ip']
                    port=random_proxy['port']
                    use_proxy='http://%s:%s'%(ip,port)
                    proxy_content=await self.fetch(url,use_proxy)
                    if proxy_content:
                        self.page_parser(proxy_content,parser)
                        return None
                except Exception:
                    count+=1
            with await self.lock:
                proxylog.info('Retry many times pagedown Failed:{},'.format(url))
            return None
        
    #代理按目标url进行检查验证    
    async def proxy_validator(self,proxy):
        await self.total_proxy_count()
        try:
            with async_timeout.timeout(self.timeout):
                self.start = time.time()
                async with self.session.get(self.valid_url,headers=self.get_headers(),proxy=proxy) as response:
                    speed=time.time()-self.start
                    
                    try:
                        assert response.status==200
                        await self.sucess_proxy_count()
                        return (True,speed)
                    except Exception as e:
                        with await self.lock:
                            proxylog.exception('proxy validator failed')
                        return (False,speed)
        except Exception as e:
            with await self.lock:
                proxylog.exception('Failed on proxy {} validator timeout'.format(proxy))
            return (False,100)
        
   #下载主流程》代理url网址下载及解析，解析出来的代理信息进行验证，同时也可以将数据库的代理信息更新     
    async def work(self):
        try:
            while True:
                seed=await self.proxyq.get()
                seed_flag=seed['flag']
                if seed_flag==1:
                    url=seed['url']
                    await self.page_download(url,seed)
                    self.proxyq.task_done()
                elif seed_flag==2:
                    ip=seed['ip']
                    port=seed['port']
                    proxys='http://%s:%s'%(ip,port)
                    valid,speed=await self.proxy_validator(proxys)
                    if valid:
                        try:
                            seed['speed']=speed
                            protocol,types=await self.protocolcheck(proxys)
                            seed['protocol']=protocol
                            seed['proxytypes']=types
                            self.sqlhelper.insert(seed)
                            with await self.lock: 
                                proxylog.info('sucess insert {} into database'.format(proxys))
                            self.proxyq.task_done()
                        except Exception as e:
                            with await self.lock: 
                                proxylog.exception('Failed insert {} into database'.format(proxys))
                            self.proxyq.task_done()
                    else:
                        self.proxyq.task_done()
                    
                elif seed_flag==3:
                    ip=seed['ip']
                    port=seed['port']
                    proxys='http://%s:%s'%(ip,port)
                    valid,speed=await self.proxy_validator(proxys)
                    if valid:
                        try:
                            update_speed={'speed':speed}
                            update_proxy={'ip':ip,'port':port}
                            self.sqlhelper.update(update_proxy,update_speed)
                            with await self.lock: 
                                proxylog.info('sucess update {} in database'.format(proxys))
                            self.proxyq.task_done()
                        except Exception as e:
                            with await self.lock: 
                                proxylog.exception('Failed update {} in database'.format(proxys))
                            self.proxyq.task_done()
                    else:
                        try:
                            self.sqlhelper.delete(seed)
                            self.proxyq.task_done()
                        except Exception as e:
                            with await self.lock: 
                                proxylog.exception('Failed delete {} in database'.format(proxys))
                            self.proxyq.task_done()
                           
                    
        except asyncio.CancelledError:
            pass
        
    #利用队列阻塞来控制爬虫    
    async def crawl(self):
        proxylog.info('start proxy crawl')
        works=[asyncio.Task(self.work(),loop=self.loop) for _ in range(self.max_tasks)]
        await self.proxyq.join()
        proxylog.info('proxy crawl done')
        for w in works:
            w.cancel()

def main():
    loop=asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    crawler=ProxyCrawling(url_list=parserList,valid_url=VALID_URL,loop=loop)
    try:
        loop.run_until_complete(crawler.crawl())
    except KeyboardInterrupt:
        for task in asyncio.Task.all_tasks():
            task.cancel()
        loop.stop()
        loop.run_forever()
    finally:
        loop.close()
        handler_remove()
                    
            
if __name__ == '__main__':
    main()