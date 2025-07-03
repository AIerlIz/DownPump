#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import random
import logging
import requests
import yaml
from datetime import datetime, timedelta
from tqdm import tqdm
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("downpump.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DownPump')

class DownPump:
    def __init__(self, config_path='config.yaml'):
        self.config_path = config_path
        self.config = self.load_config()
        self.scheduler = BackgroundScheduler()
        self.today_downloaded = 0  # 今日已下载流量(字节)
        self.current_download_task = None
        self.initialize()

    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"配置加载成功: {config}")
                return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)

    def initialize(self):
        """初始化下载器和调度器"""
        # 不再需要创建下载目录，因为我们不写入文件
        
        # 创建日志目录
        os.makedirs('logs', exist_ok=True)
        
        # 重置每日下载量计数器
        self.reset_daily_counter()
        
        # 设置定时任务
        self.setup_scheduler()
        
        # 设置流量记录定时任务
        self.setup_traffic_record()
        
        # 程序启动时记录一次初始流量
        self.record_traffic()
        
        logger.info("DownPump 初始化完成")

    def reset_daily_counter(self):
        """重置每日下载计数器"""
        # 记录重置前的最终流量
        logger.info(f"重置每日下载计数器，之前已下载: {self.today_downloaded / (1024 * 1024):.2f} MB")
        self.record_traffic(message="重置前最终流量")
        
        # 重置计数器
        self.today_downloaded = 0
        logger.info("每日下载计数器已重置")
        
        # 记录重置后的初始流量
        self.record_traffic(message="重置后初始流量")
        
    def setup_traffic_record(self):
        """设置流量记录定时任务"""
        # 获取记录间隔，默认60秒
        interval = self.config.get('record_interval_seconds', 60)
        
        # 添加定时记录任务
        self.scheduler.add_job(
            self.record_traffic,
            'interval',
            seconds=interval,
            id='traffic_record'
        )
        
        logger.info(f"已设置流量记录任务，间隔: {interval}秒")
    
    def record_traffic(self, message=None):
        """记录当日已下载流量到文件
        
        Args:
            message: 可选的附加消息，用于在特殊情况下添加说明
        """
        # 获取当前日期作为文件名
        date_str = datetime.now().strftime('%Y%m%d')
        file_path = os.path.join('logs', f'traffic_{date_str}.log')
        
        # 获取当前时间
        time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 计算已下载流量（MB和GB）
        downloaded_mb = self.today_downloaded / (1024 * 1024)
        downloaded_gb = downloaded_mb / 1024
        
        # 构建记录内容
        log_content = f"{time_str} - 已下载: {downloaded_mb:.2f} MB ({downloaded_gb:.2f} GB)"
        if message:
            log_content += f" - {message}"
        
        # 记录到文件
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(log_content + "\n")
        
        logger.debug(f"已记录流量: {downloaded_mb:.2f} MB ({downloaded_gb:.2f} GB)" + (f" - {message}" if message else ""))


    def setup_scheduler(self):
        """设置定时任务"""
        # 添加每日重置计数器的任务 (每天凌晨00:00)
        self.scheduler.add_job(
            self.reset_daily_counter,
            CronTrigger(hour=0, minute=0),
            id='reset_counter'
        )
        
        # 添加下载时间段的任务
        self.schedule_download_tasks()
        
        # 启动调度器
        self.scheduler.start()
        logger.info("调度器已启动")

    def schedule_download_tasks(self):
        """根据配置的时间段安排下载任务"""
        time_ranges = self.config.get('download_time_ranges', [])
        
        if not time_ranges:
            # 如果没有配置时间段，则全天候下载
            logger.info("未配置下载时间段，将全天候下载")
            self.start_download()
            return
        
        # 清除之前的下载任务
        for job in self.scheduler.get_jobs():
            if job.id.startswith('download_'):
                self.scheduler.remove_job(job.id)
        
        # 为每个时间段添加开始和结束任务
        for i, time_range in enumerate(time_ranges):
            start_time = time_range.get('start')
            end_time = time_range.get('end')
            
            if not start_time or not end_time:
                logger.warning(f"时间段 {i+1} 配置不完整，已跳过")
                continue
            
            # 解析时间
            start_hour, start_minute = map(int, start_time.split(':'))
            end_hour, end_minute = map(int, end_time.split(':'))
            
            # 添加开始下载的任务
            self.scheduler.add_job(
                self.start_download,
                CronTrigger(hour=start_hour, minute=start_minute),
                id=f'download_start_{i}'
            )
            
            # 添加结束下载的任务
            self.scheduler.add_job(
                self.stop_download,
                CronTrigger(hour=end_hour, minute=end_minute),
                id=f'download_end_{i}'
            )
            
            logger.info(f"已添加下载时间段: {start_time} - {end_time}")
        
        # 检查当前是否在下载时间段内，如果是则立即开始下载
        if self.is_download_time():
            logger.info("当前时间在下载时间段内，立即开始下载")
            self.start_download()
        else:
            # 计算下一个下载时间点并立即安排
            self.schedule_next_download()

    def schedule_next_download(self):
        """计算并安排下一个下载时间点的任务"""
        time_ranges = self.config.get('download_time_ranges', [])
        if not time_ranges:
            return
        
        now = datetime.now()
        next_start_time = None
        
        # 查找今天剩余时间内最近的开始时间
        for time_range in time_ranges:
            start_time = time_range.get('start')
            if not start_time:
                continue
                
            start_hour, start_minute = map(int, start_time.split(':'))
            start_datetime = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            
            if start_datetime > now:
                if next_start_time is None or start_datetime < next_start_time:
                    next_start_time = start_datetime
        
        # 如果今天没有更多的开始时间，查找明天的第一个开始时间
        if next_start_time is None and time_ranges:
            tomorrow = now + timedelta(days=1)
            earliest_start = None
            
            for time_range in time_ranges:
                start_time = time_range.get('start')
                if not start_time:
                    continue
                    
                start_hour, start_minute = map(int, start_time.split(':'))
                start_datetime = tomorrow.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                
                if earliest_start is None or start_datetime < earliest_start:
                    earliest_start = start_datetime
            
            next_start_time = earliest_start
        
        # 安排下一次下载任务
        if next_start_time:
            logger.info(f"下一次下载将在 {next_start_time} 开始")
            # 如果当前没有正在运行的下载任务，则创建一个定时任务
            if self.current_download_task is None:
                self.scheduler.add_job(
                    self.start_download,
                    'date',
                    run_date=next_start_time,
                    id='next_download'
                )

    def is_download_time(self):
        """检查当前是否在配置的下载时间段内"""
        time_ranges = self.config.get('download_time_ranges', [])
        
        # 如果没有配置时间段，则认为全天都可以下载
        if not time_ranges:
            return True
        
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        
        for time_range in time_ranges:
            start_time = time_range.get('start')
            end_time = time_range.get('end')
            
            if not start_time or not end_time:
                continue
            
            # 处理跨天的情况
            if start_time <= end_time:
                if start_time <= current_time <= end_time:
                    return True
            else:  # 跨天情况 (例如 23:00-06:00)
                if current_time >= start_time or current_time <= end_time:
                    return True
        
        return False

    def start_download(self):
        """开始下载任务"""
        # 检查是否已达到每日下载上限
        if self.check_daily_limit():
            logger.info("已达到每日下载上限，停止下载")
            self.schedule_next_download()
            return
        
        # 检查是否在允许的下载时间段内
        if not self.is_download_time():
            logger.info("当前不在下载时间段内，停止下载")
            self.schedule_next_download()
            return
        
        # 开始下载
        logger.info("开始下载任务")
        self.download()

    def stop_download(self):
        """停止当前下载任务"""
        if self.current_download_task:
            logger.info("停止当前下载任务")
            self.current_download_task = None
        
        # 安排下一次下载
        self.schedule_next_download()

    def check_daily_limit(self):
        """检查是否达到每日下载上限"""
        daily_limit_gb = self.config.get('daily_limit_gb', 0)
        
        # 如果没有设置限制或限制为0，则不限制
        if daily_limit_gb <= 0:
            return False
        
        # 转换为字节进行比较
        daily_limit_bytes = daily_limit_gb * 1024 * 1024 * 1024
        
        return self.today_downloaded >= daily_limit_bytes

    def get_random_url(self):
        """从配置的URL列表中随机选择一个"""
        urls = self.config.get('download_urls', [])
        if not urls:
            logger.error("未配置下载URL")
            return None
        
        return random.choice(urls)

    def download(self):
        """执行下载任务"""
        # 获取随机URL
        url = self.get_random_url()
        if not url:
            logger.error("无法获取下载URL，下载任务终止")
            return
        
        # 获取限速设置 (MB/s)
        speed_limit_mb = self.config.get('speed_limit_mb', 0)
        chunk_size = 1024 * 1024  # 1MB 块大小
        
        # 计算每秒最大下载块数
        max_chunks_per_second = max(1, speed_limit_mb)
        
        # 设置下载任务标识
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        download_id = f"download_{timestamp}"
        
        try:
            # 标记当前任务
            self.current_download_task = url
            
            # 开始下载
            logger.info(f"开始下载: {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 获取文件大小（如果服务器提供）
            total_size = int(response.headers.get('content-length', 0))
            
            # 创建进度条
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"下载流量消耗 - {url}") as pbar:
                downloaded_this_second = 0
                second_start_time = time.time()
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    # 检查是否应该停止下载
                    if self.current_download_task is None:
                        logger.info("下载任务被中断")
                        break
                    
                    # 检查是否达到每日下载上限
                    if self.check_daily_limit():
                        logger.info("已达到每日下载上限，停止当前下载")
                        self.current_download_task = None
                        break
                    
                    # 检查是否在允许的下载时间段内
                    if not self.is_download_time():
                        logger.info("当前不在下载时间段内，停止当前下载")
                        self.current_download_task = None
                        break
                    
                    # 只计算数据大小，不写入磁盘
                    if chunk:
                        chunk_size = len(chunk)
                        self.today_downloaded += chunk_size
                        pbar.update(chunk_size)
                        downloaded_this_second += chunk_size
                        
                        # 限速逻辑
                        if speed_limit_mb > 0:
                            current_time = time.time()
                            elapsed = current_time - second_start_time
                            
                            # 如果这一秒内下载的数据超过限制
                            if downloaded_this_second >= speed_limit_mb * 1024 * 1024:
                                # 如果一秒还没过完，则等待剩余时间
                                if elapsed < 1.0:
                                    time.sleep(1.0 - elapsed)
                                
                                # 重置计数器和时间
                                downloaded_this_second = 0
                                second_start_time = time.time()
            
            # 下载完成后记录一次流量
            self.record_traffic()
            
            # 下载完成后，检查是否达到每日下载上限
            if self.check_daily_limit():
                logger.info(f"下载完成: {download_id}，已达到每日下载上限")
                self.current_download_task = None
                # 安排下一次下载
                self.schedule_next_download()
            else:
                # 如果未达到上限且仍在下载时间段内，继续下载
                if self.is_download_time():
                    logger.info(f"下载完成: {download_id}，继续下载下一个文件")
                    self.download()
                else:
                    logger.info(f"下载完成: {download_id}，当前不在下载时间段内，停止下载")
                    self.current_download_task = None
                    # 安排下一次下载
                    self.schedule_next_download()
        
        except Exception as e:
            logger.error(f"下载出错: {e}")
            # 出错后等待一段时间再重试
            time.sleep(10)
            # 如果仍在下载时间段内且未达到上限，则重试
            if self.is_download_time() and not self.check_daily_limit():
                self.download()
            else:
                self.current_download_task = None
                self.schedule_next_download()

def main():
    """主函数"""
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'
    downpump = DownPump(config_path)
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        downpump.scheduler.shutdown()

if __name__ == "__main__":
    main()