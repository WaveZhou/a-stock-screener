"""
A股数据收集器
功能：
1. 获取A股所有股票列表
2. 获取市值数据，筛选市值倒数1000名
3. 获取归母净利润增速，筛选前30名
4. 获取选中股票的详细行情数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import json
import os


class AStockDataCollector:
    """A股数据收集器"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_all_stocks(self):
        """获取A股所有股票列表"""
        try:
            # 获取上海和深圳A股列表
            sh_stocks = ak.stock_sh_a_spot_em()
            sz_stocks = ak.stock_sz_a_spot_em()
            
            # 合并数据
            all_stocks = pd.concat([sh_stocks, sz_stocks], ignore_index=True)
            
            # 过滤掉ST、*ST、退市股票和北交所股票
            all_stocks = all_stocks[
                ~all_stocks['名称'].str.contains('ST|退|退市', na=False) &
                ~all_stocks['代码'].str.startswith('8', na=False) &  # 排除北交所
                ~all_stocks['代码'].str.startswith('4', na=False) &  # 排除新三板
                ~all_stocks['代码'].str.startswith('43', na=False)
            ]
            
            print(f"获取到 {len(all_stocks)} 只A股股票")
            return all_stocks
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_market_cap_data(self):
        """获取市值数据"""
        try:
            stocks = self.get_all_stocks()
            if stocks.empty:
                return pd.DataFrame()
            
            # 选择需要的列
            columns_needed = ['代码', '名称', '最新价', '涨跌幅', '换手率', 
                            '成交量', '成交额', '总市值', '流通市值',
                            '最高', '最低', '今开', '昨收']
            
            available_columns = [col for col in columns_needed if col in stocks.columns]
            stocks = stocks[available_columns].copy()
            
            # 确保总市值是数值类型
            stocks['总市值'] = pd.to_numeric(stocks['总市值'], errors='coerce')
            stocks = stocks.dropna(subset=['总市值'])
            
            return stocks
        except Exception as e:
            print(f"获取市值数据失败: {e}")
            return pd.DataFrame()
    
    def get_profit_growth_data(self, stock_codes):
        """获取归母净利润增速数据"""
        profit_growth_list = []
        
        for code in stock_codes:
            try:
                # 获取个股财务指标
                fina_data = ak.stock_financial_analysis_indicator(symbol=code)
                if fina_data is not None and not fina_data.empty:
                    # 获取最新的净利润同比增长率
                    latest_growth = fina_data.iloc[0].get('净利润同比增长率', None)
                    if latest_growth is not None:
                        profit_growth_list.append({
                            '代码': code,
                            '净利润同比增长率': float(str(latest_growth).replace('%', ''))
                        })
            except Exception as e:
                print(f"获取 {code} 净利润增速失败: {e}")
                continue
        
        return pd.DataFrame(profit_growth_list)
    
    def get_stock_kline(self, stock_code, period="daily"):
        """获取股票K线数据"""
        try:
            # 根据周期选择参数
            period_map = {
                "daily": "daily",
                "weekly": "weekly", 
                "monthly": "monthly"
            }
            
            ak_period = period_map.get(period, "daily")
            
            # 获取K线数据
            kline_data = ak.stock_zh_a_hist(
                symbol=stock_code,
                period=ak_period,
                start_date=(datetime.now() - timedelta(days=365*2)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust="qfq"  # 前复权
            )
            
            return kline_data
        except Exception as e:
            print(f"获取 {stock_code} {period} K线数据失败: {e}")
            return pd.DataFrame()
    
    def screen_stocks(self):
        """筛选股票：市值倒数1000名中净利润增速前30"""
        print("=" * 50)
        print("开始筛选股票...")
        print("=" * 50)
        
        # 1. 获取市值数据
        print("\n1. 获取市值数据...")
        market_cap_data = self.get_market_cap_data()
        if market_cap_data.empty:
            print("获取市值数据失败")
            return pd.DataFrame()
        
        print(f"获取到 {len(market_cap_data)} 只股票数据")
        
        # 2. 按市值升序排列，取倒数1000名（即市值最小的1000只）
        print("\n2. 筛选市值最小的1000只股票...")
        market_cap_data_sorted = market_cap_data.sort_values('总市值', ascending=True)
        small_cap_stocks = market_cap_data_sorted.head(1000).copy()
        print(f"筛选出 {len(small_cap_stocks)} 只小市值股票")
        
        # 3. 获取这1000只股票的净利润增速
        print("\n3. 获取净利润增速数据...")
        stock_codes = small_cap_stocks['代码'].tolist()
        profit_growth_df = self.get_profit_growth_data(stock_codes)
        
        if profit_growth_df.empty:
            print("获取净利润增速数据失败")
            return small_cap_stocks.head(30)
        
        print(f"获取到 {len(profit_growth_df)} 只股票的净利润增速")
        
        # 4. 合并数据
        print("\n4. 合并数据并筛选...")
        merged_data = small_cap_stocks.merge(profit_growth_df, on='代码', how='left')
        
        # 过滤掉净利润增速为空的
        merged_data = merged_data.dropna(subset=['净利润同比增长率'])
        
        # 5. 按净利润增速降序排列，取前30
        top_stocks = merged_data.sort_values('净利润同比增长率', ascending=False).head(30)
        
        print(f"\n最终筛选出 {len(top_stocks)} 只股票")
        print("\n前10只股票预览:")
        print(top_stocks[['代码', '名称', '总市值', '净利润同比增长率']].head(10).to_string(index=False))
        
        return top_stocks
    
    def save_screening_result(self, stocks_df):
        """保存筛选结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存为CSV
        csv_path = os.path.join(self.data_dir, f'screening_result_{timestamp}.csv')
        stocks_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # 保存为JSON
        json_path = os.path.join(self.data_dir, 'latest_screening_result.json')
        stocks_df.to_json(json_path, orient='records', force_ascii=False, indent=2)
        
        # 保存最新结果
        latest_csv = os.path.join(self.data_dir, 'latest_screening_result.csv')
        stocks_df.to_csv(latest_csv, index=False, encoding='utf-8-sig')
        
        print(f"\n结果已保存到:")
        print(f"  CSV: {csv_path}")
        print(f"  JSON: {json_path}")
        
        return csv_path, json_path
    
    def run_screening(self):
        """运行完整的筛选流程"""
        print("\n" + "=" * 50)
        print(f"A股小市值股票筛选 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # 执行筛选
        top_stocks = self.screen_stocks()
        
        if not top_stocks.empty:
            # 保存结果
            self.save_screening_result(top_stocks)
            
            # 返回结果
            return {
                'success': True,
                'count': len(top_stocks),
                'stocks': top_stocks.to_dict('records'),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': '筛选失败，未获取到数据',
                'timestamp': datetime.now().isoformat()
            }


if __name__ == '__main__':
    collector = AStockDataCollector()
    result = collector.run_screening()
    print("\n筛选完成!")