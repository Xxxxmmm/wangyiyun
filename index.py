#coding:utf-8
'''
@author: ZainCheung
@LastEditors: ZainCheung
@description:网易云音乐全自动每日打卡云函数版
@Date: 2020-06-25 14:28:48
@LastEditTime: 2020-06-26 17:38:18
'''
from configparser import ConfigParser
from threading import Timer
import requests 
import random
import hashlib
import datetime
import time
import json
import logging

logger = logging.getLogger()
grade = [10,40,70,130,200,400,1000,3000,8000,20000]
api = ''

class Task(object):
    
    '''
    对象的构造函数
    '''
    def __init__(self, uin, pwd, sckey):
        self.uin = uin
        self.pwd = pwd
        self.sckey = sckey

    '''
    带上用户的cookie去发送数据
    url:完整的URL路径
    postJson:要以post方式发送的数据
    返回response
    '''
    def getResponse(self, url, postJson):
        response = requests.post(url, data=postJson, headers={'Content-Type':'application/x-www-form-urlencoded'},cookies=self.cookies)
        return response

    '''
    登陆
    '''
    def login(self):
        data = {"uin":self.uin,"pwd":self.pwd,"r":random.random()}
        if '@' in self.uin:
            url = api + '?do=email'
        else:
            url = api + '?do=login'
        response = requests.post(url, data=data, headers={'Content-Type':'application/x-www-form-urlencoded'})
        code = json.loads(response.text)['code']
        self.name = json.loads(response.text)['profile']['nickname']
        self.uid = json.loads(response.text)['account']['id']
        if code==200:
            self.error = ''
        else:
            self.error = '登陆失败，请检查账号'
        self.cookies = response.cookies.get_dict()
        self.log('登陆成功')
        logger.info("登陆成功")

    '''
    每日签到
    '''
    def sign(self):
        url = api + '?do=sign'
        response = self.getResponse(url, {"r":random.random()})
        data = json.loads(response.text)
        if data['code'] == 200:
            self.log('签到成功')
            logger.info('签到成功')
        else:
            self.log('重复签到')
            logger.info('重复签到')

    '''
    每日打卡300首歌
    '''
    def daka(self):
        url = api + '?do=daka'
        response = self.getResponse(url, {"r":random.random()})
        self.log(response.text)

    '''
    查询用户详情
    '''
    def detail(self):
        url = api + '?do=detail'
        data = {"uid":self.uid, "r":random.random()}
        response = self.getResponse(url, data)
        data = json.loads(response.text)
        self.level = data['level']
        self.listenSongs = data['listenSongs']
        self.log('获取用户详情成功')
        logger.info('获取用户详情成功')

    '''
    Server推送
    '''
    def server(self):
        if self.sckey == '':
            return
        url = 'https://sc.ftqq.com/' + self.sckey + '.send'
        self.diyText() # 构造发送内容
        response = requests.get(url,params={"text":self.title, "desp":self.content})
        data = json.loads(response.text)
        if data['errno'] == 0:
            self.log('用户:' + self.name + '  Server酱推送成功')
            logger.info('用户:' + self.name + '  Server酱推送成功')
        else:
            self.log('用户:' + self.name + '  Server酱推送失败,请检查sckey是否正确')
            logger.info('用户:' + self.name + '  Server酱推送失败,请检查sckey是否正确')

    '''
    自定义要推送到微信的内容
    title:消息的标题
    content:消息的内容,支持MarkDown格式
    '''
    def diyText(self):
        today = datetime.date.today()
        kaoyan_day = datetime.date(2020,12,21) #2021考研党的末日
        date = (kaoyan_day - today).days
        one = requests.get('https://api.qinor.cn/soup/').text # 每日一句的api
        for count in grade:
            if self.level < 10:
                if self.listenSongs < 20000:
                    if self.listenSongs < count:
                        self.tip = '还需听歌' + str(count-self.listenSongs) + '首即可升级'
                        break
                else:
                    self.tip = '你已经听够20000首歌曲,如果登陆天数达到800天即可满级'
            else:
                self.tip = '恭喜你已经满级!'
        if self.error == '':
            state = '目前已完成签到，300百首歌也已听完'
            self.title = '网易云听歌任务已完成'
        else:
            state = self.error
            self.title = '网易云听歌任务出现问题！'
        self.content = ("> tip:等级数据每天下午2点更新 \n\n"
            "------\n"
            "| 用户名   | " + str(self.name) + " |\n"
            "| -------- | :----------------: |\n"
            "| 当前等级 |        " + str(self.level) + "级         |\n"
            "| 累计播放 |       " + str(self.listenSongs) + "首       |\n"
            "| 升级提示 |      " + self.tip + "       |\n"
            "------\n"
            "### 任务状态\n" + str(state) + "\n\n"
            "### 考研倒计时\n距考研还有" + str(date) + "天，主人要加油学习啊\n"
            "### 今日一句\n" + one + "\n\n")

    '''
    打印日志
    '''
    def log(self, text):
        time_stamp = datetime.datetime.now()
        print(time_stamp.strftime('%Y.%m.%d-%H:%M:%S') + '   ' + str(text))

    '''
    开始执行
    '''
    def start(self):
        try:
            self.login()
            self.sign()
            self.detail()
            for i in range(1,3):
                self.daka()
                self.log('用户:' + self.name + '  第' + str(i) + '次打卡成功,即将休眠30秒')
                logger.info('用户:' + self.name + '  第' + str(i) + '次打卡成功,即将休眠30秒')
                time.sleep(10)
            self.server()
        except:
            self.log('用户任务执行中断,请检查账号密码是否正确')
            logger.error('用户任务执行中断,请检查账号密码是否正确========================================')
        else:
            self.log('用户:' + self.name + '  今日任务已完成')
            logger.info('用户:' + self.name + '  今日任务已完成========================================')
            
        
