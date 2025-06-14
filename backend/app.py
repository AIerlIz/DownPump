#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import logging
import threading
import subprocess
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 配置日志
log_dir = '/app/logs'
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/downpump.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DownPump')

# 初始化Flask应用
app = Flask(__name__, static_folder='/app/frontend')
CORS(app)

# 默认配置
DEFAULT_CONFIG = {
    'download_sources': [
        {
            'name': '测试文件1',
            'url': 'https://speed.hetzner.de/100MB.bin',
            'enabled': True
        },
        {
            'name': '测试文件2',
            'url': 'https://speed.cloudflare.com/100mb.bin',
            'enabled': True
        }
    ],
    'interval_seconds': 60,
    'daily_limit_gb': 0,  # 0表示无限制
    'speed_limit_kbps': 0,  # 0表示无限制
    'active_hours': {
        'enabled': False,
        'start_time': '00:00',
        'end_time': '23:59'
    },
    'enabled': True
}

# 全局变量
config = DEFAULT_CONFIG.copy()
stats = {
    'is_downloading': False,
    'current_download': None,
    'today_downloaded': 0,  # 字节数
    'total_downloaded': 0,  # 字节数
    'download_history': [],
    'last_updated': datetime.now().isoformat()
}
download_process = None
download_thread = None
stop_event = threading.Event()

# 配置文件路径
CONFIG_FILE = '/app/backend/config.json'
STATS_FILE = '/app/backend/stats.json'

# 加载配置
def load_config():
    global config
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                # 合并配置，确保所有必要的字段都存在
                for key, value in DEFAULT_CONFIG.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                config = loaded_config
                logger.info("配置已加载")
        else:
            save_config()
            logger.info("创建了默认配置")
    except Exception as e:
        logger.error(f"加载配置失败: {str(e)}")
        config = DEFAULT_CONFIG.copy()
        save_config()

# 保存配置
def save_config():
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info("配置已保存")
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")

# 加载统计信息
def load_stats():
    global stats
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                loaded_stats = json.load(f)
                # 检查是否是新的一天，如果是则重置today_downloaded
                last_date = datetime.fromisoformat(loaded_stats.get('last_updated', datetime.now().isoformat())).date()
                today = datetime.now().date()
                if last_date < today:
                    loaded_stats['today_downloaded'] = 0
                    # 添加昨天的下载记录到历史
                    if last_date and loaded_stats.get('today_downloaded', 0) > 0:
                        loaded_stats['download_history'].append({
                            'date': last_date.isoformat(),
                            'downloaded': loaded_stats.get('today_downloaded', 0)
                        })
                        # 只保留最近30天的历史
                        if len(loaded_stats['download_history']) > 30:
                            loaded_stats['download_history'] = loaded_stats['download_history'][-30:]
                
                loaded_stats['last_updated'] = datetime.now().isoformat()
                stats = loaded_stats
                logger.info("统计信息已加载")
        else:
            save_stats()
            logger.info("创建了默认统计信息")
    except Exception as e:
        logger.error(f"加载统计信息失败: {str(e)}")
        save_stats()

# 保存统计信息
def save_stats():
    try:
        stats['last_updated'] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=4)
    except Exception as e:
        logger.error(f"保存统计信息失败: {str(e)}")

# 检查是否在活跃时间内
def is_active_time():
    if not config['active_hours']['enabled']:
        return True
    
    now = datetime.now().time()
    start_time = datetime.strptime(config['active_hours']['start_time'], '%H:%M').time()
    end_time = datetime.strptime(config['active_hours']['end_time'], '%H:%M').time()
    
    # 处理跨天的情况
    if start_time <= end_time:
        return start_time <= now <= end_time
    else:  # 例如 22:00 - 06:00
        return now >= start_time or now <= end_time

# 检查是否超过每日流量限制
def is_over_daily_limit():
    if config['daily_limit_gb'] <= 0:  # 无限制
        return False
    
    limit_bytes = config['daily_limit_gb'] * 1024 * 1024 * 1024  # 转换为字节
    return stats['today_downloaded'] >= limit_bytes

