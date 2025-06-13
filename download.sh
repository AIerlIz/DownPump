#!/bin/bash

# 打印脚本开始执行的信息
echo "开始执行 DownPump 下载泵..."
echo "下载间隔: $DOWNLOAD_INTERVAL 秒"
echo "下载源: $DOWNLOAD_URLS"
echo "每日流量上限: $DAILY_TRAFFIC_LIMIT GB"
echo "下载时间段: $DOWNLOAD_START_TIME - $DOWNLOAD_END_TIME"
echo "流量日志文件: $TRAFFIC_LOG_FILE"

# 处理下载限速设置
if [ "$DOWNLOAD_SPEED_LIMIT" -eq 0 ]; then
    echo "下载速度: 不限速"
else
    echo "下载速度限制: $DOWNLOAD_SPEED_LIMIT MB/s"
fi

# 不创建下载目录，直接将所有下载内容输出到/dev/null

# 初始化日志文件
touch "$TRAFFIC_LOG_FILE"

# 获取今天的日期
TODAY=$(date +"%Y-%m-%d")

# 计数器
count=0

# 初始化今日流量计数
if grep -q "$TODAY" "$TRAFFIC_LOG_FILE"; then
    # 如果今天的记录已存在，读取已下载的流量
    DAILY_TRAFFIC=$(grep "$TODAY" "$TRAFFIC_LOG_FILE" | cut -d' ' -f2)
else
    # 否则初始化为0
    DAILY_TRAFFIC=0
    echo "$TODAY $DAILY_TRAFFIC" >> "$TRAFFIC_LOG_FILE"
fi

echo "今日已下载流量: $DAILY_TRAFFIC MB"

# 检查是否在允许的下载时间段内
is_download_time() {
    local current_time=$(date +"%H:%M")
    local start_time=$DOWNLOAD_START_TIME
    local end_time=$DOWNLOAD_END_TIME
    
    # 比较时间字符串
    if [[ "$current_time" > "$start_time" ]] && [[ "$current_time" < "$end_time" ]]; then
        return 0 # 在时间段内
    else
        return 1 # 不在时间段内
    fi
}

# 检查是否超过每日流量限制
is_traffic_limit_exceeded() {
    # 将GB转换为MB进行比较
    local limit_in_mb=$(echo "$DAILY_TRAFFIC_LIMIT * 1024" | bc -l)
    if [[ $(echo "$DAILY_TRAFFIC >= $limit_in_mb" | bc -l) -eq 1 ]]; then
        return 0 # 超过限制
    else
        return 1 # 未超过限制
    fi
}

# 更新流量统计
update_traffic_stats() {
    local downloaded_mb=$1
    
    # 更新今日流量
    DAILY_TRAFFIC=$(echo "$DAILY_TRAFFIC + $downloaded_mb" | bc -l)
    
    # 更新日志文件
    sed -i "/$TODAY/d" "$TRAFFIC_LOG_FILE" # 删除今天的记录
    echo "$TODAY $DAILY_TRAFFIC" >> "$TRAFFIC_LOG_FILE" # 添加更新后的记录
    
    echo "已更新今日流量统计: $DAILY_TRAFFIC MB / $(echo "$DAILY_TRAFFIC_LIMIT * 1024" | bc -l) MB (${DAILY_TRAFFIC_LIMIT} GB)"
}

# 持续下载函数
download_files() {
    # 将URL字符串分割成数组
    IFS=' ' read -ra URLS <<< "$DOWNLOAD_URLS"
    
    for url in "${URLS[@]}"; do
        # 检查是否在允许的下载时间段内
        if ! is_download_time; then
            echo "[$(date)] 当前时间不在允许的下载时间段($DOWNLOAD_START_TIME - $DOWNLOAD_END_TIME)内，跳过下载"
            return 1
        fi
        
        # 检查是否超过流量限制
        if is_traffic_limit_exceeded; then
            echo "[$(date)] 已达到每日流量上限($DAILY_TRAFFIC_LIMIT GB)，停止下载"
            return 2
        fi
        
        echo "[$(date)] 开始下载: $url"
        
        # 获取文件大小（以字节为单位）
        file_size=$(curl -sI "$url" | grep -i Content-Length | awk '{print $2}' | tr -d '\r')
        
        # 如果无法获取文件大小，假设为10MB
        if [ -z "$file_size" ]; then
            file_size=10485760 # 10MB in bytes
        fi
        
        # 转换为MB
        file_size_mb=$(echo "scale=2; $file_size / 1048576" | bc -l)
        
        echo "文件大小: $file_size_mb MB"
        
        # 构建wget命令，根据是否设置限速添加相应参数
        WGET_CMD="wget -O /dev/null"
        CURL_CMD="curl -o /dev/null"
        
        # 如果设置了下载速度限制，添加限速参数
        if [ "$DOWNLOAD_SPEED_LIMIT" -ne 0 ]; then
            # 将MB/s转换为KB/s (1MB = 1024KB)
            local speed_limit_kb=$(echo "$DOWNLOAD_SPEED_LIMIT * 1024" | bc -l)
            WGET_CMD="$WGET_CMD --limit-rate=${speed_limit_kb}k"
            CURL_CMD="$CURL_CMD --limit-rate ${speed_limit_kb}k"
            echo "应用下载速度限制: $DOWNLOAD_SPEED_LIMIT MB/s (${speed_limit_kb} KB/s)"
        fi
        
        # 添加其他wget参数
        WGET_CMD="$WGET_CMD \"$url\" --progress=dot:mega"
        
        # 使用wget下载文件到/dev/null，显示进度但不保存文件
        eval "$WGET_CMD 2>&1" | grep --line-buffered -o "[0-9]\+%" | tail -1
        
        # 或者使用curl作为替代（注释掉，需要时可以取消注释）
        # eval "$CURL_CMD \"$url\" --progress-bar"
        
        echo "[$(date)] 完成下载: $url"
        
        # 更新流量统计
        update_traffic_stats "$file_size_mb"
    done
    
    return 0
}

