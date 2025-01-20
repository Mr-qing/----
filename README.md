# 自动备份系统

基于 Python + Flask 的自动化备份工具，支持通过 SFTP 将本地文件定时备份到远程服务器或服务器之间互相备份，并提供 Web 界面进行可视化管理。

## 功能特点

- 🔄 支持多任务定时备份
- 📊 可视化的 Web 管理界面
- 🔐 支持密码认证方式
- 📈 备份历史和统计图表
- 📝 详细的日志记录

## 系统要求

- Python 3.8+
- Windows 操作系统
- 2GB+ 内存
- 500MB+ 磁盘空间

## 快速开始

### 方式一：开发环境运行

1. 安装依赖：
bash
pip install -r requirements.txt

2. 修改配置文件 `config/config.yaml`：

```yaml
servers:
  server1:
    host: "192.168.1.100"
    port: 22
    username: "your_username"
    password: "your_password"

backup_tasks:
  task1:
    source_path: "C:/backup_source"  # 本地源目录
    target_server: "server1"         # 目标服务器
    target_path: "/backup"           # 远程目标目录
    schedule: "*/30 * * * *"         # 每30分钟执行
    retry_times: 3                   # 失败重试次数
    retry_interval: 30               # 重试间隔(秒)
```

3. 运行程序：

```bash
python main.py
```

### 方式二：打包使用

1. 运行打包脚本：

```bash
build.bat
```

2. 打包完成后，在 `release` 目录中找到可执行程序
3. 修改 `config/config.yaml` 配置文件
4. 运行 `start.bat` 启动程序

## 项目结构

```
backup-system/
├── config/                 # 配置文件目录
│   └── config.yaml        # 主配置文件
├── logs/                  # 日志目录
│   ├── backup.log        # 运行日志
│   └── backup_history.json # 备份历史
├── src/                   # 源代码目录
│   ├── static/           # 静态资源
│   │   └── css/         # CSS样式文件
│   └── templates/        # 页面模板
│       └── index.html   # 主页面
├── main.py               # 主程序
├── build.bat             # 打包脚本
└── requirements.txt      # 依赖清单
```

## Web 界面

启动后访问 `http://localhost:5000` 进入管理界面：

- 任务管理：添加、编辑、删除备份任务
- 服务器管理：配置远程服务器信息
- 备份历史：查看备份执行记录
- 统计图表：查看备份成功率等统计信息

## 调度表达式说明

支持 Cron 格式的调度表达式：
- `*/n * * * *`: 每 n 分钟执行
- `0 * * * *`: 每小时执行
- `0 0 * * *`: 每天零点执行
- `30 1 * * *`: 每天1:30执行

## 依赖列表

主要依赖包括：
- Flask 3.0.0
- Paramiko 3.4.0
- PyYAML 6.0.1
- Schedule 1.2.0
- Cryptography >= 41.0.0
- PyInstaller 6.3.0 (打包用)

## 注意事项

1. 首次使用请修改配置文件中的服务器信息
2. 确保本地和远程目录有足够的磁盘空间
3. 定期检查日志文件大小
4. 建议不同任务的执行时间错开，避免同时执行
5. 请勿删除 logs 目录，否则可能影响程序运行

## 常见问题

1. 如果遇到连接问题，请检查：
   - 服务器地址和端口是否正确
   - 防火墙设置
   - 网络连接状态

2. 备份失败常见原因：
   - 源文件访问权限不足
   - 目标目录空间不足
   - 网络不稳定

## 许可证

MIT License
