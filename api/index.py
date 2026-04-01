from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime, timedelta
import random
import os

DEFAULT_STOCKS = [
    {"代码": "300001", "名称": "特锐德", "最新价": 22.58, "涨跌幅": 5.23, "总市值": 2358000000, "流通市值": 2100000000, "净利润同比增长率": 158.5, "成交额": 125000000},
    {"代码": "300002", "名称": "神州泰岳", "最新价": 12.35, "涨跌幅": 3.85, "总市值": 2420000000, "流通市值": 1980000000, "净利润同比增长率": 142.3, "成交额": 98000000},
    {"代码": "300003", "名称": "乐普医疗", "最新价": 15.68, "涨跌幅": -1.25, "总市值": 2850000000, "流通市值": 2450000000, "净利润同比增长率": 125.8, "成交额": 87000000},
    {"代码": "300004", "名称": "南风股份", "最新价": 8.95, "涨跌幅": 8.56, "总市值": 1850000000, "流通市值": 1520000000, "净利润同比增长率": 118.6, "成交额": 156000000},
    {"代码": "300005", "名称": "探路者", "最新价": 6.85, "涨跌幅": 4.12, "总市值": 1650000000, "流通市值": 1280000000, "净利润同比增长率": 108.9, "成交额": 68000000},
    {"代码": "300006", "名称": "莱美药业", "最新价": 4.58, "涨跌幅": 6.78, "总市值": 1250000000, "流通市值": 980000000, "净利润同比增长率": 98.5, "成交额": 92000000},
    {"代码": "300007", "名称": "汉威科技", "最新价": 18.35, "涨跌幅": 2.45, "总市值": 1950000000, "流通市值": 1650000000, "净利润同比增长率": 95.2, "成交额": 78000000},
    {"代码": "300008", "名称": "天海防务", "最新价": 5.28, "涨跌幅": 7.35, "总市值": 1450000000, "流通市值": 1150000000, "净利润同比增长率": 92.8, "成交额": 112000000},
    {"代码": "300009", "名称": "安科生物", "最新价": 11.25, "涨跌幅": 1.85, "总市值": 2150000000, "流通市值": 1750000000, "净利润同比增长率": 88.6, "成交额": 65000000},
    {"代码": "300010", "名称": "立思辰", "最新价": 7.85, "涨跌幅": 5.65, "总市值": 1350000000, "流通市值": 1050000000, "净利润同比增长率": 85.3, "成交额": 89000000},
    {"代码": "300011", "名称": "鼎汉技术", "最新价": 9.58, "涨跌幅": 3.25, "总市值": 1680000000, "流通市值": 1320000000, "净利润同比增长率": 82.7, "成交额": 72000000},
    {"代码": "300012", "名称": "华测检测", "最新价": 16.85, "涨跌幅": -0.58, "总市值": 2820000000, "流通市值": 2250000000, "净利润同比增长率": 78.9, "成交额": 58000000},
    {"代码": "300013", "名称": "新宁物流", "最新价": 4.25, "涨跌幅": 9.25, "总市值": 1150000000, "流通市值": 890000000, "净利润同比增长率": 75.6, "成交额": 128000000},
    {"代码": "300014", "名称": "亿纬锂能", "最新价": 58.35, "涨跌幅": 4.85, "总市值": 2850000000, "流通市值": 2380000000, "净利润同比增长率": 72.3, "成交额": 185000000},
    {"代码": "300015", "名称": "爱尔眼科", "最新价": 18.95, "涨跌幅": 2.15, "总市值": 3250000000, "流通市值": 2680000000, "净利润同比增长率": 68.5, "成交额": 95000000},
    {"代码": "300016", "名称": "北陆药业", "最新价": 8.35, "涨跌幅": 6.25, "总市值": 1450000000, "流通市值": 1120000000, "净利润同比增长率": 65.8, "成交额": 82000000},
    {"代码": "300017", "名称": "网宿科技", "最新价": 9.85, "涨跌幅": 1.55, "总市值": 2350000000, "流通市值": 1950000000, "净利润同比增长率": 62.4, "成交额": 68000000},
    {"代码": "300018", "名称": "中元股份", "最新价": 6.45, "涨跌幅": 5.85, "总市值": 1250000000, "流通市值": 980000000, "净利润同比增长率": 58.9, "成交额": 76000000},
    {"代码": "300019", "名称": "硅宝科技", "最新价": 15.25, "涨跌幅": 3.45, "总市值": 1850000000, "流通市值": 1480000000, "净利润同比增长率": 55.2, "成交额": 62000000},
    {"代码": "300020", "名称": "银江技术", "最新价": 11.85, "涨跌幅": 4.95, "总市值": 1550000000, "流通市值": 1250000000, "净利润同比增长率": 52.8, "成交额": 71000000},
    {"代码": "300021", "名称": "大禹节水", "最新价": 5.95, "涨跌幅": 7.20, "总市值": 1350000000, "流通市值": 1050000000, "净利润同比增长率": 48.6, "成交额": 85000000},
    {"代码": "300022", "名称": "吉峰科技", "最新价": 4.85, "涨跌幅": 8.50, "总市值": 1150000000, "流通市值": 890000000, "净利润同比增长率": 45.3, "成交额": 98000000},
    {"代码": "300023", "名称": "宝德退", "最新价": 3.25, "涨跌幅": -2.50, "总市值": 950000000, "流通市值": 720000000, "净利润同比增长率": 42.5, "成交额": 45000000},
    {"代码": "300024", "名称": "机器人", "最新价": 13.85, "涨跌幅": 2.95, "总市值": 2150000000, "流通市值": 1780000000, "净利润同比增长率": 38.9, "成交额": 72000000},
    {"代码": "300025", "名称": "华星创业", "最新价": 7.25, "涨跌幅": 6.80, "总市值": 1450000000, "流通市值": 1150000000, "净利润同比增长率": 35.6, "成交额": 88000000},
    {"代码": "300026", "名称": "红日药业", "最新价": 6.15, "涨跌幅": 4.25, "总市值": 1850000000, "流通市值": 1450000000, "净利润同比增长率": 32.4, "成交额": 76000000},
    {"代码": "300027", "名称": "华谊兄弟", "最新价": 2.85, "涨跌幅": 9.60, "总市值": 1050000000, "流通市值": 780000000, "净利润同比增长率": 28.5, "成交额": 125000000},
    {"代码": "300028", "名称": "金亚退", "最新价": 2.15, "涨跌幅": -5.20, "总市值": 850000000, "流通市值": 620000000, "净利润同比增长率": 25.8, "成交额": 38000000},
    {"代码": "300029", "名称": "天龙光电", "最新价": 5.65, "涨跌幅": 5.40, "总市值": 1350000000, "流通市值": 1050000000, "净利润同比增长率": 22.6, "成交额": 68000000},
    {"代码": "300030", "名称": "阳普医疗", "最新价": 8.95, "涨跌幅": 3.80, "总市值": 1650000000, "流通市值": 1280000000, "净利润同比增长率": 18.5, "成交额": 58000000}
]

