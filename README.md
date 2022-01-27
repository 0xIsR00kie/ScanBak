# ScanBak V1.4
备份文件扫描

# 安装
```
git clone https://github.com/0xIsR00kie/ScanBak.git
pip install -r requirements.txt
```

# 使用
> 程序默认使用正常请求模式. 
> 
> 使用head 高速模式
> 
> python scanBak.py -u http://www.baidu.com --is-head
```
usage: ScanBak.py [-h] [-u URL] [-f FILE] [-p PROCESSES] [-t THREAD] [-o OUTPUT] [--timeout TIMEOUT] [--file-size FILE_SIZE] [--is-head [IS_HEAD]]

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     扫描单个目标
  -f FILE, --file FILE  批量扫描
  -p PROCESSES, --processes PROCESSES
                        进程数. 同时处理多少域名. 默认10
  -t THREAD, --thread THREAD
                        内部线程.每个域名同时处理多少检查. 默认5
  -o OUTPUT, --output OUTPUT
                        输出结果文件
  --timeout TIMEOUT     连接超时 默认: 10s
  --file-size FILE_SIZE
                        文件大小, 超过将不进行误报识别: 2m
  --is-head [IS_HEAD]   开启高速模式

```

# LOG
## V1.4
> 过滤空文件
> 
## V1.3
> 修复进程异常退出BUG
> 
## V1.2
> 普通模式识别大文件, 默认超过2m 将不进行相识度识别, 减少不必要的带宽损耗
>
添加:

    页面相识度检查, 进一步降低误报几率  

    对结果进行识别,<html 和 </html> 字符串存在,对该结果认定为误报  

    识别 Content-Length 返回结果默认超过2m 将不对其结果进行相识度识别  
## V1.1
> 添加head请求模式
