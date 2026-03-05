"""
Vercel Serverless Function Entry Point
适配Vercel Serverless环境的入口文件
"""

import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json

# 导入数据收集器和邮件发送器
try:
    from data_collector import AStockDataCollector
    from email_sender import EmailSender
except ImportError:
    # 如果在Vercel环境中，可能需要调整导入路径
    import importlib.util
    spec = importlib.util.spec_from_file_location("data_collector", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_collector.py"))
    data_collector_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data_collector_module)
    AStockDataCollector = data_collector_module.AStockDataCollector
    
    spec = importlib.util.spec_from_file_location("email_sender", os.path.join(os.path.dirname(os.path.dirname(__file__)), "email_sender.py"))
    email_sender_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(email_sender_module)
    EmailSender = email_sender_module.EmailSender

# 创建FastAPI应用
app = FastAPI(
    title="A股小市值股票筛选系统",
    description="筛选市值倒数1000名中净利润增速前30的股票",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模板目录
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates_dir = os.path.join(base_dir, "templates")

# 数据目录
data_dir = os.path.join(base_dir, "data")
os.makedirs(data_dir, exist_ok=True)

# 全局数据存储
latest_screening_result = None
last_update_time = None


def load_cached_data():
    """加载缓存的数据"""
    global latest_screening_result, last_update_time
    
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


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页 - 返回HTML"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股小市值股票筛选系统</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            padding: 20px;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .stats-bar {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .stat-card {
            background: white;
            padding: 20px 40px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            text-align: center;
            min-width: 200px;
        }
        .stat-card h3 { color: #666; font-size: 0.9em; margin-bottom: 8px; }
        .stat-card .value { font-size: 2em; font-weight: bold; color: #667eea; }
        .refresh-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.1em;
            border-radius: 30px;
            cursor: pointer;
            margin-bottom: 30px;
            transition: all 0.3s ease;
        }
        .refresh-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6); }
        .refresh-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .table-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            overflow: hidden;
            margin-bottom: 30px;
        }
        .table-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        table { width: 100%; border-collapse: collapse; }
        thead { background: #f8f9fa; }
        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #555;
            border-bottom: 2px solid #e9ecef;
            font-size: 0.9em;
        }
        td {
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
            color: #333;
        }
        tr:hover { background: #f8f9fa; }
        .stock-name {
            font-weight: 600;
            color: #667eea;
            cursor: pointer;
        }
        .stock-name:hover { color: #764ba2; text-decoration: underline; }
        .positive { color: #28a745; font-weight: 600; }
        .negative { color: #dc3545; font-weight: 600; }
        .neutral { color: #6c757d; }
        .tag {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
        }
        .tag-high { background: #d4edda; color: #155724; }
        .tag-medium { background: #fff3cd; color: #856404; }
        .tag-low { background: #f8d7da; color: #721c24; }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
        }
        .modal-content {
            background: white;
            margin: 3% auto;
            border-radius: 20px;
            width: 90%;
            max-width: 1200px;
            max-height: 90vh;
            overflow: hidden;
            box-shadow: 0 25px 80px rgba(0,0,0,0.3);
        }
        .modal-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .close { color: white; font-size: 32px; font-weight: bold; cursor: pointer; }
        .modal-body { padding: 30px; max-height: calc(90vh - 140px); overflow-y: auto; }
        .chart-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }
        .chart-tab {
            padding: 10px 25px;
            border: none;
            background: transparent;
            cursor: pointer;
            font-size: 1em;
            color: #666;
            border-radius: 8px;
        }
        .chart-tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        #klineChart { width: 100%; height: 500px; }
        .stock-info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .info-card { background: #f8f9fa; padding: 20px; border-radius: 12px; text-align: center; }
        .info-card h4 { color: #666; font-size: 0.85em; margin-bottom: 8px; }
        .info-card .value { font-size: 1.5em; font-weight: bold; color: #333; }
        .loading { text-align: center; padding: 50px; color: #666; }
        .loading-spinner {
            display: inline-block;
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 15px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .error-message { background: #f8d7da; color: #721c24; padding: 20px; border-radius: 10px; text-align: center; margin: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 A股小市值股票筛选系统</h1>
            <p>市值倒数1000名中，归母净利润增速前30</p>
        </div>
        <div class="stats-bar">
            <div class="stat-card">
                <h3>筛选股票数</h3>
                <div class="value" id="stockCount">-</div>
            </div>
            <div class="stat-card">
                <h3>平均市值</h3>
                <div class="value" id="avgCap">-</div>
            </div>
            <div class="stat-card">
                <h3>平均增速</h3>
                <div class="value" id="avgGrowth">-</div>
            </div>
        </div>
        <div style="text-align: center;">
            <button class="refresh-btn" id="refreshBtn" onclick="refreshData()">🔄 立即刷新数据</button>
        </div>
        <div class="table-container">
            <div class="table-header">
                <h2>📈 筛选结果列表</h2>
                <span class="last-update" id="lastUpdate">更新时间: -</span>
            </div>
            <div id="tableContent">
                <div class="loading">
                    <div class="loading-spinner"></div>
                    <p>正在加载数据...</p>
                </div>
            </div>
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
                <div class="stock-info-grid" id="stockInfoGrid"></div>
            </div>
        </div>
    </div>
    <script>
        let currentStock = null, currentPeriod = 'daily', klineChart = null;
        document.addEventListener('DOMContentLoaded', function() { loadData(); });
        async function loadData() {
            try {
                const response = await fetch('/api/stocks');
                const data = await response.json();
                if (data.success) {
                    renderTable(data.stocks);
                    updateStats(data.stocks);
                    document.getElementById('lastUpdate').textContent = '更新时间: ' + new Date(data.timestamp).toLocaleString('zh-CN');
                } else { showError(data.error || '加载数据失败'); }
            } catch (error) { showError('网络错误: ' + error.message); }
        }
        async function refreshData() {
            const btn = document.getElementById('refreshBtn');
            btn.disabled = true; btn.textContent = '⏳ 正在刷新...';
            try {
                const response = await fetch('/api/refresh', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    renderTable(data.stocks); updateStats(data.stocks);
                    document.getElementById('lastUpdate').textContent = '更新时间: ' + new Date(data.timestamp).toLocaleString('zh-CN');
                    alert('✅ 数据刷新成功！');
                } else { alert('❌ 刷新失败: ' + (data.error || '未知错误')); }
            } catch (error) { alert('❌ 网络错误: ' + error.message); }
            finally { btn.disabled = false; btn.textContent = '🔄 立即刷新数据'; }
        }
        function renderTable(stocks) {
            const tableHtml = `<table><thead><tr><th>排名</th><th>代码</th><th>名称</th><th>最新价</th><th>涨跌幅</th><th>总市值(亿)</th><th>流通市值(亿)</th><th>净利润增速</th><th>成交额(万)</th><th>操作</th></tr></thead><tbody>` +
                stocks.map((stock, index) => {
                    const changeClass = stock['涨跌幅'] > 0 ? 'positive' : stock['涨跌幅'] < 0 ? 'negative' : 'neutral';
                    const growthClass = stock['净利润同比增长率'] > 0 ? 'positive' : stock['净利润同比增长率'] < 0 ? 'negative' : 'neutral';
                    return `<tr><td><span class="tag ${index < 3 ? 'tag-high' : index < 10 ? 'tag-medium' : 'tag-low'}">${index + 1}</span></td><td>${stock['代码']}</td><td><span class="stock-name" onclick="openChart('${stock['代码']}', '${stock['名称']}')">${stock['名称']}</span></td><td>${stock['最新价'] ? stock['最新价'].toFixed(2) : '-'}</td><td class="${changeClass}">${stock['涨跌幅'] ? stock['涨跌幅'].toFixed(2) + '%' : '-'}</td><td>${(stock['总市值'] / 100000000).toFixed(2)}</td><td>${(stock['流通市值'] / 100000000).toFixed(2)}</td><td class="${growthClass}">${stock['净利润同比增长率'] ? stock['净利润同比增长率'].toFixed(2) + '%' : '-'}</td><td>${(stock['成交额'] / 10000).toFixed(2)}</td><td><button class="refresh-btn" style="padding: 8px 16px; font-size: 0.85em;" onclick="openChart('${stock['代码']}', '${stock['名称']}')">查看K线</button></td></tr>`;
                }).join('') + `</tbody></table>`;
            document.getElementById('tableContent').innerHTML = tableHtml;
        }
        function updateStats(stocks) {
            document.getElementById('stockCount').textContent = stocks.length;
            const avgCap = stocks.reduce((sum, s) => sum + (s['总市值'] || 0), 0) / stocks.length / 100000000;
            document.getElementById('avgCap').textContent = avgCap.toFixed(2) + '亿';
            const avgGrowth = stocks.reduce((sum, s) => sum + (s['净利润同比增长率'] || 0), 0) / stocks.length;
            document.getElementById('avgGrowth').textContent = avgGrowth.toFixed(2) + '%';
        }
        function showError(message) { document.getElementById('tableContent').innerHTML = `<div class="error-message">${message}</div>`; }
        async function openChart(code, name) {
            currentStock = { code, name }; currentPeriod = 'daily';
            document.getElementById('modalTitle').textContent = name + ' (' + code + ') - K线图';
            document.getElementById('chartModal').style.display = 'block';
            if (klineChart) klineChart.dispose();
            klineChart = echarts.init(document.getElementById('klineChart'));
            await loadKlineData(code, 'daily');
            await loadStockInfo(code);
        }
        async function switchPeriod(period) {
            currentPeriod = period;
            document.querySelectorAll('.chart-tab').forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
            if (currentStock) await loadKlineData(currentStock.code, period);
        }
        async function loadKlineData(code, period) {
            klineChart.showLoading({ text: '加载中...', color: '#667eea' });
            try {
                const response = await fetch(`/api/kline/${code}?period=${period}`);
                const data = await response.json();
                if (data.success && data.data.length > 0) renderKlineChart(data.data, period);
                else { klineChart.hideLoading(); klineChart.setOption({ title: { text: '暂无数据', left: 'center', top: 'center' } }); }
            } catch (error) { klineChart.hideLoading(); }
        }
        function renderKlineChart(data, period) {
            const dates = data.map(item => item.date);
            const values = data.map(item => [item.open, item.close, item.low, item.high]);
            const volumes = data.map(item => item.volume);
            const option = {
                backgroundColor: '#fff', animation: true, legend: { data: ['K线', 'MA5', 'MA10', 'MA20'], top: 10 },
                tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                grid: [{ left: '5%', right: '5%', top: '15%', height: '55%' }, { left: '5%', right: '5%', top: '75%', height: '15%' }],
                xAxis: [{ type: 'category', data: dates, scale: true, boundaryGap: false }, { type: 'category', gridIndex: 1, data: dates, scale: true, boundaryGap: false, axisLabel: { show: false } }],
                yAxis: [{ scale: true, splitArea: { show: true } }, { scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { show: false } }],
                dataZoom: [{ type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 }, { show: true, xAxisIndex: [0, 1], type: 'slider', top: '92%', start: 50, end: 100 }],
                series: [
                    { name: 'K线', type: 'candlestick', data: values, itemStyle: { color: '#ef232a', color0: '#14b143', borderColor: '#ef232a', borderColor0: '#14b143' } },
                    { name: 'MA5', type: 'line', data: calculateMA(5, values), smooth: true, lineStyle: { opacity: 0.8, width: 1 } },
                    { name: 'MA10', type: 'line', data: calculateMA(10, values), smooth: true, lineStyle: { opacity: 0.8, width: 1 } },
                    { name: 'MA20', type: 'line', data: calculateMA(20, values), smooth: true, lineStyle: { opacity: 0.8, width: 1 } },
                    { name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volumes, itemStyle: { color: (params) => values[params.dataIndex][1] > values[params.dataIndex][0] ? '#ef232a' : '#14b143' } }
                ]
            };
            klineChart.hideLoading(); klineChart.setOption(option);
            window.addEventListener('resize', () => klineChart.resize());
        }
        function calculateMA(dayCount, data) {
            const result = [];
            for (let i = 0; i < data.length; i++) {
                if (i < dayCount - 1) { result.push('-'); continue; }
                let sum = 0;
                for (let j = 0; j < dayCount; j++) sum += data[i - j][1];
                result.push((sum / dayCount).toFixed(2));
            }
            return result;
        }
        async function loadStockInfo(code) {
            try {
                const response = await fetch(`/api/stock/${code}`);
                const data = await response.json();
                if (data.success) {
                    const stock = data.data;
                    document.getElementById('stockInfoGrid').innerHTML = `
                        <div class="info-card"><h4>最新价</h4><div class="value">${stock['最新价'] ? stock['最新价'].toFixed(2) : '-'}</div></div>
                        <div class="info-card"><h4>涨跌幅</h4><div class="value" style="color: ${stock['涨跌幅'] > 0 ? '#28a745' : stock['涨跌幅'] < 0 ? '#dc3545' : '#666'}">${stock['涨跌幅'] ? stock['涨跌幅'].toFixed(2) + '%' : '-'}</div></div>
                        <div class="info-card"><h4>总市值</h4><div class="value">${stock['总市值'] ? (stock['总市值'] / 100000000).toFixed(2) + '亿' : '-'}</div></div>
                        <div class="info-card"><h4>流通市值</h4><div class="value">${stock['流通市值'] ? (stock['流通市值'] / 100000000).toFixed(2) + '亿' : '-'}</div></div>
                        <div class="info-card"><h4>成交量</h4><div class="value">${stock['成交量'] ? (stock['成交量'] / 10000).toFixed(2) + '万手' : '-'}</div></div>
                        <div class="info-card"><h4>成交额</h4><div class="value">${stock['成交额'] ? (stock['成交额'] / 10000).toFixed(2) + '万' : '-'}</div></div>
                        <div class="info-card"><h4>最高价</h4><div class="value">${stock['最高'] ? stock['最高'].toFixed(2) : '-'}</div></div>
                        <div class="info-card"><h4>最低价</h4><div class="value">${stock['最低'] ? stock['最低'].toFixed(2) : '-'}</div></div>`;
                }
            } catch (error) { console.error('加载股票信息失败:', error); }
        }
        function closeModal() {
            document.getElementById('chartModal').style.display = 'none';
            if (klineChart) { klineChart.dispose(); klineChart = null; }
        }
        window.onclick = function(event) { if (event.target === document.getElementById('chartModal')) closeModal(); }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/stocks")
async def get_stocks():
    """获取筛选结果"""
    global latest_screening_result, last_update_time
    
    if latest_screening_result is None:
        load_cached_data()
    
    if latest_screening_result is None:
        return JSONResponse({
            'success': False,
            'error': '暂无数据，请先执行筛选'
        })
    
    return JSONResponse({
        'success': True,
        'stocks': latest_screening_result,
        'timestamp': last_update_time or datetime.now().isoformat()
    })


@app.post("/api/refresh")
async def refresh_stocks(background_tasks: BackgroundTasks):
    """手动刷新数据"""
    global latest_screening_result, last_update_time
    
    try:
        collector = AStockDataCollector()
        result = collector.run_screening()
        
        if result['success']:
            latest_screening_result = result['stocks']
            last_update_time = result['timestamp']
            
            # 发送邮件通知
            try:
                sender = EmailSender()
                csv_path = os.path.join(data_dir, "latest_screening_result.csv")
                sender.send_screening_result(result['stocks'], csv_path)
            except Exception as e:
                print(f"邮件发送失败: {e}")
            
            return JSONResponse({
                'success': True,
                'stocks': result['stocks'],
                'timestamp': result['timestamp']
            })
        else:
            return JSONResponse({
                'success': False,
                'error': result.get('error', '筛选失败')
            })
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': f'刷新失败: {str(e)}'
        })


@app.get("/api/kline/{code}")
async def get_kline(code: str, period: str = "daily"):
    """获取K线数据"""
    try:
        collector = AStockDataCollector()
        kline_data = collector.get_stock_kline(code, period)
        
        if kline_data is not None and not kline_data.empty:
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
            
            return JSONResponse({
                'success': True,
                'data': data_list,
                'code': code,
                'period': period
            })
        else:
            return JSONResponse({
                'success': False,
                'error': '暂无K线数据',
                'code': code,
                'period': period
            })
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': f'获取K线数据失败: {str(e)}',
            'code': code,
            'period': period
        })


@app.get("/api/stock/{code}")
async def get_stock_detail(code: str):
    """获取单只股票详情"""
    global latest_screening_result
    
    if latest_screening_result:
        for stock in latest_screening_result:
            if stock.get('代码') == code:
                return JSONResponse({
                    'success': True,
                    'data': stock
                })
    
    try:
        collector = AStockDataCollector()
        market_data = collector.get_market_cap_data()
        stock_data = market_data[market_data['代码'] == code]
        
        if not stock_data.empty:
            return JSONResponse({
                'success': True,
                'data': stock_data.iloc[0].to_dict()
            })
        else:
            return JSONResponse({
                'success': False,
                'error': '未找到该股票'
            })
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': f'获取股票详情失败: {str(e)}'
        })


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return JSONResponse({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'data_loaded': latest_screening_result is not None,
        'stock_count': len(latest_screening_result) if latest_screening_result else 0
    })


# Vercel handler
from mangum import Adapter

# 尝试导入mangum，如果失败则使用简单的ASGI handler
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    # 如果没有mangum，创建一个简单的handler
    async def handler(event, context):
        from fastapi.responses import JSONResponse
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Please install mangum for Vercel deployment'}),
            'headers': {'Content-Type': 'application/json'}
        }