# 下载线程函数
def download_thread_func():
    global stats, download_process
    
    while not stop_event.is_set():
        try:
            # 检查是否启用下载
            if not config['enabled']:
                stats['is_downloading'] = False
                stats['current_download'] = None
                save_stats()
                time.sleep(5)
                continue
            
            # 检查是否在活跃时间内
            if not is_active_time():
                logger.info("当前不在活跃时间范围内，暂停下载")
                stats['is_downloading'] = False
                stats['current_download'] = None
                save_stats()
                time.sleep(60)  # 每分钟检查一次
                continue
            
            # 检查是否超过每日流量限制
            if is_over_daily_limit():
                logger.info("已达到每日流量限制，暂停下载")
                stats['is_downloading'] = False
                stats['current_download'] = None
                save_stats()
                # 计算到明天0点的秒数
                now = datetime.now()
                tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                seconds_to_tomorrow = (tomorrow - now).total_seconds()
                # 睡眠到明天0点或至少1分钟
                sleep_time = max(seconds_to_tomorrow, 60)
                time.sleep(sleep_time)
                # 重置每日下载量
                stats['today_downloaded'] = 0
                save_stats()
                continue
            
            # 获取启用的下载源
            enabled_sources = [s for s in config['download_sources'] if s['enabled']]
            if not enabled_sources:
                logger.info("没有启用的下载源，暂停下载")
                stats['is_downloading'] = False
                stats['current_download'] = None
                save_stats()
                time.sleep(60)  # 每分钟检查一次
                continue
            
            # 轮流从每个源下载
            for source in enabled_sources:
                if stop_event.is_set():
                    break
                
                url = source['url']
                name = source['name']
                
                # 更新状态
                stats['is_downloading'] = True
                stats['current_download'] = {
                    'name': name,
                    'url': url,
                    'start_time': datetime.now().isoformat(),
                    'bytes_downloaded': 0
                }
                save_stats()
                
                logger.info(f"开始下载: {name} - {url}")
                
                # 构建下载命令
                cmd = ['curl', '-s', '-o', '/dev/null']
                
                # 添加速度限制
                if config['speed_limit_kbps'] > 0:
                    limit_bytes = config['speed_limit_kbps'] * 1024 / 8  # 转换为字节/秒
                    cmd.extend(['--limit-rate', f"{limit_bytes}"]) 
                
                cmd.append(url)
                
                try:
                    # 启动下载进程
                    start_time = time.time()
                    download_process = subprocess.Popen(
                        cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE
                    )
                    
                    # 等待下载完成或被中断
                    stdout, stderr = download_process.communicate()
                    download_process = None
                    
                    # 计算下载的数据量（估算）
                    elapsed_time = time.time() - start_time
                    
                    # 如果有速度限制，使用速度限制计算下载量
                    if config['speed_limit_kbps'] > 0:
                        bytes_downloaded = int(config['speed_limit_kbps'] * 1024 / 8 * elapsed_time)
                    else:
                        # 否则假设以10MB/s的速度下载（这只是一个估计值）
                        bytes_downloaded = int(10 * 1024 * 1024 * elapsed_time)
                    
                    # 更新统计信息
                    stats['today_downloaded'] += bytes_downloaded
                    stats['total_downloaded'] += bytes_downloaded
                    stats['current_download'] = None
                    stats['is_downloading'] = False
                    save_stats()
                    
                    logger.info(f"下载完成: {name}, 估计下载了 {bytes_downloaded/(1024*1024):.2f} MB")
                    
                    # 等待间隔时间
                    if not stop_event.is_set() and config['interval_seconds'] > 0:
                        time.sleep(config['interval_seconds'])
                        
                except Exception as e:
                    logger.error(f"下载过程中出错: {str(e)}")
                    stats['is_downloading'] = False
                    stats['current_download'] = None
                    save_stats()
                    time.sleep(10)  # 出错后等待一段时间再重试
        
        except Exception as e:
            logger.error(f"下载线程出错: {str(e)}")
            time.sleep(10)  # 出错后等待一段时间再重试

# 启动下载线程
def start_download_thread():
    global download_thread, stop_event
    if download_thread is None or not download_thread.is_alive():
        stop_event.clear()
        download_thread = threading.Thread(target=download_thread_func)
        download_thread.daemon = True
        download_thread.start()
        logger.info("下载线程已启动")

# 停止下载线程
def stop_download_thread():
    global download_thread, download_process, stop_event
    stop_event.set()
    
    # 终止当前下载进程
    if download_process is not None:
        try:
            download_process.terminate()
            download_process = None
        except:
            pass
    
    # 等待线程结束
    if download_thread is not None:
        download_thread.join(timeout=5)
        download_thread = None
    
    logger.info("下载线程已停止")

# API路由
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def update_config():
    global config
    try:
        new_config = request.json
        # 验证配置
        if 'download_sources' not in new_config or not isinstance(new_config['download_sources'], list):
            return jsonify({'error': '无效的下载源配置'}), 400
        
        # 更新配置
        config = new_config
        save_config()
        
        # 如果配置已启用，确保下载线程在运行
        if config['enabled']:
            start_download_thread()
        else:
            stop_download_thread()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify(stats)

@app.route('/api/control/start', methods=['POST'])
def start_download():
    try:
        config['enabled'] = True
        save_config()
        start_download_thread()
        return jsonify({'status': 'success', 'message': '下载已启动'})
    except Exception as e:
        logger.error(f"启动下载失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/control/stop', methods=['POST'])
def stop_download():
    try:
        config['enabled'] = False
        save_config()
        stop_download_thread()
        return jsonify({'status': 'success', 'message': '下载已停止'})
    except Exception as e:
        logger.error(f"停止下载失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-stats', methods=['POST'])
def reset_stats():
    try:
        stats['today_downloaded'] = 0
        stats['total_downloaded'] = 0
        stats['download_history'] = []
        save_stats()
        return jsonify({'status': 'success', 'message': '统计信息已重置'})
    except Exception as e:
        logger.error(f"重置统计信息失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 主函数
if __name__ == '__main__':
    # 加载配置和统计信息
    load_config()
    load_stats()
    
    # 如果配置已启用，启动下载线程
    if config['enabled']:
        start_download_thread()
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=8080)