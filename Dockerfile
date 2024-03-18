FROM python:3.9

# 更换Debian软件源
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list
RUN sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 安装sqlite
RUN apt-get update && apt-get install -y sqlite3 libsqlite3-dev

# 设置工作目录
WORKDIR /app

# 复制应用程序代码
COPY . /app

# 安装Python依赖
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 暴露FastAPI端口
EXPOSE 8000

# 启动Redis服务和FastAPI应用程序
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]