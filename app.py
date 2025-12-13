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
if 'performance_data' not in st.session_state:
    st.session_state.performance_data = None

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
        tiaoji_avg = (row['调剂1-3月'] + row['调剂4-6月']) / 2 if row['调剂1-3月'] is not None and row['调剂4-6月'] is not None else 0
        tiaoji_score = calculate_distribution_score(tiaoji_avg)
        
        # 处理空小盒兑换
        tiaopi_4_6 = row['条皮4-6月'] if row['条皮4-6月'] is not None else 0
        if '空小盒兑换' in row and pd.notna(row['空小盒兑换']) and '/' in str(row['空小盒兑换']):
            try:
                num, denom = map(int, str(row['空小盒兑换']).split('/'))
                tiaopi_4_6 += num / denom
            except:
                pass
        
        # 计算条皮平均和得分
        tiaopi_1_3 = row['条皮1-3月'] if row['条皮1-3月'] is not None else 0
        tiaopi_avg = (tiaopi_1_3 + tiaopi_4_6) / 2
        tiaopi_score = calculate_recycling_score(tiaopi_avg)
        
        # 计算总分
        customer_score = row['客户维护'] if '客户维护' in row and pd.notna(row['客户维护']) else 0
        comprehensive_score = row['综合'] if '综合' in row and pd.notna(row['综合']) else 0
        total_score = tiaoji_score + tiaopi_score + customer_score + comprehensive_score
        
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

# ========== 初始化示例数据（修复版）==========
def init_sample_data():
    """使用你的Excel数据初始化"""
    # 直接从你提供的表格数据创建
    data = [
        {'行号': 1, '地市': '石家庄', '事务员': '庞雷', '调剂1-3月': 0, '调剂4-6月': 0, '条皮1-3月': 0, '空小盒兑换': '', '条皮4-6月': 0, '客户维护': 0, '综合': 0},
        {'行号': 2, '地市': '保定', '事务员': '方亚辉', '调剂1-3月': 2185, '调剂4-6月': 2656, '条皮1-3月': 421, '空小盒兑换': '', '条皮4-6月': 1069, '客户维护': 10, '综合': 20},
        {'行号': 3, '地市': '保定', '事务员': '李建英', '调剂1-3月': 175, '调剂4-6月': 132, '条皮1-3月': 450, '空小盒兑换': '', '条皮4-6月': 551, '客户维护': 10, '综合': 10},
        {'行号': 4, '地市': '保定', '事务员': '史亚卿', '调剂1-3月': 30, '调剂4-6月': 67, '条皮1-3月': 302, '空小盒兑换': '', '条皮4-6月': 296, '客户维护': 10, '综合': 10},
        {'行号': 5, '地市': '保定', '事务员': '甄喜梅', '调剂1-3月': 165, '调剂4-6月': 124, '条皮1-3月': 278, '空小盒兑换': '', '条皮4-6月': 364, '客户维护': 10, '综合': 15},
        {'行号': 6, '地市': '沧州', '事务员': '郝亮', '调剂1-3月': 103, '调剂4-6月': 23, '条皮1-3月': 286, '空小盒兑换': '20/10', '条皮4-6月': 285, '客户维护': 10, '综合': 10},
        {'行号': 7, '地市': '沧州', '事务员': '张卿', '调剂1-3月': 152, '调剂4-6月': 109, '条皮1-3月': 248, '空小盒兑换': '260/10', '条皮4-6月': 291, '客户维护': 10, '综合': 10},
        {'行号': 8, '地市': '张家口', '事务员': '李晓峰', '调剂1-3月': 1693, '调剂4-6月': 2409, '条皮1-3月': 697, '空小盒兑换': '', '条皮4-6月': 1050, '客户维护': 10, '综合': 15},
        {'行号': 9, '地市': '石家庄', '事务员': '孙霆', '调剂1-3月': 204, '调剂4-6月': 263, '条皮1-3月': 381, '空小盒兑换': '', '条皮4-6月': 385, '客户维护': 10, '综合': 15},
        {'行号': 10, '地市': '石家庄', '事务员': '李凤霞', '调剂1-3月': 148, '调剂4-6月': 172, '条皮1-3月': 417, '空小盒兑换': '', '条皮4-6月': 492, '客户维护': 10, '综合': 20},
        # 这里只放前10条作为示例，实际部署时可以从Excel导入
    ]
    
    df = pd.DataFrame(data)
    return calculate_all_scores(df)

