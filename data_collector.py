"""
A股数据收集器 v3
直接HTTP请求东方财富API，完全不依赖AKShare
- 多主机容错
- 自动重试 + 指数退避
- 详细调试日志
- 需求：市值倒数100名中，归母净利润增速前30
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

    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.session = self._create_session()

    def _create_session(self):
        session = requests.Session()
        retry = Retry(total=5, backoff_factor=2,
                      status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        # 绕过系统代理，直连东方财富API
        session.trust_env = False
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        return session

    # ─── 行情数据 ──────────────────────────────────────

    def get_all_stocks(self):
        """获取沪深A股实时行情，多主机容错"""
        print("  从东方财富获取沪深A股行情...")

        # 方案1: push2 行情API（国内环境通常可用）
        hosts = [
            "https://82.push2.eastmoney.com",
            "https://push2.eastmoney.com",
            "http://push2.eastmoney.com",
            "http://82.push2.eastmoney.com",
        ]

        for host in hosts:
            try:
                df = self._fetch_stock_list(host)
                if not df.empty and len(df) > 50:
                    print(f"  [OK] {host}: 获取到 {len(df)} 只小市值A股")
                    return df
                print(f"  [WARN] {host}: 仅 {len(df)} 只，换下一个...")
            except Exception as e:
                print(f"  [FAIL] {host}: {e}")

        # 方案2: datacenter API（海外可用的备用方案）
        print("  push2行情接口均失败，尝试datacenter备用方案...")
        try:
            df = self._fetch_stock_list_datacenter()
            if not df.empty and len(df) > 50:
                print(f"  [OK] datacenter备用方案: 获取到 {len(df)} 只股票")
                return df
        except Exception as e:
            print(f"  [FAIL] datacenter备用方案: {e}")

        print("  所有主机均失败")
        return pd.DataFrame()

    def _fetch_stock_list_datacenter(self):
        """使用新浪财经API获取小市值股票列表（海外友好备用方案）
        新浪API对海外IP无限制，支持按市值排序"""
        print("    使用新浪财经API获取小市值股票...")
        sina_session = requests.Session()
        sina_session.trust_env = False
        sina_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://finance.sina.com.cn',
        })

        all_stocks = []
        # 从沪市A股和深市A股分别获取市值最小的股票
        for node in ['sh_a', 'sz_a']:
            for page in range(1, 3):  # 每个市场取2页×80=160只
                try:
                    url = ('https://vip.stock.finance.sina.com.cn/'
                           'quotes_service/api/json_v2.php/'
                           'Market_Center.getHQNodeData')
                    params = {
                        'page': str(page),
                        'num': '80',
                        'sort': 'mktcap',
                        'asc': '1',
                        'node': node,
                        'symbol': '',
                        '_s_r_a': 'init',
                    }
                    resp = sina_session.get(url, params=params, timeout=20)
                    stocks = resp.json()
                    if stocks:
                        all_stocks.extend(stocks)
                        print(f"    {node} page {page}: {len(stocks)} 只")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"    {node} page {page} 失败: {e}")

        if not all_stocks:
            return pd.DataFrame()

        # 按市值排序，转换为标准格式
        all_stocks.sort(key=lambda x: x.get('mktcap', 999999999))

        records = []
        for item in all_stocks:
            name = item.get('name', '')
            symbol = item.get('symbol', '')
            code = item.get('code', '')
            # 过滤ST、退市
            if 'ST' in name or '退' in name:
                continue
            # 过滤无效数据
            mktcap = item.get('mktcap', 0)
            if not mktcap or mktcap <= 0:
                continue
            records.append({
                '代码': code,
                '名称': name,
                '最新价': self._safe_float(item.get('trade')),
                '涨跌幅': self._safe_float(item.get('changepercent')),
                '成交量': self._safe_float(item.get('volume')),
                '成交额': self._safe_float(item.get('amount')),
                '最高': self._safe_float(item.get('high')),
                '最低': self._safe_float(item.get('low')),
                '今开': self._safe_float(item.get('open')),
                '昨收': self._safe_float(item.get('settlement')),
                '总市值': mktcap * 10000,  # 万元转元
                '流通市值': self._safe_float(item.get('nmc', 0)) * 10000,
                '换手率': self._safe_float(item.get('turnoverratio')),
            })

        df = pd.DataFrame(records)
        df = df[df['总市值'] > 0]
        print(f"    新浪API获取到 {len(df)} 只有效股票")
        return df

    def _fetch_stock_list(self, host):
        """从指定主机获取股票列表 - 直接按市值升序排列获取前200"""
        all_items = []
        page = 1
        # 只需要市值最小的股票，按f20(总市值)升序
        # API最大每页100条，取2页共200条足矣（需要100只，多取些做过滤缓冲）
        max_pages = 2

        while page <= max_pages:
            url = f"{host}/api/qt/clist/get"
            params = {
                "pn": str(page),
                "pz": "100",
                "po": "1",
                "np": "1",
                "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                "fltt": "2",
                "invt": "2",
                "wbp2u": "|0|0|0|web",
                "fid": "f20",
                "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048",
                "fields": "f2,f3,f5,f6,f8,f12,f14,f15,f16,f17,f18,f20,f21",
                "_": str(int(time.time() * 1000)),
            }

            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()

            if data.get('data') is None:
                print(f"    第{page}页: data=None")
                break

            items = data['data'].get('diff', [])
            total = data['data'].get('total', 0)
            print(f"    第{page}页: {len(items)} 条 (total={total})")

            if not items:
                break

            all_items.extend(items)
            page += 1
            time.sleep(0.5)

        if not all_items:
            return pd.DataFrame()

        records = []
        for item in all_items:
            code = str(item.get('f12', ''))
            name = str(item.get('f14', ''))
            if not code or code == '-' or not name or name == '-':
                continue
            records.append({
                '代码': code,
                '名称': name,
                '最新价': self._safe_float(item.get('f2')),
                '涨跌幅': self._safe_float(item.get('f3')),
                '成交量': self._safe_float(item.get('f5')),
                '成交额': self._safe_float(item.get('f6')),
                '最高': self._safe_float(item.get('f15')),
                '最低': self._safe_float(item.get('f16')),
                '今开': self._safe_float(item.get('f17')),
                '昨收': self._safe_float(item.get('f18')),
                '总市值': self._safe_float(item.get('f20')),
                '流通市值': self._safe_float(item.get('f21')),
                '换手率': self._safe_float(item.get('f8')),
            })

        df = pd.DataFrame(records)

        # 过滤 ST、退市、北交所、新三板
        df = df[
            ~df['名称'].str.contains('ST|退', na=False)
            & ~df['代码'].str.startswith('8', na=False)
            & ~df['代码'].str.startswith('4', na=False)
            & ~df['代码'].str.startswith('9', na=False)
        ]

        df = df.dropna(subset=['总市值'])
        df = df[df['总市值'] > 0]
        return df

    # ─── 业绩报表（净利润增速） ──────────────────────

    def get_profit_growth_bulk(self):
        """批量获取归母净利润同比增速 - 合并多报告期，优先最新"""
        print("  获取业绩报表数据（多报告期合并）...")

        api_urls = [
            "https://datacenter-web.eastmoney.com/api/data/v1/get",
            "https://datacenter.eastmoney.com/api/data/v1/get",
        ]
        report_dates = ['2025-12-31', '2025-09-30', '2025-06-30',
                        '2024-12-31', '2024-09-30']

        all_profit = pd.DataFrame()

        for api_url in api_urls:
            for report_date in report_dates:
                try:
                    df = self._fetch_profit_from(api_url, report_date)
                    if not df.empty:
                        if all_profit.empty:
                            all_profit = df
                        else:
                            # 只补充之前没有的股票，保证优先用最新报告期
                            existing_codes = set(all_profit['代码'].values)
                            new_rows = df[~df['代码'].isin(existing_codes)]
                            if not new_rows.empty:
                                all_profit = pd.concat(
                                    [all_profit, new_rows], ignore_index=True)
                                print(f"    补充 {len(new_rows)} 条新记录，"
                                      f"累计 {len(all_profit)} 条")
                except Exception as e:
                    print(f"    {report_date} @ "
                          f"{api_url.split('//')[1][:30]}: {e}")

            if not all_profit.empty:
                print(f"  累计获取 {len(all_profit)} 条业绩数据")
                return all_profit

            print(f"    该主机所有报告期均失败，换下一个...")

        print("  所有业绩数据源均失败")
        return pd.DataFrame()

    def _fetch_profit_from(self, api_url, report_date):
        """从指定API获取某个报告期的业绩数据"""
        all_records = []
        page = 1

        while True:
            params = {
                'sortColumns': 'NOTICE_DATE,SECURITY_CODE',
                'sortTypes': '-1,-1',
                'pageSize': '500',
                'pageNumber': str(page),
                'reportName': 'RPT_LICO_FN_CPD',
                'columns': 'SECURITY_CODE,SECURITY_NAME_ABBR,'
                           'PARENT_NETPROFIT,SJLTZ',
                'filter': f"(REPORTDATE='{report_date}')",
                'source': 'WEB',
                'client': 'WEB',
            }

            resp = self.session.get(api_url, params=params, timeout=30)
            data = resp.json()

            if page == 1:
                print(f"    {report_date}: HTTP {resp.status_code}, "
                      f"success={data.get('success')}, "
                      f"code={data.get('code')}, "
                      f"has_result={data.get('result') is not None}")

            if not data.get('success') or data.get('result') is None:
                if page == 1:
                    msg = data.get('message', '')
                    print(f"    返回消息: {msg[:100]}")
                break

            items = data['result'].get('data', [])
            if not items:
                break

            for item in items:
                code = item.get('SECURITY_CODE', '')
                growth = item.get('SJLTZ')
                if code and growth is not None:
                    try:
                        all_records.append({
                            '代码': code,
                            '净利润同比增长率': float(growth),
                        })
                    except (ValueError, TypeError):
                        continue

            total_pages = data['result'].get('pages', 1)
            total_count = data['result'].get('count', 0)
            if page == 1:
                print(f"    总计 {total_count} 条, {total_pages} 页")

            if page >= total_pages:
                break
            page += 1
            time.sleep(0.5)

        if all_records:
            print(f"    [OK] 获取到 {len(all_records)} 条业绩数据"
                  f"（报告期: {report_date}）")
            return pd.DataFrame(all_records)
        return pd.DataFrame()

    # ─── 多周期涨幅 ─────────────────────────────────

    def get_period_gains_batch(self, stock_codes):
        """批量获取股票的多周期涨幅（周/月/年）
        如果前3只都失败则跳过（API不可达）"""
        print(f"\n5. 计算 {len(stock_codes)} 只股票的多周期涨幅...")
        results = {}
        success = 0
        fail_streak = 0

        for i, code in enumerate(stock_codes):
            try:
                gains = self._calc_period_gains(code)
                results[code] = gains
                if gains:
                    success += 1
                    fail_streak = 0
                else:
                    fail_streak += 1
                if (i + 1) % 10 == 0:
                    print(f"  已处理 {i+1}/{len(stock_codes)}...")
                # 如果连续3只都失败，说明K线API不可达，跳过剩余
                if fail_streak >= 3 and success == 0:
                    print(f"  前{i+1}只均无法获取K线，跳过涨幅计算")
                    break
                time.sleep(0.2)
            except Exception as e:
                print(f"  {code} 失败: {e}")
                results[code] = {}
                fail_streak += 1
                if fail_streak >= 3 and success == 0:
                    print(f"  连续失败，跳过涨幅计算")
                    break
        print(f"  完成: {success}/{len(stock_codes)} 成功")
        return results

    def _calc_period_gains(self, stock_code):
        """计算单只股票的周/月/年涨幅（东方财富+新浪双源）"""
        closes, dates = [], []

        # 方案1: 东方财富K线（短超时，不走重试adapter）
        try:
            secid = (f"1.{stock_code}" if stock_code.startswith('6')
                     else f"0.{stock_code}")
            url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                'secid': secid,
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53',
                'klt': '101',
                'fqt': '1',
                'beg': (datetime.now() - timedelta(days=400)).strftime("%Y%m%d"),
                'end': datetime.now().strftime("%Y%m%d"),
            }
            # 直接用requests.get，不走有重试的session
            resp = requests.get(url, params=params, timeout=5,
                                headers=self.session.headers, verify=True)
            klines = resp.json().get('data', {}).get('klines', [])
            for line in klines:
                p = line.split(',')
                if len(p) >= 3:
                    closes.append(float(p[2]))
                    dates.append(p[0])
        except Exception:
            pass

        # 方案2: 新浪K线（如果东方财富失败）
        if len(closes) < 30:
            try:
                prefix = 'sh' if stock_code.startswith('6') else 'sz'
                url = (f"https://quotes.sina.cn/cn/api/jsonp_v2.php/"
                       f"var/CN_MarketDataService.getKLineData"
                       f"?symbol={prefix}{stock_code}"
                       f"&scale=240&ma=no&datalen=250")
                resp = requests.get(url, timeout=5,
                                    headers={'User-Agent': 'Mozilla/5.0',
                                             'Referer': 'https://finance.sina.com.cn'})
                text = resp.text
                # 解析 JSONP: var=([...]);
                start = text.find('([')
                end = text.rfind('])')
                if start > 0 and end > start:
                    import json
                    data = json.loads(text[start + 1:end + 1])
                    closes, dates = [], []
                    for item in data:
                        closes.append(float(item['close']))
                        dates.append(item['day'][:10])
            except Exception:
                pass

        if len(closes) < 2:
            return {}

        latest = closes[-1]
        gains = {}

        # 周涨幅（5个交易日）
        if len(closes) >= 6:
            gains['周涨幅'] = round((latest / closes[-6] - 1) * 100, 2)

        # 月涨幅（20个交易日）
        if len(closes) >= 21:
            gains['月涨幅'] = round((latest / closes[-21] - 1) * 100, 2)

        # 年涨幅（年初至今）
        year_str = datetime.now().strftime("%Y")
        for i, d in enumerate(dates):
            if d.startswith(year_str):
                base = closes[i - 1] if i > 0 else closes[0]
                gains['年涨幅'] = round((latest / base - 1) * 100, 2)
                break

        return gains

    # ─── K线数据 ─────────────────────────────────────

    def get_stock_kline(self, stock_code, period="daily"):
        """获取K线数据 - 直接请求东方财富"""
        try:
            klt = {"daily": "101", "weekly": "102", "monthly": "103"
                   }.get(period, "101")

            if stock_code.startswith('6') or stock_code.startswith('9'):
                secid = f"1.{stock_code}"
            else:
                secid = f"0.{stock_code}"

            url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                'secid': secid,
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57',
                'klt': klt,
                'fqt': '1',
                'beg': (datetime.now() - timedelta(days=730)).strftime("%Y%m%d"),
                'end': datetime.now().strftime("%Y%m%d"),
            }

            resp = self.session.get(url, params=params, timeout=30)
            klines = resp.json().get('data', {}).get('klines', [])

            records = []
            for line in klines:
                p = line.split(',')
                if len(p) >= 7:
                    records.append({
                        '日期': p[0], '开盘': float(p[1]), '收盘': float(p[2]),
                        '最高': float(p[3]), '最低': float(p[4]),
                        '成交量': float(p[5]), '成交额': float(p[6]),
                    })
            return pd.DataFrame(records) if records else pd.DataFrame()
        except Exception as e:
            print(f"获取 {stock_code} K线失败: {e}")
            return pd.DataFrame()

    # ─── 筛选主流程 ──────────────────────────────────

    def screen_stocks(self):
        """筛选：市值倒数100名中，归母净利润增速前30"""
        print("=" * 50)
        print("开始筛选股票...")
        print("=" * 50)

        # 1. 行情
        print("\n1. 获取沪深A股行情数据...")
        all_stocks = self.get_all_stocks()
        if all_stocks.empty:
            print("行情数据获取失败！")
            return pd.DataFrame()
        print(f"  共 {len(all_stocks)} 只股票")

        # 2. 市值倒数100
        print("\n2. 筛选市值最小的100只股票...")
        all_stocks = all_stocks.sort_values('总市值', ascending=True)
        small_cap = all_stocks.head(100).copy()
        print(f"  筛选出 {len(small_cap)} 只小市值股票")
        print(f"  市值范围: {small_cap['总市值'].min()/1e8:.2f}亿 "
              f"~ {small_cap['总市值'].max()/1e8:.2f}亿")

        # 3. 净利润增速
        print("\n3. 获取归母净利润增速数据...")
        profit_df = self.get_profit_growth_bulk()

        if profit_df.empty:
            print("  业绩数据获取失败，无法按净利润增速筛选")
            # 降级方案：直接返回市值最小的30只
            print("  降级方案：返回市值最小的30只股票")
            return small_cap.head(30)

        # 4. 合并
        print("\n4. 合并数据并筛选...")
        merged = small_cap.merge(profit_df, on='代码', how='inner')
        print(f"  匹配到 {len(merged)} 只有业绩数据的小市值股票")

        if merged.empty:
            print("  没有匹配到任何数据")
            # 降级方案：左连接，保留所有小市值股票
            merged = small_cap.merge(profit_df, on='代码', how='left')
            merged['净利润同比增长率'] = merged['净利润同比增长率'].fillna(0)
            print(f"  降级方案：保留全部 {len(merged)} 只，增速缺失按0处理")

        # 5. 取前30
        top30 = merged.sort_values('净利润同比增长率', ascending=False).head(30)

        print(f"\n最终筛选出 {len(top30)} 只股票")

        # 6. 计算多周期涨幅
        stock_codes = top30['代码'].tolist()
        period_gains = self.get_period_gains_batch(stock_codes)
        for col in ['周涨幅', '月涨幅', '年涨幅']:
            top30[col] = top30['代码'].map(
                lambda c, _col=col: period_gains.get(c, {}).get(_col, 0.0))

        print("\n前10只股票预览:")
        preview = top30[['代码', '名称', '总市值', '净利润同比增长率',
                         '周涨幅', '月涨幅', '年涨幅']].head(10).copy()
        preview['总市值'] = (preview['总市值'] / 1e8).round(2)
        preview.columns = ['代码', '名称', '总市值(亿)', '净利润增速(%)',
                           '周涨幅(%)', '月涨幅(%)', '年涨幅(%)']
        print(preview.to_string(index=False))

        return top30

    # ─── 保存结果 ────────────────────────────────────

    def save_screening_result(self, stocks_df):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        csv_path = os.path.join(self.data_dir, f'screening_result_{timestamp}.csv')
        stocks_df.to_csv(csv_path, index=False, encoding='utf-8-sig')

        json_path = os.path.join(self.data_dir, 'latest_screening_result.json')
        stocks_df.to_json(json_path, orient='records', force_ascii=False, indent=2)

        latest_csv = os.path.join(self.data_dir, 'latest_screening_result.csv')
        stocks_df.to_csv(latest_csv, index=False, encoding='utf-8-sig')

        root_json = os.path.join(os.path.dirname(__file__), 'screening_result.json')
        with open(root_json, 'w', encoding='utf-8') as f:
            json.dump({
                'stocks': stocks_df.to_dict('records'),
                'timestamp': datetime.now().isoformat(),
                'count': len(stocks_df),
            }, f, ensure_ascii=False, indent=2)

        print(f"\n结果已保存:")
        print(f"  CSV: {csv_path}")
        print(f"  Root JSON: {root_json}")
        return csv_path, json_path

    def run_screening(self):
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
        return {
            'success': False,
            'error': '筛选失败，未获取到数据',
            'timestamp': datetime.now().isoformat(),
        }

    # ─── 工具方法 ────────────────────────────────────

    @staticmethod
    def _safe_float(val):
        if val is None or val == '-' or val == '':
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0


if __name__ == '__main__':
    collector = AStockDataCollector()
    result = collector.run_screening()
    if result['success']:
        print(f"\n筛选完成! 共 {result['count']} 只股票")
    else:
        print(f"\n筛选失败: {result['error']}")
