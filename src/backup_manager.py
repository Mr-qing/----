import os
import time
from typing import Dict
import logging
from .sftp_client import SFTPClient

class BackupManager:
    def __init__(self, servers_config: Dict, task_config: Dict):
        self.servers = servers_config
        self.task_config = task_config
        self.logger = logging.getLogger(__name__)
        self.backup_stats = {
            'start_time': None,
            'end_time': None,
            'total_files': 0,
            'total_size': 0,
            'success_files': 0,
            'failed_files': 0,
            'skipped_files': 0
        }
        
    def _reset_stats(self):
        """重置统计信息"""
        self.backup_stats = {
            'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': None,
            'total_files': 0,
            'total_size': 0,
            'success_files': 0,
            'failed_files': 0,
            'skipped_files': 0
        }
        
    def _log_backup_summary(self, task_name: str):
        """记录备份任务的总结信息"""
        self.backup_stats['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        summary = [
            "-" * 50,
            f"备份任务总结 - {task_name}",
            f"开始时间: {self.backup_stats['start_time']}",
            f"结束时间: {self.backup_stats['end_time']}",
            f"总文件数: {self.backup_stats['total_files']}",
            f"总大小: {self._format_size(self.backup_stats['total_size'])}",
            f"成功: {self.backup_stats['success_files']} 个文件",
            f"失败: {self.backup_stats['failed_files']} 个文件",
            f"跳过: {self.backup_stats['skipped_files']} 个文件（已是最新）",
            "-" * 50
        ]
        
        # 确保每行都被记录
        for line in summary:
            self.logger.info(line)
        
    def execute_backup(self, task_name: str) -> bool:
        """执行指定的备份任务"""
        self._reset_stats()  # 重置统计信息
        self.logger.debug(f"开始执行备份任务: {task_name}")
        task = self.task_config.get(task_name)
        if not task:
            self.logger.error(f"任务配置不存在: {task_name}")
            return False
            
        target_server = self.servers.get(task['target_server'])
        
        self.logger.debug(f"目标服务器信息: {task['target_server']}")
        
        if not target_server:
            self.logger.error(f"目标服务器配置不存在: target={task['target_server']}")
            return False
            
        retry_count = 0
        max_retries = task.get('retry_times', 3)
        retry_interval = task.get('retry_interval', 300)
        
        success = False
        while retry_count < max_retries:
            try:
                self.logger.debug(f"尝试执行备份 (第{retry_count + 1}次)")
                success = self._perform_backup(
                    task_name,
                    target_server,
                    task['source_path'],
                    task['target_path']
                )
                if success:
                    self.logger.info(f"备份任务 {task_name} 执行成功")
                    break
                    
            except Exception as e:
                self.logger.error(f"备份失败: {str(e)}", exc_info=True)
                
            retry_count += 1
            if retry_count < max_retries:
                self.logger.info(f"将在 {retry_interval} 秒后重试...")
                time.sleep(retry_interval)
        
        # 记录备份总结
        self._log_backup_summary(task_name)
        return success
        
    def _perform_backup(self, task_name: str, target: Dict, 
                       source_path: str, target_path: str) -> bool:
        """执行实际的备份操作"""
        # 创建SFTP客户端
        sftp_client = SFTPClient(
            host=target['host'],
            port=target['port'],
            username=target['username'],
            password=target.get('password'),
            key_file=target.get('key_file')
        )
        
        try:
            # 检查源文件是否存在
            if not os.path.exists(source_path):
                self.logger.error(f"源路径不存在: {source_path}")
                return False
                
            # 如果源路径是目录，则进行递归备份
            if os.path.isdir(source_path):
                return self._backup_directory(sftp_client, source_path, target_path)
            else:
                return self._backup_file(sftp_client, source_path, target_path)
                
        finally:
            sftp_client.close()
            
    def _backup_directory(self, sftp_client: SFTPClient, 
                         source_dir: str, target_dir: str) -> bool:
        """递归备份整个目录"""
        success = True
        total_files = 0
        success_files = 0
        
        self.logger.info(f"开始备份目录: {source_dir} -> {target_dir}")
        
        for root, dirs, files in os.walk(source_dir):
            # 计算目标路径
            relative_path = os.path.relpath(root, source_dir)
            current_target_dir = os.path.join(target_dir, relative_path)
            
            # 备份文件
            for file in files:
                total_files += 1
                source_file = os.path.join(root, file)
                target_file = os.path.join(current_target_dir, file)
                if self._backup_file(sftp_client, source_file, target_file):
                    success_files += 1
                else:
                    success = False
        
        if success:
            self.logger.info(f"目录备份完成: {source_dir}")
            self.logger.info(f"成功备份 {success_files}/{total_files} 个文件")
        else:
            self.logger.warning(f"目录部分备份完成: {source_dir}")
            self.logger.warning(f"成功备份 {success_files}/{total_files} 个文件，有文件备份失败")
                    
        return success
        
    def _backup_file(self, sftp_client: SFTPClient, 
                     source_file: str, target_file: str) -> bool:
        """备份单个文件"""
        try:
            file_size = os.path.getsize(source_file)
            self.backup_stats['total_files'] += 1
            self.backup_stats['total_size'] += file_size
            
            self.logger.debug(f"开始备份文件: {source_file} ({self._format_size(file_size)})")
            
            result = sftp_client.upload_file(source_file, target_file)
            
            if result:
                if sftp_client.last_skipped:  # 需要在SFTPClient中添加此属性
                    self.backup_stats['skipped_files'] += 1
                    self.logger.debug(f"文件跳过: {source_file} -> {target_file}")
                else:
                    self.backup_stats['success_files'] += 1
                    self.logger.info(f"文件备份成功: {source_file} -> {target_file} ({self._format_size(file_size)})")
            else:
                self.backup_stats['failed_files'] += 1
                
            return result
            
        except Exception as e:
            self.backup_stats['failed_files'] += 1
            self.logger.error(f"文件备份失败: {source_file}: {str(e)}")
            return False
            
    def _format_size(self, size_in_bytes):
        """格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.2f} PB" 