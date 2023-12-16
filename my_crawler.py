from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import NoSuchElementException,WebDriverException
from selenium.webdriver.edge.service import Service

import ddddocr
from time import sleep
from bs4 import BeautifulSoup

import json
import requests

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime



class WeChatAPI:
    '''微信公众号类'''
    def __init__(self, appID, appsecret):
        self.appID = appID
        self.appsecret = appsecret
        self.access_token = self.get_access_token()
        self.open_ids = self.get_openid()

    def get_access_token(self):
        url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}'.format(self.appID, self.appsecret)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36'
        }
        response = requests.get(url, headers=headers).json()
        access_token = response.get('access_token')
        # print('access_token:', access_token)
        return access_token

    def get_openid(self):
        '''获取关注者列表'''
        next_openid = ''
        url_openid = 'https://api.weixin.qq.com/cgi-bin/user/get?access_token=%s&next_openid=%s' % (self.access_token, next_openid)
        ans = requests.get(url_openid)
        open_ids = json.loads(ans.content)['data']['openid']
        return open_ids

    def sendmsg(self, template_id, msg_data, news_url=''):
        '''给关注者群发模板消息'''
        msg_url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(self.access_token)

        if len(self.open_ids) > 0:
            print('给这个用户发送成功open_ids', self.open_ids)
            for open_id in self.open_ids:
                body = {
                    "touser": open_id,
                    "template_id": template_id,
                    "topcolor": "#FF0000",
                    # 对应模板中的数据模板
                    # 格式如下
                    # "data":{
                    #     "keyword1":{
                    #         "value":"巧克力"
                    #     },
                    #     "keyword2": {
                    #         "value":"39.8元"
                    #     },
                    #     "keyword3": {
                    #         "value":"2014年9月22日"
                    #     }
                    # }
                    "data": msg_data
                }
                if(news_url!=''): # 如果url不为空，则给表单数据加上url信息
                    body['url']=news_url
                form_data = bytes(json.dumps(body, ensure_ascii=False).encode('utf-8'))
                response = requests.post(msg_url, data=form_data)
                # result = response.json()
                # print('result:', result)
        else:
            print("当前没有用户关注该公众号！")


def read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"文件 '{path}' 未找到.")
        return []    

def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def split_string(input_str):
    '''切分字符串为三部分，每部分最多15个字符'''
    parts = [input_str[i:i+15] for i in range(0, len(input_str), 15)]
    
    # 如果切分后的部分数量不足3个，添加空字符串补足
    while len(parts) < 3:
        parts.append('')
    
    # 如果超出部分长度超过15，截断
    for i in range(2, len(parts)):
        if len(parts[i]) > 15:
            parts[i] = parts[i][:15]
    
    return parts

def get_datetime():
    '''获取当前的年月日时分秒'''
    # 获取当前时间
    current_time = datetime.now()

    # 格式化为字符串
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time

class WebCrawler():
    def __init__(self,driver_path='') -> None:
        '''爬虫类, driver_path为浏览器驱动器的路径, 若为空则默认不需要进行设置(需要已经配置好了环境变量)'''
        options = Options()
        # options.add_argument('--headless')  # 启用无头模式（即不会显示浏览器）

        if(driver_path==''):
            self.driver = webdriver.Edge(options=options) # 主机不需要配置webdriver路径
        else:
            service = Service(executable_path=driver_path) # 固定搭配直接用就行了
            self.driver = webdriver.Edge(options=options,service=service) # 服务器需要配置webdriver路径
        
    def login_vpn(self,username,password):
        '''登录vpn'''
        url_vpn='https://webvpn.bupt.edu.cn'
        self.driver.get(url_vpn)
        sleep(1) 
        # 找到账号输入框、密码输入框、登录按钮
        username_input = self.driver.find_element(By.NAME,'username')
        password_input = self.driver.find_element(By.NAME,'password')
        login_button = self.driver.find_element(By.ID, "login")


        # 输入用户名和密码并登录
        username_input.send_keys(username)
        password_input.send_keys(password)
        login_button.click()
        
        sleep(3) # 等待页面跳转(不等待的话其他操作可能失败)
        print('登录VPN已完成')

    def login_news(self,username,password):
        '''登录信息门户, 需要先登录vpn才能用'''
        # 该url其实不是信息门户的主页，而是信息门户的通知页
        
        url_news='https://webvpn.bupt.edu.cn/http/77726476706e69737468656265737421fdee0f9e32207c1e7b0c9ce29b5b/list.jsp?urltype=tree.TreeTempUrl&wbtreeid=1154'
        self.driver.get(url_news) 
        sleep(1)
        # 切换到登录框架，否则找不到输入框和登录按钮
        iframe = self.driver.find_element(By.XPATH, "//*[@id='loginIframe']")
        self.driver.switch_to.frame(iframe)

        # 找到账号输入框、密码输入框、登录按钮
        username_input = self.driver.find_element(By.ID,'username')
        password_input = self.driver.find_element(By.ID,'password')
        button = self.driver.find_element(By.CLASS_NAME, "submit-btn")

        # 保证按钮可用(此处参考知乎帖子代码)
        login_pwd = self.driver.find_element(By.XPATH, "//a[@i18n='login.type.password']")
        self.driver.execute_script("arguments[0].click();", login_pwd)


        
        username_input.send_keys(username) # 输入账号
        password_input.send_keys(password) # 输入密码
        
        # 尝试输入验证码
        try:
            capt_input=self.driver.find_element(By.ID,'cptValue') # 找到验证码输入框
            self.driver.find_element(By.XPATH,'//img[@class="code"]').screenshot('capt.jpg') # 截取验证码图片并保存
            ocr=ddddocr.DdddOcr(show_ad=False) 
            with open('capt.jpg','rb') as f:
                img_bytes=f.read()
            capt_str= ocr.classification(img_bytes) # 获取验证码识别结果
            print('验证识别结果:',capt_str)
            capt_input.send_keys(capt_str) # 输入验证码
            
        # 捕获异常，其实都是因为不需要输入验证码
        except NoSuchElementException: # 没找到验证码element
            print('不需要输入验证码')
        except WebDriverException: # 截图失败(失败的原因是没找到验证码图片)
            print('不需要输入验证码')

        button.click() # 点击登录按钮
        
        sleep(3) # 等待页面跳转(不等待的话其他操作可能失败)
        print('登录信息门户已完成')
        
        

    def get_html(self):
        '''获取当前页面的html文本'''
        return self.driver.page_source

    def __del__(self):
        '''析构函数, 关闭浏览器'''
        self.driver.quit()

