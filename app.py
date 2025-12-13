import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# ========== 页面配置 ==========
st.set_page_config(
    page_title="广东中烟事务员绩效系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 自定义CSS美化 ==========
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #4f46e5;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
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

# ========== 模拟数据库（实际使用时替换为真实数据库） ==========
def init_sample_data():
    """初始化示例数据"""
    data = {
        '行号': list(range(1, 35)),
        '地市': ['石家庄', '保定', '保定', '保定', '保定', '沧州', '沧州', '张家口', '石家庄', '石家庄', 
                '石家庄', '石家庄', '邯郸', '邯郸', '邢台', '唐山', '廊坊', '秦皇岛', '天津', '天津',
                '北京', '北京', '临沂', '临沂', '潍坊', '潍坊', '枣庄', '淄博', '济南', '济南',
                '威海', '青岛', '烟台', '烟台', '太原', '太原', '晋中'],
        '事务员': ['庞雷', '方亚辉', '李建英', '史亚卿', '甄喜梅', '郝亮', '张卿', '李晓峰', '孙霆', '李凤霞',
                 '赵晴', '刘东青', '冯斌', '谷巧霞', '黄小刚', '张丽颖', '王玉刚', '陈晔', '夏美佳', '刘波',
                 '段体春', '胡颖', '王培娟', '朱森', '李雪兰', '王军军', '黄成志', '杨秀霞', '陈蕾', '杨晶晶',
                 '马晓燕', '田亮', '岳东玉', '高韶伟', '辛伟', '樊芳', '聂江波'],
        '调剂1-3月': [0, 2185, 175, 30, 165, 103, 152, 1693, 204, 148, 154, 160, 160, 150, 268, 166, 991, 54, 152, 0,
                   70, 14, 297, 284, 151, 160, 196, 50, 343, 226, 50, 141, 221, 51, 768, 456, 0],
        '调剂4-6月': [0, 2656, 132, 67, 124, 23, 109, 2409, 263, 172, 150, 174, 220, 162, 390, 157, 590, 28, 91, 0,
                   20, 41, 395, 287, 152, 166, 539, 165, 272, 264, 152, 178, 314, 160, 530, 303, 100],
        '条皮1-3月': [0, 421, 450, 302, 278, 286, 248, 697, 381, 417, 471, 320, 365, 345, 547, 354, 475, 176, 245, 0,
                   200, 129, 277, 289, 196, 270, 180, 137, 375, 318, 123, 132, 243, 148, 308, 210, 0],
        '空小盒兑换': ['', '', '', '', '', '20/10', '260/10', '', '', '', '', '', '280/10', '240/10', '1260/10', '', '', '', '', '',
                   '220/10', '360/10', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
        '条皮4-6月': [0, 1069, 551, 296, 364, 285, 291, 1050, 385, 492, 501, 389, 410, 313, 641, 397, 500, 317, 202, 0,
                   194, 258, 273, 302, 279, 337, 362, 223, 419, 353, 245, 264, 391, 321, 318, 333, 338],
        '客户维护': [0, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 0,
                  10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        '综合': [0, 20, 10, 10, 15, 10, 10, 15, 15, 20, 10, 10, 15, 10, 15, 15, 15, 10, 15, 0,
               10, 10, 20, 10, 10, 10, 15, 10, 15, 10, 10, 10, 10, 10, 15, 10, 10]
    }
    df = pd.DataFrame(data)
    return df

# 全局数据变量
if 'performance_data' not in st.session_state:
    st.session_state.performance_data = init_sample_data()
    st.session_state.performance_data = calculate_all_scores(st.session_state.performance_data)

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

def calculate_all_scores(df):
    """计算所有得分"""
    results = []
    for _, row in df.iterrows():
        # 计算调剂平均和得分
        tiaoji_avg = (row['调剂1-3月'] + row['调剂4-6月']) / 2
        tiaoji_score = calculate_distribution_score(tiaoji_avg)
        
        # 处理空小盒兑换
        tiaopi_4_6 = row['条皮4-6月']
        if row['空小盒兑换'] and '/' in str(row['空小盒兑换']):
            try:
                num, denom = map(int, str(row['空小盒兑换']).split('/'))
                tiaopi_4_6 += num / denom
            except:
                pass
        
        # 计算条皮平均和得分
        tiaopi_avg = (row['条皮1-3月'] + tiaopi_4_6) / 2
        tiaopi_score = calculate_recycling_score(tiaopi_avg)
        
        # 计算总分
        total_score = tiaoji_score + tiaopi_score + row['客户维护'] + row['综合']
        
        # 计算薪酬档位
        if total_score >= 91:
            grade, salary = 1, 6000
        elif total_score >= 81:
            grade, salary = 2, 5500
        elif total_score >= 71:
            grade, salary = 3, 5000
        elif total_score >= 61:
            grade, salary = 4, 4700
        elif total_score >= 51:
            grade, salary = 5, 4400
        elif total_score >= 46:
            grade, salary = 6, 4100
        elif total_score >= 41:
            grade, salary = 7, 3900
        elif total_score >= 36:
            grade, salary = 8, 3700
        elif total_score >= 31:
            grade, salary = 9, 3500
        else:
            grade, salary = 10, 3300
        
        results.append({
            '调剂平均': tiaoji_avg,
            '调剂得分': tiaoji_score,
            '条皮平均': tiaopi_avg,
            '条皮得分': tiaopi_score,
            '总分': total_score,
            '档位': grade,
            '预估月薪': salary
        })
    
    scores_df = pd.DataFrame(results)
    return pd.concat([df, scores_df], axis=1)

# ========== 登录页面 ==========
def login_page():
    st.markdown('<h1 class="main-header">🔐 广东中烟事务员绩效系统</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("请选择登录方式")
            
            role = st.radio("身份", ["事务员", "管理员", "地市经理"], horizontal=True)
            
            if role in ["事务员", "地市经理"]:
                user_name = st.selectbox("请选择您的姓名", 
                                        st.session_state.performance_data['事务员'].tolist())
                
                # 简化登录：选择姓名后直接登录（实际使用时可以加密码）
                if st.button("登录系统", type="primary", use_container_width=True):
                    st.session_state.authenticated = True
                    st.session_state.user_role = "staff" if role == "事务员" else "manager"
                    st.session_state.user_name = user_name
                    city = st.session_state.performance_data[
                        st.session_state.performance_data['事务员'] == user_name]['地市'].values[0]
                    st.session_state.current_city = city
                    st.success(f"欢迎回来，{user_name}！")
                    st.rerun()
                    
            else:  # 管理员
                admin_pwd = st.text_input("管理员密码", type="password", 
                                         placeholder="请输入管理员密码")
                if st.button("管理员登录", type="primary", use_container_width=True):
                    if admin_pwd == "admin123":  # 默认密码，请务必修改！
                        st.session_state.authenticated = True
                        st.session_state.user_role = "admin"
                        st.session_state.user_name = "管理员"
                        st.success("管理员登录成功！")
                        st.rerun()
                    else:
                        st.error("密码错误！")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 使用说明
    with st.expander("📖 系统使用说明"):
        st.markdown("""
        ### 系统功能简介
        1. **事务员**：查看个人绩效、填报数据
        2. **地市经理**：查看本地区所有事务员数据
        3. **管理员**：管理所有数据、系统设置
        
        ### 首次使用
        - 事务员请直接选择姓名登录
        - 管理员密码：admin123（请首次登录后修改）
        - 如有问题请联系技术支持
        """)

# ========== 事务员个人页面 ==========
def staff_dashboard():
    st.markdown(f'<h2 class="main-header">👤 {st.session_state.user_name} 的绩效看板</h2>', unsafe_allow_html=True)
    
    # 获取用户数据
    user_data = st.session_state.performance_data[
        st.session_state.performance_data['事务员'] == st.session_state.user_name
    ].iloc[0]
    
    # 顶部指标卡
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("所属地市", user_data['地市'])
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("当前总分", f"{user_data['总分']:.1f}分")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("薪酬档位", f"{user_data['档位']}档")
        st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("预估月薪", f"¥{user_data['预估月薪']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # 详细得分卡片
    st.subheader("📊 详细得分分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown("### 分销得分")
            fig1 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=user_data['调剂得分'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"得分：{user_data['调剂得分']}/25"},
                gauge={'axis': {'range': [None, 25]},
                      'bar': {'color': "darkblue"},
                      'steps': [
                          {'range': [0, 5], 'color': "lightgray"},
                          {'range': [5, 10], 'color': "gray"},
                          {'range': [10, 15], 'color': "lightblue"},
                          {'range': [15, 20], 'color': "blue"},
                          {'range': [20, 25], 'color': "darkblue"}],
                      'threshold': {'line': {'color': "red", 'width': 4},
                                   'thickness': 0.75,
                                   'value': user_data['调剂得分']}}))
            fig1.update_layout(height=300)
            st.plotly_chart(fig1, use_container_width=True)
            
            st.info(f"**调剂平均：** {user_data['调剂平均']:.1f}条")
    
    with col2:
        with st.container():
            st.markdown("### 条盒回收得分")
            fig2 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=user_data['条皮得分'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"得分：{user_data['条皮得分']}/35"},
                gauge={'axis': {'range': [None, 35]},
                      'bar': {'color': "darkgreen"},
                      'steps': [
                          {'range': [0, 5], 'color': "lightgray"},
                          {'range': [5, 10], 'color': "gray"},
                          {'range': [10, 15], 'color': "lightgreen"},
                          {'range': [15, 20], 'color': "green"},
                          {'range': [20, 25], 'color': "darkgreen"},
                          {'range': [25, 30], 'color': "green"},
                          {'range': [30, 35], 'color': "darkgreen"}],
                      'threshold': {'line': {'color': "red", 'width': 4},
                                   'thickness': 0.75,
                                   'value': user_data['条皮得分']}}))
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)
            
            st.info(f"**条皮平均：** {user_data['条皮平均']:.1f}条")
    
    # 其他得分
    col3, col4 = st.columns(2)
    with col3:
        st.metric("客户维护得分", f"{user_data['客户维护']}/20")
    with col4:
        st.metric("综合评分", f"{user_data['综合']}/20")
    
    st.divider()
    
    # 原始数据查看
    with st.expander("📋 查看原始数据"):
        st.write("### 您的原始数据")
        display_cols = ['行号', '地市', '事务员', '调剂1-3月', '调剂4-6月', 
                       '条皮1-3月', '空小盒兑换', '条皮4-6月', '客户维护', '综合']
        st.dataframe(user_data[display_cols], use_container_width=True)

# ========== 地市经理页面 ==========
def manager_dashboard():
    st.markdown(f'<h2 class="main-header">📈 {st.session_state.current_city} 地区管理</h2>', unsafe_allow_html=True)
    
    # 获取本地区所有数据
    city_data = st.session_state.performance_data[
        st.session_state.performance_data['地市'] == st.session_state.current_city
    ]
    
    # 地区统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("地区人数", len(city_data))
    with col2:
        st.metric("平均总分", f"{city_data['总分'].mean():.1f}")
    with col3:
        st.metric("最高分", f"{city_data['总分'].max():.1f}")
    
    st.divider()
    
    # 地区排名表
    st.subheader("🏆 地区排名")
    display_data = city_data[['事务员', '调剂得分', '条皮得分', '客户维护', '综合', '总分', '档位']]
    display_data = display_data.sort_values('总分', ascending=False)
    display_data.index = range(1, len(display_data) + 1)
    
    st.dataframe(display_data, use_container_width=True)
    
    # 地区分布图
    st.divider()
    st.subheader("📊 地区得分分布")
    
    fig = px.bar(display_data, x='事务员', y='总分', 
                 title='各地区事务员总分对比',
                 color='总分',
                 color_continuous_scale='viridis')
    st.plotly_chart(fig, use_container_width=True)

# ========== 数据填报页面 ==========
def data_entry_page():
    st.markdown('<h2 class="main-header">📝 数据填报</h2>', unsafe_allow_html=True)
    
    with st.form("data_entry_form"):
        st.subheader("请填写本季度数据")
        
        col1, col2 = st.columns(2)
        with col1:
            调剂1_3月 = st.number_input("调剂1-3月数量", min_value=0, step=1, value=0)
            调剂4_6月 = st.number_input("调剂4-6月数量", min_value=0, step=1, value=0)
            空小盒兑换 = st.text_input("空小盒兑换（格式如：280/10）", value="")
        
        with col2:
            条皮1_3月 = st.number_input("条皮1-3月数量", min_value=0, step=1, value=0)
            条皮4_6月 = st.number_input("条皮4-6月数量", min_value=0, step=1, value=0)
            客户维护得分 = st.selectbox("客户维护得分", [10, 15, 20], index=0)
        
        综合评分 = st.slider("综合评分（1-20分）", 1, 20, 10)
        
        submitted = st.form_submit_button("计算得分", type="primary")
        
        if submitted:
            # 计算得分
            调剂平均 = (调剂1_3月 + 调剂4_6月) / 2
            调剂得分 = calculate_distribution_score(调剂平均)
            
            # 处理空小盒兑换
            tiaopi_4_6_adj = 条皮4_6月
            if 空小盒兑换 and '/' in 空小盒兑换:
                try:
                    num, denom = map(int, 空小盒兑换.split('/'))
                    tiaopi_4_6_adj += num / denom
                except:
                    st.warning("空小盒兑换格式错误，已忽略")
            
            条皮平均 = (条皮1_3月 + tiaopi_4_6_adj) / 2
            条皮得分 = calculate_recycling_score(条皮平均)
            
            总分 = 调剂得分 + 条皮得分 + 客户维护得分 + 综合评分
            
            # 显示结果
            st.success("✅ 得分计算完成！")
            
            results_df = pd.DataFrame({
                '项目': ['调剂平均', '调剂得分', '条皮平均', '条皮得分', '客户维护', '综合评分', '总分'],
                '数值': [调剂平均, 调剂得分, 条皮平均, 条皮得分, 客户维护得分, 综合评分, 总分]
            })
            
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(results_df, use_container_width=True, hide_index=True)
            
            with col2:
                # 计算薪酬档位
                if 总分 >= 91:
                    grade, salary = 1, 6000
                elif 总分 >= 81:
                    grade, salary = 2, 5500
                elif 总分 >= 71:
                    grade, salary = 3, 5000
                elif 总分 >= 61:
                    grade, salary = 4, 4700
                elif 总分 >= 51:
                    grade, salary = 5, 4400
                elif 总分 >= 46:
                    grade, salary = 6, 4100
                elif 总分 >= 41:
                    grade, salary = 7, 3900
                elif 总分 >= 36:
                    grade, salary = 8, 3700
                elif 总分 >= 31:
                    grade, salary = 9, 3500
                else:
                    grade, salary = 10, 3300
                
                st.info(f"""
                ### 薪酬预估
                - **总分：** {总分}分
                - **档位：** {grade}档
                - **预估月薪：** ¥{salary}
                """)
            
            # 保存数据按钮
            st.divider()
            if st.button("📤 提交数据到系统", type="primary", use_container_width=True):
                st.success("数据已提交！管理员审核后会更新到系统中")
                st.balloons()

# ========== 管理员后台 ==========
def admin_dashboard():
    st.markdown('<h2 class="main-header">👑 管理员控制台</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 数据总览", "📈 统计分析", "📤 数据管理", "⚙️ 系统设置"])
    
    with tab1:
        st.subheader("全员数据总览")
        
        # 搜索和筛选
        col1, col2, col3 = st.columns(3)
        with col1:
            search_name = st.text_input("搜索事务员")
        with col2:
            filter_city = st.selectbox("筛选地市", ["全部"] + st.session_state.performance_data['地市'].unique().tolist())
        with col3:
            filter_grade = st.selectbox("筛选档位", ["全部"] + list(range(1, 11)))
        
        # 筛选数据
        display_df = st.session_state.performance_data.copy()
        if search_name:
            display_df = display_df[display_df['事务员'].str.contains(search_name)]
        if filter_city != "全部":
            display_df = display_df[display_df['地市'] == filter_city]
        if filter_grade != "全部":
            display_df = display_df[display_df['档位'] == filter_grade]
        
        # 显示数据
        st.dataframe(display_df, use_container_width=True)
        
        # 导出数据
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 导出CSV",
            data=csv,
            file_name=f"事务员绩效数据_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with tab2:
        st.subheader("统计分析")
        
        col1, col2 = st.columns(2)
        with col1:
            # 总分分布图
            fig1 = px.histogram(st.session_state.performance_data, x='总分', 
                               title='总分分布图', nbins=20)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # 档位分布图
            fig2 = px.pie(st.session_state.performance_data, names='档位', 
                         title='薪酬档位分布')
            st.plotly_chart(fig2, use_container_width=True)
        
        # 地市对比
        st.subheader("各地市平均分对比")
        city_avg = st.session_state.performance_data.groupby('地市')['总分'].mean().reset_index()
        fig3 = px.bar(city_avg, x='地市', y='总分', title='各地市平均分')
        st.plotly_chart(fig3, use_container_width=True)
    
    with tab3:
        st.subheader("数据管理")
        
        # 手动添加数据
        with st.expander("➕ 手动添加事务员"):
            with st.form("add_staff_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_city = st.text_input("地市")
                    new_name = st.text_input("事务员姓名")
                    new_tiaoji1 = st.number_input("调剂1-3月", min_value=0)
                    new_tiaoji2 = st.number_input("调剂4-6月", min_value=0)
                with col2:
                    new_tiaopi1 = st.number_input("条皮1-3月", min_value=0)
                    new_konghe = st.text_input("空小盒兑换")
                    new_tiaopi2 = st.number_input("条皮4-6月", min_value=0)
                    new_customer = st.selectbox("客户维护", [10, 15, 20])
                    new_comprehensive = st.slider("综合评分", 1, 20, 10)
                
                if st.form_submit_button("添加事务员"):
                    st.success("事务员添加成功！")
        
        # 批量导入
        st.subheader("批量导入Excel数据")
        uploaded_file = st.file_uploader("选择Excel文件", type=['xlsx', 'xls'])
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("预览上传的数据：")
                st.dataframe(df.head())
                
                if st.button("导入数据到系统", type="primary"):
                    # 这里可以添加数据合并逻辑
                    st.success("数据导入成功！")
                    st.rerun()
            except Exception as e:
                st.error(f"读取文件出错：{str(e)}")
    
    with tab4:
        st.subheader("系统设置")
        
        # 修改管理员密码
        st.write("### 修改管理员密码")
        current_pwd = st.text_input("当前密码", type="password")
        new_pwd = st.text_input("新密码", type="password")
        confirm_pwd = st.text_input("确认新密码", type="password")
        
        if st.button("修改密码", type="primary"):
            if current_pwd == "admin123":
                if new_pwd == confirm_pwd:
                    st.success("密码修改成功！")
                    # 实际应该保存到配置文件中
                else:
                    st.error("两次输入的新密码不一致")
            else:
                st.error("当前密码错误")
        
        # 评分规则查看
        st.divider()
        st.write("### 当前评分规则")
        
        with st.expander("查看分销得分规则"):
            st.write("""
            - S级：1000条以上；得25分
            - A级：601-1000条；得20分
            - B级：301-600条；得15分
            - C级：151-300条；得10分
            - D级：61-150条；得5分
            - E级：60条以下；不得分
            """)
        
        with st.expander("查看条盒回收得分规则"):
            st.write("""
            - S级：1000条以上；得35分
            - A级：801-1000条；得30分
            - B级：601-800条；得25分
            - C级：401-600条；得20分
            - D级：301-400条；得15分
            - E级：201-300条；得10分
            - F级：181-200条；得5分
            - G级：180条以下；不得分
            """)

# ========== 主程序 ==========
def main():
    # 检查登录状态
    if not st.session_state.authenticated:
        login_page()
        return
    
    # 顶部导航栏
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        if st.session_state.user_role == "staff":
            st.markdown(f'<h3>👤 {st.session_state.user_name} - 事务员</h3>', unsafe_allow_html=True)
        elif st.session_state.user_role == "manager":
            st.markdown(f'<h3>📊 {st.session_state.user_name} - {st.session_state.current_city}地市经理</h3>', unsafe_allow_html=True)
        else:
            st.markdown('<h3>👑 管理员控制台</h3>', unsafe_allow_html=True)
    
    with col3:
        if st.button("退出登录", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.divider()
    
    # 侧边栏菜单
    if st.session_state.user_role == "staff":
        menu = st.sidebar.radio("导航菜单", 
                               ["📈 我的绩效", "📝 数据填报", "📖 帮助说明"],
                               index=0)
        
        if menu == "📈 我的绩效":
            staff_dashboard()
        elif menu == "📝 数据填报":
            data_entry_page()
        else:
            st.write("## 帮助说明")
            st.info("""
            ### 常见问题
            1. **如何查看我的绩效？**
               - 登录后点击"我的绩效"即可查看详细得分
            
            2. **数据填报后如何生效？**
               - 填报后数据会提交给管理员审核
               - 审核通过后会更新到系统中
            
            3. **分数是如何计算的？**
               - 系统根据《办事处工作得分规范》自动计算
               - 如有疑问请联系管理员
            
            4. **忘记密码怎么办？**
               - 请联系管理员重置密码
            """)
    
    elif st.session_state.user_role == "manager":
        menu = st.sidebar.radio("导航菜单", 
                               ["📊 地区管理", "📈 数据分析", "📖 帮助说明"],
                               index=0)
        
        if menu == "📊 地区管理":
            manager_dashboard()
        elif menu == "📈 数据分析":
            st.write("数据分析功能开发中...")
        else:
            st.write("地市经理帮助说明...")
    
    else:  # 管理员
        admin_dashboard()

# 运行主程序
if __name__ == "__main__":
    main()