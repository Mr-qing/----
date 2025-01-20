import yaml
import os
from src.logger import setup_logger
from src.scheduler import BackupScheduler

def load_config():
    """加载配置文件"""
    config_path = os.path.join('config', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

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

if __name__ == "__main__":
    main() 