# 检查是否是新的一天，如果是则重置流量计数
check_new_day() {
    local current_date=$(date +"%Y-%m-%d")
    
    if [[ "$current_date" != "$TODAY" ]]; then
        echo "检测到新的一天，重置流量计数..."
        TODAY=$current_date
        DAILY_TRAFFIC=0
        echo "$TODAY $DAILY_TRAFFIC" >> "$TRAFFIC_LOG_FILE"
        echo "流量计数已重置为0 MB"
        return 0 # 是新的一天
    fi
    
    return 1 # 不是新的一天
}

# 等待直到下一个允许的下载时间段
wait_until_download_time() {
    local current_time=$(date +"%H:%M")
    local start_time=$DOWNLOAD_START_TIME
    
    echo "当前时间 $current_time 不在允许的下载时间段内"
    
    # 如果当前时间已经超过了今天的下载结束时间，等待到明天的开始时间
    if [[ "$current_time" > "$DOWNLOAD_END_TIME" ]]; then
        echo "已超过今天的下载结束时间，等待到明天 $start_time 继续下载"
        
        # 计算到明天开始时间的秒数
        local tomorrow=$(date -d "tomorrow $start_time" +%s)
        local now=$(date +%s)
        local sleep_seconds=$((tomorrow - now))
        
        echo "将在 $(($sleep_seconds / 60)) 分钟后继续下载"
        sleep $sleep_seconds
    else
        # 否则等待到今天的开始时间
        echo "等待到今天 $start_time 继续下载"
        
        # 计算到今天开始时间的秒数
        local target=$(date -d "today $start_time" +%s)
        local now=$(date +%s)
        local sleep_seconds=$((target - now))
        
        if [[ $sleep_seconds -lt 0 ]]; then
            sleep_seconds=60 # 如果计算错误，至少等待1分钟
        fi
        
        echo "将在 $(($sleep_seconds / 60)) 分钟后继续下载"
        sleep $sleep_seconds
    fi
}

# 等待到第二天重置流量计数
wait_until_tomorrow() {
    echo "已达到今日流量上限 $DAILY_TRAFFIC_LIMIT GB，等待到明天继续下载"
    
    # 计算到明天0点的秒数
    local tomorrow=$(date -d "tomorrow 00:00" +%s)
    local now=$(date +%s)
    local sleep_seconds=$((tomorrow - now))
    
    echo "将在 $(($sleep_seconds / 60)) 分钟后重置流量计数并继续下载"
    sleep $sleep_seconds
    
    # 重置流量计数
    check_new_day
}

# 主循环
while true; do
    # 检查是否是新的一天
    check_new_day
    
    count=$((count+1))
    echo "\n===== 第 $count 轮下载开始 ====="
    
    # 执行下载
    download_files
    download_status=$?
    
    # 根据下载状态决定下一步操作
    if [[ $download_status -eq 1 ]]; then
        # 不在下载时间段内
        echo "===== 下载暂停：不在允许的时间段内 =====\n"
        wait_until_download_time
        continue
    elif [[ $download_status -eq 2 ]]; then
        # 超过流量上限
        echo "===== 下载暂停：已达到每日流量上限 =====\n"
        wait_until_tomorrow
        continue
    else
        # 下载成功完成
        echo "===== 第 $count 轮下载完成 =====\n"
    fi
    
    # 等待指定的间隔时间
    echo "等待 $DOWNLOAD_INTERVAL 秒后开始下一轮下载..."
    sleep "$DOWNLOAD_INTERVAL"
done