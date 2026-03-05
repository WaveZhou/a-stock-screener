"""
FastAPI主应用
提供Web界面和API接口
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.requests import Request
from pydantic import BaseModel
from datetime import datetime
import os
import json
import pandas as pd

from data_collector import AStockDataCollector
from email_sender import EmailSender

# 创建FastAPI应用
app = FastAPI(
    title="A股小市值股票筛选系统",
    description="筛选市值倒数1000名中净利润增速前30的股票",
    version="1.0.0"
)

# 模板和静态文件
base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# 数据目录
data_dir = os.path.join(base_dir, "data")
os.makedirs(data_dir, exist_ok=True)

# 全局数据存储
latest_screening_result = None
last_update_time = None


class StockResponse(BaseModel):
    """股票响应模型"""
    success: bool
    stocks: list = []
    timestamp: str = None
    error: str = None


class KlineResponse(BaseModel):
    """K线数据响应模型"""
    success: bool
    data: list = []
    code: str = None
    period: str = None
    error: str = None


@app.on_event("startup")
async def startup_event():
    """应用启动时加载最新数据"""
    global latest_screening_result, last_update_time
    
    # 尝试加载本地缓存的数据
    latest_json = os.path.join(data_dir, "latest_screening_result.json")
    if os.path.exists(latest_json):
        try:
            with open(latest_json, 'r', encoding='utf-8') as f:
                latest_screening_result = json.load(f)
                last_update_time = datetime.fromtimestamp(
                    os.path.getmtime(latest_json)
                ).isoformat()
            print(f"✅ 已加载缓存数据，共 {len(latest_screening_result)} 只股票")
        except Exception as e:
            print(f"⚠️ 加载缓存数据失败: {e}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/stocks", response_model=StockResponse)
async def get_stocks():
    """获取筛选结果"""
    global latest_screening_result, last_update_time
    
    if latest_screening_result is None:
        # 尝试从文件加载
        latest_json = os.path.join(data_dir, "latest_screening_result.json")
        if os.path.exists(latest_json):
            try:
                with open(latest_json, 'r', encoding='utf-8') as f:
                    latest_screening_result = json.load(f)
                    last_update_time = datetime.fromtimestamp(
                        os.path.getmtime(latest_json)
                    ).isoformat()
            except Exception as e:
                return StockResponse(
                    success=False,
                    error=f"加载数据失败: {str(e)}"
                )
        else:
            return StockResponse(
                success=False,
                error="暂无数据，请先执行筛选"
            )
    
    return StockResponse(
        success=True,
        stocks=latest_screening_result,
        timestamp=last_update_time or datetime.now().isoformat()
    )


@app.post("/api/refresh", response_model=StockResponse)
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
            background_tasks.add_task(send_email_notification, result['stocks'])
            
            return StockResponse(
                success=True,
                stocks=result['stocks'],
                timestamp=result['timestamp']
            )
        else:
            return StockResponse(
                success=False,
                error=result.get('error', '筛选失败')
            )
    except Exception as e:
        return StockResponse(
            success=False,
            error=f"刷新失败: {str(e)}"
        )


@app.get("/api/kline/{code}", response_model=KlineResponse)
async def get_kline(code: str, period: str = "daily"):
    """获取K线数据"""
    try:
        collector = AStockDataCollector()
        kline_data = collector.get_stock_kline(code, period)
        
        if kline_data is not None and not kline_data.empty:
            # 转换为前端需要的格式
            data_list = []
            for _, row in kline_data.iterrows():
                data_list.append({
                    'date': row['日期'],
                    'open': float(row['开盘']),
                    'close': float(row['收盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'volume': float(row['成交量']),
                    'amount': float(row['成交额'])
                })
            
            return KlineResponse(
                success=True,
                data=data_list,
                code=code,
                period=period
            )
        else:
            return KlineResponse(
                success=False,
                error="暂无K线数据",
                code=code,
                period=period
            )
    except Exception as e:
        return KlineResponse(
            success=False,
            error=f"获取K线数据失败: {str(e)}",
            code=code,
            period=period
        )


@app.get("/api/stock/{code}")
async def get_stock_detail(code: str):
    """获取单只股票详情"""
    global latest_screening_result
    
    if latest_screening_result:
        for stock in latest_screening_result:
            if stock.get('代码') == code:
                return {
                    'success': True,
                    'data': stock
                }
    
    # 如果缓存中没有，实时获取
    try:
        collector = AStockDataCollector()
        market_data = collector.get_market_cap_data()
        stock_data = market_data[market_data['代码'] == code]
        
        if not stock_data.empty:
            return {
                'success': True,
                'data': stock_data.iloc[0].to_dict()
            }
        else:
            return {
                'success': False,
                'error': '未找到该股票'
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'获取股票详情失败: {str(e)}'
        }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'data_loaded': latest_screening_result is not None,
        'stock_count': len(latest_screening_result) if latest_screening_result else 0
    }


def send_email_notification(stocks_data):
    """发送邮件通知"""
    try:
        sender = EmailSender()
        csv_path = os.path.join(data_dir, "latest_screening_result.csv")
        sender.send_screening_result(stocks_data, csv_path)
    except Exception as e:
        print(f"邮件发送失败: {e}")


# Vercel Serverless Handler
# 用于Vercel部署
from fastapi.middleware.cors import CORSMiddleware

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 如果是直接运行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)