HTML_CONTENT = '''<!DOCTYPE html>
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
        .refresh-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6); }
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
        .message { text-align: center; padding: 10px; margin: 10px 0; border-radius: 8px; background: #e3f2fd; color: #1976d2; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>A股小市值股票筛选系统</h1>
            <p>市值倒数100名中，归母净利润增速前30</p>
        </div>
        <div class="stats-bar">
            <div class="stat-card"><h3>筛选股票数</h3><div class="value" id="stockCount">30</div></div>
            <div class="stat-card"><h3>平均市值</h3><div class="value" id="avgCap">-</div></div>
            <div class="stat-card"><h3>平均增速</h3><div class="value" id="avgGrowth">-</div></div>
        </div>
        <div style="text-align: center;">
            <button class="refresh-btn" id="refreshBtn">立即刷新数据</button>
        </div>
        <div id="messageArea"></div>
        <div class="table-container">
            <div class="table-header">
                <h2>筛选结果列表</h2>
                <span id="lastUpdate">更新时间: -</span>
            </div>
            <div id="tableContent"></div>
        </div>
    </div>
    <div id="chartModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">股票详情</h2>
                <span class="close" id="closeBtn">&times;</span>
            </div>
            <div class="modal-body">
                <div class="chart-tabs">
                    <button class="chart-tab active" data-period="daily">日线</button>
                    <button class="chart-tab" data-period="weekly">周线</button>
                    <button class="chart-tab" data-period="monthly">月线</button>
                </div>
                <div id="klineChart"></div>
            </div>
        </div>
    </div>
    <script>
        var klineChart = null;
        var currentStocks = [];
        
        document.addEventListener('DOMContentLoaded', function() { 
            document.getElementById('refreshBtn').addEventListener('click', refreshData);
            document.getElementById('closeBtn').addEventListener('click', closeModal);
            
            var tabs = document.querySelectorAll('.chart-tab');
            for (var i = 0; i < tabs.length; i++) {
                tabs[i].addEventListener('click', function() {
                    for (var j = 0; j < tabs.length; j++) {
                        tabs[j].classList.remove('active');
                    }
                    this.classList.add('active');
                });
            }
            
            window.addEventListener('click', function(event) {
                if (event.target === document.getElementById('chartModal')) {
                    closeModal();
                }
            });
            
            loadData();
        });
        
        function loadData() {
            fetch('/api/stocks')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success) {
                        currentStocks = data.stocks;
                        renderTable(data.stocks);
                        updateStats(data.stocks);
                        document.getElementById('lastUpdate').textContent = '更新时间: ' + new Date(data.timestamp).toLocaleString('zh-CN');
                        if (data.message) {
                            showMessage(data.message);
                        }
                    }
                })
                .catch(function(error) { 
                    document.getElementById('tableContent').innerHTML = '<div style="padding: 50px; text-align: center;">加载失败，请刷新重试</div>'; 
                });
        }
        
        function refreshData() {
            var btn = document.getElementById('refreshBtn');
            btn.disabled = true;
            btn.textContent = '正在刷新...';
            
            fetch('/api/refresh', { method: 'POST' })
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success) {
                        currentStocks = data.stocks;
                        renderTable(data.stocks);
                        updateStats(data.stocks);
                        document.getElementById('lastUpdate').textContent = '更新时间: ' + new Date(data.timestamp).toLocaleString('zh-CN');
                        showMessage(data.message || '数据刷新成功');
                    } else {
                        showMessage('刷新失败: ' + (data.error || '未知错误'));
                    }
                })
                .catch(function(error) { 
                    showMessage('网络错误: ' + error.message);
                })
                .finally(function() {
                    btn.disabled = false;
                    btn.textContent = '立即刷新数据';
                });
        }
        
        function showMessage(msg) {
            var area = document.getElementById('messageArea');
            area.innerHTML = '<div class="message">' + msg + '</div>';
            setTimeout(function() { area.innerHTML = ''; }, 5000);
        }
        
        function renderTable(stocks) {
            if (!stocks || stocks.length === 0) {
                document.getElementById('tableContent').innerHTML = '<div style="padding: 50px; text-align: center;">暂无数据</div>';
                return;
            }
            
            var html = '<table><thead><tr><th>排名</th><th>代码</th><th>名称</th><th>最新价</th><th>涨跌幅</th><th>总市值(亿)</th><th>流通市值(亿)</th><th>净利润增速</th><th>成交额(万)</th><th>操作</th></tr></thead><tbody>';
            for (var i = 0; i < stocks.length; i++) {
                var stock = stocks[i];
                var changeClass = stock['涨跌幅'] > 0 ? 'positive' : stock['涨跌幅'] < 0 ? 'negative' : '';
                var growthClass = stock['净利润同比增长率'] > 0 ? 'positive' : stock['净利润同比增长率'] < 0 ? 'negative' : '';
                var tagClass = i < 3 ? 'tag-high' : i < 10 ? 'tag-medium' : 'tag-low';
                var latestPrice = stock['最新价'] ? stock['最新价'].toFixed(2) : '-';
                var changePct = stock['涨跌幅'] ? stock['涨跌幅'].toFixed(2) : '-';
                var totalCap = (stock['总市值']/100000000).toFixed(2);
                var floatCap = (stock['流通市值']/100000000).toFixed(2);
                var growth = stock['净利润同比增长率'] ? stock['净利润同比增长率'].toFixed(2) : '-';
                var turnover = (stock['成交额']/10000).toFixed(2);
                html += '<tr><td><span class="tag ' + tagClass + '">' + (i + 1) + '</span></td><td>' + stock['代码'] + '</td><td><span class="stock-name" data-code="' + stock['代码'] + '" data-name="' + stock['名称'] + '">' + stock['名称'] + '</span></td><td>' + latestPrice + '</td><td class="' + changeClass + '">' + changePct + '%</td><td>' + totalCap + '</td><td>' + floatCap + '</td><td class="' + growthClass + '">' + growth + '%</td><td>' + turnover + '</td><td><button class="refresh-btn chart-btn" style="padding: 8px 16px; font-size: 0.85em;" data-code="' + stock['代码'] + '" data-name="' + stock['名称'] + '">查看K线</button></td></tr>';
            }
            html += '</tbody></table>';
            document.getElementById('tableContent').innerHTML = html;
            
            var stockNames = document.querySelectorAll('.stock-name');
            for (var j = 0; j < stockNames.length; j++) {
                stockNames[j].addEventListener('click', function() {
                    openChart(this.getAttribute('data-code'), this.getAttribute('data-name'));
                });
            }
            
            var chartBtns = document.querySelectorAll('.chart-btn');
            for (var k = 0; k < chartBtns.length; k++) {
                chartBtns[k].addEventListener('click', function() {
                    openChart(this.getAttribute('data-code'), this.getAttribute('data-name'));
                });
            }
        }
        
        function updateStats(stocks) {
            if (!stocks || stocks.length === 0) return;
            document.getElementById('stockCount').textContent = stocks.length;
            var totalCap = 0;
            var totalGrowth = 0;
            for (var i = 0; i < stocks.length; i++) {
                totalCap += (stocks[i]['总市值'] || 0);
                totalGrowth += (stocks[i]['净利润同比增长率'] || 0);
            }
            var avgCap = totalCap / stocks.length / 100000000;
            var avgGrowth = totalGrowth / stocks.length;
            document.getElementById('avgCap').textContent = avgCap.toFixed(2) + '亿';
            document.getElementById('avgGrowth').textContent = avgGrowth.toFixed(2) + '%';
        }
        
        function openChart(code, name) {
            document.getElementById('modalTitle').textContent = name + ' (' + code + ') - K线图';
            document.getElementById('chartModal').style.display = 'block';
            if (klineChart) klineChart.dispose();
            klineChart = echarts.init(document.getElementById('klineChart'));
            fetch('/api/kline/' + code + '?period=daily')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success) renderKlineChart(data.data);
                });
        }
        
        function renderKlineChart(data) {
            var dates = [];
            var values = [];
            for (var i = 0; i < data.length; i++) {
                dates.push(data[i].date);
                values.push([data[i].open, data[i].close, data[i].low, data[i].high]);
            }
            var option = {
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
    </script>
</body>
</html>'''

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        
        if path == '/' or path == '':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode())
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
    
    def get_stocks(self):
        """页面加载时获取数据 - 优先读取本地真实数据"""
        return self.do_screening()
    
    def do_screening(self):
        """
        执行股票筛选 - 返回最新的本地数据
        由于Vercel Serverless环境无法直接访问外部API，
        数据由GitHub Actions每日更新到 screening_result.json
        """
        # 尝试读取本地数据文件
        try:
            # 首先尝试读取根目录的 screening_result.json
            result_path = os.path.join(os.path.dirname(__file__), '..', 'screening_result.json')
            if os.path.exists(result_path):
                with open(result_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data and 'stocks' in data and len(data['stocks']) > 0:
                        return {
                            'success': True,
                            'stocks': data['stocks'],
                            'timestamp': data.get('timestamp', datetime.now().isoformat()),
                            'message': '已获取最新筛选数据'
                        }
        except Exception as e:
            print(f"读取根目录数据文件失败: {e}")
        
        try:
            # 尝试读取 api 目录下的数据文件
            result_path = os.path.join(os.path.dirname(__file__), 'screening_result.json')
            if os.path.exists(result_path):
                with open(result_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data and 'stocks' in data and len(data['stocks']) > 0:
                        return {
                            'success': True,
                            'stocks': data['stocks'],
                            'timestamp': data.get('timestamp', datetime.now().isoformat()),
                            'message': '已获取最新筛选数据'
                        }
        except Exception as e:
            print(f"读取api目录数据文件失败: {e}")
        
        # 如果都没有，返回默认数据
        return {
            'success': True,
            'stocks': DEFAULT_STOCKS,
            'timestamp': datetime.now().isoformat(),
            'message': '显示示例数据。GitHub Actions每天14:30自动更新真实数据。'
        }
    
    def get_kline(self, code):
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
        return {'success': True, 'data': data_list, 'code': code}