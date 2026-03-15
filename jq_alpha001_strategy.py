# 聚宽平台Alpha #1因子策略
# JoinQuant Alpha #1 Factor Strategy
# 
# 使用说明：
# 1. 将此文件内容复制到聚宽平台
# 2. 确保已上传alpha_helpers.py和alpha_factors.py文件
# 3. 或者将辅助函数直接包含在策略中

# 导入函数库
from jqdata import *
import pandas as pd
import numpy as np

# ============================================================================
# 辅助函数定义（如果没有上传模块文件，请使用以下函数）
# ============================================================================

def rank(df):
    """横截面排名"""
    return df.rank(axis=1, pct=True)

def ts_argmax(df, window):
    """时间序列最大值索引"""
    return df.rolling(window=int(window)).apply(lambda x: x.argmax(), raw=True)

def signed_power(df, exp):
    """带符号的幂运算"""
    return df.abs() ** exp * np.sign(df)

def alpha001(returns):
    """
    Alpha #1: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)
    
    Args:
        returns: 收益率数据框
    
    Returns:
        Alpha #1因子值
    """
    # 计算20日标准差
    stddev_20 = returns.rolling(window=20).std()
    
    # 条件判断：returns < 0 时使用stddev，否则使用returns的绝对值
    condition = returns < 0
    power_input = np.where(condition, stddev_20, returns.abs())
    
    # 转换为DataFrame以保持索引和列名
    power_input_df = pd.DataFrame(power_input, index=returns.index, columns=returns.columns)
    
    # 计算SignedPower(power_input, 2)
    signed_power_result = signed_power(power_input_df, 2)
    
    # 计算Ts_ArgMax(..., 5)
    ts_argmax_result = ts_argmax(signed_power_result, 5)
    
    # 计算rank并减去0.5
    return rank(ts_argmax_result) - 0.5

# ============================================================================
# 策略主体
# ============================================================================

def initialize(context):
    """初始化函数"""
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    
    # 输出内容到日志
    log.info('Alpha #1 因子策略初始化完成')
    
    # 股票池：选择沪深300成分股
    g.stock_pool = get_index_stocks('000300.XSHG')
    
    # 过滤掉ST股票和停牌股票
    g.stock_pool = [stock for stock in g.stock_pool if not is_st_stock(stock)]
    
    # 策略参数
    g.top_stock_count = 20  # 选择因子值最高的前20只股票
    g.rebalance_freq = 5    # 每5个交易日调仓一次
    g.trade_day_count = 0   # 交易日计数器
    
    # 股票类每笔交易时的手续费设定
    set_order_cost(OrderCost(
        close_tax=0.001,        # 印花税
        open_commission=0.0003, # 买入佣金
        close_commission=0.0003,# 卖出佣金
        min_commission=5        # 最低佣金
    ), type='stock')
    
    # 运行函数设定
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')

def before_market_open(context):
    """开盘前运行函数"""
    log.info(f'函数运行时间(before_market_open): {context.current_dt.time()}')
    
    # 更新股票池（过滤ST和停牌股票）
    g.stock_pool = [stock for stock in get_index_stocks('000300.XSHG') 
                   if not is_st_stock(stock) and not is_paused_stock(stock)]
    
    # 每隔指定天数重新计算因子并调仓
    if g.trade_day_count % g.rebalance_freq == 0:
        log.info('开始计算Alpha #1因子...')
        
        # 计算Alpha #1因子
        alpha1_scores = calculate_alpha001(context)
        
        if alpha1_scores is not None and len(alpha1_scores) > 0:
            # 选择因子值最高的前N只股票
            top_stocks = alpha1_scores.nlargest(g.top_stock_count)
            g.target_stocks = list(top_stocks.index)
            
            log.info(f'Alpha #1因子计算完成，选出 {len(g.target_stocks)} 只目标股票')
            log.info(f'目标股票: {g.target_stocks[:5]}...')  # 只显示前5只
        else:
            log.warning('Alpha #1因子计算失败，保持当前持仓')
            g.target_stocks = list(context.portfolio.positions.keys())
    
    g.trade_day_count += 1

def market_open(context):
    """开盘时运行函数"""
    log.info(f'函数运行时间(market_open): {context.current_dt.time()}')
    
    # 只在调仓日执行交易
    if (g.trade_day_count - 1) % g.rebalance_freq == 0 and hasattr(g, 'target_stocks'):
        execute_trade(context)

