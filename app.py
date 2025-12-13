import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from io import BytesIO
import json

# ========== 页面配置 ==========
st.set_page_config(
    page_title="广东中烟绩效管理系统",
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

def reset_quarter_data(df, target_grade=6):
    """重置季度数据并设置目标档位"""
    # 保存当前季度数据到历史记录
    current_q = st.session_state.current_quarter
    if current_q and not df.empty:
        # 只保存关键数据到历史
        history_data = df[['行号', '地市', '事务员', '总分', '档位', '预估月薪']].copy()
        st.session_state.quarter_history[current_q] = history_data.to_dict('records')
    
    # 重置月度数据（保留基本信息）
    for col in df.columns:
        if '月' in col and '均季度' not in col:
            df[col] = 0
        elif col in ['核心户数', '综合评分', '备注']:
            df[col] = 0 if col != '备注' else ''
        elif col in ['分销得分', '条盒回收得分', '核心户得分', '综合得分', '总分', '档位', '预估月薪']:
            df[col] = 0
    
    # 设置季度目标（例如目标为6档）
    df['季度目标档位'] = target_grade
    
    return df

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

def calculate_monthly_to_quarter(monthly_data, month_count):
    if month_count == 0 or not monthly_data:
        return 0
    return sum(monthly_data) * (3 / month_count)

# ========== 数据初始化 ==========
def init_data_from_template():
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
            # 当前季度数据
            '分销_本月1': 0, '分销_本月2': 0, '分销_本月3': 0,
            '条盒_本月1': 0, '条盒_本月2': 0, '条盒_本月3': 0,
            # 其他数据
            '核心户数': 0,
            '综合评分': 0,
            '季度目标档位': 6,  # 默认目标6档
            '备注': '',
            # 历史季度数据（初始为空）
            '上季度总分': 0,
            '上季度档位': 0,
            '上季度月薪': 0
        })
    
    df = pd.DataFrame(data)
    return df

def calculate_performance(df, quarter):
    """根据季度计算绩效"""
    results = []
    quarter_months = get_quarter_months(quarter)
    
    for _, row in df.iterrows():
        # 获取当前季度数据
        if "Q1" in quarter:
            dist_data = [row['分销_本月1'], row['分销_本月2'], row['分销_本月3']]
            recycle_data = [row['条盒_本月1'], row['条盒_本月2'], row['条盒_本月3']]
            month_count = 3
        elif "Q2" in quarter:
            dist_data = [row['分销_本月1'], row['分销_本月2'], row['分销_本月3']]
            recycle_data = [row['条盒_本月1'], row['条盒_本月2'], row['条盒_本月3']]
            month_count = 3
        elif "Q4" in quarter:
            # Q4有4个月
            dist_data = [row['分销_本月1'], row['分销_本月2'], row['分销_本月3'], 0]  # 第4个月默认为0
            recycle_data = [row['条盒_本月1'], row['条盒_本月2'], row['条盒_本月3'], 0]
            month_count = 4
        else:
            dist_data = [row['分销_本月1'], row['分销_本月2'], row['分销_本月3']]
            recycle_data = [row['条盒_本月1'], row['条盒_本月2'], row['条盒_本月3']]
            month_count = 3
        
        # 计算季度平均
        dist_avg = calculate_monthly_to_quarter(dist_data, month_count)
        recycle_avg = calculate_monthly_to_quarter(recycle_data, month_count)
        
        # 计算得分
        dist_score = calculate_distribution_score(dist_avg)
        recycle_score = calculate_recycling_score(recycle_avg)
        core_score = calculate_core_customer_score(row['核心户数'])
        comp_score = row['综合评分']
        
        # 总分和档位
        total_score = dist_score + recycle_score + core_score + comp_score
        grade, salary = calculate_salary_grade(total_score)
        
        # 检查档位提醒
        target_grade = row.get('季度目标档位', 6)
        warning_level, warning_msg = check_grade_warning(grade, target_grade)
        
        results.append({
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
        })
    
    scores_df = pd.DataFrame(results)
    return pd.concat([df, scores_df], axis=1)

