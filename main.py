import yaml
import os
import sys
from src.logger import setup_logger
from src.scheduler import BackupScheduler
from src.web_app import create_app

def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller打包后的路径
        base_path = sys._MEIPASS
    else:
        # 开发环境路径
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_config():
    """加载配置文件"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'config', 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        raise

def main():
    # 加载配置
    config = load_config()
    
    # 设置日志
    logger = setup_logger(config['logging'])
    logger.info("Starting backup system")
    
    try:
        # 创建并启动调度器
        scheduler = BackupScheduler(config)
        scheduler.setup_schedules()
        scheduler.run()
    except KeyboardInterrupt:
        logger.info("Backup system stopped by user")
    except Exception as e:
        logger.error(f"Backup system error: {str(e)}")
        raise

if __name__ == '__main__':
    # 设置工作目录为exe所在目录
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    
    app = create_app()
    app.run(host='0.0.0.0', port=5000) 