def craw_and_send():
    '''爬取通知并发送到订阅号'''
    driver_path = '' # 服务器上webdriver的路径
    web_crawler=WebCrawler()
    
    username='' 
    password=''
    
    web_crawler.login_vpn(username,password)
    web_crawler.login_news(username,password)
    html=web_crawler.get_html()
    del web_crawler # 销毁
    soup = BeautifulSoup(html, 'html.parser')

    # html代码格式如下：
    # 开头的script不用管，从剩下的代码中可以看出是一个<ul>，<ul>里包含了许多<li>，<li>里有通知的网址、标题、发布部门、时间这些信息
    # 当然，网址前面还要加上http://my.bupt.edu.cn/
    '''

    <script language="javascript" src="/system/resource/js/dynclicks.js"></script><script language="javascript" src="/system/resource/js/ajax.js"></script><ul class="newslist list-unstyled">
            <li>
            <a href="xntz_content.jsp?urltype=news.NewsContentUrl&wbtreeid=1744&wbnewsid=113288" target="_blank" title="关于召开共青团北京邮电大学第十七次代表大会的通知" style="">关于召开共青团北京邮电大学第十七次代表大会的通知</a>
            <span class="author">校团委</span>
            <span class="time">2023-12-11</span>
        </li>
        <li>
            <a href="xntz_content.jsp?urltype=news.NewsContentUrl&wbtreeid=1737&wbnewsid=113283" target="_blank" title="关于开展“卓越·院长零距离”第四期圆桌座谈会的报名通知" style="">关于开展“卓越·院长零距离”第四期圆桌座谈会的报名通知</a>
            <span class="author">研究生工作部</span>
            <span class="time">2023-12-11</span>
        </li>
        <li>
            <a href="xntz_content.jsp?urltype=news.NewsContentUrl&wbtreeid=1635&wbnewsid=113277" target="_blank" title="讲座预告：北京邮电大学课程思政工作坊•系列讲座第三讲" style="">讲座预告：北京邮电大学课程思政工作坊•系列讲座第三讲</a>
            <span class="author">教务处</span>
            <span class="time">2023-12-11</span>
        </li>
        (此处省略许多<li>)
    </ul>

    '''

    news_list=read_json('news_list.json') # 已有的通知列表
    titles=[news['title'] for news in news_list] # 获取已有通知的标题列表

    target_ul = soup.find('ul', class_='newslist list-unstyled') # 查找具有包含了通知列表的<ul>元素

    appID=''
    appSecret=''
    wechat_api = WeChatAPI(appID, appSecret) # 创建微信公众号对象
    # 如果找到了目标<ul>元素, 就提取信息并发送给订阅号
    if target_ul:
        new_news_list=[] # 新通知列表
        # 遍历<li>元素并提取信息
        for li in target_ul.find_all('li'):
            if li.a.get('title') in titles: # 如果当前通知已经爬到过了，就不再继续爬取
                print('停止爬取')
                break # 由于通知是是按时间顺序排列的，最新通知在最前面，所以后面的通知都不用爬了
            else: # 否则将通知的信息放入通知列表
                news={
                    'url':'http://my.bupt.edu.cn/'+li.a.get('href'),
                    'title':li.a.get('title'),
                    'author':li.find('span', class_='author').text,
                    'time':li.find('span', class_='time').text
                }
                new_news_list.append(news)
                splited_title=split_string(news['title'])
                template_id='' # 模板id
                news_data={
                    "title1":{
                        "value":splited_title[0]
                    },
                    "title2":{
                        "value":splited_title[1]
                    },
                    "title3":{
                        "value":splited_title[2]
                    },
                    "author":{
                        "value":news['author']
                    },
                    "time":{
                        "value":news['url']
                    }
                }
                wechat_api.sendmsg(template_id,news_data,news_url=news['url'])
                
        news_list=new_news_list+news_list # 新通知放在最前面
        write_json('news_list.json',news_list) # 保存通知信息
    else:
        print("未找到目标<ul>元素")

    now=get_datetime()
    print('本次发送已完成, 发送时间:',now)

# 每天固定三个时间点进行爬取和发送
scheduler=BlockingScheduler() # 调度器
# 添加定时任务，每天的9点、14点和22点执行一次
# scheduler.add_job(craw_and_send, 'cron', hour='0,9,14,22') # cron表示cron表达式，允许使用按照精确的日期和时间点运行任务
scheduler.add_job(craw_and_send, 'interval',seconds=60) # cron表示cron表达式，允许使用按照精确的日期和时间点运行任务

# 启动调度器
print("爬虫程序正在调度中, 每天的0点、9点、14点、22点执行一次")
craw_and_send()
scheduler.start()


