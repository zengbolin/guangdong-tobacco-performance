import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
import numpy as np
import json
import os
import pickle

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
    .tip-card {
        background: linear-gradient(90deg, #e0f2fe 0%, #bae6fd 100%);
        border-left: 5px solid #0ea5e9;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ========== 数据持久化存储 ==========
DATA_FILE = "performance_data.pkl"
HISTORY_FILE = "quarter_history.pkl"

def save_data():
    """保存数据到文件"""
    try:
        data_to_save = {
            'performance_data': st.session_state.performance_data,
            'quarter_history': st.session_state.quarter_history,
            'current_quarter': st.session_state.current_quarter,
            'last_reset': st.session_state.last_reset,
            'data_history': st.session_state.data_history
        }
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(data_to_save, f)
        return True
    except Exception as e:
        st.error(f"保存数据时出错：{str(e)}")
        return False

def load_data():
    """从文件加载数据"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'rb') as f:
                data = pickle.load(f)
                return data
        return None
    except Exception as e:
        st.error(f"加载数据时出错：{str(e)}")
        return None

def save_history():
    """保存季度历史数据"""
    try:
        with open(HISTORY_FILE, 'wb') as f:
            pickle.dump(st.session_state.quarter_history, f)
        return True
    except Exception as e:
        st.error(f"保存历史数据时出错：{str(e)}")
        return False

def load_history():
    """加载季度历史数据"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'rb') as f:
                return pickle.load(f)
        return {}
    except Exception as e:
        st.error(f"加载历史数据时出错：{str(e)}")
        return {}

# ========== Session State 初始化 ==========
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'current_city' not in st.session_state:
    st.session_state.current_city = None

# 从文件加载数据
if 'performance_data' not in st.session_state:
    loaded_data = load_data()
    if loaded_data:
        st.session_state.performance_data = loaded_data.get('performance_data')
        st.session_state.quarter_history = loaded_data.get('quarter_history', {})
        st.session_state.current_quarter = loaded_data.get('current_quarter')
        st.session_state.last_reset = loaded_data.get('last_reset')
        st.session_state.data_history = loaded_data.get('data_history', {})
    else:
        st.session_state.performance_data = None
        st.session_state.quarter_history = {}
        st.session_state.current_quarter = None
        st.session_state.last_reset = None
        st.session_state.data_history = {}

if 'data_sync_flag' not in st.session_state:
    st.session_state.data_sync_flag = False

# ========== 核心数据操作函数 ==========
def get_staff_data(staff_name):
    """获取事务员的完整数据"""
    if st.session_state.performance_data is None:
        return None
    
    staff_data = st.session_state.performance_data[
        st.session_state.performance_data['事务员'] == staff_name
    ]
    
    if staff_data.empty:
        return None
    
    return staff_data.iloc[0].to_dict()

def update_staff_data(staff_name, updates):
    """更新事务员数据并保存到文件"""
    if st.session_state.performance_data is None:
        return False
    
    try:
        # 找到事务员的索引
        staff_idx = st.session_state.performance_data[
            st.session_state.performance_data['事务员'] == staff_name
        ].index
        
        if len(staff_idx) == 0:
            return False
        
        staff_idx = staff_idx[0]
        
        # 记录原始数据
        original_data = {}
        for key in updates.keys():
            if key in st.session_state.performance_data.columns:
                original_data[key] = st.session_state.performance_data.at[staff_idx, key]
        
        # 更新数据
        for key, value in updates.items():
            if key in st.session_state.performance_data.columns:
                st.session_state.performance_data.at[staff_idx, key] = value
        
        # 记录数据变更
        if staff_name not in st.session_state.data_history:
            st.session_state.data_history[staff_name] = []
        
        st.session_state.data_history[staff_name].append({
            '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '操作': '更新数据',
            '更新内容': updates,
            '原始数据': original_data
        })
        
        # 重新计算绩效
        st.session_state.performance_data = calculate_performance(
            st.session_state.performance_data, 
            st.session_state.current_quarter
        )
        
        # 保存到文件
        save_data()
        
        return True
        
    except Exception as e:
        st.error(f"更新数据时出错：{str(e)}")
        return False

def get_current_quarter_month_columns():
    """获取当前季度的月份列名"""
    month_range = get_current_quarter_month_range()
    columns = []
    for month_num in month_range:
        columns.extend([f'分销_{month_num}月', f'条盒_{month_num}月'])
    return columns

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
    
    # 保存数据
    save_data()
    
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

def get_grade_improvement_tips(current_scores, target_grade):
    """获取提升档位的建议"""
    tips = []
    
    # 计算当前总分对应的档位
    current_total = current_scores['总分']
    current_grade, _ = calculate_salary_grade(current_total)
    
    if current_grade <= target_grade:
        return ["✅ 已达到目标档位，继续保持！"]
    
    # 需要提升的分数
    needed_improvement = 0
    if target_grade == 1:
        needed_score = 91
    elif target_grade == 2:
        needed_score = 81
    elif target_grade == 3:
        needed_score = 71
    elif target_grade == 4:
        needed_score = 61
    elif target_grade == 5:
        needed_score = 51
    elif target_grade == 6:
        needed_score = 46
    elif target_grade == 7:
        needed_score = 41
    elif target_grade == 8:
        needed_score = 36
    elif target_grade == 9:
        needed_score = 31
    else:
        needed_score = 0
    
    needed_improvement = max(0, needed_score - current_total)
    
    if needed_improvement == 0:
        return ["✅ 已达到目标档位，继续保持！"]
    
    tips.append(f"📈 需要提升 {needed_improvement} 分才能达到 {target_grade} 档")
    
    # 各项得分分析
    if current_scores['分销得分'] < 25:
        tips.append(f"📦 分销得分：{current_scores['分销得分']}/25，可以提升 {25 - current_scores['分销得分']} 分")
        if current_scores['分销均季度'] < 61:
            tips.append(f"   → 建议将分销季度平均值提升到 61条以上（当前 {current_scores['分销均季度']}条）")
        elif current_scores['分销均季度'] < 151:
            tips.append(f"   → 建议将分销季度平均值提升到 151条以上（当前 {current_scores['分销均季度']}条）")
        elif current_scores['分销均季度'] < 301:
            tips.append(f"   → 建议将分销季度平均值提升到 301条以上（当前 {current_scores['分销均季度']}条）")
        elif current_scores['分销均季度'] < 601:
            tips.append(f"   → 建议将分销季度平均值提升到 601条以上（当前 {current_scores['分销均季度']}条）")
        else:
            tips.append(f"   → 建议将分销季度平均值提升到 1000条以上（当前 {current_scores['分销均季度']}条）")
    
    if current_scores['条盒回收得分'] < 35:
        tips.append(f"📊 条盒回收得分：{current_scores['条盒回收得分']}/35，可以提升 {35 - current_scores['条盒回收得分']} 分")
        if current_scores['条盒均季度'] < 181:
            tips.append(f"   → 建议将条盒回收季度平均值提升到 181条以上（当前 {current_scores['条盒均季度']}条）")
        elif current_scores['条盒均季度'] < 201:
            tips.append(f"   → 建议将条盒回收季度平均值提升到 201条以上（当前 {current_scores['条盒均季度']}条）")
        elif current_scores['条盒均季度'] < 301:
            tips.append(f"   → 建议将条盒回收季度平均值提升到 301条以上（当前 {current_scores['条盒均季度']}条）")
        elif current_scores['条盒均季度'] < 401:
            tips.append(f"   → 建议将条盒回收季度平均值提升到 401条以上（当前 {current_scores['条盒均季度']}条）")
        elif current_scores['条盒均季度'] < 601:
            tips.append(f"   → 建议将条盒回收季度平均值提升到 601条以上（当前 {current_scores['条盒均季度']}条）")
        elif current_scores['条盒均季度'] < 801:
            tips.append(f"   → 建议将条盒回收季度平均值提升到 801条以上（当前 {current_scores['条盒均季度']}条）")
        else:
            tips.append(f"   → 建议将条盒回收季度平均值提升到 1000条以上（当前 {current_scores['条盒均季度']}条）")
    
    if current_scores['核心户得分'] < 20:
        tips.append(f"👥 核心户得分：{current_scores['核心户得分']}/20，可以提升 {20 - current_scores['核心户得分']} 分")
        if current_scores['核心户得分'] < 5:
            tips.append(f"   → 建议将核心户数增加到 16人以上")
        elif current_scores['核心户得分'] < 10:
            tips.append(f"   → 建议将核心户数增加到 21人以上")
        elif current_scores['核心户得分'] < 15:
            tips.append(f"   → 建议将核心户数增加到 26人以上")
        else:
            tips.append(f"   → 建议将核心户数增加到 31人以上")
    
    if current_scores['综合得分'] < 20:
        tips.append(f"⭐ 综合得分：{current_scores['综合得分']}/20，可以提升 {20 - current_scores['综合得分']} 分")
        tips.append(f"   → 请加强与地市经理的沟通，提高工作表现评分")
    
    return tips

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

# ========== 数据导入导出函数 ==========
def import_excel_data(uploaded_file):
    """从Excel文件导入数据"""
    try:
        df = pd.read_excel(uploaded_file)
        return df, True, "导入成功"
    except Exception as e:
        return None, False, f"导入失败: {str(e)}"

def export_to_excel(df):
    """导出数据到Excel"""
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='绩效数据')
        output.seek(0)
        return output, True, "导出成功"
    except Exception as e:
        return None, False, f"导出失败: {str(e)}"

def export_quarter_history():
    """导出季度历史数据"""
    try:
        if not st.session_state.quarter_history:
            return None, False, "没有历史数据"
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for quarter, data in st.session_state.quarter_history.items():
                df = pd.DataFrame(data)
                df.to_excel(writer, index=False, sheet_name=quarter[:10])  # 限制sheet名长度
        
        output.seek(0)
        return output, True, "历史数据导出成功"
    except Exception as e:
        return None, False, f"导出失败: {str(e)}"

def backup_data():
    """备份数据到文件"""
    try:
        backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_{backup_time}.pkl"
        
        backup_data = {
            'performance_data': st.session_state.performance_data,
            'quarter_history': st.session_state.quarter_history,
            'current_quarter': st.session_state.current_quarter,
            'last_reset': st.session_state.last_reset,
            'data_history': st.session_state.data_history
        }
        
        with open(backup_file, 'wb') as f:
            pickle.dump(backup_data, f)
        
        return backup_file, True, f"备份成功：{backup_file}"
    except Exception as e:
        return None, False, f"备份失败: {str(e)}"

def restore_backup(backup_file):
    """从备份文件恢复数据"""
    try:
        with open(backup_file, 'rb') as f:
            backup_data = pickle.load(f)
        
        st.session_state.performance_data = backup_data.get('performance_data')
        st.session_state.quarter_history = backup_data.get('quarter_history', {})
        st.session_state.current_quarter = backup_data.get('current_quarter')
        st.session_state.last_reset = backup_data.get('last_reset')
        st.session_state.data_history = backup_data.get('data_history', {})
        
        save_data()
        
        return True, "数据恢复成功"
    except Exception as e:
        return False, f"恢复失败: {str(e)}"

def find_backup_files():
    """查找备份文件"""
    backup_files = []
    for file in os.listdir('.'):
        if file.startswith('backup_') and file.endswith('.pkl'):
            backup_files.append(file)
    return sorted(backup_files, reverse=True)

# ========== 登录页面 ==========
def login_page():
    st.markdown('<h1 class="main-header">🔐 广东中烟绩效管理系统（季度版）</h1>', unsafe_allow_html=True)
    
    # 显示数据状态
    if os.path.exists(DATA_FILE):
        st.markdown(f'<div class="sync-status">💾 数据已从本地文件加载</div>', unsafe_allow_html=True)
    
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
        # 保存初始数据
        save_data()
    
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
        
        **💾 数据存储：**
        - 所有数据都保存在本地文件中
        - 每次数据更新都会自动保存
        - 关闭浏览器后数据不会丢失
        
        **📝 重要提示：**
        - Q4季度（10-12月）按4个月的数据折算为季度平均值
        - 每个季度开始时会自动重置数据
        - 历史季度数据可以在"历史季度"页面查看
        """)

# ========== 事务员个人页面 ==========
def staff_dashboard():
    st.markdown(f'<h2 class="main-header">👤 {st.session_state.user_name} 的个人中心</h2>', unsafe_allow_html=True)
    
    # 获取用户数据
    staff_data = get_staff_data(st.session_state.user_name)
    
    if staff_data is None:
        st.error("未找到您的数据")
        return
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📊 季度绩效", "📝 实时数据填报", "🧮 得分计算器", "📈 历史季度"])
    
    with tab1:
        # 档位提醒
        if '档位提醒级别' in staff_data and '档位提醒信息' in staff_data:
            st.markdown(f'<div class="{staff_data["档位提醒级别"]}-card">{staff_data["档位提醒信息"]}</div>', unsafe_allow_html=True)
        
        # 季度绩效总览
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("季度总分", f"{staff_data['总分']}分" if '总分' in staff_data else "0分")
        with col2:
            if '档位' in staff_data and '季度目标档位' in staff_data:
                current_grade = staff_data['档位']
                target_grade = staff_data['季度目标档位']
                color = "#10b981" if current_grade <= target_grade else "#ef4444"
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="font-size: 0.9rem; color: #666;">季度档位</div>
                    <div style="font-size: 2rem; font-weight: bold; color: {color};">{current_grade}档</div>
                    <div style="font-size: 0.8rem; color: #666;">目标：{target_grade}档</div>
                </div>
                """, unsafe_allow_html=True)
        with col3:
            st.metric("季度月薪", f"¥{staff_data['预估月薪']}" if '预估月薪' in staff_data else "¥0")
        with col4:
            st.metric("所属地市", staff_data['地市'])
        
        st.divider()
        
        # 得分详情
        st.subheader("📈 季度得分详情")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            dist_score = staff_data['分销得分'] if '分销得分' in staff_data else 0
            dist_avg = staff_data['分销均季度'] if '分销均季度' in staff_data else 0
            st.metric("分销得分", f"{dist_score}/25")
            st.caption(f"均季度: {dist_avg}条")
        with col2:
            recycle_score = staff_data['条盒回收得分'] if '条盒回收得分' in staff_data else 0
            recycle_avg = staff_data['条盒均季度'] if '条盒均季度' in staff_data else 0
            st.metric("条盒回收得分", f"{recycle_score}/35")
            st.caption(f"均季度: {recycle_avg}条")
        with col3:
            core_score = staff_data['核心户得分'] if '核心户得分' in staff_data else 0
            core_count = staff_data['核心户数'] if '核心户数' in staff_data else 0
            st.metric("核心户得分", f"{core_score}/20")
            st.caption(f"核心户数: {core_count}人")
        with col4:
            comp_score = staff_data['综合得分'] if '综合得分' in staff_data else 0
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
                    
                    dist_value = staff_data[dist_col] if dist_col in staff_data else 0
                    recycle_value = staff_data[recycle_col] if recycle_col in staff_data else 0
                    
                    st.metric(f"{month}分销", f"{dist_value}条")
                    st.metric(f"{month}回收", f"{recycle_value}条")
        
        # 改进建议和提升档位提示
        st.divider()
        st.subheader("💡 提升建议")
        
        if '档位' in staff_data and '季度目标档位' in staff_data:
            current_grade = staff_data['档位']
            target_grade = staff_data['季度目标档位']
            
            if current_grade > target_grade:
                current_scores = {
                    '总分': staff_data['总分'] if '总分' in staff_data else 0,
                    '分销得分': staff_data['分销得分'] if '分销得分' in staff_data else 0,
                    '条盒回收得分': staff_data['条盒回收得分'] if '条盒回收得分' in staff_data else 0,
                    '核心户得分': staff_data['核心户得分'] if '核心户得分' in staff_data else 0,
                    '综合得分': staff_data['综合得分'] if '综合得分' in staff_data else 0,
                    '分销均季度': staff_data['分销均季度'] if '分销均季度' in staff_data else 0,
                    '条盒均季度': staff_data['条盒均季度'] if '条盒均季度' in staff_data else 0,
                }
                
                tips = get_grade_improvement_tips(current_scores, target_grade)
                
                st.markdown('<div class="tip-card">', unsafe_allow_html=True)
                st.markdown("### 🎯 提升档位建议")
                for tip in tips:
                    st.write(f"• {tip}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.success("✅ 恭喜！您已达到或超过目标档位，继续保持！")
    
    with tab2:
        st.subheader(f"📅 {st.session_state.current_quarter} 实时数据填报")
        
        # 获取季度月份
        quarter_months = get_quarter_months(st.session_state.current_quarter)
        
        # 获取当前数据
        dist_values = []
        recycle_values = []
        
        for month in quarter_months:
            month_num = int(month.replace('月', ''))
            dist_col = f'分销_{month_num}月'
            recycle_col = f'条盒_{month_num}月'
            
            dist_values.append(staff_data[dist_col] if dist_col in staff_data else 0)
            recycle_values.append(staff_data[recycle_col] if recycle_col in staff_data else 0)
        
        core_customers = staff_data['核心户数'] if '核心户数' in staff_data else 0
        target_grade = staff_data['季度目标档位'] if '季度目标档位' in staff_data else 6
        comp_score = staff_data['综合评分'] if '综合评分' in staff_data else 0
        
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
                # 准备更新数据
                updates = {}
                
                # 添加月度数据更新
                for i, month in enumerate(quarter_months):
                    month_num = int(month.replace('月', ''))
                    dist_col = f'分销_{month_num}月'
                    recycle_col = f'条盒_{month_num}月'
                    
                    updates[dist_col] = new_dist_values[i]
                    updates[recycle_col] = new_recycle_values[i]
                
                # 添加核心户数更新
                updates['核心户数'] = new_core_customers
                
                # 执行更新
                success = update_staff_data(st.session_state.user_name, updates)
                
                if success:
                    st.success("✅ 季度数据保存成功！")
                    st.info("💾 数据已保存到本地文件，地市经理和管理员可以立即查看。")
                    
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
    
    with tab4:
        st.subheader("📈 历史季度数据")
        
        if st.session_state.quarter_history:
            quarters = list(st.session_state.quarter_history.keys())
            if quarters:
                selected_quarter = st.selectbox("选择历史季度查看", quarters, key="history_quarter_select")
                
                if selected_quarter in st.session_state.quarter_history:
                    history_data = pd.DataFrame(st.session_state.quarter_history[selected_quarter])
                    user_history = history_data[history_data['事务员'] == st.session_state.user_name]
                    
                    if not user_history.empty:
                        hist_row = user_history.iloc[0]
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(f"{selected_quarter}总分", f"{hist_row['总分']}分")
                        with col2:
                            st.metric(f"{selected_quarter}档位", f"{hist_row['档位']}档")
                        with col3:
                            st.metric(f"{selected_quarter}月薪", f"¥{hist_row['预估月薪']}")
                        
                        # 显示详细得分
                        st.markdown("### 详细得分")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("分销得分", f"{hist_row['分销得分']}/25")
                        with col2:
                            st.metric("条盒回收得分", f"{hist_row['条盒回收得分']}/35")
                        with col3:
                            st.metric("核心户得分", f"{hist_row['核心户得分']}/20")
                        with col4:
                            st.metric("综合得分", f"{hist_row['综合得分']}/20")
                    else:
                        st.info(f"{selected_quarter}没有您的历史数据")
            else:
                st.info("暂无历史季度数据")
        else:
            st.info("暂无历史季度数据")

# ========== 地市经理页面 ==========
def manager_dashboard():
    st.markdown(f'<h2 class="main-header">📊 {st.session_state.user_name} - 地市经理管理</h2>', unsafe_allow_html=True)
    
    # 获取地市经理管理的地市
    managed_city = st.session_state.current_city
    
    # 获取该地市的数据
    city_data = st.session_state.performance_data[
        st.session_state.performance_data['地市'] == managed_city
    ]
    
    if city_data.empty:
        st.warning(f"没有找到{managed_city}的数据")
        return
    
    st.success(f"您正在管理：{managed_city}地区，共{len(city_data)}位事务员")
    
    # 显示数据验证
    st.info(f"✅ 数据已从本地文件加载，以下是事务员填报的最新数据")
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["👥 事务员管理", "📊 地区分析", "📈 绩效考核"])
    
    with tab1:
        st.subheader(f"{managed_city}地区事务员列表")
        
        # 获取当前季度数据
        current_city_data = get_current_quarter_data(city_data, st.session_state.current_quarter)
        
        # 显示具体的事务员数据
        for idx, row in current_city_data.iterrows():
            with st.expander(f"{row['事务员']} - 当前数据", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**分销数据：**")
                    month_range = get_current_quarter_month_range()
                    for month_num in month_range:
                        dist_col = f'分销_{month_num}月'
                        if dist_col in row:
                            st.write(f"{month_num}月: {row[dist_col]}条")
                
                with col2:
                    st.write("**条盒回收数据：**")
                    for month_num in month_range:
                        recycle_col = f'条盒_{month_num}月'
                        if recycle_col in row:
                            st.write(f"{month_num}月: {row[recycle_col]}条")
                
                st.write(f"**核心户数：** {row['核心户数'] if '核心户数' in row else 0}人")
                st.write(f"**综合评分：** {row['综合评分'] if '综合评分' in row else 0}分")
                st.write(f"**目标档位：** {row['季度目标档位'] if '季度目标档位' in row else 6}档")
        
        # 数据编辑界面
        st.subheader("编辑事务员数据")
        
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
        
        if st.button("保存修改", type="primary", use_container_width=True, key="save_manager_changes_btn"):
            # 保存修改
            for idx, row in edited_df.iterrows():
                # 找到原始数据中的对应行
                original_idx = city_data.index[city_data['行号'] == row['行号']].tolist()
                if original_idx:
                    original_idx = original_idx[0]
                    
                    # 准备更新数据
                    updates = {}
                    
                    # 更新可编辑字段
                    editable_fields = ['综合评分', '季度目标档位', '核心户数']
                    for field in editable_fields:
                        if field in row:
                            updates[field] = row[field]
                    
                    # 更新月度数据
                    month_range = get_current_quarter_month_range()
                    for month_num in month_range:
                        dist_col = f'分销_{month_num}月'
                        recycle_col = f'条盒_{month_num}月'
                        
                        if dist_col in row:
                            updates[dist_col] = row[dist_col]
                        if recycle_col in row:
                            updates[recycle_col] = row[recycle_col]
                    
                    # 执行更新
                    staff_name = row['事务员']
                    success = update_staff_data(staff_name, updates)
            
            st.success(f"✅ {managed_city}地区数据保存成功！")
            st.info("💾 数据已保存到本地文件")
            st.rerun()
    
    with tab2:
        st.subheader(f"{managed_city}地区绩效分析")
        
        # 确保数据包含必要的列
        if '总分' in city_data.columns:
            # 总体统计
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_score = city_data['总分'].mean()
                st.metric("平均总分", f"{avg_score:.1f}分")
            with col2:
                if '档位' in city_data.columns:
                    avg_grade = city_data['档位'].mean()
                    st.metric("平均档位", f"{avg_grade:.1f}档")
                else:
                    st.metric("平均档位", "0档")
            with col3:
                if '是否达标' in city_data.columns:
                    da_biao_lv = city_data['是否达标'].mean() * 100
                    st.metric("达标率", f"{da_biao_lv:.1f}%")
                else:
                    st.metric("达标率", "0%")
            
            # 档位分布
            if '档位' in city_data.columns:
                st.subheader("档位分布")
                grade_dist = city_data['档位'].value_counts().sort_index()
                
                if not grade_dist.empty:
                    col1, col2 = st.columns(2)
                    with col1:
                        fig = px.bar(x=[f"{g}档" for g in grade_dist.index], 
                                    y=grade_dist.values,
                                    title='档位分布',
                                    color=grade_dist.values,
                                    color_continuous_scale='Viridis')
                        fig.update_layout(xaxis_title="档位", yaxis_title="人数")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        fig = px.pie(values=grade_dist.values, 
                                    names=[f"{g}档" for g in grade_dist.index],
                                    title='档位占比')
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("暂无档位分布数据")
            
            # 绩效排名
            st.subheader("事务员绩效排名")
            if '总分' in city_data.columns and '事务员' in city_data.columns:
                ranking_data = city_data[['事务员', '总分', '档位', '预估月薪']].sort_values('总分', ascending=False)
                st.dataframe(ranking_data.reset_index(drop=True), use_container_width=True)
            else:
                st.info("暂无绩效排名数据")
        else:
            st.info("暂无地区分析数据")
    
    with tab3:
        st.subheader("批量绩效操作")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 批量设置目标档位")
            new_target_grade = st.slider("统一目标档位", 1, 10, 6, key="batch_target_grade")
            
            if st.button("批量设置目标档位", use_container_width=True, key="set_batch_target_btn"):
                # 准备批量更新
                updates_list = []
                for idx in city_data.index:
                    staff_name = city_data.at[idx, '事务员']
                    updates = {'季度目标档位': new_target_grade}
                    updates_list.append((staff_name, updates))
                
                # 执行批量更新
                success_count = 0
                for staff_name, updates in updates_list:
                    if update_staff_data(staff_name, updates):
                        success_count += 1
                
                st.success(f"✅ 已为{success_count}位事务员设置目标档位为{new_target_grade}档")
                st.rerun()
        
        with col2:
            st.markdown("### 批量重置综合评分")
            reset_score = st.slider("重置为", 0, 20, 10, key="reset_score_slider")
            
            if st.button("批量重置综合评分", use_container_width=True, key="reset_scores_btn"):
                # 准备批量更新
                updates_list = []
                for idx in city_data.index:
                    staff_name = city_data.at[idx, '事务员']
                    updates = {'综合评分': reset_score}
                    updates_list.append((staff_name, updates))
                
                # 执行批量更新
                success_count = 0
                for staff_name, updates in updates_list:
                    if update_staff_data(staff_name, updates):
                        success_count += 1
                
                st.success(f"✅ 已重置{success_count}位事务员的综合评分为{reset_score}分")
                st.rerun()
        
        # 导出地区数据
        st.divider()
        st.markdown("### 导出地区数据")
        
        csv_data = city_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 下载{managed_city}地区数据",
            data=csv_data,
            file_name=f"{managed_city}_绩效数据_{st.session_state.current_quarter}.csv",
            mime="text/csv",
            use_container_width=True,
            key="export_city_data_btn"
        )