# ========== 登录页面 ==========
def login_page():
    st.markdown('<h1 class="main-header">🔐 广东中烟绩效管理系统（季度版）</h1>', unsafe_allow_html=True)
    
    # 初始化当前季度
    if st.session_state.current_quarter is None:
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
            
            role = st.radio("您的身份", ["事务员", "地市经理", "管理员"], horizontal=True)
            
            if role == "事务员":
                staff_names = st.session_state.performance_data['事务员'].tolist()
                user_name = st.selectbox("请选择您的姓名", staff_names)
                
                if st.button("登录", type="primary", use_container_width=True):
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
                city = st.selectbox("请选择您管理的地市", cities)
                manager_pwd = st.text_input("地市经理密码", type="password", value="manager123")
                
                if st.button("地市经理登录", type="primary", use_container_width=True):
                    if manager_pwd == "manager123":
                        st.session_state.authenticated = True
                        st.session_state.user_role = "manager"
                        st.session_state.current_city = city
                        st.session_state.user_name = f"{city}地市经理"
                        st.rerun()
                    else:
                        st.error("密码错误！")
            
            else:  # 管理员
                admin_pwd = st.text_input("管理员密码", type="password")
                
                if st.button("管理员登录", type="primary", use_container_width=True):
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
        
        **🎯 档位提醒系统：**
        - 绿色✅：超过目标档位
        - 黄色📊：达到目标档位  
        - 红色⚠️：低于目标档位（需要改进）
        
        **👤 各角色功能：**
        - 事务员：填报月度数据，查看季度成绩和提醒
        - 地市经理：查看本地区数据，进行综合评分
        - 管理员：季度管理、数据重置、系统设置
        
        **🔑 默认密码：**
        - 事务员：直接选择姓名（无需密码）
        - 地市经理：manager123
        - 管理员：admin123
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
    
    # 档位提醒
    st.markdown(f'<div class="{user_row["档位提醒级别"]}-card">{user_row["档位提醒信息"]}</div>', unsafe_allow_html=True)
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📊 季度绩效", "📝 数据填报", "🧮 得分计算器", "📈 历史季度"])
    
    with tab1:
        # 季度绩效总览
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("季度总分", f"{user_row['总分']}分")
        with col2:
            color = "#10b981" if user_row['档位'] <= user_row['季度目标档位'] else "#ef4444"
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; color: #666;">季度档位</div>
                <div style="font-size: 2rem; font-weight: bold; color: {color};">{user_row['档位']}档</div>
                <div style="font-size: 0.8rem; color: #666;">目标：{user_row['季度目标档位']}档</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.metric("季度月薪", f"¥{user_row['预估月薪']}")
        with col4:
            st.metric("所属地市", user_row['地市'])
        
        st.divider()
        
        # 得分详情
        st.subheader("📈 季度得分详情")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("分销得分", f"{user_row['分销得分']}/25")
            st.caption(f"均季度: {user_row['分销均季度']}条")
        with col2:
            st.metric("条盒回收得分", f"{user_row['条盒回收得分']}/35")
            st.caption(f"均季度: {user_row['条盒均季度']}条")
        with col3:
            st.metric("核心户得分", f"{user_row['核心户得分']}/20")
            st.caption(f"核心户数: {user_row['核心户数']}人")
        with col4:
            st.metric("综合得分", f"{user_row['综合得分']}/20")
            st.caption("地市经理评分")
        
        # 改进建议
        if user_row['档位'] > user_row['季度目标档位']:
            st.divider()
            st.subheader("💡 改进建议")
            
            suggestions = []
            if user_row['分销得分'] < 15:
                suggestions.append("分销得分较低，建议增加分销数量")
            if user_row['条盒回收得分'] < 20:
                suggestions.append("条盒回收需要加强")
            if user_row['核心户得分'] < 10:
                suggestions.append("需要发展更多核心户")
            
            if suggestions:
                for suggestion in suggestions:
                    st.write(f"• {suggestion}")
            else:
                st.write("各项表现均衡，继续保持！")
    
    with tab2:
        st.subheader(f"📅 {st.session_state.current_quarter} 数据填报")
        
        # 获取季度月份
        quarter_months = get_quarter_months(st.session_state.current_quarter)
        
        with st.form("monthly_data_form"):
            st.markdown("### 分销数据填报（单位：条）")
            
            cols = st.columns(len(quarter_months))
            dist_values = []
            for i, month in enumerate(quarter_months):
                with cols[i]:
                    value = st.number_input(f"{month}分销", 
                                          min_value=0, 
                                          value=int(user_row[f'分销_本月{i+1}']),
                                          key=f"dist_{i}")
                    dist_values.append(value)
            
            st.markdown("### 条盒回收数据填报（单位：条）")
            
            cols = st.columns(len(quarter_months))
            recycle_values = []
            for i, month in enumerate(quarter_months):
                with cols[i]:
                    value = st.number_input(f"{month}回收", 
                                          min_value=0, 
                                          value=int(user_row[f'条盒_本月{i+1}']),
                                          key=f"recycle_{i}")
                    recycle_values.append(value)
            
            # 核心户数
            core_customers = st.number_input("本季度核心户数", 
                                           min_value=0, 
                                           value=int(user_row['核心户数']))
            
            submitted = st.form_submit_button("保存季度数据", type="primary")
            
            if submitted:
                idx = user_data.index[0]
                
                # 更新分销数据
                for i in range(len(quarter_months)):
                    st.session_state.performance_data.at[idx, f'分销_本月{i+1}'] = dist_values[i]
                    st.session_state.performance_data.at[idx, f'条盒_本月{i+1}'] = recycle_values[i]
                
                # 更新核心户数
                st.session_state.performance_data.at[idx, '核心户数'] = core_customers
                
                # 重新计算绩效
                st.session_state.performance_data = calculate_performance(
                    st.session_state.performance_data, 
                    st.session_state.current_quarter
                )
                
                st.success("季度数据保存成功！")
                st.rerun()
    
    with tab3:
        st.subheader("🧮 得分与工资计算器")
        
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 输入模拟数据")
                target_grade = st.selectbox("目标档位", list(range(1, 11)), index=5)
                dist_q = st.number_input("分销季度总量（条）", min_value=0, value=900)
                recycle_q = st.number_input("条盒回收季度总量（条）", min_value=0, value=1200)
                core_customers = st.number_input("核心户数", min_value=0, value=28)
                comp_score = st.number_input("综合评分（0-20）", min_value=0, max_value=20, value=16)
            
            with col2:
                # 计算得分
                dist_avg = dist_q  # 季度总量直接作为均季度
                recycle_avg = recycle_q
                
                dist_score = calculate_distribution_score(dist_avg)
                recycle_score = calculate_recycling_score(recycle_avg)
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
            selected_quarter = st.selectbox("选择历史季度查看", quarters)
            
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
                else:
                    st.info(f"{selected_quarter}没有您的历史数据")
        else:
            st.info("暂无历史季度数据")

