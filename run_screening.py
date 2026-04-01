"""
股票筛选脚本 - 由GitHub Actions调用
"""
import sys
import os
import json

# 添加当前目录到路径
sys.path.append('.')

from data_collector import AStockDataCollector
from email_sender import EmailSender

def main():
    print("开始执行股票筛选...")
    
    collector = AStockDataCollector()
    result = collector.run_screening()
    
    if result['success']:
        print(f"筛选完成，共 {len(result['stocks'])} 只股票")
        
        # 保存结果到文件（供后续步骤使用）
        with open('screening_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print('结果已保存到 screening_result.json')
        
        # 发送邮件（失败不阻塞）
        try:
            sender = EmailSender()
            sender.send_screening_result(result['stocks'])
            print('邮件发送成功')
        except Exception as e:
            print(f'邮件发送失败: {e}')
            print('继续执行...')
        
        return 0
    else:
        print(f"筛选失败: {result.get('error', '未知错误')}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