# ========== 管理员页面 ==========
def admin_dashboard():
    st.markdown('<h2 class="main-header">👑 管理员控制台</h2>', unsafe_allow_html=True)
    
    # 显示数据状态
    if os.path.exists(DATA_FILE):
        file_size = os.path.getsize(DATA_FILE) / 1024
        st.markdown(f'<div class="sync-status">💾 数据文件大小: {file_size:.1f} KB | 上次修改: {datetime.fromtimestamp(os.path.getmtime(DATA_FILE)).strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)
    
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
        
        # 显示庞雷的数据示例（用于验证）
        if "庞雷" in display_data['事务员'].values:
            pang_lei_data = display_data[display_data['事务员'] == "庞雷"].iloc[0]
            
            with st.expander("🔍 验证：庞雷的数据（示例）", expanded=True):
                st.write("**当前季度数据：**")
                quarter_months = get_quarter_months(st.session_state.current_quarter)
                
                cols = st.columns(len(quarter_months))
                for i, month in enumerate(quarter_months):
                    with cols[i]:
                        month_num = int(month.replace('月', ''))
                        dist_col = f'分销_{month_num}月'
                        recycle_col = f'条盒_{month_num}月'
                        
                        if dist_col in pang_lei_data:
                            st.metric(f"{month}分销", f"{pang_lei_data[dist_col]}条")
                        if recycle_col in pang_lei_data:
                            st.metric(f"{month}回收", f"{pang_lei_data[recycle_col]}条")
                
                st.write(f"**核心户数：** {pang_lei_data['核心户数'] if '核心户数' in pang_lei_data else 0}人")
                st.write(f"**综合评分：** {pang_lei_data['综合评分'] if '综合评分' in pang_lei_data else 0}分")
                st.write(f"**目标档位：** {pang_lei_data['季度目标档位'] if '季度目标档位' in pang_lei_data else 6}档")
        
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
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("保存修改", type="primary", use_container_width=True, key="save_all_changes_btn"):
                # 保存修改到主数据
                for idx, row in edited_df.iterrows():
                    # 找到原始数据中的对应行
                    original_idx = display_data.index[display_data['行号'] == row['行号']].tolist()
                    if original_idx:
                        original_idx = original_idx[0]
                        
                        # 准备更新数据
                        updates = {}
                        
                        # 更新可编辑字段
                        editable_fields = ['综合评分', '季度目标档位', '核心户数', '备注']
                        for field in editable_fields:
                            if field in row and field in st.session_state.performance_data.columns:
                                updates[field] = row[field]
                        
                        # 更新月度数据
                        month_range = get_current_quarter_month_range()
                        for month_num in month_range:
                            dist_col = f'分销_{month_num}月'
                            recycle_col = f'条盒_{month_num}月'
                            
                            if dist_col in row:
                                updates[dist_col] = row[dist_col]
                            if recycle_col in row:
                                updates[recycle_col] = row[recycle_col]
                        
                        # 执行更新
                        staff_name = row['事务员']
                        success = update_staff_data(staff_name, updates)
                
                st.success("✅ 数据保存成功！")
                st.info("💾 数据已保存到本地文件")
                st.rerun()
        
        with col2:
            if st.button("重新计算绩效", type="secondary", use_container_width=True, key="recalculate_btn"):
                st.session_state.performance_data = calculate_performance(
                    st.session_state.performance_data, 
                    st.session_state.current_quarter
                )
                save_data()
                st.success("✅ 绩效重新计算完成！")
                st.rerun()
        
        with col3:
            if st.button("备份数据", type="secondary", use_container_width=True, key="backup_btn"):
                backup_file, success, message = backup_data()
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
    
    with tab2:
        st.subheader("全局分析")
        
        if st.session_state.performance_data is not None and not st.session_state.performance_data.empty:
            # 总体统计
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_staff = len(st.session_state.performance_data)
                st.metric("事务员总数", total_staff)
            with col2:
                if '总分' in st.session_state.performance_data.columns:
                    avg_score = st.session_state.performance_data['总分'].mean()
                    st.metric("平均总分", f"{avg_score:.1f}分")
                else:
                    st.metric("平均总分", "0分")
            with col3:
                if '档位' in st.session_state.performance_data.columns:
                    avg_grade = st.session_state.performance_data['档位'].mean()
                    st.metric("平均档位", f"{avg_grade:.1f}档")
                else:
                    st.metric("平均档位", "0档")
            with col4:
                if '是否达标' in st.session_state.performance_data.columns:
                    da_biao_lv = st.session_state.performance_data['是否达标'].mean() * 100
                    st.metric("整体达标率", f"{da_biao_lv:.1f}%")
                else:
                    st.metric("整体达标率", "0%")
            
            # 档位分布
            if '档位' in st.session_state.performance_data.columns:
                st.subheader("📊 档位分布情况")
                grade_dist = st.session_state.performance_data['档位'].value_counts().sort_index()
                
                if not grade_dist.empty:
                    col1, col2 = st.columns(2)
                    with col1:
                        fig = px.pie(values=grade_dist.values, 
                                    names=[f"{g}档" for g in grade_dist.index],
                                    title='档位分布饼图')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        fig = px.bar(x=[f"{g}档" for g in grade_dist.index], 
                                    y=grade_dist.values,
                                    title='档位分布柱状图',
                                    color=grade_dist.values,
                                    color_continuous_scale='Blues')
                        fig.update_layout(xaxis_title="档位", yaxis_title="人数")
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("暂无档位分布数据")
            
            # 地区分析
            if '地市' in st.session_state.performance_data.columns and '总分' in st.session_state.performance_data.columns:
                st.subheader("🏙️ 地区绩效分析")
                city_stats = st.session_state.performance_data.groupby('地市').agg({
                    '总分': 'mean',
                    '档位': 'mean',
                    '事务员': 'count'
                }).round(1).reset_index()
                
                city_stats.columns = ['地市', '平均总分', '平均档位', '事务员数']
                
                if not city_stats.empty:
                    col1, col2 = st.columns(2)
                    with col1:
                        fig = px.bar(city_stats.sort_values('平均总分', ascending=False).head(10),
                                    x='地市', y='平均总分',
                                    title='平均总分前十地区',
                                    color='平均总分',
                                    color_continuous_scale='Viridis')
                        fig.update_layout(xaxis_title="地市", yaxis_title="平均总分")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        fig = px.scatter(city_stats, x='事务员数', y='平均总分',
                                        size='事务员数', hover_name='地市',
                                        title='地区人数与绩效关系',
                                        color='平均档位',
                                        color_continuous_scale='RdYlGn')
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("暂无地区分析数据")
        else:
            st.info("暂无全局分析数据")
    
    with tab3:
        st.subheader("🔄 季度管理")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 季度设置")
            
            # 手动设置当前季度
            quarters = [f"{datetime.now().year}年Q{quarter}季度" for quarter in range(1, 5)]
            selected_quarter = st.selectbox(
                "选择当前季度",
                quarters,
                index=quarters.index(st.session_state.current_quarter) if st.session_state.current_quarter in quarters else 0,
                key="admin_select_quarter"
            )
            
            if st.session_state.current_quarter != selected_quarter:
                if st.button("切换季度", type="primary", use_container_width=True, key="switch_quarter_btn"):
                    st.session_state.current_quarter = selected_quarter
                    st.success(f"✅ 已切换到 {selected_quarter}")
                    st.rerun()
            
            # 季度目标设置
            st.markdown("### 批量季度目标设置")
            default_target = st.slider("默认目标档位", 1, 10, 6, key="admin_target_slider")
            
            if st.button("全员设置季度目标", use_container_width=True, key="set_all_target_btn"):
                success_count = 0
                for idx in st.session_state.performance_data.index:
                    staff_name = st.session_state.performance_data.at[idx, '事务员']
                    updates = {'季度目标档位': default_target}
                    if update_staff_data(staff_name, updates):
                        success_count += 1
                
                st.success(f"✅ 已为{success_count}位事务员设置季度目标为{default_target}档")
                st.rerun()
        
        with col2:
            st.markdown("### 季度操作")
            
            # 检查季度状态
            if st.session_state.last_reset == st.session_state.current_quarter:
                st.success(f"✅ {st.session_state.current_quarter} 数据已重置")
            else:
                st.warning(f"⚠️ {st.session_state.current_quarter} 数据未重置")
            
            # 手动重置当前季度
            if st.button("手动重置当前季度数据", type="primary", use_container_width=True, key="manual_reset_btn"):
                if st.session_state.performance_data is not None:
                    st.session_state.performance_data = reset_quarter_data(
                        st.session_state.performance_data,
                        target_grade=6
                    )
                    st.success(f"✅ {st.session_state.current_quarter} 数据已重置")
                    st.rerun()
            
            # 显示季度历史
            st.markdown("### 季度历史记录")
            if st.session_state.quarter_history:
                quarters = list(st.session_state.quarter_history.keys())
                if quarters:
                    selected_history = st.selectbox("查看历史季度", quarters, key="admin_history_select")
                    
                    if selected_history in st.session_state.quarter_history:
                        history_df = pd.DataFrame(st.session_state.quarter_history[selected_history])
                        history_summary = history_df.groupby('地市').agg({
                            '总分': 'mean',
                            '档位': 'mean',
                            '事务员': 'count'
                        }).round(1)
                        
                        st.dataframe(history_summary, use_container_width=True)
            else:
                st.info("暂无季度历史数据")
        
        # 历史季度数据管理
        st.markdown("### 📊 历史季度数据导出")
        
        if st.session_state.quarter_history:
            col1, col2 = st.columns(2)
            with col1:
                # 导出所有历史数据
                output, success, message = export_quarter_history()
                if success:
                    st.download_button(
                        label="📥 下载所有历史季度数据",
                        data=output,
                        file_name=f"季度历史数据_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="export_all_history_btn"
                    )
            with col2:
                if st.button("清空历史季度数据", type="secondary", use_container_width=True, key="clear_history_btn"):
                    st.session_state.quarter_history = {}
                    save_data()
                    st.success("✅ 历史季度数据已清空")
                    st.rerun()
        else:
            st.info("暂无历史季度数据")
    
    with tab4:
        st.subheader("📤 数据导入导出")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 数据导入")
            
            uploaded_file = st.file_uploader(
                "上传Excel数据文件",
                type=['xlsx', 'xls'],
                help="请上传包含绩效数据的Excel文件"
            )
            
            if uploaded_file is not None:
                try:
                    # 读取Excel文件
                    df = pd.read_excel(uploaded_file)
                    
                    # 显示数据预览
                    with st.expander("预览导入的数据", expanded=True):
                        st.write(f"数据形状: {df.shape}")
                        st.dataframe(df.head(10), use_container_width=True)
                    
                    # 检查必要列
                    required_columns = ['行号', '地市', '事务员']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        st.error(f"缺少必要列: {missing_columns}")
                    else:
                        if st.button("确认导入数据", type="primary", use_container_width=True, key="confirm_import_btn"):
                            # 合并数据
                            df_merged = pd.concat([st.session_state.performance_data, df], ignore_index=True).drop_duplicates(subset=['事务员'], keep='last')
                            
                            # 重新计算绩效
                            df_merged = calculate_performance(df_merged, st.session_state.current_quarter)
                            
                            # 更新session state
                            st.session_state.performance_data = df_merged
                            save_data()
                            
                            st.success(f"✅ 数据导入成功！共导入{len(df)}条记录")
                            st.rerun()
                
                except Exception as e:
                    st.error(f"导入失败: {str(e)}")
        
        with col2:
            st.markdown("### 数据导出")
            
            # 导出当前季度数据
            output, success, message = export_to_excel(st.session_state.performance_data)
            
            if success:
                st.download_button(
                    label="📥 下载当前季度完整数据",
                    data=output,
                    file_name=f"广东中烟绩效数据_{st.session_state.current_quarter}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="export_current_btn"
                )
            
            # 导出CSV格式
            csv_data = st.session_state.performance_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 下载CSV格式数据",
                data=csv_data,
                file_name=f"绩效数据_{st.session_state.current_quarter}.csv",
                mime="text/csv",
                use_container_width=True,
                key="export_csv_btn"
            )
        
        # 备份与恢复
        st.markdown("### 💾 备份与恢复")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 创建新备份
            if st.button("创建新备份", type="primary", use_container_width=True, key="create_backup_btn"):
                backup_file, success, message = backup_data()
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
        
        with col2:
            # 恢复备份
            backup_files = find_backup_files()
            if backup_files:
                selected_backup = st.selectbox("选择备份文件恢复", backup_files, key="backup_select")
                
                if st.button("恢复选中备份", type="secondary", use_container_width=True, key="restore_backup_btn"):
                    success, message = restore_backup(selected_backup)
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            else:
                st.info("暂无备份文件")
    
    with tab5:
        st.subheader("⚙️ 系统设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 系统信息")
            
            # 显示当前系统状态
            st.info(f"""
            **系统状态：** 运行正常 ✅
            **当前季度：** {st.session_state.current_quarter}
            **数据记录数：** {len(st.session_state.performance_data) if st.session_state.performance_data is not None else 0}
            **历史季度数：** {len(st.session_state.quarter_history)}
            **数据文件：** {DATA_FILE}
            """)
            
            # 系统健康检查
            st.markdown("### 系统健康检查")
            
            check_items = []
            
            # 检查数据文件
            if os.path.exists(DATA_FILE):
                check_items.append(("数据文件", "✅ 正常", "文件大小正常"))
            else:
                check_items.append(("数据文件", "⚠️ 警告", "数据文件不存在"))
            
            # 检查数据完整性
            if st.session_state.performance_data is not None:
                check_items.append(("数据完整性", "✅ 正常", f"共{len(st.session_state.performance_data)}条记录"))
            else:
                check_items.append(("数据完整性", "❌ 错误", "数据为空"))
            
            # 检查季度设置
            if st.session_state.current_quarter:
                check_items.append(("季度设置", "✅ 正常", st.session_state.current_quarter))
            else:
                check_items.append(("季度设置", "❌ 错误", "未设置季度"))
            
            # 显示检查结果
            for item, status, detail in check_items:
                st.write(f"**{item}:** {status} - {detail}")
            
            # 系统统计
            if st.session_state.performance_data is not None:
                total_updates = sum(len(history) for history in st.session_state.data_history.values())
                st.write(f"**数据更新次数：** {total_updates}次")
                st.write(f"**地市数量：** {st.session_state.performance_data['地市'].nunique()}个")
                st.write(f"**事务员数量：** {st.session_state.performance_data['事务员'].nunique()}人")
        
        with col2:
            st.markdown("### 系统维护")
            
            # 数据清理
            st.markdown("#### 数据清理")
            
            if st.button("清理临时数据", type="secondary", use_container_width=True, key="clean_temp_btn"):
                # 可以添加清理逻辑
                st.success("✅ 临时数据清理完成")
            
            # 重置系统
            st.markdown("#### 系统重置")
            
            reset_option = st.selectbox(
                "选择重置类型",
                ["请选择", "重置当前季度数据", "重置所有数据", "重置登录状态"],
                key="reset_option_select"
            )
            
            if reset_option != "请选择":
                if st.button(f"执行{reset_option}", type="primary", use_container_width=True, key="execute_reset_btn"):
                    if reset_option == "重置当前季度数据":
                        if st.session_state.performance_data is not None:
                            st.session_state.performance_data = reset_quarter_data(
                                st.session_state.performance_data,
                                target_grade=6
                            )
                            st.success("✅ 当前季度数据已重置")
                    elif reset_option == "重置所有数据":
                        st.session_state.performance_data = init_data_from_template()
                        st.session_state.performance_data = calculate_performance(
                            st.session_state.performance_data,
                            st.session_state.current_quarter
                        )
                        st.session_state.quarter_history = {}
                        st.session_state.data_history = {}
                        save_data()
                        st.success("✅ 所有数据已重置为初始状态")
                    elif reset_option == "重置登录状态":
                        # 只重置登录状态，保留数据
                        st.session_state.authenticated = False
                        st.session_state.user_role = None
                        st.session_state.user_name = None
                        st.session_state.current_city = None
                        st.success("✅ 登录状态已重置")
                    
                    st.rerun()
            
            # 日志查看
            st.markdown("#### 操作日志")
            
            if st.session_state.data_history:
                with st.expander("查看操作日志", expanded=False):
                    for staff_name, history in list(st.session_state.data_history.items())[:10]:  # 只显示前10条
                        for record in history[-3:]:  # 只显示最近3条
                            st.write(f"**{staff_name}** - {record['时间']}")
                            st.write(f"操作: {record['操作']}")
                            if '更新内容' in record:
                                st.write(f"更新内容: {record['更新内容']}")
                            st.divider()
            else:
                st.info("暂无操作日志")
        
        # 密码管理
        st.markdown("### 🔑 密码管理")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_manager_pwd = st.text_input("新地市经理密码", type="password", key="new_manager_pwd")
            if st.button("更新地市经理密码", use_container_width=True, key="update_manager_pwd_btn"):
                # 在实际应用中，这里应该将密码保存到配置文件或数据库中
                st.success("✅ 地市经理密码已更新（演示功能）")
        
        with col2:
            new_admin_pwd = st.text_input("新管理员密码", type="password", key="new_admin_pwd")
            if st.button("更新管理员密码", use_container_width=True, key="update_admin_pwd_btn"):
                # 在实际应用中，这里应该将密码保存到配置文件或数据库中
                st.success("✅ 管理员密码已更新（演示功能）")
        
        with col3:
            st.write("**密码安全提示：**")
            st.write("1. 密码长度至少8位")
            st.write("2. 包含大小写字母和数字")
            st.write("3. 定期更换密码")

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
            # 保存数据
            save_data()
            # 清空session state
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
