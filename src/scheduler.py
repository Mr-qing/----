import schedule
import time
from typing import Dict
import logging
from src.backup_manager import BackupManager

class BackupScheduler:
    def __init__(self, config: Dict):
        self.config = config
        self.backup_manager = BackupManager(
            config['servers'],
            config['backup_tasks']
        )
        self.logger = logging.getLogger(__name__)
        # 添加任务运行状态跟踪
        self.running_tasks = set()
        
    def _run_backup_task(self, task_name: str):
        """运行备份任务"""
        # 检查任务是否已在运行
        if task_name in self.running_tasks:
            self.logger.warning(f"任务 {task_name} 正在执行中，跳过本次执行")
            return
            
        try:
            # 标记任务开始运行
            self.running_tasks.add(task_name)
            
            self.logger.info("=" * 50)
            self.logger.info(f"开始执行调度任务: {task_name}")
            self.logger.info(f"执行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            success = self.backup_manager.execute_backup(task_name)
            
            if success:
                self.logger.info(f"调度任务 {task_name} 执行成功")
            else:
                self.logger.error(f"调度任务 {task_name} 执行失败")
            self.logger.info("=" * 50)
            
        except Exception as e:
            self.logger.error(f"执行任务 {task_name} 时发生错误: {str(e)}", exc_info=True)
        finally:
            # 任务完成后移除运行标记
            self.running_tasks.discard(task_name)
    
    def is_backup_running(self) -> bool:
        """检查是否有备份任务正在运行"""
        return len(self.running_tasks) > 0
        
    def setup_schedules(self):
        """设置所有备份任务的调度"""
        for task_name, task_config in self.config['backup_tasks'].items():
            schedule_str = task_config.get('schedule')
            if not schedule_str:
                self.logger.warning(f"任务 {task_name} 未配置调度时间")
                continue
                
            try:
                # 解析调度表达式
                parts = schedule_str.split()
                
                # 处理 */n 格式（每n分钟执行一次）
                if len(parts) == 1 and parts[0].startswith('*/'):
                    try:
                        interval = int(parts[0][2:])
                        self.logger.debug(f"设置任务 {task_name} 为每 {interval} 分钟执行一次")
                        schedule.every(interval).minutes.do(self._run_backup_task, task_name)
                    except ValueError:
                        self.logger.error(f"无效的分钟间隔值: {parts[0]}")
                        continue
                
                # 处理 HH:MM 格式（每天特定时间执行）
                elif len(parts) == 1 and ':' in parts[0]:
                    time_str = parts[0]
                    self.logger.debug(f"设置任务 {task_name} 为每天 {time_str} 执行")
                    schedule.every().day.at(time_str).do(self._run_backup_task, task_name)
                
                # 处理 MM HH 格式（每天特定时间执行）
                elif len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    minute, hour = parts
                    time_str = f"{hour.zfill(2)}:{minute.zfill(2)}"
                    self.logger.debug(f"设置任务 {task_name} 为每天 {time_str} 执行")
                    schedule.every().day.at(time_str).do(self._run_backup_task, task_name)
                
                # 处理 HH:MM W 格式（每周特定时间执行）
                elif len(parts) == 2 and ':' in parts[0] and parts[1].isdigit():
                    time_str, weekday = parts
                    weekday = int(weekday)
                    if 0 <= weekday <= 6:
                        self.logger.debug(f"设置任务 {task_name} 为每周{weekday}的 {time_str} 执行")
                        getattr(schedule.every(), ['monday', 'tuesday', 'wednesday', 
                                'thursday', 'friday', 'saturday', 'sunday'][weekday]
                        ).at(time_str).do(self._run_backup_task, task_name)
                    else:
                        self.logger.error(f"无效的星期值: {weekday}")
                        continue
                
                # 处理 */n h-h 格式（在特定小时范围内每n分钟执行）
                elif len(parts) == 2 and parts[0].startswith('*/') and '-' in parts[1]:
                    interval_str, hours = parts
                    try:
                        interval = int(interval_str[2:])
                        start_hour, end_hour = map(int, hours.split('-'))
                        if 0 <= start_hour <= 23 and 0 <= end_hour <= 23:
                            self.logger.debug(f"设置任务 {task_name} 为在 {start_hour}:00-{end_hour}:00 之间每 {interval} 分钟执行一次")
                            job = schedule.every(interval).minutes
                            job.do(self._run_backup_task, task_name)
                            # 添加时间范围限制
                            job.at(f"{start_hour:02d}:00").until(f"{end_hour:02d}:00")
                        else:
                            self.logger.error(f"无效的小时范围: {hours}")
                            continue
                    except ValueError:
                        self.logger.error(f"无效的时间范围格式: {schedule_str}")
                        continue
                
                else:
                    self.logger.error(f"不支持的调度格式: {schedule_str}")
                    continue
                
                self.logger.info(f"成功设置任务 {task_name} 的调度: {schedule_str}")
                
            except Exception as e:
                self.logger.error(f"设置任务 {task_name} 的调度失败: {str(e)}", exc_info=True)
    
    def run(self):
        """运行调度器"""
        self.logger.info("启动备份调度器")
        self.logger.info("等待执行调度任务...")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(7200)  # 每7200秒（2小时）检查一次待执行的任务
            except Exception as e:
                self.logger.error(f"调度器运行出错: {str(e)}", exc_info=True)
                time.sleep(5)  # 发生错误时等待5秒后继续 