"""
邮件发送模块
用于发送筛选结果到指定邮箱
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone, timedelta
import pandas as pd

# 北京时间 UTC+8
BJT = timezone(timedelta(hours=8))


class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        # 163邮箱配置
        self.smtp_server = "smtp.163.com"
        self.smtp_port = 465  # SSL端口
        self.sender_email = "zhoulang0411@163.com"
        self.sender_password = "ZNcg9FLhtZASH6sh"  # 邮箱授权码
        self.receiver_email = "zhoulang0411@163.com"
    
    def create_email_content(self, stocks_data, timestamp):
        """创建邮件内容"""
        
        # HTML邮件模板
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
                h2 {{ color: #555; margin-top: 30px; }}
                .info {{ color: #666; margin-bottom: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th {{ background-color: #007bff; color: white; padding: 12px; text-align: left; }}
                td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                tr:hover {{ background-color: #f1f1f1; }}
                .positive {{ color: #28a745; font-weight: bold; }}
                .negative {{ color: #dc3545; font-weight: bold; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <h1>📊 A股小市值股票筛选报告</h1>
            <p class="info">生成时间: {timestamp}</p>
            <p class="info">筛选条件: 市值倒数100名中，归母净利润增速前30</p>
            
            <h2>📈 筛选结果概览</h2>
            <p>共筛选出 <strong>{len(stocks_data)}</strong> 只股票</p>
            
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>代码</th>
                        <th>名称</th>
                        <th>最新价</th>
                        <th>涨跌幅</th>
                        <th>总市值(亿)</th>
                        <th>流通市值(亿)</th>
                        <th>净利润增速</th>
                        <th>成交额(万)</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # 添加股票数据行
        for idx, stock in enumerate(stocks_data, 1):
            # 格式化数值
            latest_price = stock.get('最新价', 'N/A')
            change_pct = stock.get('涨跌幅', 'N/A')
            total_cap = stock.get('总市值', 0)
            float_cap = stock.get('流通市值', 0)
            profit_growth = stock.get('净利润同比增长率', 'N/A')
            turnover = stock.get('成交额', 0)
            
            # 格式化市值（转换为亿）
            total_cap_yi = total_cap / 100000000 if total_cap else 0
            float_cap_yi = float_cap / 100000000 if float_cap else 0
            turnover_wan = turnover / 10000 if turnover else 0
            
            # 涨跌幅颜色
            change_class = "positive" if change_pct and float(change_pct) > 0 else "negative" if change_pct and float(change_pct) < 0 else ""
            growth_class = "positive" if profit_growth and float(profit_growth) > 0 else "negative" if profit_growth and float(profit_growth) < 0 else ""
            
            html_content += f"""
                    <tr>
                        <td>{idx}</td>
                        <td>{stock.get('代码', 'N/A')}</td>
                        <td><strong>{stock.get('名称', 'N/A')}</strong></td>
                        <td>{latest_price}</td>
                        <td class="{change_class}">{change_pct}%</td>
                        <td>{total_cap_yi:.2f}</td>
                        <td>{float_cap_yi:.2f}</td>
                        <td class="{growth_class}">{profit_growth}%</td>
                        <td>{turnover_wan:.2f}</td>
                    </tr>
            """
        
        html_content += f"""
                </tbody>
            </table>
            
            <div class="footer">
                <p>本报告由A股小市值股票筛选系统自动生成</p>
                <p>访问Web界面查看详细K线图: <a href="https://a-stock-screener.vercel.app">点击查看</a></p>
                <p>免责声明：本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def send_screening_result(self, stocks_data, attachment_path=None):
        """发送筛选结果邮件"""
        try:
            timestamp = datetime.now(BJT).strftime("%Y-%m-%d %H:%M:%S")
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email
            msg['Subject'] = f"📊 A股小市值股票筛选报告 - {datetime.now(BJT).strftime('%Y年%m月%d日')}"
            
            # 添加HTML内容
            html_content = self.create_email_content(stocks_data, timestamp)
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 添加附件
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    attachment = MIMEBase('application', 'octet-stream')
                    attachment.set_payload(f.read())
                    encoders.encode_base64(attachment)
                    attachment.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment_path)}'
                    )
                    msg.attach(attachment)
            
            # 连接SMTP服务器并发送
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"[OK] 邮件发送成功！发送至: {self.receiver_email}")
            return True
            
        except Exception as e:
            print(f"[FAIL] 邮件发送失败: {e}")
            return False
    
    def send_error_notification(self, error_message):
        """发送错误通知邮件"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email
            msg['Subject'] = f"⚠️ A股筛选系统运行异常 - {datetime.now(BJT).strftime('%Y年%m月%d日')}"
            
            html_content = f"""
            <html>
            <body>
                <h2 style="color: #dc3545;">⚠️ 系统运行异常</h2>
                <p><strong>时间:</strong> {datetime.now(BJT).strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>错误信息:</strong></p>
                <pre style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">{error_message}</pre>
                <p>请检查系统日志或手动运行脚本排查问题。</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            print("[OK] 错误通知邮件已发送")
            return True
            
        except Exception as e:
            print(f"[FAIL] 错误通知邮件发送失败: {e}")
            return False


if __name__ == '__main__':
    # 测试邮件发送
    sender = EmailSender()
    
    # 模拟测试数据
    test_data = [
        {
            '代码': '000001',
            '名称': '平安银行',
            '最新价': 10.50,
            '涨跌幅': 2.5,
            '总市值': 2000000000,
            '流通市值': 1800000000,
            '净利润同比增长率': 15.8,
            '成交额': 50000000
        }
    ]
    
    sender.send_screening_result(test_data)