为了方便家里老人看电视，所以开发了一个接口，便于远程维护iptv接口。

注意，对应的m3u8文件还是需要自己找，并非该接口自动获取

推荐txt接口使用DIYP播放器进行播放,PC则推荐m3u接口使用PotPlayer进行播放

##### Python直接执行
~~~shell
git clone https://github.com/maopashui/TabIPTV.git
cd TabIPTV
pip install requirements.txt
uvicron main:app
~~~

##### Docker安装

~~~shell
docker pull maopashui/tabiptv:latest
docker run -d -p 8000:8000 --name tabiptv maopashui/tabiptv:latest
~~~

以下截图为wsl环境执行截图：

![image](https://github.com/maopashui/TabIPTV/assets/38207700/09336891-a7b5-4afa-8e1f-fea7c29d6ea4)

##### 使用方式：

1.访问`http://ip:8000/login`，ip为本机ip地址，请自行查看，访问如图。

_首次需要`注册`用户，注册后则无法再新建用户了_，如果不注册的话，随意登录页面会提示报错。

![image](https://github.com/maopashui/TabIPTV/assets/38207700/fee2db6f-f88e-4038-8374-8da053e1f12c)

2.点击`注册`，输入用户密码，<font color=red>这里需要请牢记用户密码，暂未提供密码重置功能</font>，所以需要重置就得重新将docker重新run一个新的

![image](https://github.com/maopashui/TabIPTV/assets/38207700/1ceeac44-a983-4ab1-8102-f8faf984d113)

3.进入首页，没有内容，如图

![image](https://github.com/maopashui/TabIPTV/assets/38207700/9a6ba261-a45c-4360-9390-0b63c6583718)

4.首次进入先添加路径，如iptv_123456，如图

_偷懒没有写删除，所以这里建议只添加一个路径，每次需要变化就编辑_ 230319调整为前缀`iptv_`开头+路径，所以访问接口时记得添加前缀

![image](https://github.com/maopashui/TabIPTV/assets/38207700/a63720a3-87df-49bc-8bbd-7f37ee214caf)

5.新增频道，不想填写图标也可以留个任意字符放那，如图示

首次需要一个个添加，比较麻烦

_当前编辑功能有问题，下一版本修复_ 已修复，时间240319 16:26

![image](https://github.com/maopashui/TabIPTV/assets/38207700/2c5f7b59-f756-4ab6-a2ea-087d5198b655)

6.访问接口

txt接口，就访问路径:http://ip:8000/iptv_123456/txt

_当前txt接口有问题，下一版本修复_ 已修复，时间240319 16:26

m3u接口就访问路径：http://ip:8000/iptv_123456/m3u

![image](https://github.com/maopashui/TabIPTV/assets/38207700/3de4980c-2ae4-4a46-bf66-0aad69f02ef4)

7.PC使用potplayer测试m3u效果图

![image](https://github.com/maopashui/TabIPTV/assets/38207700/2397c725-ffb7-4c49-b920-2d3ad5ed412f)
