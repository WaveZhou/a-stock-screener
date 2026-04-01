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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>A股小市值股票筛选系统</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; -webkit-text-size-adjust: 100%; }
        .container { max-width: 1400px; margin: 0 auto; }

        /* Header */
        .header { text-align: center; color: white; margin-bottom: 24px; padding: 16px 10px; }
        .header h1 { font-size: 2.2em; margin-bottom: 8px; line-height: 1.2; }
        .header p { font-size: 1em; opacity: 0.9; }

        /* Stats */
        .stats-bar { display: flex; justify-content: center; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
        .stat-card { background: white; padding: 16px 28px; border-radius: 15px; box-shadow: 0 8px 30px rgba(0,0,0,0.1); text-align: center; flex: 1; min-width: 120px; max-width: 240px; }
        .stat-card h3 { color: #888; font-size: 0.8em; margin-bottom: 6px; font-weight: 500; }
        .stat-card .value { font-size: 1.6em; font-weight: 700; color: #667eea; }

        /* Buttons */
        .btn-bar { display: flex; justify-content: center; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
        .btn { color: white; border: none; padding: 12px 32px; font-size: 1em; border-radius: 30px; cursor: pointer; transition: all 0.3s ease; font-weight: 500; white-space: nowrap; }
        .btn:active { transform: scale(0.97); }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .btn-primary:hover { box-shadow: 0 6px 20px rgba(102,126,234,0.5); }
        .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
        .btn-success { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); }
        .btn-success:hover { box-shadow: 0 6px 20px rgba(40,167,69,0.5); }

        /* Table container */
        .table-container { background: white; border-radius: 16px; box-shadow: 0 16px 48px rgba(0,0,0,0.1); overflow: hidden; margin-bottom: 30px; }
        .table-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
        .table-header h2 { font-size: 1.1em; }
        .table-header span { font-size: 0.85em; opacity: 0.9; }

        /* Desktop table */
        .desktop-view { overflow-x: auto; -webkit-overflow-scrolling: touch; }
        .desktop-view table { width: 100%; border-collapse: collapse; min-width: 900px; }
        .desktop-view thead { background: #f8f9fa; }
        .desktop-view th { padding: 12px 10px; text-align: left; font-weight: 600; color: #555; border-bottom: 2px solid #e9ecef; font-size: 0.82em; white-space: nowrap; }
        .desktop-view td { padding: 11px 10px; border-bottom: 1px solid #f0f0f0; color: #333; font-size: 0.88em; white-space: nowrap; }
        .desktop-view tr:hover { background: #f8f9fa; }

        /* Mobile cards */
        .mobile-view { display: none; }
        .stock-card { padding: 14px 16px; border-bottom: 1px solid #f0f0f0; }
        .stock-card:active { background: #f8f9fa; }
        .card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .card-rank { display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; border-radius: 50%; font-size: 0.75em; font-weight: 700; color: white; margin-right: 8px; flex-shrink: 0; }
        .rank-gold { background: linear-gradient(135deg, #f5af19, #f12711); }
        .rank-silver { background: linear-gradient(135deg, #667eea, #764ba2); }
        .rank-normal { background: #adb5bd; }
        .card-name { font-weight: 600; color: #333; font-size: 1em; }
        .card-code { color: #888; font-size: 0.82em; margin-left: 6px; }
        .card-price { text-align: right; }
        .card-price .price { font-size: 1.1em; font-weight: 600; }
        .card-price .change { font-size: 0.85em; }
        .card-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px 12px; margin-top: 8px; }
        .card-field { display: flex; justify-content: space-between; font-size: 0.78em; color: #666; }
        .card-field .label { color: #999; }
        .card-field .val { font-weight: 500; color: #333; }
        .card-actions { margin-top: 10px; text-align: right; }
        .card-actions .btn { padding: 7px 18px; font-size: 0.82em; }

        /* Common */
        .stock-link { font-weight: 600; color: #667eea; cursor: pointer; }
        .stock-link:hover { color: #764ba2; text-decoration: underline; }
        .positive { color: #cf1322; font-weight: 600; }
        .negative { color: #3f8600; font-weight: 600; }
        .tag { display: inline-block; padding: 3px 9px; border-radius: 10px; font-size: 0.75em; font-weight: 600; }
        .tag-high { background: #fff1f0; color: #cf1322; }
        .tag-medium { background: #fff7e6; color: #d46b08; }
        .tag-low { background: #f6ffed; color: #389e0d; }
        .message { text-align: center; padding: 10px 16px; margin: 0 0 16px 0; border-radius: 10px; background: #e3f2fd; color: #1976d2; font-size: 0.9em; }

        /* Modal */
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.65); }
        .modal-content { background: white; margin: 2% auto; border-radius: 16px; width: 94%; max-width: 1200px; max-height: 96vh; overflow: hidden; display: flex; flex-direction: column; }
        .modal-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
        .modal-header h2 { font-size: 1em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-right: 12px; }
        .close { color: white; font-size: 28px; font-weight: bold; cursor: pointer; line-height: 1; padding: 0 4px; }
        .modal-body { padding: 16px; flex: 1; overflow-y: auto; }
        .chart-tabs { display: flex; gap: 8px; margin-bottom: 14px; }
        .chart-tab { padding: 8px 20px; border: 2px solid #e9ecef; background: white; cursor: pointer; font-size: 0.9em; color: #666; border-radius: 20px; transition: all 0.2s; }
        .chart-tab.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-color: transparent; }
        #klineChart { width: 100%; height: 480px; }

        /* ====== Responsive ====== */
        @media (max-width: 768px) {
            body { padding: 10px; }
            .header { margin-bottom: 16px; padding: 10px 4px; }
            .header h1 { font-size: 1.4em; }
            .header p { font-size: 0.85em; }
            .stats-bar { gap: 8px; margin-bottom: 16px; }
            .stat-card { padding: 12px 10px; min-width: 90px; border-radius: 12px; }
            .stat-card h3 { font-size: 0.7em; }
            .stat-card .value { font-size: 1.2em; }
            .btn-bar { gap: 8px; margin-bottom: 16px; }
            .btn { padding: 10px 20px; font-size: 0.88em; flex: 1; text-align: center; }
            .table-container { border-radius: 12px; }
            .table-header { padding: 12px 14px; }
            .table-header h2 { font-size: 0.95em; }
            .desktop-view { display: none; }
            .mobile-view { display: block; }
            .modal-content { margin: 0; border-radius: 0; width: 100%; max-width: 100%; height: 100%; max-height: 100%; }
            .modal-body { padding: 12px; }
            .chart-tabs { gap: 6px; }
            .chart-tab { padding: 7px 14px; font-size: 0.82em; }
            #klineChart { height: 320px; }
        }
        @media (min-width: 769px) and (max-width: 1024px) {
            .header h1 { font-size: 1.8em; }
            .stat-card { padding: 14px 20px; }
            #klineChart { height: 420px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>A股小市值股票筛选系统</h1>
            <p>市值倒数100名中，归母净利润增速前30</p>
        </div>
        <div class="stats-bar">
            <div class="stat-card"><h3>筛选股票数</h3><div class="value" id="stockCount">-</div></div>
            <div class="stat-card"><h3>平均市值</h3><div class="value" id="avgCap">-</div></div>
            <div class="stat-card"><h3>平均增速</h3><div class="value" id="avgGrowth">-</div></div>
        </div>
        <div class="btn-bar">
            <button class="btn btn-primary" id="refreshBtn">刷新数据</button>
            <button class="btn btn-success" id="exportBtn">导出Excel</button>
        </div>
        <div id="messageArea"></div>
        <div class="table-container">
            <div class="table-header">
                <h2>筛选结果</h2>
                <span id="lastUpdate">更新时间: -</span>
            </div>
            <div class="desktop-view" id="desktopView"></div>
            <div class="mobile-view" id="mobileView"></div>
        </div>
    </div>
    <div id="chartModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">K线图</h2>
                <span class="close" id="closeBtn">&times;</span>
            </div>
            <div class="modal-body">
                <div class="chart-tabs">
                    <button class="chart-tab active" data-period="daily">日K</button>
                    <button class="chart-tab" data-period="weekly">周K</button>
                    <button class="chart-tab" data-period="monthly">月K</button>
                </div>
                <div id="klineChart"></div>
            </div>
        </div>
    </div>
    <script>
        var klineChart = null;
        var currentStocks = [];
        var currentStockCode = '';
        var currentStockName = '';

        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('refreshBtn').addEventListener('click', refreshData);
            document.getElementById('exportBtn').addEventListener('click', exportExcel);
            document.getElementById('closeBtn').addEventListener('click', closeModal);

            var tabs = document.querySelectorAll('.chart-tab');
            for (var i = 0; i < tabs.length; i++) {
                tabs[i].addEventListener('click', function() {
                    for (var j = 0; j < tabs.length; j++) tabs[j].classList.remove('active');
                    this.classList.add('active');
                    if (currentStockCode) loadKlineData(currentStockCode, this.getAttribute('data-period'));
                });
            }

            window.addEventListener('click', function(e) {
                if (e.target === document.getElementById('chartModal')) closeModal();
            });

            window.addEventListener('resize', function() {
                if (klineChart) klineChart.resize();
            });

            loadData();
        });

        function loadData() {
            fetch('/api/stocks')
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.success) {
                        currentStocks = data.stocks;
                        renderStocks(data.stocks);
                        updateStats(data.stocks);
                        document.getElementById('lastUpdate').textContent = '更新: ' + new Date(data.timestamp).toLocaleString('zh-CN');
                        if (data.message) showMessage(data.message);
                    }
                })
                .catch(function() {
                    document.getElementById('desktopView').innerHTML = '<div style="padding:40px;text-align:center;color:#999;">加载失败，请刷新重试</div>';
                    document.getElementById('mobileView').innerHTML = '<div style="padding:40px;text-align:center;color:#999;">加载失败，请刷新重试</div>';
                });
        }

        function refreshData() {
            var btn = document.getElementById('refreshBtn');
            btn.disabled = true; btn.textContent = '刷新中...';
            fetch('/api/refresh', { method: 'POST' })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.success) {
                        currentStocks = data.stocks;
                        renderStocks(data.stocks);
                        updateStats(data.stocks);
                        document.getElementById('lastUpdate').textContent = '更新: ' + new Date(data.timestamp).toLocaleString('zh-CN');
                        showMessage(data.message || '数据已刷新');
                    } else { showMessage('刷新失败: ' + (data.error || '')); }
                })
                .catch(function(e) { showMessage('网络错误'); })
                .finally(function() { btn.disabled = false; btn.textContent = '刷新数据'; });
        }

        function showMessage(msg) {
            var area = document.getElementById('messageArea');
            area.innerHTML = '<div class="message">' + msg + '</div>';
            setTimeout(function() { area.innerHTML = ''; }, 4000);
        }

        function renderStocks(stocks) {
            if (!stocks || stocks.length === 0) {
                var empty = '<div style="padding:40px;text-align:center;color:#999;">暂无数据</div>';
                document.getElementById('desktopView').innerHTML = empty;
                document.getElementById('mobileView').innerHTML = empty;
                return;
            }
            renderDesktopTable(stocks);
            renderMobileCards(stocks);
        }

        function renderDesktopTable(stocks) {
            var h = '<table><thead><tr><th>#</th><th>代码</th><th>名称</th><th>最新价</th><th>涨跌幅</th><th>总市值(亿)</th><th>流通市值(亿)</th><th>净利润增速</th><th>成交额(万)</th><th>操作</th></tr></thead><tbody>';
            for (var i = 0; i < stocks.length; i++) {
                var s = stocks[i];
                var cc = s['涨跌幅'] > 0 ? 'positive' : s['涨跌幅'] < 0 ? 'negative' : '';
                var gc = (s['净利润同比增长率']||0) > 0 ? 'positive' : (s['净利润同比增长率']||0) < 0 ? 'negative' : '';
                var tc = i < 3 ? 'tag-high' : i < 10 ? 'tag-medium' : 'tag-low';
                h += '<tr>'
                    + '<td><span class="tag ' + tc + '">' + (i+1) + '</span></td>'
                    + '<td>' + s['代码'] + '</td>'
                    + '<td><span class="stock-link" data-c="' + s['代码'] + '" data-n="' + s['名称'] + '">' + s['名称'] + '</span></td>'
                    + '<td>' + fmt(s['最新价'],2) + '</td>'
                    + '<td class="' + cc + '">' + fmt(s['涨跌幅'],2) + '%</td>'
                    + '<td>' + fmt(s['总市值']/1e8,2) + '</td>'
                    + '<td>' + fmt(s['流通市值']/1e8,2) + '</td>'
                    + '<td class="' + gc + '">' + fmt(s['净利润同比增长率'],2) + '%</td>'
                    + '<td>' + fmt(s['成交额']/1e4,0) + '</td>'
                    + '<td><button class="btn btn-primary kbtn" style="padding:6px 14px;font-size:0.78em;" data-c="' + s['代码'] + '" data-n="' + s['名称'] + '">K线</button></td>'
                    + '</tr>';
            }
            h += '</tbody></table>';
            document.getElementById('desktopView').innerHTML = h;
            bindClicks('desktopView');
        }

        function renderMobileCards(stocks) {
            var h = '';
            for (var i = 0; i < stocks.length; i++) {
                var s = stocks[i];
                var cc = s['涨跌幅'] > 0 ? 'positive' : s['涨跌幅'] < 0 ? 'negative' : '';
                var gc = (s['净利润同比增长率']||0) > 0 ? 'positive' : (s['净利润同比增长率']||0) < 0 ? 'negative' : '';
                var rc = i < 3 ? 'rank-gold' : i < 10 ? 'rank-silver' : 'rank-normal';
                h += '<div class="stock-card">'
                    + '<div class="card-top">'
                    +   '<div style="display:flex;align-items:center;">'
                    +     '<span class="card-rank ' + rc + '">' + (i+1) + '</span>'
                    +     '<span class="card-name stock-link" data-c="' + s['代码'] + '" data-n="' + s['名称'] + '">' + s['名称'] + '</span>'
                    +     '<span class="card-code">' + s['代码'] + '</span>'
                    +   '</div>'
                    +   '<div class="card-price">'
                    +     '<div class="price ' + cc + '">' + fmt(s['最新价'],2) + '</div>'
                    +     '<div class="change ' + cc + '">' + (s['涨跌幅']>0?'+':'') + fmt(s['涨跌幅'],2) + '%</div>'
                    +   '</div>'
                    + '</div>'
                    + '<div class="card-grid">'
                    +   '<div class="card-field"><span class="label">市值</span><span class="val">' + fmt(s['总市值']/1e8,2) + '亿</span></div>'
                    +   '<div class="card-field"><span class="label">增速</span><span class="val ' + gc + '">' + fmt(s['净利润同比增长率'],1) + '%</span></div>'
                    +   '<div class="card-field"><span class="label">成交额</span><span class="val">' + fmt(s['成交额']/1e4,0) + '万</span></div>'
                    + '</div>'
                    + '<div class="card-actions"><button class="btn btn-primary kbtn" style="padding:6px 16px;font-size:0.78em;" data-c="' + s['代码'] + '" data-n="' + s['名称'] + '">查看K线</button></div>'
                    + '</div>';
            }
            document.getElementById('mobileView').innerHTML = h;
            bindClicks('mobileView');
        }

        function bindClicks(containerId) {
            var el = document.getElementById(containerId);
            var links = el.querySelectorAll('.stock-link');
            for (var i = 0; i < links.length; i++) {
                links[i].addEventListener('click', function() {
                    openChart(this.getAttribute('data-c'), this.getAttribute('data-n'));
                });
            }
            var btns = el.querySelectorAll('.kbtn');
            for (var j = 0; j < btns.length; j++) {
                btns[j].addEventListener('click', function() {
                    openChart(this.getAttribute('data-c'), this.getAttribute('data-n'));
                });
            }
        }

        function updateStats(stocks) {
            if (!stocks || stocks.length === 0) return;
            document.getElementById('stockCount').textContent = stocks.length;
            var tc = 0, tg = 0;
            for (var i = 0; i < stocks.length; i++) {
                tc += (stocks[i]['总市值'] || 0);
                tg += (stocks[i]['净利润同比增长率'] || 0);
            }
            document.getElementById('avgCap').textContent = (tc / stocks.length / 1e8).toFixed(1) + '亿';
            document.getElementById('avgGrowth').textContent = (tg / stocks.length).toFixed(1) + '%';
        }

        function fmt(v, d) {
            if (v === null || v === undefined || isNaN(v)) return '-';
            return Number(v).toFixed(d);
        }

        /* ===== K-line ===== */
        function openChart(code, name) {
            currentStockCode = code;
            currentStockName = name;
            document.getElementById('modalTitle').textContent = name + ' (' + code + ')';
            document.getElementById('chartModal').style.display = 'block';
            document.body.style.overflow = 'hidden';
            var tabs = document.querySelectorAll('.chart-tab');
            for (var i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove('active');
                if (tabs[i].getAttribute('data-period') === 'daily') tabs[i].classList.add('active');
            }
            loadKlineData(code, 'daily');
        }

        function loadKlineData(code, period) {
            if (klineChart) klineChart.dispose();
            klineChart = echarts.init(document.getElementById('klineChart'));
            klineChart.showLoading({text: '加载中...', color: '#667eea'});

            var klt = {daily:'101',weekly:'102',monthly:'103'}[period] || '101';
            var secid = (code.startsWith('6')||code.startsWith('9')) ? '1.'+code : '0.'+code;
            var cbName = 'kcb_' + Date.now();

            var today = new Date();
            var ago = new Date(today.getTime() - 730*86400000);
            var beg = ago.toISOString().slice(0,10).replace(/-/g,'');
            var end = today.toISOString().slice(0,10).replace(/-/g,'');

            window[cbName] = function(data) {
                klineChart.hideLoading();
                if (data && data.data && data.data.klines && data.data.klines.length > 0) {
                    var arr = [], kl = data.data.klines;
                    for (var i = 0; i < kl.length; i++) {
                        var p = kl[i].split(',');
                        if (p.length >= 7) arr.push({date:p[0],open:+p[1],close:+p[2],high:+p[3],low:+p[4],volume:+p[5],amount:+p[6]});
                    }
                    renderKlineChart(arr, period);
                } else {
                    klineChart.setOption({title:{text:'暂无K线数据',left:'center',top:'center',textStyle:{color:'#999'}}});
                }
                delete window[cbName];
            };

            var old = document.getElementById('kline_jsonp');
            if (old) old.remove();
            var sc = document.createElement('script');
            sc.id = 'kline_jsonp';
            sc.src = 'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid='+secid
                +'&ut=bd1d9ddb04089700cf9c27f6f7426281&fields1=f1,f2,f3,f4,f5,f6'
                +'&fields2=f51,f52,f53,f54,f55,f56,f57&klt='+klt
                +'&fqt=1&beg='+beg+'&end='+end+'&cb='+cbName;
            sc.onerror = function() {
                klineChart.hideLoading();
                klineChart.setOption({title:{text:'加载失败',left:'center',top:'center',textStyle:{color:'#999'}}});
                delete window[cbName];
            };
            document.body.appendChild(sc);
            setTimeout(function() { if (window[cbName]) { klineChart.hideLoading(); klineChart.setOption({title:{text:'请求超时',left:'center',top:'center',textStyle:{color:'#999'}}}); delete window[cbName]; } }, 15000);
        }

        function renderKlineChart(data, period) {
            var isMobile = window.innerWidth < 769;
            var pLabel = {daily:'日K',weekly:'周K',monthly:'月K'}[period]||'日K';
            var dates=[],vals=[],vols=[];
            for (var i=0;i<data.length;i++) {
                dates.push(data[i].date);
                vals.push([data[i].open,data[i].close,data[i].low,data[i].high]);
                vols.push({value:data[i].volume, itemStyle:{color:data[i].close>=data[i].open?'#ef232a':'#14b143'}});
            }
            function ma(n) {
                var r=[];
                for (var i=0;i<dates.length;i++) {
                    if (i<n-1){r.push('-');continue;}
                    var s=0; for(var j=0;j<n;j++) s+=vals[i-j][1];
                    r.push((s/n).toFixed(2));
                }
                return r;
            }
            var gl = isMobile ? '12%' : '8%';
            var gr = isMobile ? '4%' : '5%';
            var opt = {
                backgroundColor:'#fff', animation:true,
                title:{text:currentStockName+' '+pLabel,left:'center',top:2,textStyle:{fontSize:isMobile?13:16}},
                legend:{data:['MA5','MA10','MA20'],top:isMobile?22:28,textStyle:{fontSize:isMobile?10:12},itemWidth:isMobile?14:25},
                tooltip:{trigger:'axis',axisPointer:{type:'cross'},textStyle:{fontSize:isMobile?11:13},confine:true,
                    formatter:function(p){
                        if(!p||!p[0])return'';
                        var t=p[0].axisValue+'<br/>';
                        for(var i=0;i<p.length;i++){
                            var x=p[i];
                            if(x.seriesType==='candlestick') t+='开:'+x.data[1]+' 收:'+x.data[2]+'<br/>低:'+x.data[3]+' 高:'+x.data[4]+'<br/>';
                            else if(x.seriesType==='bar') t+='量:'+(x.data.value/1e4).toFixed(0)+'万手<br/>';
                            else if(x.data!=='-') t+=x.seriesName+':'+x.data+'<br/>';
                        }
                        return t;
                    }
                },
                axisPointer:{link:[{xAxisIndex:'all'}]},
                grid:[
                    {left:gl,right:gr,top:isMobile?'18%':'14%',height:isMobile?'45%':'50%'},
                    {left:gl,right:gr,top:isMobile?'70%':'71%',height:isMobile?'16%':'18%'}
                ],
                xAxis:[
                    {type:'category',data:dates,gridIndex:0,axisLine:{onZero:false},splitLine:{show:false},axisLabel:{show:false}},
                    {type:'category',data:dates,gridIndex:1,axisLine:{onZero:false},splitLine:{show:false},axisLabel:{fontSize:isMobile?9:11}}
                ],
                yAxis:[
                    {scale:true,gridIndex:0,splitArea:{show:true},axisLabel:{fontSize:isMobile?9:11}},
                    {scale:true,gridIndex:1,splitNumber:2,axisLabel:{show:false},splitArea:{show:false}}
                ],
                dataZoom:[
                    {type:'inside',xAxisIndex:[0,1],start:isMobile?70:60,end:100},
                    {type:'slider',xAxisIndex:[0,1],bottom:isMobile?2:5,height:isMobile?14:20,start:isMobile?70:60,end:100}
                ],
                series:[
                    {name:'K线',type:'candlestick',data:vals,xAxisIndex:0,yAxisIndex:0,
                     itemStyle:{color:'#ef232a',color0:'#14b143',borderColor:'#ef232a',borderColor0:'#14b143'}},
                    {name:'MA5',type:'line',data:ma(5),smooth:true,lineStyle:{width:1},symbol:'none',xAxisIndex:0,yAxisIndex:0},
                    {name:'MA10',type:'line',data:ma(10),smooth:true,lineStyle:{width:1},symbol:'none',xAxisIndex:0,yAxisIndex:0},
                    {name:'MA20',type:'line',data:ma(20),smooth:true,lineStyle:{width:1},symbol:'none',xAxisIndex:0,yAxisIndex:0},
                    {name:'成交量',type:'bar',data:vols,xAxisIndex:1,yAxisIndex:1}
                ]
            };
            klineChart.setOption(opt);
        }

        /* ===== Export ===== */
        function exportExcel() {
            if (!currentStocks||currentStocks.length===0){alert('暂无数据');return;}
            var d=[['排名','代码','名称','最新价','涨跌幅(%)','总市值(亿)','流通市值(亿)','净利润增速(%)','成交额(万)','今开','最高','最低','昨收','换手率(%)']];
            for(var i=0;i<currentStocks.length;i++){
                var s=currentStocks[i];
                d.push([i+1,s['代码'],s['名称'],s['最新价']||0,s['涨跌幅']||0,
                    +((s['总市值']||0)/1e8).toFixed(2),+((s['流通市值']||0)/1e8).toFixed(2),
                    s['净利润同比增长率']||0,+((s['成交额']||0)/1e4).toFixed(2),
                    s['今开']||0,s['最高']||0,s['最低']||0,s['昨收']||0,s['换手率']||0]);
            }
            var wb=XLSX.utils.book_new(),ws=XLSX.utils.aoa_to_sheet(d);
            ws['!cols']=[{wch:5},{wch:10},{wch:12},{wch:8},{wch:10},{wch:11},{wch:11},{wch:12},{wch:12},{wch:8},{wch:8},{wch:8},{wch:8},{wch:10}];
            XLSX.utils.book_append_sheet(wb,ws,'筛选结果');
            XLSX.writeFile(wb,'A股筛选结果_'+new Date().toISOString().slice(0,10)+'.xlsx');
        }

        function closeModal() {
            document.getElementById('chartModal').style.display = 'none';
            document.body.style.overflow = '';
            if (klineChart){klineChart.dispose();klineChart=null;}
            currentStockCode='';currentStockName='';
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