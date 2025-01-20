import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Dict

def setup_logger(config: Dict) -> logging.Logger:
    """配置日志系统"""
    # 创建日志目录
    log_file = config.get('file', 'logs/backup.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger()  # 使用root logger
    logger.setLevel(config.get('level', 'INFO'))
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 文件处理器 - 支持日志轮转
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    
    # 设置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 设置处理器的日志级别
    file_handler.setLevel(config.get('level', 'INFO'))
    console_handler.setLevel(config.get('level', 'INFO'))
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 