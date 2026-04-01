"""
A股数据收集器
直接通过HTTP请求东方财富API获取数据，不依赖AKShare
解决GitHub Actions海外服务器连接中国API不稳定的问题

功能：
1. 获取沪深A股实时行情（东方财富推送API）
2. 批量获取归母净利润增速（东方财富业绩报表API）
3. 筛选市值倒数1000名中净利润增速前30
"""

import pandas as pd
from datetime import datetime, timedelta
import json
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class AStockDataCollector:
    """A股数据收集器"""

    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.session = self._create_session()

    def _create_session(self):
        """创建带重试机制的HTTP会话"""
        session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://quote.eastmoney.com/',
        })
        return session

    def get_all_stocks(self):
        """通过东方财富推送API获取沪深A股实时行情"""
        print("  从东方财富获取沪深A股行情...")

        all_stocks = []
        page = 1

        while True:
            url = "https://82.push2.eastmoney.com/api/qt/clist/get"
            params = {
                'pn': str(page),
                'pz': '5000',
                'po': '1',
                'np': '1',
                'fltt': '2',
                'invt': '2',
                'fid': 'f20',
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048',
                'fields': 'f2,f3,f5,f6,f8,f12,f14,f15,f16,f17,f18,f20,f21',
                '_': str(int(time.time() * 1000)),
            }

            try:
                resp = self.session.get(url, params=params, timeout=30)
                data = resp.json()

                if data.get('data') is None or data['data'].get('diff') is None:
                    break

                items = data['data']['diff']
                if not items:
                    break

                for item in items:
                    code = str(item.get('f12', ''))
                    name = str(item.get('f14', ''))
                    if not code or code == '-' or not name:
                        continue

                    all_stocks.append({
                        '代码': code,
                        '名称': name,
                        '最新价': item.get('f2') if item.get('f2') != '-' else 0,
                        '涨跌幅': item.get('f3') if item.get('f3') != '-' else 0,
                        '成交量': item.get('f5') if item.get('f5') != '-' else 0,
                        '成交额': item.get('f6') if item.get('f6') != '-' else 0,
                        '最高': item.get('f15') if item.get('f15') != '-' else 0,
                        '最低': item.get('f16') if item.get('f16') != '-' else 0,
                        '今开': item.get('f17') if item.get('f17') != '-' else 0,
                        '昨收': item.get('f18') if item.get('f18') != '-' else 0,
                        '总市值': item.get('f20') if item.get('f20') != '-' else 0,
                        '流通市值': item.get('f21') if item.get('f21') != '-' else 0,
                        '换手率': item.get('f8') if item.get('f8') != '-' else 0,
                    })

                total = data['data'].get('total', 0)
                if page * 5000 >= total:
                    break
                page += 1
                time.sleep(1)

            except Exception as e:
                print(f"  获取第{page}页数据失败: {e}")
                break

        if not all_stocks:
            return pd.DataFrame()

        df = pd.DataFrame(all_stocks)

        # 过滤ST、退市、北交所、新三板
        df = df[
            ~df['名称'].str.contains('ST|退', na=False)
            & ~df['代码'].str.startswith('8', na=False)
            & ~df['代码'].str.startswith('4', na=False)
        ]

        # 转换数值类型
        num_cols = ['最新价', '涨跌幅', '总市值', '流通市值', '成交量', '成交额',
                    '最高', '最低', '今开', '昨收', '换手率']
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.dropna(subset=['总市值'])
        df = df[df['总市值'] > 0]

        print(f"  获取到 {len(df)} 只A股股票")
        return df

    def get_profit_growth_bulk(self):
        """批量获取归母净利润增速 - 东方财富业绩报表API"""
        print("  获取业绩报表数据（批量）...")

        # 按时间倒序尝试多个报告期
        report_dates = ['2025-12-31', '2025-09-30', '2025-06-30', '2024-12-31']

        for report_date in report_dates:
            try:
                all_records = []
                page = 1

                while True:
                    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
                    params = {
                        'sortColumns': 'NOTICE_DATE,SECURITY_CODE',
                        'sortTypes': '-1,-1',
                        'pageSize': '500',
                        'pageNumber': str(page),
                        'reportName': 'RPT_LICO_FN_CPD',
                        'columns': 'SECURITY_CODE,SECURITY_NAME_ABBR,PARENT_NETPROFIT,NETPROFIT_YOY_RATIO',
                        'filter': f"(REPORTDATE='{report_date}')",
                    }

                    resp = self.session.get(url, params=params, timeout=30)
                    data = resp.json()

                    if not data.get('success') or data.get('result') is None:
                        break

                    items = data['result'].get('data', [])
                    if not items:
                        break

                    for item in items:
                        code = item.get('SECURITY_CODE', '')
                        growth = item.get('NETPROFIT_YOY_RATIO')
                        if code and growth is not None:
                            all_records.append({
                                '代码': code,
                                '净利润同比增长率': float(growth),
                            })

                    total_pages = data['result'].get('pages', 1)
                    if page >= total_pages:
                        break
                    page += 1
                    time.sleep(0.5)

                if all_records:
                    print(f"  获取到 {len(all_records)} 条业绩数据（报告期: {report_date}）")
                    return pd.DataFrame(all_records)

            except Exception as e:
                print(f"  获取 {report_date} 业绩数据失败: {e}")
                continue

        return pd.DataFrame()

    def get_stock_kline(self, stock_code, period="daily"):
        """获取股票K线数据 - 直接请求东方财富"""
        try:
            period_map = {"daily": "101", "weekly": "102", "monthly": "103"}
            klt = period_map.get(period, "101")

            # 确定市场代码
            if stock_code.startswith('6') or stock_code.startswith('9'):
                secid = f"1.{stock_code}"
            else:
                secid = f"0.{stock_code}"

            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=365 * 2)).strftime("%Y%m%d")

            url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                'secid': secid,
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57',
                'klt': klt,
                'fqt': '1',
                'beg': start_date,
                'end': end_date,
                '_': str(int(time.time() * 1000)),
            }

            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()

            klines = data.get('data', {}).get('klines', [])
            records = []
            for line in klines:
                parts = line.split(',')
                if len(parts) >= 7:
                    records.append({
                        '日期': parts[0],
                        '开盘': float(parts[1]),
                        '收盘': float(parts[2]),
                        '最高': float(parts[3]),
                        '最低': float(parts[4]),
                        '成交量': float(parts[5]),
                        '成交额': float(parts[6]),
                    })

            return pd.DataFrame(records) if records else pd.DataFrame()

        except Exception as e:
            print(f"获取 {stock_code} {period} K线数据失败: {e}")
            return pd.DataFrame()

    def screen_stocks(self):
        """筛选股票：市值倒数1000名中净利润增速前30"""
        print("=" * 50)
        print("开始筛选股票...")
        print("=" * 50)

        # 1. 获取行情数据
        print("\n1. 获取沪深A股行情数据...")
        all_stocks = self.get_all_stocks()
        if all_stocks.empty:
            print("获取行情数据失败！")
            return pd.DataFrame()
        print(f"  共 {len(all_stocks)} 只股票")

        # 2. 按市值升序，取最小的1000只
        print("\n2. 筛选市值最小的1000只股票...")
        all_stocks = all_stocks.sort_values('总市值', ascending=True)
        small_cap = all_stocks.head(1000).copy()
        print(f"  筛选出 {len(small_cap)} 只小市值股票")
        print(f"  市值范围: {small_cap['总市值'].min()/1e8:.2f}亿 ~ {small_cap['总市值'].max()/1e8:.2f}亿")

        # 3. 批量获取净利润增速
        print("\n3. 获取归母净利润增速数据...")
        profit_df = self.get_profit_growth_bulk()

        if profit_df.empty:
            print("  业绩数据获取失败，无法筛选净利润增速")
            return pd.DataFrame()

        # 4. 合并数据
        print("\n4. 合并数据并筛选...")
        merged = small_cap.merge(profit_df, on='代码', how='inner')
        print(f"  匹配到 {len(merged)} 只有业绩数据的小市值股票")

        if merged.empty:
            print("  没有匹配到数据")
            return pd.DataFrame()

        # 5. 按净利润增速降序，取前30
        top30 = merged.sort_values('净利润同比增长率', ascending=False).head(30)

        print(f"\n最终筛选出 {len(top30)} 只股票")
        print("\n前10只股票预览:")
        preview_cols = ['代码', '名称', '总市值', '净利润同比增长率']
        preview = top30[preview_cols].head(10).copy()
        preview['总市值'] = (preview['总市值'] / 1e8).round(2)
        preview.columns = ['代码', '名称', '总市值(亿)', '净利润增速(%)']
        print(preview.to_string(index=False))

        return top30

    def save_screening_result(self, stocks_df):
        """保存筛选结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存为CSV
        csv_path = os.path.join(self.data_dir, f'screening_result_{timestamp}.csv')
        stocks_df.to_csv(csv_path, index=False, encoding='utf-8-sig')

        # 保存为JSON
        json_path = os.path.join(self.data_dir, 'latest_screening_result.json')
        stocks_df.to_json(json_path, orient='records', force_ascii=False, indent=2)

        # 保存最新CSV
        latest_csv = os.path.join(self.data_dir, 'latest_screening_result.csv')
        stocks_df.to_csv(latest_csv, index=False, encoding='utf-8-sig')

        # 保存到根目录，供Vercel读取
        root_json_path = os.path.join(os.path.dirname(__file__), 'screening_result.json')
        result_data = {
            'stocks': stocks_df.to_dict('records'),
            'timestamp': datetime.now().isoformat(),
            'count': len(stocks_df),
        }
        with open(root_json_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        print(f"\n结果已保存:")
        print(f"  CSV: {csv_path}")
        print(f"  JSON: {json_path}")
        print(f"  Root JSON: {root_json_path}")

        return csv_path, json_path

    def run_screening(self):
        """运行完整的筛选流程"""
        print("\n" + "=" * 50)
        print(f"A股小市值股票筛选 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)

        top_stocks = self.screen_stocks()

        if top_stocks is not None and not top_stocks.empty:
            self.save_screening_result(top_stocks)
            return {
                'success': True,
                'count': len(top_stocks),
                'stocks': top_stocks.to_dict('records'),
                'timestamp': datetime.now().isoformat(),
            }
        else:
            return {
                'success': False,
                'error': '筛选失败，未获取到数据',
                'timestamp': datetime.now().isoformat(),
            }


if __name__ == '__main__':
    collector = AStockDataCollector()
    result = collector.run_screening()
    if result['success']:
        print(f"\n筛选完成! 共 {result['count']} 只股票")
    else:
        print(f"\n筛选失败: {result['error']}")
