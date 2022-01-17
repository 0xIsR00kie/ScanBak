# ScanBak
备份文件扫描

# 安装
```
git clone https://github.com/0xIsR00kie/ScanBak.git
pip install -r requirements.txt
```

# 使用
```
usage: ScanBak.py [-h] [-u URL] [-f FILE] [-p PROCESSES] [-t THREAD] [-o OUTPUT]

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

```