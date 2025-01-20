import os
import json
from typing import List, Dict
import logging

# 历史记录列表
backup_history: List[Dict] = []

# 历史记录文件路径
HISTORY_FILE = os.path.join('logs', 'backup_history.json')

def load_history():
    """加载历史记录"""
    global backup_history
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                backup_history = json.load(f)
    except Exception as e:
        logging.error(f"加载历史记录失败: {str(e)}")
        backup_history = []

def save_history():
    """保存历史记录"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(backup_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"保存历史记录失败: {str(e)}")

def add_history_record(task_name: str, success: bool, details: str):
    """添加历史记录"""
    from datetime import datetime
    record = {
        'task_name': task_name,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'success': success,
        'details': details
    }
    backup_history.append(record)
    save_history()

def get_history() -> List[Dict]:
    """获取历史记录"""
    return backup_history

# 初始化时加载历史记录
load_history() 