def execute_trade(context):
    """执行交易"""
    if not g.target_stocks:
        log.warning('目标股票列表为空，跳过交易')
        return
    
    # 获取当前持仓
    current_positions = list(context.portfolio.positions.keys())
    
    # 卖出不在目标股票中的持仓
    for stock in current_positions:
        if stock not in g.target_stocks:
            if context.portfolio.positions[stock].closeable_amount > 0:
                order_target(stock, 0)
                log.info(f'卖出 {stock}')
    
    # 等权重买入目标股票
    if g.target_stocks:
        weight = 0.95 / len(g.target_stocks)  # 保留5%现金
        
        for stock in g.target_stocks:
            try:
                order_target_percent(stock, weight)
                log.info(f'买入 {stock}, 目标权重: {weight:.2%}')
            except Exception as e:
                log.warning(f'买入 {stock} 失败: {str(e)}')

def calculate_alpha001(context):
    """计算Alpha #1因子"""
    try:
        # 获取足够的历史数据（需要至少25天数据来计算20日标准差和5日ArgMax）
        hist_data = get_price(
            g.stock_pool, 
            count=30,  # 获取30天数据确保足够
            end_date=context.current_dt, 
            fields=['close'], 
            panel=False
        )
        
        if hist_data.empty:
            log.warning('获取历史数据失败')
            return None
        
        # 数据透视：时间为行，股票为列
        price_pivot = hist_data.pivot(index='time', columns='code', values='close')
        
        # 过滤掉数据不足的股票
        price_pivot = price_pivot.dropna(axis=1, thresh=25)  # 至少需要25天数据
        
        if price_pivot.empty:
            log.warning('有效价格数据为空')
            return None
        
        # 计算收益率
        returns_df = price_pivot.pct_change().dropna()
        
        if len(returns_df) < 20:
            log.warning('收益率数据不足，无法计算20日标准差')
            return None
        
        # 计算Alpha #1因子
        alpha1_result = alpha001(returns_df)
        
        # 返回最新的因子值
        if not alpha1_result.empty:
            latest_scores = alpha1_result.iloc[-1].dropna()
            
            # 过滤异常值
            latest_scores = latest_scores[
                (latest_scores > latest_scores.quantile(0.01)) & 
                (latest_scores < latest_scores.quantile(0.99))
            ]
            
            log.info(f'Alpha #1因子计算完成，有效股票数: {len(latest_scores)}')
            return latest_scores
        else:
            log.warning('Alpha #1因子计算结果为空')
            return None
            
    except Exception as e:
        log.error(f'Alpha #1因子计算出错: {str(e)}')
        return None

def after_market_close(context):
    """收盘后运行函数"""
    log.info(f'函数运行时间(after_market_close): {context.current_dt.time()}')
    
    # 获取当天所有成交记录
    trades = get_trades()
    if trades:
        log.info(f'今日成交笔数: {len(trades)}')
        total_amount = sum([abs(trade.amount) for trade in trades.values()])
        log.info(f'今日总成交金额: {total_amount:.2f}')
    
    # 输出持仓信息
    positions = context.portfolio.positions
    if positions:
        log.info(f'当前持仓股票数: {len([p for p in positions.values() if p.total_amount > 0])}')
    
    # 输出组合价值
    log.info(f'组合总价值: {context.portfolio.total_value:.2f}')
    log.info(f'可用现金: {context.portfolio.available_cash:.2f}')
    
    log.info('一天结束')
    log.info('=' * 60)

def is_st_stock(stock):
    """判断是否为ST股票"""
    try:
        stock_info = get_security_info(stock)
        return 'ST' in stock_info.display_name or '*ST' in stock_info.display_name
    except:
        return False

def is_paused_stock(stock):
    """判断股票是否停牌"""
    try:
        return get_current_data()[stock].paused
    except:
        return False

# ============================================================================
# 策略说明
# ============================================================================
"""
Alpha #1 因子策略说明：

1. 因子公式：
   rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5

2. 因子逻辑：
   - 当收益率为负时，使用20日收益率标准差
   - 当收益率为正时，使用收益率绝对值
   - 对上述值进行2次幂运算（保持符号）
   - 计算5日滚动窗口内的最大值位置
   - 对结果进行横截面排名并减去0.5

3. 策略特点：
   - 基于短期反转逻辑
   - 适合中高频交易
   - 需要考虑交易成本

4. 风险提示：
   - 因子可能存在时效性
   - 需要定期验证因子有效性
   - 建议与其他因子组合使用
   - 注意控制换手率和交易成本

5. 参数设置：
   - 股票池：沪深300成分股
   - 选股数量：20只
   - 调仓频率：5个交易日
   - 权重分配：等权重
"""