'''
初始化：读取配置,配置文件为init.config
返回字典类型的配置对象
'''
def init():
    global api # 初始化时设置api
    config = ConfigParser()
    config.read('init.config', encoding='UTF-8-sig')
    uin = config['token']['account']
    pwd = config['token']['password']
    api = config['setting']['api']
    md5Switch = config.getboolean('setting','md5Switch')
    peopleSwitch = config.getboolean('setting','peopleSwitch')
    sckey = config['setting']['sckey']
    logger.info('配置文件读取完毕')
    conf = {
            'uin': uin,
            'pwd': pwd,
            'api': api,
            'md5Switch': md5Switch, 
            'peopleSwitch':peopleSwitch,
            'sckey':sckey
        }
    return conf

'''
MD5加密
str:待加密字符
返回加密后的字符
'''
def md5(str):
    hl = hashlib.md5()
    hl.update(str.encode(encoding='utf-8'))
    return hl.hexdigest()

'''
加载Json文件
jsonPath:json文件的名字,例如account.json
'''
def loadJson(jsonPath):
    with open(jsonPath,encoding='utf-8') as f:
        account = json.load(f)
    return account

'''
检查api
'''
def check():
    url = api + '?do=check'
    respones = requests.get(url)
    if respones.status_code == 200:
        logger.info('api测试正常')
    else:
        logger.error('api测试异常')

'''
任务池
'''
def taskPool():
    
    config = init()
    check() # 每天对api做一次检查
    if config['peopleSwitch'] is True:
        logger.info('多人开关已打开,即将执行进行多人任务')
        account = loadJson("account.json")
        for man in account:
            logger.info('账号: ' + man['account'] + '  开始执行========================================')
            task = Task(man['account'], man['password'], man['sckey'])
            task.start()
            time.sleep(10)
        logger.info('所有账号已全部完成任务,服务进入休眠中,等待明天重新启动')
    else :
        logger.info('账号: ' + config['uin'] + '  开始执行========================================')
        if config['md5Switch'] is True:
            logger.info('MD5开关已打开,即将开始为你加密,密码不会上传至服务器,请知悉')
            config['pwd'] = md5(config['pwd'])
        task = Task(config['uin'], config['pwd'], config['sckey'])
        task.start()

'''
程序的入口
'''
def main(event,content):
    taskPool()
