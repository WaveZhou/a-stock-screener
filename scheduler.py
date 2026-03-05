"""
定时任务调度器
每日14:30执行股票筛选任务
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_collector import AStockDataCollector
from email_sender import EmailSender


def scheduled_screening():
    """定时执行的筛选任务"""
    print("\n" + "=" * 60)
    print(f"⏰ 定时任务启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 执行筛选
        collector = AStockDataCollector()
        result = collector.run_screening()
        
        if result['success']:
            # 发送邮件
            sender = EmailSender()
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            csv_path = os.path.join(data_dir, 'latest_screening_result.csv')
            
            email_sent = sender.send_screening_result(result['stocks'], csv_path)
            
            if email_sent:
                print("\n✅ 定时任务完成：数据筛选并发送邮件成功")
            else:
                print("\n⚠️ 定时任务部分完成：数据筛选成功，但邮件发送失败")
        else:
            # 发送错误通知
            sender = EmailSender()
            sender.send_error_notification(result.get('error', '未知错误'))
            print(f"\n❌ 定时任务失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"\n❌ 定时任务异常: {e}")
        # 发送错误通知
        try:
            sender = EmailSender()
            sender.send_error_notification(str(e))
        except:
            pass


def start_scheduler():
    """启动定时任务调度器"""
    scheduler = BackgroundScheduler()
    
    # 添加定时任务：每天14:30执行
    trigger = CronTrigger(hour=14, minute=30)
    scheduler.add_job(
        scheduled_screening,
        trigger=trigger,
        id='daily_stock_screening',
        name='每日A股小市值股票筛选',
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ 定时任务调度器已启动")
    print("📅 下次执行时间: 每天 14:30")
    print("📝 任务: A股小市值股票筛选并发送邮件")
    
    return scheduler


def run_once():
    """立即执行一次筛选任务"""
    print("\n" + "=" * 60)
    print("🚀 手动执行股票筛选任务")
    print("=" * 60)
    scheduled_screening()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='A股股票筛选定时任务')
    parser.add_argument('--run-now', action='store_true', help='立即执行一次')
    parser.add_argument('--start', action='store_true', help='启动定时调度器')
    
    args = parser.parse_args()
    
    if args.run_now:
        run_once()
    elif args.start:
        scheduler = start_scheduler()
        
        # 保持程序运行
        print("\n按 Ctrl+C 停止调度器\n")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n正在停止调度器...")
            scheduler.shutdown()
            print("✅ 调度器已停止")
    else:
        print("请指定操作模式:")
        print("  python scheduler.py --run-now  # 立即执行一次")
        print("  python scheduler.py --start    # 启动定时调度器")