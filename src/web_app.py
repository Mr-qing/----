from flask import Flask, render_template, jsonify, request
import yaml
import os
import threading
from .scheduler import BackupScheduler
from .logger import setup_logger
from .history import get_history, backup_history  # 从history模块导入
import time

app = Flask(__name__)
scheduler = None
config = None

def load_config():
    """加载配置文件"""
    config_path = os.path.join('config', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def run_scheduler():
    """在后台线程运行调度器"""
    global scheduler
    scheduler.run()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html', 
                         tasks=config['backup_tasks'],
                         servers=config['servers'])

@app.route('/api/tasks')
def get_tasks():
    """获取所有任务"""
    return jsonify(config['backup_tasks'])

@app.route('/api/servers')
def get_servers():
    """获取所有服务器"""
    return jsonify(config['servers'])

@app.route('/api/logs')
def get_logs():
    """获取最新的日志"""
    log_file = config['logging']['file']
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = f.readlines()[-100:]  # 获取最后100行
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/run_backup', methods=['POST'])
def run_backup():
    """手动触发备份任务"""
    task_name = request.json.get('task_name')
    if not task_name or task_name not in config['backup_tasks']:
        return jsonify({'success': False, 'message': '无效的任务名称'})
    
    try:
        success = scheduler.backup_manager.execute_backup(task_name)
        return jsonify({
            'success': success,
            'message': '备份任务执行成功' if success else '备份任务执行失败'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/servers/add', methods=['POST'])
def add_server():
    """添加新服务器"""
    try:
        server_data = request.json
        if not all(k in server_data for k in ['name', 'host', 'port', 'username']):
            return jsonify({'success': False, 'message': '缺少必要的服务器信息'})
            
        # 加载当前配置
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            current_config = yaml.safe_load(f)
            
        # 检查服务器名是否已存在
        if server_data['name'] in current_config['servers']:
            return jsonify({'success': False, 'message': '服务器名称已存在'})
            
        # 添加新服务器
        current_config['servers'][server_data['name']] = {
            'host': server_data['host'],
            'port': int(server_data['port']),
            'username': server_data['username'],
            'password': server_data.get('password', '')
        }
        
        # 保存配置
        with open('config/config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(current_config, f, allow_unicode=True)
            
        return jsonify({'success': True, 'message': '服务器添加成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/servers/edit', methods=['POST'])
def edit_server():
    """编辑服务器信息"""
    try:
        server_data = request.json
        if not all(k in server_data for k in ['name', 'host', 'port', 'username']):
            return jsonify({'success': False, 'message': '缺少必要的服务器信息'})
            
        # 加载当前配置
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            current_config = yaml.safe_load(f)
            
        # 更新服务器信息
        current_config['servers'][server_data['name']] = {
            'host': server_data['host'],
            'port': int(server_data['port']),
            'username': server_data['username'],
            'password': server_data.get('password', '')
        }
        
        # 保存配置
        with open('config/config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(current_config, f, allow_unicode=True)
            
        return jsonify({'success': True, 'message': '服务器信息更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/servers/delete', methods=['POST'])
def delete_server():
    """删除服务器"""
    try:
        server_name = request.json.get('name')
        if not server_name:
            return jsonify({'success': False, 'message': '未指定服务器名称'})
            
        # 加载当前配置
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            current_config = yaml.safe_load(f)
            
        # 检查服务器是否在使用中
        for task in current_config['backup_tasks'].values():
            if task['target_server'] == server_name:
                return jsonify({
                    'success': False, 
                    'message': '该服务器正在被备份任务使用，无法删除'
                })
                
        # 删除服务器
        if server_name in current_config['servers']:
            del current_config['servers'][server_name]
            
            # 保存配置
            with open('config/config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(current_config, f, allow_unicode=True)
                
            return jsonify({'success': True, 'message': '服务器删除成功'})
        else:
            return jsonify({'success': False, 'message': '服务器不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/servers/test', methods=['POST'])
def test_server():
    """测试服务器连接"""
    try:
        server_data = request.json
        if not all(k in server_data for k in ['host', 'port', 'username']):
            return jsonify({'success': False, 'message': '缺少必要的服务器信息'})
            
        # 创建临时SFTP客户端测试连接
        from .sftp_client import SFTPClient
        client = SFTPClient(
            host=server_data['host'],
            port=int(server_data['port']),
            username=server_data['username'],
            password=server_data.get('password', '')
        )
        
        success = client.connect()
        client.close()
        
        if success:
            return jsonify({'success': True, 'message': '服务器连接测试成功'})
        else:
            return jsonify({'success': False, 'message': '服务器连接测试失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器连接测试失败: {str(e)}'})

@app.route('/api/tasks/add', methods=['POST'])
def add_task():
    """添加新备份任务"""
    try:
        task_data = request.json
        if not all(k in task_data for k in ['name', 'source_path', 'target_server', 'target_path', 'schedule']):
            return jsonify({'success': False, 'message': '缺少必要的任务信息'})
            
        # 加载当前配置
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            current_config = yaml.safe_load(f)
            
        # 检查任务名是否已存在
        if task_data['name'] in current_config['backup_tasks']:
            return jsonify({'success': False, 'message': '任务名称已存在'})
            
        # 检查目标服务器是否存在
        if task_data['target_server'] not in current_config['servers']:
            return jsonify({'success': False, 'message': '目标服务器不存在'})
            
        # 添加新任务
        current_config['backup_tasks'][task_data['name']] = {
            'source_path': task_data['source_path'],
            'target_server': task_data['target_server'],
            'target_path': task_data['target_path'],
            'schedule': task_data['schedule'],
            'retry_times': task_data.get('retry_times', 3),
            'retry_interval': task_data.get('retry_interval', 30)
        }
        
        # 保存配置
        with open('config/config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(current_config, f, allow_unicode=True)
            
        # 重新加载调度器
        scheduler.setup_schedules()
            
        return jsonify({'success': True, 'message': '任务添加成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/tasks/edit', methods=['POST'])
def edit_task():
    """编辑备份任务"""
    try:
        task_data = request.json
        if not all(k in task_data for k in ['name', 'source_path', 'target_server', 'target_path', 'schedule']):
            return jsonify({'success': False, 'message': '缺少必要的任务信息'})
            
        # 加载当前配置
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            current_config = yaml.safe_load(f)
            
        # 检查目标服务器是否存在
        if task_data['target_server'] not in current_config['servers']:
            return jsonify({'success': False, 'message': '目标服务器不存在'})
            
        # 更新任务信息
        current_config['backup_tasks'][task_data['name']] = {
            'source_path': task_data['source_path'],
            'target_server': task_data['target_server'],
            'target_path': task_data['target_path'],
            'schedule': task_data['schedule'],
            'retry_times': task_data.get('retry_times', 3),
            'retry_interval': task_data.get('retry_interval', 30)
        }
        
        # 保存配置
        with open('config/config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(current_config, f, allow_unicode=True)
            
        # 重新加载调度器
        scheduler.setup_schedules()
            
        return jsonify({'success': True, 'message': '任务更新成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/tasks/delete', methods=['POST'])
def delete_task():
    """删除备份任务"""
    try:
        task_name = request.json.get('name')
        if not task_name:
            return jsonify({'success': False, 'message': '未指定任务名称'})
            
        # 加载当前配置
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            current_config = yaml.safe_load(f)
            
        # 删除任务
        if task_name in current_config['backup_tasks']:
            del current_config['backup_tasks'][task_name]
            
            # 保存配置
            with open('config/config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(current_config, f, allow_unicode=True)
                
            # 重新加载调度器
            scheduler.setup_schedules()
                
            return jsonify({'success': True, 'message': '任务删除成功'})
        else:
            return jsonify({'success': False, 'message': '任务不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/history')
def get_history_api():
    """获取备份历史记录"""
    return jsonify(get_history())

@app.route('/api/stats')
def get_stats():
    """获取备份统计信息"""
    stats = {
        'total_backups': len(backup_history),
        'success_rate': 0,
        'total_files': 0,
        'total_size': 0,
        'daily_stats': {},
        'task_stats': {}
    }
    
    if backup_history:
        success_count = sum(1 for record in backup_history if record['success'])
        stats['success_rate'] = (success_count / len(backup_history)) * 100
        
        # 按日期统计
        from datetime import datetime, timedelta
        today = datetime.now().date()
        for i in range(7):  # 最近7天
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            stats['daily_stats'][date] = {
                'total': 0,
                'success': 0,
                'failed': 0
            }
            
        # 统计每个任务的情况
        for record in backup_history:
            # 更新任务统计
            if record['task_name'] not in stats['task_stats']:
                stats['task_stats'][record['task_name']] = {
                    'total': 0,
                    'success': 0,
                    'failed': 0
                }
            task_stat = stats['task_stats'][record['task_name']]
            task_stat['total'] += 1
            if record['success']:
                task_stat['success'] += 1
            else:
                task_stat['failed'] += 1
                
            # 更新日期统计
            date = datetime.strptime(record['time'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            if date in stats['daily_stats']:
                day_stat = stats['daily_stats'][date]
                day_stat['total'] += 1
                if record['success']:
                    day_stat['success'] += 1
                else:
                    day_stat['failed'] += 1
    
    return jsonify(stats)

def create_app():
    """创建并配置Flask应用"""
    global config, scheduler
    
    # 加载配置
    config = load_config()
    
    # 设置日志
    logger = setup_logger(config['logging'])
    
    # 创建调度器
    scheduler = BackupScheduler(config)
    scheduler.setup_schedules()
    
    # 启动调度器线程
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    return app 