# ========== 管理员页面 - 添加季度管理 ==========
def admin_dashboard():
    st.markdown('<h2 class="main-header">👑 管理员控制台</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 数据管理", "📊 全局分析", "🔄 季度管理", "📤 数据导入导出", "⚙️ 系统设置"])
    
    with tab1:
        st.subheader("全员数据管理")
        
        edited_df = st.data_editor(
            st.session_state.performance_data,
            column_config={
                '季度目标档位': st.column_config.NumberColumn(
                    "目标档位",
                    min_value=1,
                    max_value=10,
                    step=1
                )
            },
            use_container_width=True,
            height=500,
            key="admin_editor"
        )
        
        if st.button("保存所有修改", type="primary", use_container_width=True):
            for col in edited_df.columns:
                if col in st.session_state.performance_data.columns:
                    st.session_state.performance_data[col] = edited_df[col]
            
            st.session_state.performance_data = calculate_performance(
                st.session_state.performance_data, 
                st.session_state.current_quarter
            )
            st.success("数据保存成功！")
            st.rerun()
    
    with tab2:
        st.subheader("全局分析")
        
        # 档位分布
        st.subheader("📊 档位分布情况")
        grade_dist = st.session_state.performance_data['档位'].value_counts().sort_index()
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(values=grade_dist.values, 
                        names=[f"{g}档" for g in grade_dist.index],
                        title='当前季度档位分布')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 达标情况
            df = st.session_state.performance_data
            df['是否达标'] = df['档位'] <= df['季度目标档位']
           达标率 = df['是否达标'].mean() * 100
            
            st.metric("整体达标率", f"{达标率:.1f}%")
            st.metric("平均档位", f"{df['档位'].mean():.1f}档")
            st.metric("平均目标档位", f"{df['季度目标档位'].mean():.1f}档")
    
    with tab3:
        st.subheader("🔄 季度管理")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 当前季度信息")
            st.info(f"当前季度：{st.session_state.current_quarter}")
            st.info(f"数据行数：{len(st.session_state.performance_data)}")
            st.info(f"历史季度数：{len(st.session_state.quarter_history)}")
            
            # 手动切换季度
            st.markdown("### 手动切换季度")
            new_quarter = st.selectbox("选择新季度", 
                                      [f"2024年{quarter}" for quarter in ["Q1季度", "Q2季度", "Q3季度", "Q4季度"]])
            
            if st.button("切换到新季度", type="primary"):
                st.session_state.current_quarter = new_quarter
                st.success(f"已切换到{new_quarter}")
                st.rerun()
        
        with col2:
            st.markdown("### 季度重置操作")
            st.warning("⚠️ 季度重置会清空当前数据并保存到历史记录")
            
            target_grade = st.slider("设置下季度目标档位", 1, 10, 6)
            
            if st.button("执行季度重置", type="primary", use_container_width=True):
                st.session_state.performance_data = reset_quarter_data(
                    st.session_state.performance_data,
                    target_grade
                )
                st.session_state.performance_data = calculate_performance(
                    st.session_state.performance_data,
                    st.session_state.current_quarter
                )
                st.success(f"季度数据已重置！下季度目标档位：{target_grade}档")
                st.rerun()
            
            # 查看历史季度
            st.markdown("### 历史季度数据")
            if st.session_state.quarter_history:
                quarters = list(st.session_state.quarter_history.keys())
                selected_q = st.selectbox("查看历史季度", quarters)
                
                if st.button("导出历史季度数据"):
                    hist_data = pd.DataFrame(st.session_state.quarter_history[selected_q])
                    csv = hist_data.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label=f"下载{selected_q}数据",
                        data=csv,
                        file_name=f"{selected_q}_绩效数据.csv",
                        mime="text/csv"
                    )
            else:
                st.info("暂无历史季度数据")
    
    with tab4:
        # 数据导入导出（同上）
        pass
    
    with tab5:
        # 系统设置（同上）
        pass

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
        if st.button("退出登录", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.divider()
    
    # 根据角色显示对应页面
    if st.session_state.user_role == "staff":
        staff_dashboard()
    elif st.session_state.user_role == "manager":
        # 地市经理页面（简化版）
        st.info("地市经理功能开发中，当前版本请使用管理员账号管理")
        admin_dashboard()
    else:  # admin
        admin_dashboard()

if __name__ == "__main__":
    main()
