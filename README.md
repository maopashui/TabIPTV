为了方便播放电视，所以开发了一个接口，便于远程维护iptv接口

可以直接docker安装
~~~shell
docker pull maopashui/tabiptv
docker run -d -p 8000:8000 --name tabiptv tabiptv:latest
~~~

使用方式：
访问http://ip:8000/login，首次需要注册用户，注册后则无法再新建用户了，如果不注册的话，会报错。
首次进入需要添加路径，如iptv
然后自行新增频道，如图示
![image](https://github.com/maopashui/TabIPTV/assets/38207700/d2f5b932-91b8-48ec-adb8-8df533cb76ef)

最后想访问txt接口，就访问路径:http://ip:8000/iptv/txt,m3u接口就访问路径：http://ip:8000/iptv/m3u