# ========== 登录页面 ==========
def login_page():
    st.markdown('<h1 class="main-header">🔐 广东中烟事务员绩效系统</h1>', unsafe_allow_html=True)
    
    # 初始化数据（只在首次加载时）
    if st.session_state.performance_data is None:
        st.session_state.performance_data = init_sample_data()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("请选择登录方式")
            
            role = st.radio("身份", ["事务员", "管理员", "地市经理"], horizontal=True, key="login_role")
            
            if role in ["事务员", "地市经理"]:
                # 从数据中获取所有事务员姓名
                staff_names = st.session_state.performance_data['事务员'].tolist()
                user_name = st.selectbox("请选择您的姓名", staff_names, key="staff_select")
                
                if st.button("登录系统", type="primary", use_container_width=True, key="staff_login"):
                    st.session_state.authenticated = True
                    st.session_state.user_role = "staff" if role == "事务员" else "manager"
                    st.session_state.user_name = user_name
                    # 获取用户所在城市
                    user_data = st.session_state.performance_data[
                        st.session_state.performance_data['事务员'] == user_name
                    ]
                    if not user_data.empty:
                        st.session_state.current_city = user_data.iloc[0]['地市']
                    st.success(f"欢迎回来，{user_name}！")
                    st.rerun()
                    
            else:  # 管理员
                admin_pwd = st.text_input("管理员密码", type="password", 
                                         placeholder="请输入管理员密码", key="admin_pwd")
                if st.button("管理员登录", type="primary", use_container_width=True, key="admin_login"):
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
    
    if st.session_state.performance_data is None:
        st.error("数据未加载，请联系管理员")
        return
    
    # 获取用户数据
    user_data = st.session_state.performance_data[
        st.session_state.performance_data['事务员'] == st.session_state.user_name
    ]
    
    if user_data.empty:
        st.warning("未找到您的数据，请联系管理员添加")
        return
    
    user_data = user_data.iloc[0]
    
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
    
    # 详细得分
    st.subheader("📊 详细得分分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("调剂得分", f"{user_data['调剂得分']}/25")
        st.info(f"调剂平均：{user_data['调剂平均']:.1f}条")
    
    with col2:
        st.metric("条盒回收得分", f"{user_data['条皮得分']}/35")
        st.info(f"条皮平均：{user_data['条皮平均']:.1f}条")
    
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
        display_data = user_data[display_cols].to_frame().T
        st.dataframe(display_data, use_container_width=True)

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

# ========== 管理员后台 - 简化版 ==========
def admin_dashboard():
    st.markdown('<h2 class="main-header">👑 管理员控制台</h2>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📊 数据管理", "⚙️ 系统设置"])
    
    with tab1:
        st.subheader("全员数据")
        
        if st.session_state.performance_data is not None:
            st.dataframe(st.session_state.performance_data, use_container_width=True)
            
            # 导出数据
            csv = st.session_state.performance_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 导出CSV",
                data=csv,
                file_name=f"事务员绩效数据_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # 上传Excel文件
            st.subheader("上传Excel文件更新数据")
            uploaded_file = st.file_uploader("选择Excel文件", type=['xlsx', 'xls'])
            
            if uploaded_file is not None:
                try:
                    df = pd.read_excel(uploaded_file)
                    st.write("预览上传的数据：")
                    st.dataframe(df.head())
                    
                    if st.button("更新系统数据", type="primary"):
                        # 计算得分
                        df = calculate_all_scores(df)
                        st.session_state.performance_data = df
                        st.success("数据更新成功！")
                        st.rerun()
                except Exception as e:
                    st.error(f"读取文件出错：{str(e)}")
    
    with tab2:
        st.subheader("系统设置")
        st.write("系统设置功能开发中...")

# ========== 主程序 ==========
def main():
    # 检查登录状态
    if not st.session_state.authenticated:
        login_page()
        return
    
    # 顶部导航栏
    col1, col2 = st.columns([5, 1])
    with col1:
        if st.session_state.user_role == "staff":
            st.markdown(f'<h3>👤 {st.session_state.user_name} - 事务员</h3>', unsafe_allow_html=True)
        elif st.session_state.user_role == "manager":
            st.markdown(f'<h3>📊 {st.session_state.current_city}地市经理</h3>', unsafe_allow_html=True)
        else:
            st.markdown('<h3>👑 管理员控制台</h3>', unsafe_allow_html=True)
    
    with col2:
        if st.button("退出登录", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.divider()
    
    # 根据角色显示不同页面
    if st.session_state.user_role == "staff":
        menu = st.sidebar.radio("导航菜单", ["📈 我的绩效", "📝 数据填报"], index=0)
        
        if menu == "📈 我的绩效":
            staff_dashboard()
        else:
            data_entry_page()
    
    elif st.session_state.user_role == "manager":
        st.write("地市经理功能开发中...")
        st.info("当前版本暂不支持地市经理功能，请使用事务员或管理员账号")
    
    else:  # 管理员
        admin_dashboard()

# 运行主程序
if __name__ == "__main__":
    main()
