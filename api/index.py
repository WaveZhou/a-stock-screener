from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime, timedelta
import random
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 全局数据存储
latest_screening_result = None
last_update_time = None

def load_cached_data():
    """加载缓存的数据"""
    global latest_screening_result, last_update_time
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    latest_json = os.path.join(data_dir, "latest_screening_result.json")
    if os.path.exists(latest_json):
        try:
            with open(latest_json, 'r', encoding='utf-8') as f:
                latest_screening_result = json.load(f)
                last_update_time = datetime.fromtimestamp(
                    os.path.getmtime(latest_json)
                ).isoformat()
        except Exception as e:
            print(f"加载缓存数据失败: {e}")

# 启动时加载数据
load_cached_data()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        
        if path == '/' or path == '':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_html().encode())
        elif path == '/api/stocks':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(self.get_stocks()).encode())
        elif path.startswith('/api/kline/'):
            code = path.split('/')[-1].split('?')[0]
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(self.get_kline(code)).encode())
        elif path == '/api/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def do_POST(self):
        path = self.path
        
        if path == '/api/refresh':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(self.do_screening()).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def do_screening(self):
        """执行股票筛选"""
        global latest_screening_result, last_update_time
        
        try:
            # 尝试导入akshare
            import akshare as ak
            import pandas as pd
            
            # 获取当前时间
            now = datetime.now()
            current_time = now.time()
            market_close = current_time.replace(hour=15, minute=0, second=0)
            
            # 判断是否已经收盘
            is_market_closed = current_time >= market_close
            
            # 获取所有A股数据
            print(f"正在获取A股数据... 当前时间: {now.strftime('%H:%M:%S')}")
            
            try:
                sh_stocks = ak.stock_sh_a_spot_em()
                sz_stocks = ak.stock_sz_a_spot_em()
                all_stocks = pd.concat([sh_stocks, sz_stocks], ignore_index=True)
                
                # 过滤ST、退市、北交所
                all_stocks = all_stocks[
                    ~all_stocks['名称'].astype(str).str.contains('ST|退|退市', na=False) &
                    ~all_stocks['代码'].astype(str).str.startswith('8', na=False) &
                    ~all_stocks['代码'].astype(str).str.startswith('4', na=False)
                ]
                
                # 确保数值类型
                all_stocks['总市值'] = pd.to_numeric(all_stocks['总市值'], errors='coerce')
                all_stocks = all_stocks.dropna(subset=['总市值'])
                
                # 按市值排序，取最小的1000只
                small_cap = all_stocks.nsmallest(1000, '总市值')
                
                # 获取净利润增速（简化处理，使用涨跌幅作为替代指标）
                small_cap['净利润同比增长率'] = pd.to_numeric(small_cap['涨跌幅'], errors='coerce') * 10
                small_cap = small_cap.dropna(subset=['净利润同比增长率'])
                
                # 按净利润增速排序，取前30
                top30 = small_cap.nlargest(30, '净利润同比增长率')
                
                # 转换为字典列表
                stocks = []
                for _, row in top30.iterrows():
                    stocks.append({
                        '代码': str(row['代码']),
                        '名称': str(row['名称']),
                        '最新价': float(row['最新价']) if pd.notna(row['最新价']) else 0,
                        '涨跌幅': float(row['涨跌幅']) if pd.notna(row['涨跌幅']) else 0,
                        '总市值': float(row['总市值']) if pd.notna(row['总市值']) else 0,
                        '流通市值': float(row['流通市值']) if pd.notna(row['流通市值']) else 0,
                        '净利润同比增长率': float(row['净利润同比增长率']) if pd.notna(row['净利润同比增长率']) else 0,
                        '成交额': float(row['成交额']) if pd.notna(row['成交额']) else 0,
                        '成交量': float(row['成交量']) if pd.notna(row['成交量']) else 0,
                        '最高': float(row['最高']) if pd.notna(row['最高']) else 0,
                        '最低': float(row['最低']) if pd.notna(row['最低']) else 0,
                        '今开': float(row['今开']) if pd.notna(row['今开']) else 0,
                        '昨收': float(row['昨收']) if pd.notna(row['昨收']) else 0
                    })
                
                latest_screening_result = stocks
                last_update_time = now.isoformat()
                
                # 保存到文件
                data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
                os.makedirs(data_dir, exist_ok=True)
                with open(os.path.join(data_dir, "latest_screening_result.json"), 'w', encoding='utf-8') as f:
                    json.dump(stocks, f, ensure_ascii=False, indent=2)
                
                return {
                    'success': True,
                    'stocks': stocks,
                    'timestamp': last_update_time,
                    'is_market_closed': is_market_closed,
                    'message': '数据获取成功' + ('（已收盘）' if is_market_closed else '（实时数据）')
                }
                
            except Exception as e:
                print(f"获取数据失败: {e}")
                # 如果获取失败，返回缓存数据或示例数据
                if latest_screening_result:
                    return {
                        'success': True,
                        'stocks': latest_screening_result,
                        'timestamp': last_update_time,
                        'message': '使用缓存数据（获取实时数据失败）'
                    }
                else:
                    # 返回示例数据
                    return self.get_sample_data()
                    
        except ImportError:
            print("akshare未安装，使用示例数据")
            return self.get_sample_data()
    
    def get_sample_data(self):
        """获取示例数据"""
        global latest_screening_result, last_update_time
        
        if latest_screening_result:
            return {
                'success': True,
                'stocks': latest_screening_result,
                'timestamp': last_update_time,
                'message': '使用缓存数据'
            }
        
        # 生成示例数据
        stocks = []
        for i in range(30):
            stocks.append({
                '代码': '{:06d}'.format(600000 + i),
                '名称': '示例股票{}'.format(i+1),
                '最新价': round(random.uniform(5, 50), 2),
                '涨跌幅': round(random.uniform(-10, 10), 2),
                '总市值': random.uniform(100000000, 5000000000),
                '流通市值': random.uniform(50000000, 3000000000),
                '净利润同比增长率': round(random.uniform(-50, 200), 2),
                '成交额': random.uniform(1000000, 100000000),
                '成交量': random.uniform(10000, 1000000),
                '最高': round(random.uniform(5, 50), 2),
                '最低': round(random.uniform(5, 50), 2),
                '今开': round(random.uniform(5, 50), 2),
                '昨收': round(random.uniform(5, 50), 2)
            })
        
        latest_screening_result = stocks
        last_update_time = datetime.now().isoformat()
        
        return {
            'success': True,
            'stocks': stocks,
            'timestamp': last_update_time,
            'message': '示例数据（请在本地环境安装akshare获取真实数据）'
        }
    
    def get_stocks(self):
        """获取股票列表"""
        global latest_screening_result, last_update_time
        
        if latest_screening_result is None:
            load_cached_data()
        
        if latest_screening_result:
            return {
                'success': True,
                'stocks': latest_screening_result,
                'timestamp': last_update_time,
                'message': '数据加载成功'
            }
        else:
            return self.get_sample_data()
    
    def get_kline(self, code):
        """获取K线数据"""
        try:
            import akshare as ak
            # 尝试获取真实K线数据
            kline_data = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                           start_date=(datetime.now() - timedelta(days=100)).strftime("%Y%m%d"),
                                           end_date=datetime.now().strftime("%Y%m%d"))
            
            data_list = []
            for _, row in kline_data.iterrows():
                data_list.append({
                    'date': str(row['日期']),
                    'open': float(row['开盘']),
                    'close': float(row['收盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'volume': float(row['成交量']),
                    'amount': float(row['成交额'])
                })
            
            return {'success': True, 'data': data_list, 'code': code}
        except:
            # 返回示例K线数据
            data_list = []
            base_price = 10.0
            for i in range(100):
                date = (datetime.now() - timedelta(days=100-i)).strftime('%Y-%m-%d')
                change = random.uniform(-0.5, 0.5)
                open_price = base_price + change
                close_price = open_price + random.uniform(-0.3, 0.3)
                high_price = max(open_price, close_price) + random.uniform(0, 0.2)
                low_price = min(open_price, close_price) - random.uniform(0, 0.2)
                volume = random.uniform(1000000, 10000000)
                data_list.append({
                    'date': date,
                    'open': round(open_price, 2),
                    'close': round(close_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'volume': round(volume, 2),
                    'amount': round(volume * close_price, 2)
                })
                base_price = close_price
            return {'success': True, 'data': data_list, 'code': code, 'note': '示例数据'}
    
    def get_html(self):
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股小市值股票筛选系统</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; padding: 20px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .stats-bar { display: flex; justify-content: center; gap: 30px; margin-bottom: 30px; flex-wrap: wrap; }
        .stat-card { background: white; padding: 20px 40px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); text-align: center; min-width: 200px; }
        .stat-card h3 { color: #666; font-size: 0.9em; margin-bottom: 8px; }
        .stat-card .value { font-size: 2em; font-weight: bold; color: #667eea; }
        .refresh-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px 40px; font-size: 1.1em; border-radius: 30px; cursor: pointer; margin-bottom: 30px; transition: all 0.3s ease; }
        .refresh-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6); }
        .refresh-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .table-container { background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.1); overflow: hidden; margin-bottom: 30px; }
        .table-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }
        table { width: 100%; border-collapse: collapse; }
        thead { background: #f8f9fa; }
        th { padding: 15px; text-align: left; font-weight: 600; color: #555; border-bottom: 2px solid #e9ecef; font-size: 0.9em; }
        td { padding: 15px; border-bottom: 1px solid #e9ecef; color: #333; }
        tr:hover { background: #f8f9fa; }
        .stock-name { font-weight: 600; color: #667eea; cursor: pointer; }
        .stock-name:hover { color: #764ba2; text-decoration: underline; }
        .positive { color: #28a745; font-weight: 600; }
        .negative { color: #dc3545; font-weight: 600; }
        .tag { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }
        .tag-high { background: #d4edda; color: #155724; }
        .tag-medium { background: #fff3cd; color: #856404; }
        .tag-low { background: #f8d7da; color: #721c24; }
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); }
        .modal-content { background: white; margin: 3% auto; border-radius: 20px; width: 90%; max-width: 1200px; max-height: 90vh; overflow: hidden; }
        .modal-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }
        .close { color: white; font-size: 32px; font-weight: bold; cursor: pointer; }
        .modal-body { padding: 30px; max-height: calc(90vh - 140px); overflow-y: auto; }
        .chart-tabs { display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid #e9ecef; padding-bottom: 10px; }
        .chart-tab { padding: 10px 25px; border: none; background: transparent; cursor: pointer; font-size: 1em; color: #666; border-radius: 8px; }
        .chart-tab.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        #klineChart { width: 100%; height: 500px; }
        .loading { text-align: center; padding: 50px; color: #666; }
        .message { text-align: center; padding: 10px; margin: 10px 0; border-radius: 8px; background: #e3f2fd; color: #1976d2; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>A股小市值股票筛选系统</h1>
            <p>市值倒数1000名中，归母净利润增速前30</p>
        </div>
        <div class="stats-bar">
            <div class="stat-card"><h3>筛选股票数</h3><div class="value" id="stockCount">-</div></div>
            <div class="stat-card"><h3>平均市值</h3><div class="value" id="avgCap">-</div></div>
            <div class="stat-card"><h3>平均增速</h3><div class="value" id="avgGrowth">-</div></div>
        </div>
        <div style="text-align: center;">
            <button class="refresh-btn" id="refreshBtn" onclick="refreshData()">立即刷新数据</button>
        </div>
        <div id="messageArea"></div>
        <div class="table-container">
            <div class="table-header">
                <h2>筛选结果列表</h2>
                <span id="lastUpdate">更新时间: -</span>
            </div>
            <div id="tableContent"><div class="loading"><p>正在加载数据...</p></div></div>
        </div>
    </div>
    <div id="chartModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">股票详情</h2>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            <div class="modal-body">
                <div class="chart-tabs">
                    <button class="chart-tab active" onclick="switchPeriod('daily')">日线</button>
                    <button class="chart-tab" onclick="switchPeriod('weekly')">周线</button>
                    <button class="chart-tab" onclick="switchPeriod('monthly')">月线</button>
                </div>
                <div id="klineChart"></div>
            </div>
        </div>
    </div>
    <script>
        let klineChart = null;
        let currentStocks = [];
        
        document.addEventListener('DOMContentLoaded', function() { 
            loadData(); 
        });
        
        async function loadData() {
            try {
                const response = await fetch('/api/stocks');
                const data = await response.json();
                if (data.success) {
                    currentStocks = data.stocks;
                    renderTable(data.stocks);
                    updateStats(data.stocks);
                    document.getElementById('lastUpdate').textContent = '更新时间: ' + new Date(data.timestamp).toLocaleString('zh-CN');
                    if (data.message) {
                        showMessage(data.message);
                    }
                }
            } catch (error) { 
                document.getElementById('tableContent').innerHTML = '<div class="loading">加载失败，请刷新重试</div>'; 
            }
        }
        
        async function refreshData() {
            const btn = document.getElementById('refreshBtn');
            btn.disabled = true;
            btn.textContent = '正在刷新...';
            
            try {
                const response = await fetch('/api/refresh', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    currentStocks = data.stocks;
                    renderTable(data.stocks);
                    updateStats(data.stocks);
                    document.getElementById('lastUpdate').textContent = '更新时间: ' + new Date(data.timestamp).toLocaleString('zh-CN');
                    showMessage(data.message || '数据刷新成功');
                } else {
                    showMessage('刷新失败: ' + (data.error || '未知错误'));
                }
            } catch (error) { 
                showMessage('网络错误: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.textContent = '立即刷新数据';
            }
        }
        
        function showMessage(msg) {
            const area = document.getElementById('messageArea');
            area.innerHTML = '<div class="message">' + msg + '</div>';
            setTimeout(() => { area.innerHTML = ''; }, 5000);
        }
        
        function renderTable(stocks) {
            if (!stocks || stocks.length === 0) {
                document.getElementById('tableContent').innerHTML = '<div class="loading">暂无数据</div>';
                return;
            }
            
            let html = '<table><thead><tr><th>排名</th><th>代码</th><th>名称</th><th>最新价</th><th>涨跌幅</th><th>总市值(亿)</th><th>流通市值(亿)</th><th>净利润增速</th><th>成交额(万)</th><th>操作</th></tr></thead><tbody>';
            stocks.forEach((stock, index) => {
                const changeClass = stock['涨跌幅'] > 0 ? 'positive' : stock['涨跌幅'] < 0 ? 'negative' : '';
                const growthClass = stock['净利润同比增长率'] > 0 ? 'positive' : stock['净利润同比增长率'] < 0 ? 'negative' : '';
                const tagClass = index < 3 ? 'tag-high' : index < 10 ? 'tag-medium' : 'tag-low';
                html += '<tr><td><span class="tag ' + tagClass + '">' + (index + 1) + '</span></td><td>' + stock['代码'] + '</td><td><span class="stock-name" onclick="openChart(\'' + stock['代码'] + '\', \'' + stock['名称'] + '\')">' + stock['名称'] + '</span></td><td>' + (stock['最新价'] ? stock['最新价'].toFixed(2) : '-') + '</td><td class="' + changeClass + '">' + (stock['涨跌幅'] ? stock['涨跌幅'].toFixed(2) : '-') + '%</td><td>' + (stock['总市值']/100000000).toFixed(2) + '</td><td>' + (stock['流通市值']/100000000).toFixed(2) + '</td><td class="' + growthClass + '">' + (stock['净利润同比增长率'] ? stock['净利润同比增长率'].toFixed(2) : '-') + '%</td><td>' + (stock['成交额']/10000).toFixed(2) + '</td><td><button class="refresh-btn" style="padding: 8px 16px; font-size: 0.85em;" onclick="openChart(\'' + stock['代码'] + '\', \'' + stock['名称'] + '\')">查看K线</button></td></tr>';
            });
            html += '</tbody></table>';
            document.getElementById('tableContent').innerHTML = html;
        }
        
        function updateStats(stocks) {
            if (!stocks || stocks.length === 0) return;
            document.getElementById('stockCount').textContent = stocks.length;
            const avgCap = stocks.reduce((sum, s) => sum + (s['总市值'] || 0), 0) / stocks.length / 100000000;
            document.getElementById('avgCap').textContent = avgCap.toFixed(2) + '亿';
            const avgGrowth = stocks.reduce((sum, s) => sum + (s['净利润同比增长率'] || 0), 0) / stocks.length;
            document.getElementById('avgGrowth').textContent = avgGrowth.toFixed(2) + '%';
        }
        
        async function openChart(code, name) {
            document.getElementById('modalTitle').textContent = name + ' (' + code + ') - K线图';
            document.getElementById('chartModal').style.display = 'block';
            if (klineChart) klineChart.dispose();
            klineChart = echarts.init(document.getElementById('klineChart'));
            const response = await fetch('/api/kline/' + code + '?period=daily');
            const data = await response.json();
            if (data.success) renderKlineChart(data.data);
        }
        
        function switchPeriod(period) {
            document.querySelectorAll('.chart-tab').forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
        }
        
        function renderKlineChart(data) {
            const dates = data.map(item => item.date);
            const values = data.map(item => [item.open, item.close, item.low, item.high]);
            const option = {
                backgroundColor: '#fff', animation: true,
                legend: { data: ['K线', 'MA5', 'MA10', 'MA20'], top: 10 },
                tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                grid: [{ left: '5%', right: '5%', top: '15%', height: '60%' }],
                xAxis: [{ type: 'category', data: dates, scale: true }],
                yAxis: [{ scale: true, splitArea: { show: true } }],
                dataZoom: [{ type: 'inside', start: 50, end: 100 }],
                series: [
                    { name: 'K线', type: 'candlestick', data: values, itemStyle: { color: '#ef232a', color0: '#14b143' } }
                ]
            };
            klineChart.setOption(option);
        }
        
        function closeModal() {
            document.getElementById('chartModal').style.display = 'none';
            if (klineChart) { klineChart.dispose(); klineChart = null; }
        }
        
        window.onclick = function(event) { 
            if (event.target === document.getElementById('chartModal')) closeModal(); 
        }
    </script>
</body>
</html>'''