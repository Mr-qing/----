import paramiko
import os
from typing import Optional
import logging

class SFTPClient:
    def __init__(self, host: str, port: int, username: str, 
                 password: Optional[str] = None, key_file: Optional[str] = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.ssh = None
        self.sftp = None
        self.logger = logging.getLogger(__name__)
        self.last_skipped = False  # 添加跳过标记

    def connect(self) -> bool:
        """连接到SFTP服务器"""
        try:
            self.logger.debug(f"正在连接到服务器 {self.host}:{self.port}")
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.key_file:
                self.logger.debug("使用密钥文件认证")
                key = paramiko.RSAKey.from_private_key_file(self.key_file)
                self.ssh.connect(self.host, self.port, self.username, pkey=key)
            else:
                self.logger.debug("使用密码认证")
                self.ssh.connect(self.host, self.port, 
                               self.username, self.password)
            
            self.sftp = self.ssh.open_sftp()
            self.logger.info(f"成功连接到服务器 {self.host}")
            return True
            
        except paramiko.AuthenticationException:
            self.logger.error(f"认证失败: 用户名或密码错误 (host={self.host})")
            return False
        except paramiko.SSHException as e:
            self.logger.error(f"SSH连接错误: {str(e)} (host={self.host})")
            return False
        except Exception as e:
            self.logger.error(f"连接失败: {str(e)} (host={self.host})", exc_info=True)
            return False

    def check_remote_file(self, local_path: str, remote_path: str) -> bool:
        """检查远程文件是否需要更新
        
        通过比较文件大小和修改时间来判断是否需要更新
        返回 True 表示需要更新，False 表示不需要更新
        """
        try:
            # 获取本地文件信息
            local_stat = os.stat(local_path)
            local_size = local_stat.st_size
            local_mtime = local_stat.st_mtime
            
            # 获取远程文件信息
            try:
                remote_stat = self.sftp.stat(remote_path)
                remote_size = remote_stat.st_size
                remote_mtime = remote_stat.st_mtime
                
                # 如果远程文件存在，比较大小和修改时间
                if remote_size == local_size and abs(remote_mtime - local_mtime) < 1:
                    self.logger.debug(f"文件无需更新: {local_path} (大小: {self._format_size(local_size)})")
                    return False
                else:
                    self.logger.debug(f"文件需要更新: {local_path} (本地大小: {self._format_size(local_size)}, 远程大小: {self._format_size(remote_size)})")
                    return True
                    
            except FileNotFoundError:
                # 远程文件不存在，需要备份
                self.logger.debug(f"远程文件不存在，需要备份: {remote_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"检查文件状态失败: {str(e)}")
            # 如果检查失败，为安全起见返回 True 进行备份
            return True

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """上传文件到远程服务器"""
        try:
            self.last_skipped = False  # 重置跳过标记
            self.logger.debug(f"准备上传文件: {local_path} -> {remote_path}")
            if not self.sftp:
                self.logger.debug("SFTP连接未建立，尝试重新连接")
                if not self.connect():
                    return False
                    
            # 检查本地文件
            if not os.path.exists(local_path):
                self.logger.error(f"本地文件不存在: {local_path}")
                return False
            
            # 检查是否需要更新
            if not self.check_remote_file(local_path, remote_path):
                self.last_skipped = True  # 设置跳过标记
                self.logger.info(f"文件已是最新版本，跳过: {local_path}")
                return True
            
            # 确保远程目录存在
            remote_dir = os.path.dirname(remote_path)
            try:
                self.logger.debug(f"检查远程目录: {remote_dir}")
                self.sftp.stat(remote_dir)
            except FileNotFoundError:
                self.logger.debug(f"创建远程目录: {remote_dir}")
                self._mkdir_p(remote_dir)

            # 上传文件
            file_size = os.path.getsize(local_path)
            self.logger.debug(f"开始上传文件 ({self._format_size(file_size)}): {local_path}")
            self.sftp.put(local_path, remote_path)
            
            # 设置远程文件的修改时间与本地文件一致
            local_stat = os.stat(local_path)
            self.sftp.utime(remote_path, (local_stat.st_atime, local_stat.st_mtime))
            
            self.logger.info(f"文件上传成功: {local_path} -> {remote_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"文件上传失败: {str(e)}", exc_info=True)
            return False

    def _mkdir_p(self, remote_directory):
        """递归创建远程目录"""
        if remote_directory == '/':
            return
        try:
            self.sftp.stat(remote_directory)
        except IOError:
            parent = os.path.dirname(remote_directory)
            if parent != '/':
                self._mkdir_p(parent)
            self.sftp.mkdir(remote_directory)

    def _format_size(self, size_in_bytes):
        """格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.2f} PB"

    def close(self):
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close() 