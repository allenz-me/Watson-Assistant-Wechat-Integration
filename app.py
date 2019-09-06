"""
python >= 3.5
需要安装的第三方库：lxml, ibm_watson, flask
安装方法：pip - python3环境
pip install lxml
pip install ibm-watson
pip install flask

iam_apikey和url要根据watson的服务凭证进行填写，获取见另一个doc文档的末尾部分
Assistant ID 在settings设置的API details中获取
"""

import time
import hashlib

from ibm_watson import AssistantV2    # Watson 官方推荐使用API V2
from lxml import etree    # 用来解析微信平台发送的xml格式的文件
from flask import Flask, request    # Flask 一个简易的python web框架

# 建立一个 assistant 对象
assistant = AssistantV2(
    version='2019-02-28',
    iam_apikey='***',    # 根据watson服务凭证填写
    url='***'
)
# 每个Asistant都会有一个独一无二的ID
ASSISTANT_ID = '***'

# 记录与Watson的会话信息
# user_id: 微信平台给这个用户在本公众号设定的用户id
# session_id: 该用户与Watson会话的消息id，用来建立与Watson Assistant的交互
# lastInvokeTime: 上一次响应该用户请求的时间戳，watson的会话间隔时间不能超过5分钟
session_dict = {}   # user_id:str -> Tuple(session_id:str, lastInvokeTime:int)

# 定义一个web application
app = Flask(__name__)

# 微信平台发送消息的xml格式模板
XmlForm = """
        <xml>
        <ToUserName><![CDATA[{ToUserName}]]></ToUserName>
        <FromUserName><![CDATA[{FromUserName}]]></FromUserName>
        <CreateTime>{CreateTime}</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{Content}]]></Content>
        </xml>
        """

# 微信平台的 token 和 key
TOKEN = '***'
# EncodingAESKey = '***' , 但是后续没有用到这个

# 在每个request之前的行为
@app.before_request
def before_request():
    '''在每个web请求之前，删掉已经会话结束的user_id'''
    now = int(time.time())
    keys = list(session_dict)    # 所有的 user_id 的 list
    for user_id in keys:
        # 如果时间差达到了 298 秒，就把这个用户删掉
        if now - session_dict[user_id][1] >= 298:
            del session_dict[user_id]

@app.route('/weixin', methods=['GET', 'POST'])
def wx():
    # GET 方法用于微信平台验证url的有效性
    # 可见https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Access_Overview.html
    # 只在微信平台验证服务器时用到一次
    if request.method == 'GET':
        # 此处按照微信给定的格式解析并哈希加密收到的数据
        # 加密后的数据与微信发送来的signature做对比，如果一样，那么验证消息确实来自微信平台
        signature = request.args.get('signature')     # 获取携带的signature参数
        timestamp = request.args.get('timestamp')     # 获取携带的timestamp参数
        nonce = request.args.get('nonce')        # 获取携带的nonce参数
        echostr = request.args.get('echostr')

        data = sorted([TOKEN, timestamp ,nonce])

        # 对接收到的消息进行验证，确定是否来自微信公众平台
        mysignature = hashlib.sha1(''.join(data).encode()).hexdigest()
        # 如果来自微信平台
        if mysignature == signature:
            return echostr    # 完成验证

    elif request.method == 'POST':
        # 用户向公众号发送一条消息，微信以xml格式文本post到服务器上
        # 首先验证消息是否来自微信
        signature = request.args.get('signature')     # 获取携带的signature参数
        timestamp = request.args.get('timestamp')     # 获取携带的timestamp参数
        nonce = request.args.get('nonce')        # 获取携带的nonce参数
        data = sorted([token, timestamp ,nonce])
        mysignature = hashlib.sha1(''.join(data).encode()).hexdigest()
        if mysignature != signature:    # 如果不是微信平台的消息
            return ''

        # 如果是微信平台的消息，那么开始解析数据
        webData = request.get_data()    # 获取post到的数据
        recMsg = etree.fromstring(webData)    # 用lxml.etree来解析xml格式数据

        # 提取xml中的信息
        ToUserName = recMsg.findtext('ToUserName')  # 公众号id
        FromUserName = recMsg.findtext('FromUserName')  # 粉丝号id
        CreateTime = recMsg.findtext('CreateTime')  # 时间戳，整型

        ret = {}    # 回复的消息
        ret['ToUserName'] = FromUserName
        ret['FromUserName'] = ToUserName
        ret['CreateTime'] = int(time.time())    # 此时的时间戳
        # 如果发送的是文本信息
        if recMsg.findtext('MsgType') == 'text':    
            Content = recMsg.findtext('Content')    # 粉丝给公众号发送的内容
            # 如果这个用户在session_dict中，意味着他5分钟内发送过消息
            # 那么就维持原来的session_id不变，否则就为这个用户创建新的会话
            if FromUserName in session_dict:
                session_id = session_dict[FromUserName][0]
            else:
                response = assistant.create_session(    # 创建新会话
                    assistant_id=ASSISTANT_ID).get_result()
                session_id = response['session_id']
            
            # 记录下这个用户的session_id和时间
            session_dict[FromUserName] = (session_id, int(time.time()))

            # 调用Watson assistant的API，给这个用户的会话发送消息
            # response: API 返回的内容，json格式
            response = assistant.message(
                assistant_id=ASSISTANT_ID,
                session_id=session_id,
                input=dict(message_type='text', text=Content)).get_result()
            
            ret['Content'] = response['output']['generic'][0]['text']   # 提取Watson响应的内容
            # 按照微信平台的要求返回xml格式的文本
            return XmlForm.format(**ret)
        else:
            # 如果发送的不是文本信息，用户可能向微信公众号发送图片或者语言等
            # 需要注意，用户关注公众号的时候也是返回这个内容
            ret['Content'] = '请发送文本消息'    # 定义在这种情况下发送的消息
            return XmlForm.format(**ret)


if __name__ == '__main__':
    # 开启服务
    app.run()
