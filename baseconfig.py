# coding:utf-8
'''
定义规则 urls:url列表
         type：解析方式,取值 regular(正则表达式),xpath(xpath解析),module(自定义第三方模块解析)
         patten：可以是正则表达式,可以是xpath语句不过要和上面的相对应
'''
from fake_useragent import UserAgent

'''
ip，端口，类型(0高匿名，1透明)，protocol(0 http,1 https),country(国家),area(省市),updatetime(更新时间)
 speed(连接速度)
'''


parserList = [
    {
        'urls': ['http://www.66ip.cn/%s.html' % n for n in ['index'] + list(range(2, 12))],
        'flag': 1,
        'pattern': ".//*[@id='main']/div/div[1]/table/tr[position()>1]",
        'position': {'ip': './td[1]', 'port': './td[2]', 'type': './td[4]', 'protocol': ''}
    },
    {
        'urls': ['http://www.66ip.cn/areaindex_%s/%s.html' % (m, n) for m in range(1, 35) for n in range(1, 10)],
        'flag': 1,
        'pattern': ".//*[@id='footer']/div/table/tr[position()>1]",
        'position': {'ip': './td[1]', 'port': './td[2]', 'type': './td[4]', 'protocol': ''}
    },
    {
        'urls': ['http://cn-proxy.com/', 'http://cn-proxy.com/archives/218'],
        'flag': 1,
        'pattern': ".//table[@class='sortable']/tbody/tr",
        'position': {'ip': './td[1]', 'port': './td[2]', 'type': '', 'protocol': ''}

    },
    {
        'urls': ['http://www.mimiip.com/gngao/%s' % n for n in range(1, 10)],
        'flag': 1,
        'pattern': ".//table[@class='list']/tr",
        'position': {'ip': './td[1]', 'port': './td[2]', 'type': '', 'protocol': ''}

    },
    {
        'urls': ['http://incloak.com/proxy-list/%s#list' % n for n in
                 ([''] + ['?start=%s' % (64 * m) for m in range(1, 10)])],
        'flag': 1,
        'pattern': ".//table[@class='proxy__t']/tbody/tr",
        'position': {'ip': './td[1]', 'port': './td[2]', 'type': '', 'protocol': ''}

    },
    {
        'urls': ['http://www.kuaidaili.com/proxylist/%s/' % n for n in range(1, 11)],
        'flag': 1,
        'pattern': ".//*[@id='index_free_list']/table/tbody/tr[position()>0]",
        'position': {'ip': './td[1]', 'port': './td[2]', 'type': './td[3]', 'protocol': './td[4]'}
    },
    {
        'urls': ['http://www.kuaidaili.com/free/%s/%s/' % (m, n) for m in ['inha', 'intr', 'outha', 'outtr'] for n in
                 range(1, 11)],
        'flag': 1,
        'pattern': ".//*[@id='list']/table/tbody/tr[position()>0]",
        'position': {'ip': './td[1]', 'port': './td[2]', 'type': './td[3]', 'protocol': './td[4]'}
    },
    {
        'urls': ['http://www.cz88.net/proxy/%s' % m for m in
                 ['index.shtml'] + ['http_%s.shtml' % n for n in range(2, 11)]],
        'flag': 1,
        'pattern': ".//*[@id='boxright']/div/ul/li[position()>1]",
        'position': {'ip': './div[1]', 'port': './div[2]', 'type': './div[3]', 'protocol': ''}

    },
    {
        'urls': ['http://www.ip181.com/daili/%s.html' % n for n in range(1, 11)],
        'flag': 1,
        'pattern': ".//div[@class='row']/div[3]/table/tbody/tr[position()>1]",
        'position': {'ip': './td[1]', 'port': './td[2]', 'type': './td[3]', 'protocol': './td[4]'}

    },
    {
        'urls': ['http://www.xicidaili.com/%s/%s' % (m, n) for m in ['nn', 'nt', 'wn', 'wt'] for n in range(1, 8)],
        'flag': 1,
        'pattern': ".//*[@id='ip_list']/tr[position()>1]",
        'position': {'ip': './td[2]', 'port': './td[3]', 'type': './td[5]', 'protocol': './td[6]'}
    },

]
    
'''
数据库的配置
'''
DB_CONFIG = {

    'DB_CONNECT_STRING': "mysql+pymysql://root:LearnPy@localhost:3306/LearnPy?charset=utf8"

}

THREADNUM = 5
API_PORT = 8000
'''
爬虫爬取和检测ip的设置条件
不需要检测ip是否已经存在，因为会定时清理
'''
UPDATE_TIME = 30 * 60  # 每半个小时检测一次是否有代理ip失效
MINNUM = 50  # 当有效的ip值小于一个时 需要启动爬虫进行爬取

TIMEOUT = 5  # socket延时
'''
反爬虫的设置
'''
'''
重试次数
'''
RETRY_TIME = 3

'''
USER_AGENTS 随机头信息
'''
ua=UserAgent()


def get_header():
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate',
    }
#默认给抓取的ip分配20分,每次连接失败,减一分,直到分数全部扣完从数据库中删除
DEFAULT_SCORE=10

VALID_URL = 'http://httpbin.org/ip'
TEST_IP = 'http://ip.chinaz.com/getip.aspx'
TEST_HTTP_URL = 'http://httpbin.org/get'
TEST_HTTPS_URL = 'https://httpbin.org/get'
#CHECK_PROXY变量是为了用户自定义检测代理的函数
#现在使用检测的网址是httpbin.org,但是即使ip通过了验证和检测
#也只能说明通过此代理ip可以到达httpbin.org,但是不一定能到达用户爬取的网址
#因此在这个地方用户可以自己添加检测函数,我以百度为访问网址尝试一下
#大家可以看一下Validator.py文件中的baidu_check函数和detect_proxy函数就会明白

CHECK_PROXY={'function':'checkProxy'}#{'function':'baidu_check'}

#下面配置squid,现在还没实现
#SQUID={'path':None,'confpath':'C:/squid/etc/squid.conf'}

MAX_CHECK_PROCESS = 2 # CHECK_PROXY最大进程数
MAX_CHECK_CONCURRENT_PER_PROCESS = 30 # CHECK_PROXY时每个进程的最大并发
TASK_QUEUE_SIZE = 50 # 任务队列SIZE
MAX_DOWNLOAD_CONCURRENT = 3 # 从免费代理网站下载时的最大并发 
CHECK_WATI_TIME = 1#进程数达到上限时的等待时间