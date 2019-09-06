# Watson-Assistant-Wechat-Integration
Connect watson assistant with wechat public platform.   
在微信公众号上应用Watson Assistant构建一个聊天机器人

Watson Assistant的官网地址: https://www.ibm.com/cloud/watson-assistant/

在github上另有用Watson Assistant联结微信公众号的repo，但是IBM Watson的API在2018年11月有过更新，原来的API会被逐渐弃用，我这里用的是最新的官方API V2，版本是2019年2月的，整段代码是用Flask框架写的。

一个曾经发布在IBM 中国的教程，已经不能用了. https://developer.ibm.com/cn/blog/2018/watson-assistant-chatbot-wechat/ 但还是可以参考一下

具体的代码和逻辑详见app.py，启动服务也很简单，在linux服务器上执行  
`nohup sudo python -m flask run --host=0.0.0.0 --port=80`
就ok了（注意80端口的开放必须要root权限哦）

如果在使用过程有任何的问题，欢迎issue
