import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
import numpy as np
import json

# ========== 页面配置 ==========
st.set_page_config(
    page_title="广东中烟绩效管理系统（季度版）",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 自定义CSS ==========
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #4f46e5;
        margin-bottom: 1rem;
    }
    .warning-card {
        background: linear-gradient(90deg, #fef3c7 0%, #fde68a 100%);
        border-left: 5px solid #f59e0b;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .danger-card {
        background: linear-gradient(90deg, #fee2e2 0%, #fecaca 100%);
        border-left: 5px solid #ef4444;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-card {
        background: linear-gradient(90deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 5px solid #10b981;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stButton>button {
        border-radius: 8px;
        background-color: #4f46e5;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .quarter-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.875rem;
        margin: 0 0.5rem;
    }
    .badge-q1 { background: #3b82f6; color: white; }
    .badge-q2 { background: #10b981; color: white; }
    .badge-q3 { background: #f59e0b; color: white; }
    .badge-q4 { background: #8b5cf6; color: white; }
    .data-card {
        background: #f8fafc;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #e2e8f0;
        margin: 0.5rem 0;
    }
    .real-time-score {
        background: linear-gradient(90deg, #e0e7ff 0%, #c7d2fe 100%);
        border-radius: 10px;
        padding: 1rem;
        border: 2px solid #4f46e5;
        margin: 1rem 0;
    }
    .data-changed {
        background: linear-gradient(90deg, #fef3c7 0%, #fde68a 100%);
        border: 2px solid #f59e0b;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .sync-status {
        background: linear-gradient(90deg, #d1fae5 0%, #a7f3d0 100%);
        border: 2px solid #10b981;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ========== Session State 初始化 ==========
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'current_city' not in st.session_state:
    st.session_state.current_city = None
if 'performance_data' not in st.session_state:
    st.session_state.performance_data = None
if 'quarter_history' not in st.session_state:
    st.session_state.quarter_history = {}
if 'current_quarter' not in st.session_state:
    st.session_state.current_quarter = None
if 'last_reset' not in st.session_state:
    st.session_state.last_reset = None
if 'data_history' not in st.session_state:
    st.session_state.data_history = {}
if 'data_sync_flag' not in st.session_state:
    st.session_state.data_sync_flag = False

# ========== 数据同步函数 ==========
def save_staff_data(staff_name, dist_values, recycle_values, core_customers, quarter_months):
    """保存事务员数据到主数据库"""
    try:
        # 找到事务员的索引
        staff_idx = st.session_state.performance_data[
            st.session_state.performance_data['事务员'] == staff_name
        ].index
        
        if len(staff_idx) == 0:
            st.error(f"找不到事务员：{staff_name}")
            return False
        
        staff_idx = staff_idx[0]
        
        # 记录原始数据（用于比较）
        original_data = {}
        
        # 更新分销数据
        for i, month in enumerate(quarter_months):
            month_num = int(month.replace('月', ''))
            dist_col = f'分销_{month_num}月'
            recycle_col = f'条盒_{month_num}月'
            
            # 记录原始值
            original_data[dist_col] = st.session_state.performance_data.at[staff_idx, dist_col]
            original_data[recycle_col] = st.session_state.performance_data.at[staff_idx, recycle_col]
            
            # 更新新值
            st.session_state.performance_data.at[staff_idx, dist_col] = dist_values[i]
            st.session_state.performance_data.at[staff_idx, recycle_col] = recycle_values[i]
        
        # 更新核心户数
        original_core = st.session_state.performance_data.at[staff_idx, '核心户数']
        st.session_state.performance_data.at[staff_idx, '核心户数'] = core_customers
        
        # 重新计算绩效
        st.session_state.performance_data = calculate_performance(
            st.session_state.performance_data, 
            st.session_state.current_quarter
        )
        
        # 检查数据是否有变化
        data_changed = False
        for i, month in enumerate(quarter_months):
            month_num = int(month.replace('月', ''))
            dist_col = f'分销_{month_num}月'
            if original_data.get(dist_col, 0) != dist_values[i]:
                data_changed = True
                break
        
        if original_core != core_customers:
            data_changed = True
        
        # 记录数据变更
        if data_changed:
            if staff_name not in st.session_state.data_history:
                st.session_state.data_history[staff_name] = []
            
            st.session_state.data_history[staff_name].append({
                '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '操作': '事务员填报数据',
                '分销数据': dist_values,
                '回收数据': recycle_values,
                '核心户数': core_customers,
                '原始数据': original_data,
                '原始核心户数': original_core
            })
        
        # 设置数据同步标志
        st.session_state.data_sync_flag = True
        
        return True
        
    except Exception as e:
        st.error(f"保存数据时出错：{str(e)}")
        return False

# ========== 季度管理函数 ==========
def get_current_quarter():
    """获取当前季度"""
    today = datetime.now()
    month = today.month
    year = today.year
    
    if month in [1, 2, 3]:
        return f"{year}年Q1季度"
    elif month in [4, 5, 6]:
        return f"{year}年Q2季度"
    elif month in [7, 8, 9]:
        return f"{year}年Q3季度"
    else:
        return f"{year}年Q4季度"

def get_quarter_months(quarter):
    """获取季度对应的月份"""
    quarter_map = {
        "Q1季度": ["1月", "2月", "3月"],
        "Q2季度": ["4月", "5月", "6月"],
        "Q3季度": ["7月", "8月", "9月"],
        "Q4季度": ["10月", "11月", "12月"]
    }
    for key, months in quarter_map.items():
        if key in quarter:
            return months
    return []

def get_current_quarter_month_range():
    """获取当前季度对应的月份范围"""
    quarter = st.session_state.current_quarter
    if "Q1" in quarter:
        return [1, 2, 3]
    elif "Q2" in quarter:
        return [4, 5, 6]
    elif "Q3" in quarter:
        return [7, 8, 9]
    elif "Q4" in quarter:
        return [10, 11, 12]
    else:
        return [1, 2, 3]

def check_reset_needed():
    """检查是否需要季度重置"""
    current_quarter = get_current_quarter()
    
    # 如果是新季度，且还未重置
    if (st.session_state.current_quarter != current_quarter or 
        (st.session_state.last_reset and st.session_state.last_reset != current_quarter)):
        return True
    return False

def reset_quarter_data(df, target_grade=6):
    """重置季度数据并设置目标档位"""
    # 保存当前季度数据到历史记录
    current_q = st.session_state.current_quarter
    if current_q and not df.empty:
        # 保存完整的季度数据到历史
        history_df = df.copy()
        
        # 只保留关键字段
        key_columns = ['行号', '地市', '事务员', '分销均季度', '条盒均季度', 
                      '分销得分', '条盒回收得分', '核心户得分', '综合得分', 
                      '总分', '档位', '预估月薪', '季度目标档位']
        
        history_df = history_df[key_columns].copy()
        history_df['季度'] = current_q
        st.session_state.quarter_history[current_q] = history_df.to_dict('records')
    
    # 重置数据
    reset_df = df.copy()
    
    # 获取当前季度月份范围
    month_range = get_current_quarter_month_range()
    
    # 只清空当前季度的月度数据
    for month_num in month_range:
        dist_col = f'分销_{month_num}月'
        recycle_col = f'条盒_{month_num}月'
        
        if dist_col in reset_df.columns:
            reset_df[dist_col] = 0
        if recycle_col in reset_df.columns:
            reset_df[recycle_col] = 0
    
    # 重置其他可编辑字段
    reset_columns = ['核心户数', '综合评分']
    for col in reset_columns:
        if col in reset_df.columns:
            reset_df[col] = 0
    
    # 设置季度目标
    reset_df['季度目标档位'] = target_grade
    
    # 清空计算结果（重新计算时会生成）
    calc_columns = ['分销均季度', '条盒均季度', '分销得分', '条盒回收得分', 
                   '核心户得分', '综合得分', '总分', '档位', '预估月薪']
    for col in calc_columns:
        if col in reset_df.columns:
            reset_df[col] = 0
    
    # 更新重置记录
    st.session_state.last_reset = st.session_state.current_quarter
    
    # 清空数据历史（新季度开始）
    st.session_state.data_history = {}
    
    return reset_df

def check_grade_warning(current_grade, target_grade):
    """检查档位是否需要提醒"""
    if current_grade > target_grade:
        return "danger", f"⚠️ 警告：当前档位为{current_grade}档，低于目标{target_grade}档！"
    elif current_grade == target_grade:
        return "warning", f"📊 注意：当前档位为{current_grade}档，刚好达到目标。"
    else:
        return "success", f"✅ 优秀：当前档位为{current_grade}档，超过目标{target_grade}档！"

# ========== 评分计算函数 ==========
def calculate_distribution_score(average):
    """计算分销得分"""
    if average >= 1000:
        return 25
    elif average >= 601:
        return 20
    elif average >= 301:
        return 15
    elif average >= 151:
        return 10
    elif average >= 61:
        return 5
    else:
        return 0

def calculate_recycling_score(average):
    """计算条盒回收得分"""
    if average >= 1000:
        return 35
    elif average >= 801:
        return 30
    elif average >= 601:
        return 25
    elif average >= 401:
        return 20
    elif average >= 301:
        return 15
    elif average >= 201:
        return 10
    elif average >= 181:
        return 5
    else:
        return 0

def calculate_core_customer_score(customer_count):
    """计算核心户得分"""
    if customer_count >= 31:
        return 20
    elif customer_count >= 26:
        return 15
    elif customer_count >= 21:
        return 10
    elif customer_count >= 16:
        return 5
    else:
        return 0

def calculate_salary_grade(total_score):
    """计算档位和工资"""
    if total_score >= 91:
        return 1, 6000
    elif total_score >= 81:
        return 2, 5500
    elif total_score >= 71:
        return 3, 5000
    elif total_score >= 61:
        return 4, 4700
    elif total_score >= 51:
        return 5, 4400
    elif total_score >= 46:
        return 6, 4100
    elif total_score >= 41:
        return 7, 3900
    elif total_score >= 36:
        return 8, 3700
    elif total_score >= 31:
        return 9, 3500
    else:
        return 10, 3300

def calculate_quarter_average(monthly_data, quarter):
    """计算季度平均值（处理4个月的特殊情况）"""
    # 过滤掉为0的月份（未填报）
    valid_data = [x for x in monthly_data if x > 0]
    
    if not valid_data:
        return 0
    
    # 如果是Q4季度，且填报了4个月的数据
    if "Q4" in quarter and len(valid_data) == 4:
        # 4个月的数据转换为季度平均值（乘以3/4）
        return sum(valid_data) * 0.75
    else:
        # 其他季度按实际填报月数计算平均值
        avg_monthly = sum(valid_data) / len(valid_data)
        return avg_monthly * 3

def calculate_realtime_score_for_staff(dist_values, recycle_values, core_customers, comp_score, quarter, target_grade=6):
    """为事务员计算实时得分"""
    # 计算季度平均值
    dist_avg = calculate_quarter_average(dist_values, quarter)
    recycle_avg = calculate_quarter_average(recycle_values, quarter)
    
    # 计算各项得分
    dist_score = calculate_distribution_score(dist_avg)
    recycle_score = calculate_recycling_score(recycle_avg)
    core_score = calculate_core_customer_score(core_customers)
    
    # 限制综合评分为0-20
    comp_score = min(20, max(0, comp_score))
    
    # 总分和档位
    total_score = dist_score + recycle_score + core_score + comp_score
    grade, salary = calculate_salary_grade(total_score)
    
    # 检查档位提醒
    warning_level, warning_msg = check_grade_warning(grade, target_grade)
    
    return {
        '分销均季度': round(dist_avg, 1),
        '条盒均季度': round(recycle_avg, 1),
        '分销得分': dist_score,
        '条盒回收得分': recycle_score,
        '核心户得分': core_score,
        '综合得分': comp_score,
        '总分': total_score,
        '档位': grade,
        '预估月薪': salary,
        '档位提醒级别': warning_level,
        '档位提醒信息': warning_msg,
        '是否达标': grade <= target_grade
    }

# ========== 数据初始化 ==========
def init_data_from_template():
    """从模板初始化数据"""
    data = []
    staff_list = [
        ('石家庄', '庞雷'), ('保定', '方亚辉'), ('保定', '李建英'), ('保定', '史亚卿'),
        ('保定', '甄喜梅'), ('沧州', '郝亮'), ('沧州', '张卿'), ('张家口', '李晓峰'),
        ('石家庄', '孙霆'), ('石家庄', '李凤霞'), ('石家庄', '赵晴'), ('石家庄', '刘东青'),
        ('邯郸', '冯斌'), ('邯郸', '谷巧霞'), ('邢台', '黄小刚'), ('唐山', '张丽颖'),
        ('廊坊', '王玉刚'), ('秦皇岛', '陈晔'), ('天津', '夏美佳'), ('天津', '刘波'),
        ('北京', '段体春'), ('北京', '胡颖'), ('临沂', '王培娟'), ('临沂', '朱森'),
        ('潍坊', '李雪兰'), ('潍坊', '王军军'), ('枣庄', '黄成志'), ('淄博', '杨秀霞'),
        ('济南', '陈蕾'), ('济南', '杨晶晶'), ('威海', '马晓燕'), ('青岛', '田亮'),
        ('烟台', '岳东玉'), ('烟台', '高韶伟'), ('太原', '辛伟'), ('太原', '樊芳'),
        ('晋中', '聂江波')
    ]
    
    for i, (city, name) in enumerate(staff_list, 1):
        data.append({
            '行号': i,
            '地市': city,
            '事务员': name,
            # 月度数据 - 所有月份都保留
            '分销_1月': 0, '分销_2月': 0, '分销_3月': 0,
            '分销_4月': 0, '分销_5月': 0, '分销_6月': 0,
            '分销_7月': 0, '分销_8月': 0, '分销_9月': 0,
            '分销_10月': 0, '分销_11月': 0, '分销_12月': 0,
            '条盒_1月': 0, '条盒_2月': 0, '条盒_3月': 0,
            '条盒_4月': 0, '条盒_5月': 0, '条盒_6月': 0,
            '条盒_7月': 0, '条盒_8月': 0, '条盒_9月': 0,
            '条盒_10月': 0, '条盒_11月': 0, '条盒_12月': 0,
            # 其他数据
            '核心户数': 0,
            '综合评分': 0,
            '季度目标档位': 6,
            '备注': ''
        })
    
    df = pd.DataFrame(data)
    return df

def calculate_performance(df, quarter):
    """根据季度计算绩效"""
    # 确定月份范围
    if "Q1" in quarter:
        month_range = [1, 2, 3]
    elif "Q2" in quarter:
        month_range = [4, 5, 6]
    elif "Q3" in quarter:
        month_range = [7, 8, 9]
    elif "Q4" in quarter:
        month_range = [10, 11, 12]
    else:
        month_range = [1, 2, 3]
    
    for idx, row in df.iterrows():
        # 收集当前季度的分销数据
        dist_data = []
        recycle_data = []
        
        for month_num in month_range:
            dist_col = f'分销_{month_num}月'
            recycle_col = f'条盒_{month_num}月'
            
            if dist_col in row:
                dist_data.append(row[dist_col])
            if recycle_col in row:
                recycle_data.append(row[recycle_col])
        
        # 计算季度平均值
        dist_avg = calculate_quarter_average(dist_data, quarter)
        recycle_avg = calculate_quarter_average(recycle_data, quarter)
        
        # 计算各项得分
        dist_score = calculate_distribution_score(dist_avg)
        recycle_score = calculate_recycling_score(recycle_avg)
        core_score = calculate_core_customer_score(row['核心户数'])
        comp_score = row['综合评分'] if row['综合评分'] <= 20 else 20
        
        # 总分和档位
        total_score = dist_score + recycle_score + core_score + comp_score
        grade, salary = calculate_salary_grade(total_score)
        
        # 检查档位提醒
        target_grade = row.get('季度目标档位', 6)
        warning_level, warning_msg = check_grade_warning(grade, target_grade)
        
        # 添加到结果
        df.at[idx, '分销均季度'] = round(dist_avg, 1)
        df.at[idx, '条盒均季度'] = round(recycle_avg, 1)
        df.at[idx, '分销得分'] = dist_score
        df.at[idx, '条盒回收得分'] = recycle_score
        df.at[idx, '核心户得分'] = core_score
        df.at[idx, '综合得分'] = comp_score
        df.at[idx, '总分'] = total_score
        df.at[idx, '档位'] = grade
        df.at[idx, '预估月薪'] = salary
        df.at[idx, '档位提醒级别'] = warning_level
        df.at[idx, '档位提醒信息'] = warning_msg
        df.at[idx, '是否达标'] = grade <= target_grade
    
    return df

def get_current_quarter_data(df, quarter):
    """获取当前季度的数据（只显示当前季度的相关列）"""
    if df.empty:
        return df
    
    # 确定当前季度月份范围
    if "Q1" in quarter:
        month_range = [1, 2, 3]
    elif "Q2" in quarter:
        month_range = [4, 5, 6]
    elif "Q3" in quarter:
        month_range = [7, 8, 9]
    elif "Q4" in quarter:
        month_range = [10, 11, 12]
    else:
        month_range = [1, 2, 3]
    
    # 基本列
    base_columns = ['行号', '地市', '事务员', '核心户数', '综合评分', 
                   '季度目标档位', '备注']
    
    # 当前季度月份列
    month_columns = []
    for month_num in month_range:
        month_columns.extend([f'分销_{month_num}月', f'条盒_{month_num}月'])
    
    # 计算列
    calc_columns = ['分销均季度', '条盒均季度', '分销得分', '条盒回收得分',
                   '核心户得分', '综合得分', '总分', '档位', '预估月薪',
                   '是否达标']
    
    # 合并所有需要显示的列
    display_columns = base_columns + month_columns
    
    # 只保留存在的列
    available_columns = [col for col in display_columns if col in df.columns]
    
    # 创建新的DataFrame
    result_df = df[available_columns].copy()
    
    # 添加计算列（如果存在）
    for col in calc_columns:
        if col in df.columns:
            result_df[col] = df[col]
    
    return result_df

# ========== 登录页面 ==========
def login_page():
    st.markdown('<h1 class="main-header">🔐 广东中烟绩效管理系统（季度版）</h1>', unsafe_allow_html=True)
    
    # 显示数据同步状态
    if st.session_state.get('data_sync_flag', False):
        st.markdown('<div class="sync-status">✅ 数据已同步</div>', unsafe_allow_html=True)
        st.session_state.data_sync_flag = False
    
    # 初始化当前季度
    if st.session_state.current_quarter is None:
        st.session_state.current_quarter = get_current_quarter()
    
    # 检查是否需要季度重置
    if check_reset_needed():
        st.warning(f"检测到新季度开始，即将自动重置数据...")
        if st.session_state.performance_data is not None:
            st.session_state.performance_data = reset_quarter_data(
                st.session_state.performance_data, 
                target_grade=6
            )
        st.session_state.current_quarter = get_current_quarter()
    
    # 初始化数据
    if st.session_state.performance_data is None:
        st.session_state.performance_data = init_data_from_template()
        st.session_state.performance_data = calculate_performance(
            st.session_state.performance_data, 
            st.session_state.current_quarter
        )
    
    # 季度显示
    quarter_badge = {
        "Q1季度": "badge-q1",
        "Q2季度": "badge-q2", 
        "Q3季度": "badge-q3",
        "Q4季度": "badge-q4"
    }
    
    q_class = "badge-q2"
    for key, cls in quarter_badge.items():
        if key in st.session_state.current_quarter:
            q_class = cls
            break
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2rem;">
        <span class="quarter-badge {q_class}">当前季度：{st.session_state.current_quarter}</span>
        <span style="color: #666; font-size: 0.9rem;">工资按季度结算，每季度重置数据</span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.subheader("请选择身份登录")
            
            role = st.radio("您的身份", ["事务员", "地市经理", "管理员"], horizontal=True, key="role_radio")
            
            if role == "事务员":
                staff_names = st.session_state.performance_data['事务员'].tolist()
                user_name = st.selectbox("请选择您的姓名", staff_names, key="staff_select")
                
                if st.button("登录", type="primary", use_container_width=True, key="staff_login_btn"):
                    st.session_state.authenticated = True
                    st.session_state.user_role = "staff"
                    st.session_state.user_name = user_name
                    user_city = st.session_state.performance_data[
                        st.session_state.performance_data['事务员'] == user_name
                    ]['地市'].values[0]
                    st.session_state.current_city = user_city
                    st.rerun()
            
            elif role == "地市经理":
                cities = st.session_state.performance_data['地市'].unique().tolist()
                city = st.selectbox("请选择您管理的地市", cities, key="city_select")
                manager_pwd = st.text_input("地市经理密码", type="password", value="manager123", key="manager_pwd_input")
                
                if st.button("地市经理登录", type="primary", use_container_width=True, key="manager_login_btn"):
                    if manager_pwd == "manager123":
                        st.session_state.authenticated = True
                        st.session_state.user_role = "manager"
                        st.session_state.current_city = city
                        st.session_state.user_name = f"{city}地市经理"
                        st.rerun()
                    else:
                        st.error("密码错误！")
            
            else:  # 管理员
                admin_pwd = st.text_input("管理员密码", type="password", key="admin_pwd_input")
                
                if st.button("管理员登录", type="primary", use_container_width=True, key="admin_login_btn"):
                    if admin_pwd == "admin123":
                        st.session_state.authenticated = True
                        st.session_state.user_role = "admin"
                        st.session_state.user_name = "管理员"
                        st.rerun()
                    else:
                        st.error("密码错误！")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 使用说明
    with st.expander("📖 系统使用说明（季度版）", expanded=False):
        st.markdown(f"""
        ### 当前季度：{st.session_state.current_quarter}
        
        **📅 季度结算规则：**
        1. 工资按季度计算和发放
        2. 每季度结束后数据自动重置
        3. 系统会记录每个季度的历史数据
        
        **🎯 实时评分系统：**
        - 事务员填写数据时，实时显示预估得分和档位
        - 绿色✅：超过目标档位
        - 黄色📊：达到目标档位  
        - 红色⚠️：低于目标档位（需要改进）
        
        **👤 各角色功能：**
        - 事务员：填报月度数据，实时查看预估成绩和提醒
        - 地市经理：查看和修改本地区数据，进行综合评分
        - 管理员：季度管理、数据重置、系统设置
        
        **🔑 默认密码：**
        - 事务员：直接选择姓名（无需密码）
        - 地市经理：manager123
        - 管理员：admin123
        
        **📝 重要提示：**
        - Q4季度（10-12月）按4个月的数据折算为季度平均值
        - 每个季度开始时会自动重置数据
        - 历史季度数据可以在"历史季度"页面查看
        """)

# ========== 事务员个人页面 ==========
def staff_dashboard():
    st.markdown(f'<h2 class="main-header">👤 {st.session_state.user_name} 的个人中心</h2>', unsafe_allow_html=True)
    
    # 获取用户数据
    user_data = st.session_state.performance_data[
        st.session_state.performance_data['事务员'] == st.session_state.user_name
    ]
    
    if user_data.empty:
        st.error("未找到您的数据")
        return
    
    user_row = user_data.iloc[0]
    
    # 显示当前数据状态
    st.markdown(f'<div class="data-card">当前状态：您的数据已保存到系统，地市经理和管理员可以查看</div>', unsafe_allow_html=True)
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📊 季度绩效", "📝 实时数据填报", "🧮 得分计算器", "📈 历史季度"])
    
    with tab1:
        # 档位提醒
        if '档位提醒级别' in user_row and '档位提醒信息' in user_row:
            st.markdown(f'<div class="{user_row["档位提醒级别"]}-card">{user_row["档位提醒信息"]}</div>', unsafe_allow_html=True)
        
        # 季度绩效总览
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("季度总分", f"{user_row['总分']}分" if '总分' in user_row else "0分")
        with col2:
            if '档位' in user_row and '季度目标档位' in user_row:
                color = "#10b981" if user_row['档位'] <= user_row['季度目标档位'] else "#ef4444"
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="font-size: 0.9rem; color: #666;">季度档位</div>
                    <div style="font-size: 2rem; font-weight: bold; color: {color};">{user_row['档位']}档</div>
                    <div style="font-size: 0.8rem; color: #666;">目标：{user_row['季度目标档位']}档</div>
                </div>
                """, unsafe_allow_html=True)
        with col3:
            st.metric("季度月薪", f"¥{user_row['预估月薪']}" if '预估月薪' in user_row else "¥0")
        with col4:
            st.metric("所属地市", user_row['地市'])
        
        st.divider()
        
        # 得分详情
        st.subheader("📈 季度得分详情")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            dist_score = user_row['分销得分'] if '分销得分' in user_row else 0
            dist_avg = user_row['分销均季度'] if '分销均季度' in user_row else 0
            st.metric("分销得分", f"{dist_score}/25")
            st.caption(f"均季度: {dist_avg}条")
        with col2:
            recycle_score = user_row['条盒回收得分'] if '条盒回收得分' in user_row else 0
            recycle_avg = user_row['条盒均季度'] if '条盒均季度' in user_row else 0
            st.metric("条盒回收得分", f"{recycle_score}/35")
            st.caption(f"均季度: {recycle_avg}条")
        with col3:
            core_score = user_row['核心户得分'] if '核心户得分' in user_row else 0
            core_count = user_row['核心户数'] if '核心户数' in user_row else 0
            st.metric("核心户得分", f"{core_score}/20")
            st.caption(f"核心户数: {core_count}人")
        with col4:
            comp_score = user_row['综合得分'] if '综合得分' in user_row else 0
            st.metric("综合得分", f"{comp_score}/20")
            st.caption("地市经理评分")
        
        # 显示当前填报的数据
        st.divider()
        st.subheader("📋 当前填报数据")
        
        quarter_months = get_quarter_months(st.session_state.current_quarter)
        col_count = len(quarter_months)
        
        if col_count > 0:
            cols = st.columns(col_count)
            for i, month in enumerate(quarter_months):
                with cols[i]:
                    month_num = int(month.replace('月', ''))
                    dist_col = f'分销_{month_num}月'
                    recycle_col = f'条盒_{month_num}月'
                    
                    dist_value = user_row[dist_col] if dist_col in user_row else 0
                    recycle_value = user_row[recycle_col] if recycle_col in user_row else 0
                    
                    st.metric(f"{month}分销", f"{dist_value}条")
                    st.metric(f"{month}回收", f"{recycle_value}条")
    
    with tab2:
        st.subheader(f"📅 {st.session_state.current_quarter} 实时数据填报")
        
        # 获取季度月份
        quarter_months = get_quarter_months(st.session_state.current_quarter)
        
        # 初始化表单数据
        dist_values = []
        recycle_values = []
        
        # 获取当前数据
        for month in quarter_months:
            month_num = int(month.replace('月', ''))
            dist_col = f'分销_{month_num}月'
            recycle_col = f'条盒_{month_num}月'
            
            dist_values.append(user_row[dist_col] if dist_col in user_row else 0)
            recycle_values.append(user_row[recycle_col] if recycle_col in user_row else 0)
        
        core_customers = user_row['核心户数'] if '核心户数' in user_row else 0
        target_grade = user_row['季度目标档位'] if '季度目标档位' in user_row else 6
        comp_score = user_row['综合评分'] if '综合评分' in user_row else 0
        
        # 实时计算当前得分
        current_score = calculate_realtime_score_for_staff(
            dist_values, recycle_values, core_customers, comp_score,
            st.session_state.current_quarter, target_grade
        )
        
        # 显示实时评分卡片
        st.markdown('<div class="real-time-score">', unsafe_allow_html=True)
        st.subheader("🎯 实时评分预览")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("预估总分", f"{current_score['总分']}分")
        with col2:
            color = "#10b981" if current_score['档位'] <= target_grade else "#ef4444"
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; color: #666;">预估档位</div>
                <div style="font-size: 2rem; font-weight: bold; color: {color};">{current_score['档位']}档</div>
                <div style="font-size: 0.8rem; color: #666;">目标：{target_grade}档</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.metric("预估月薪", f"¥{current_score['预估月薪']}")
        
        # 显示各项得分详情
        st.markdown("##### 各项得分详情")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("分销得分", f"{current_score['分销得分']}/25")
            st.caption(f"均季度: {current_score['分销均季度']}条")
        with col2:
            st.metric("条盒回收得分", f"{current_score['条盒回收得分']}/35")
            st.caption(f"均季度: {current_score['条盒均季度']}条")
        with col3:
            st.metric("核心户得分", f"{current_score['核心户得分']}/20")
            st.caption(f"核心户数: {core_customers}人")
        with col4:
            st.metric("综合得分", f"{current_score['综合得分']}/20")
            st.caption("地市经理评分")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 数据填报表单
        with st.form("monthly_data_form", clear_on_submit=False):
            st.markdown("### 分销数据填报（单位：条）")
            
            cols = st.columns(len(quarter_months))
            new_dist_values = []
            
            for i, month in enumerate(quarter_months):
                with cols[i]:
                    # 获取月份数字
                    month_num = int(month.replace('月', ''))
                    
                    value = st.number_input(f"{month}分销", 
                                          min_value=0, 
                                          value=int(dist_values[i]),
                                          key=f"dist_{st.session_state.user_name}_{month_num}")
                    new_dist_values.append(value)
            
            st.markdown("### 条盒回收数据填报（单位：条）")
            
            cols = st.columns(len(quarter_months))
            new_recycle_values = []
            
            for i, month in enumerate(quarter_months):
                with cols[i]:
                    # 获取月份数字
                    month_num = int(month.replace('月', ''))
                    
                    value = st.number_input(f"{month}回收", 
                                          min_value=0, 
                                          value=int(recycle_values[i]),
                                          key=f"recycle_{st.session_state.user_name}_{month_num}")
                    new_recycle_values.append(value)
            
            # 核心户数
            new_core_customers = st.number_input("本季度核心户数", 
                                               min_value=0, 
                                               value=int(core_customers),
                                               key=f"core_{st.session_state.user_name}")
            
            submitted = st.form_submit_button("保存季度数据", type="primary")
            
            if submitted:
                # 使用专用函数保存数据
                success = save_staff_data(
                    st.session_state.user_name,
                    new_dist_values,
                    new_recycle_values,
                    new_core_customers,
                    quarter_months
                )
                
                if success:
                    st.success("✅ 季度数据保存成功！数据已同步到系统中。")
                    st.markdown("""
                    **数据已同步：**
                    - ✅ 您的数据已保存到主数据库
                    - ✅ 地市经理可以立即查看您的数据
                    - ✅ 管理员可以立即查看您的数据
                    - ✅ 系统已重新计算您的绩效得分
                    """)
                    
                    # 显示保存的数据
                    with st.expander("查看保存的数据详情", expanded=True):
                        for i, month in enumerate(quarter_months):
                            st.write(f"{month}: 分销 {new_dist_values[i]}条, 回收 {new_recycle_values[i]}条")
                        st.write(f"核心户数: {new_core_customers}人")
                    
                    # 自动刷新页面
                    st.rerun()
                else:
                    st.error("❌ 保存数据失败，请重试")
    
    with tab3:
        st.subheader("🧮 得分与工资计算器")
        
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 输入模拟数据")
                target_grade = st.selectbox("目标档位", list(range(1, 11)), index=5, key="calc_target_grade")
                dist_q = st.number_input("分销季度总量（条）", min_value=0, value=900, key="calc_dist_q")
                recycle_q = st.number_input("条盒回收季度总量（条）", min_value=0, value=1200, key="calc_recycle_q")
                core_customers = st.number_input("核心户数", min_value=0, value=28, key="calc_core_customers")
                comp_score = st.slider("综合评分（0-20）", 0, 20, 16, key="calc_comp_score")
            
            with col2:
                # 计算得分
                dist_score = calculate_distribution_score(dist_q)
                recycle_score = calculate_recycling_score(recycle_q)
                core_score = calculate_core_customer_score(core_customers)
                total_score = dist_score + recycle_score + core_score + comp_score
                grade, salary = calculate_salary_grade(total_score)
                
                # 检查档位
                warning_level, warning_msg = check_grade_warning(grade, target_grade)
                
                st.markdown(f"""
                <div class="{warning_level}-card">
                    <h4>{warning_msg}</h4>
                </div>
                <div class="data-card" style="margin-top: 1rem;">
                    <h4>各项得分：</h4>
                    <p>📦 分销得分：<b>{dist_score}/25</b></p>
                    <p>📊 条盒回收得分：<b>{recycle_score}/35</b></p>
                    <p>👥 核心户得分：<b>{core_score}/20</b></p>
                    <p>⭐ 综合得分：<b>{comp_score}/20</b></p>
                    <hr>
                    <h3>总分：<span style="color:#4f46e5">{total_score}分</span></h3>
                    <h4>档位：{grade}档 (目标：{target_grade}档)</h4>
                    <h2>预估季度月薪：<span style="color:#10b981">¥{salary}</span></h2>
                </div>
                """, unsafe_allow_html=True)

# ========== 地市经理页面 ==========
def manager_dashboard():
    st.markdown(f'<h2 class="main-header">📊 {st.session_state.user_name} - 地市经理管理</h2>', unsafe_allow_html=True)
    
    # 获取地市经理管理的地市
    managed_city = st.session_state.current_city
    
    # 筛选该地市的事务员数据
    city_data = st.session_state.performance_data[
        st.session_state.performance_data['地市'] == managed_city
    ]
    
    if city_data.empty:
        st.warning(f"没有找到{managed_city}的数据")
        return
    
    st.success(f"您正在管理：{managed_city}地区，共{len(city_data)}位事务员")
    
    # 显示最近的数据变更记录
    show_recent_changes = False
    if st.session_state.data_history:
        recent_changes = []
        for staff_name, records in st.session_state.data_history.items():
            # 只显示本地区的事务员
            if staff_name in city_data['事务员'].values:
                if records:
                    latest_record = records[-1]
                    recent_changes.append({
                        '事务员': staff_name,
                        '时间': latest_record['时间'],
                        '操作': latest_record['操作']
                    })
        
        if recent_changes:
            show_recent_changes = True
            st.markdown('<div class="data-changed">', unsafe_allow_html=True)
            st.subheader("📝 最近数据变更记录")
            for change in recent_changes[-3:]:  # 只显示最近3条
                st.write(f"**{change['事务员']}** - {change['时间']} - {change['操作']}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["👥 事务员管理", "📊 地区分析", "📈 绩效考核"])
    
    with tab1:
        st.subheader(f"{managed_city}地区事务员列表")
        
        # 获取当前季度数据（只显示相关列）
        current_city_data = get_current_quarter_data(city_data, st.session_state.current_quarter)
        
        if current_city_data.empty:
            st.warning("没有找到当前季度的数据")
            return
        
        # 显示数据验证
        st.info(f"✅ 数据已同步，共{len(current_city_data)}位事务员的数据")
        
        # 显示数据编辑界面
        edited_df = st.data_editor(
            current_city_data,
            column_config={
                '综合评分': st.column_config.NumberColumn(
                    "综合评分（0-20）",
                    min_value=0,
                    max_value=20,
                    step=1,
                    help="地市经理对事务员的综合表现评分"
                ),
                '季度目标档位': st.column_config.NumberColumn(
                    "目标档位",
                    min_value=1,
                    max_value=10,
                    step=1,
                    help="为该事务员设定的季度目标档位"
                ),
                '核心户数': st.column_config.NumberColumn(
                    "核心户数",
                    min_value=0,
                    step=1,
                    help="事务员的核心客户数量"
                )
            },
            use_container_width=True,
            height=400,
            key="manager_editor"
        )
        
        # 检查数据差异
        data_diff = not edited_df.equals(current_city_data)
        
        if data_diff:
            st.markdown('<div class="data-changed">📝 检测到数据修改，请保存以应用更改</div>', unsafe_allow_html=True)
            
            # 显示具体修改
            with st.expander("查看具体修改", expanded=False):
                for idx, row in edited_df.iterrows():
                    original_row = current_city_data.loc[idx]
                    changes = []
                    
                    for col in edited_df.columns:
                        if col in original_row and row[col] != original_row[col]:
                            changes.append(f"{col}: {original_row[col]} → {row[col]}")
                    
                    if changes:
                        staff_name = row['事务员'] if '事务员' in row else f"行{idx+1}"
                        st.write(f"**{staff_name}** 的修改：")
                        for change in changes:
                            st.write(f"  - {change}")
        
        if st.button("保存修改", type="primary", use_container_width=True, key="save_manager_changes_btn"):
            # 保存修改到主数据
            for idx, row in edited_df.iterrows():
                # 找到原始数据中的对应行
                original_idx = city_data.index[city_data['行号'] == row['行号']].tolist()
                if original_idx:
                    original_idx = original_idx[0]
                    
                    # 更新综合评分
                    if '综合评分' in row:
                        old_score = st.session_state.performance_data.at[original_idx, '综合评分']
                        new_score = row['综合评分']
                        if old_score != new_score:
                            st.session_state.performance_data.at[original_idx, '综合评分'] = new_score
                    
                    # 更新目标档位
                    if '季度目标档位' in row:
                        old_target = st.session_state.performance_data.at[original_idx, '季度目标档位']
                        new_target = row['季度目标档位']
                        if old_target != new_target:
                            st.session_state.performance_data.at[original_idx, '季度目标档位'] = new_target
                    
                    # 更新核心户数
                    if '核心户数' in row:
                        old_core = st.session_state.performance_data.at[original_idx, '核心户数']
                        new_core = row['核心户数']
                        if old_core != new_core:
                            st.session_state.performance_data.at[original_idx, '核心户数'] = new_core
                    
                    # 更新月度数据
                    month_range = get_current_quarter_month_range()
                    for month_num in month_range:
                        dist_col = f'分销_{month_num}月'
                        recycle_col = f'条盒_{month_num}月'
                        
                        if dist_col in row:
                            old_dist = st.session_state.performance_data.at[original_idx, dist_col]
                            new_dist = row[dist_col]
                            if old_dist != new_dist:
                                st.session_state.performance_data.at[original_idx, dist_col] = new_dist
                        
                        if recycle_col in row:
                            old_recycle = st.session_state.performance_data.at[original_idx, recycle_col]
                            new_recycle = row[recycle_col]
                            if old_recycle != new_recycle:
                                st.session_state.performance_data.at[original_idx, recycle_col] = new_recycle
            
            # 重新计算绩效
            st.session_state.performance_data = calculate_performance(
                st.session_state.performance_data, 
                st.session_state.current_quarter
            )
            
            # 记录数据变更
            if st.session_state.user_name not in st.session_state.data_history:
                st.session_state.data_history[st.session_state.user_name] = []
            
            st.session_state.data_history[st.session_state.user_name].append({
                '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '操作': '地市经理修改数据',
                '修改地区': managed_city,
                '修改人数': len(edited_df)
            })
            
            # 设置同步标志
            st.session_state.data_sync_flag = True
            
            st.success(f"✅ {managed_city}地区数据保存成功！")
            st.rerun()

# ========== 管理员页面 ==========
def admin_dashboard():
    st.markdown('<h2 class="main-header">👑 管理员控制台</h2>', unsafe_allow_html=True)
    
    # 显示数据同步状态
    if st.session_state.get('data_sync_flag', False):
        st.markdown('<div class="sync-status">✅ 数据已同步，所有角色都可以看到最新数据</div>', unsafe_allow_html=True)
        st.session_state.data_sync_flag = False
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 数据管理", "📊 全局分析", "🔄 季度管理", "📤 数据导入导出", "⚙️ 系统设置"])
    
    with tab1:
        st.subheader("全员数据管理")
        
        # 显示筛选选项
        col1, col2 = st.columns(2)
        with col1:
            # 只显示当前季度数据
            display_current_only = st.checkbox(
                "只显示当前季度数据", 
                value=True,
                help="勾选后只显示当前季度的相关数据列",
                key="display_current_only"
            )
        
        with col2:
            # 选择查看的地市
            all_cities = st.session_state.performance_data['地市'].unique().tolist()
            selected_city = st.selectbox(
                "选择地市查看", 
                ["全部"] + all_cities,
                key="admin_city_select"
            )
        
        # 获取要显示的数据
        if display_current_only:
            display_data = get_current_quarter_data(
                st.session_state.performance_data, 
                st.session_state.current_quarter
            )
        else:
            display_data = st.session_state.performance_data.copy()
        
        # 按地市筛选
        if selected_city != "全部":
            display_data = display_data[display_data['地市'] == selected_city]
        
        # 显示最近数据变更
        if st.session_state.data_history:
            with st.expander("📝 最近数据变更记录", expanded=False):
                changes_count = 0
                for user_name, records in list(st.session_state.data_history.items())[-10:]:  # 只显示最近10条
                    if records:
                        latest_record = records[-1]
                        st.write(f"**{user_name}** - {latest_record['时间']}")
                        st.write(f"操作：{latest_record['操作']}")
                        
                        if '分销数据' in latest_record:
                            st.write(f"分销数据：{latest_record['分销数据']}")
                        if '地区' in latest_record:
                            st.write(f"地区：{latest_record['地区']}")
                        if '修改人数' in latest_record:
                            st.write(f"修改人数：{latest_record['修改人数']}")
                        
                        st.divider()
                        changes_count += 1
                
                if changes_count > 0:
                    st.info(f"共显示{changes_count}条最近的数据变更记录")
        
        # 显示庞雷的示例数据（特别验证）
        if "庞雷" in st.session_state.performance_data['事务员'].values:
            pang_lei_data = st.session_state.performance_data[
                st.session_state.performance_data['事务员'] == "庞雷"
            ].iloc[0]
            
            with st.expander("🔍 验证：庞雷的数据（示例）", expanded=False):
                st.write("**庞雷的当前季度数据：**")
                quarter_months = get_quarter_months(st.session_state.current_quarter)
                
                for month in quarter_months:
                    month_num = int(month.replace('月', ''))
                    dist_col = f'分销_{month_num}月'
                    recycle_col = f'条盒_{month_num}月'
                    
                    if dist_col in pang_lei_data:
                        st.write(f"{month}分销：{pang_lei_data[dist_col]}条")
                    if recycle_col in pang_lei_data:
                        st.write(f"{month}回收：{pang_lei_data[recycle_col]}条")
                
                if '核心户数' in pang_lei_data:
                    st.write(f"核心户数：{pang_lei_data['核心户数']}人")
                if '综合评分' in pang_lei_data:
                    st.write(f"综合评分：{pang_lei_data['综合评分']}分")
        
        # 显示数据编辑界面
        st.write(f"显示数据：{len(display_data)} 行")
        
        edited_df = st.data_editor(
            display_data,
            column_config={
                '季度目标档位': st.column_config.NumberColumn(
                    "目标档位",
                    min_value=1,
                    max_value=10,
                    step=1
                ),
                '综合评分': st.column_config.NumberColumn(
                    "综合评分",
                    min_value=0,
                    max_value=20,
                    step=1
                ),
                '核心户数': st.column_config.NumberColumn(
                    "核心户数",
                    min_value=0,
                    step=1
                )
            },
            use_container_width=True,
            height=500,
            key="admin_editor"
        )
        
        # 检查是否有数据被修改
        if not edited_df.equals(display_data):
            st.markdown('<div class="data-changed">📝 检测到数据修改，请保存以应用更改</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("保存修改", type="primary", use_container_width=True, key="save_all_changes_btn"):
                # 保存修改到主数据
                for idx, row in edited_df.iterrows():
                    # 找到原始数据中的对应行
                    original_idx = display_data.index[display_data['行号'] == row['行号']].tolist()
                    if original_idx:
                        original_idx = original_idx[0]
                        
                        # 更新可编辑字段
                        editable_fields = ['综合评分', '季度目标档位', '核心户数', '备注']
                        
                        for field in editable_fields:
                            if field in row and field in st.session_state.performance_data.columns:
                                st.session_state.performance_data.at[original_idx, field] = row[field]
                        
                        # 更新月度数据
                        month_range = get_current_quarter_month_range()
                        for month_num in month_range:
                            dist_col = f'分销_{month_num}月'
                            recycle_col = f'条盒_{month_num}月'
                            
                            if dist_col in row:
                                st.session_state.performance_data.at[original_idx, dist_col] = row[dist_col]
                            if recycle_col in row:
                                st.session_state.performance_data.at[original_idx, recycle_col] = row[recycle_col]
                
                # 重新计算绩效
                st.session_state.performance_data = calculate_performance(
                    st.session_state.performance_data, 
                    st.session_state.current_quarter
                )
                
                # 记录操作
                if st.session_state.user_name not in st.session_state.data_history:
                    st.session_state.data_history[st.session_state.user_name] = []
                
                st.session_state.data_history[st.session_state.user_name].append({
                    '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '操作': '管理员修改数据',
                    '修改行数': len(edited_df)
                })
                
                # 设置同步标志
                st.session_state.data_sync_flag = True
                
                st.success("✅ 数据保存成功！")
                st.rerun()
        
        with col2:
            if st.button("重新计算绩效", type="secondary", use_container_width=True, key="recalculate_btn"):
                st.session_state.performance_data = calculate_performance(
                    st.session_state.performance_data, 
                    st.session_state.current_quarter
                )
                st.success("✅ 绩效重新计算完成！")
                st.rerun()

# ========== 主程序 ==========
def main():
    # 检查登录状态
    if not st.session_state.authenticated:
        login_page()
        return
    
    # 顶部导航栏
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        role_display = {
            "staff": f"👤 {st.session_state.user_name}",
            "manager": f"📊 {st.session_state.user_name}",
            "admin": "👑 管理员控制台"
        }
        st.markdown(f'<h3>{role_display[st.session_state.user_role]}</h3>', unsafe_allow_html=True)
    
    with col2:
        quarter_badge = {
            "Q1季度": "badge-q1",
            "Q2季度": "badge-q2", 
            "Q3季度": "badge-q3",
            "Q4季度": "badge-q4"
        }
        
        q_class = "badge-q2"
        for key, cls in quarter_badge.items():
            if key in st.session_state.current_quarter:
                q_class = cls
                break
        
        st.markdown(f'<span class="quarter-badge {q_class}">{st.session_state.current_quarter}</span>', unsafe_allow_html=True)
    
    with col3:
        if st.button("退出登录", use_container_width=True, key="logout_btn"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.divider()
    
    # 根据角色显示对应页面
    if st.session_state.user_role == "staff":
        staff_dashboard()
    elif st.session_state.user_role == "manager":
        manager_dashboard()
    else:
        admin_dashboard()

if __name__ == "__main__":
    main()
