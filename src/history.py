import time

# 备份历史记录
backup_history = []

def add_history_record(task_name: str, success: bool, details: str):
    """添加历史记录"""
    backup_history.append({
        'task_name': task_name,
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'success': success,
        'details': details
    })
    # 只保留最近100条记录
    if len(backup_history) > 100:
        backup_history.pop(0)

def get_history():
    """获取历史记录"""
    return backup_history 