import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json

# 初始化数据存储
def init_data():
    if 'users_data' not in st.session_state:
        # 从EXCEL1初始化人员数据
        base_data = [
            # 这里包含EXCEL1中的所有人员信息
            {"编号": 1, "地区": "石家庄", "姓名": "庞雷", "角色": "事务员"},
            {"编号": 2, "地区": "保定", "姓名": "方亚辉", "角色": "事务员"},
            # ... 其他人员数据
        ]
        st.session_state.users_data = base_data
        
        # 初始化季度数据
        st.session_state.quarter_data = {}
        for user in base_data:
            st.session_state.quarter_data[user['姓名']] = {
                '分销数量': 0,
                '条盒回收': 0,
                '核心户数': 0,
                '办事处评分': 0,
                '月度记录': {}
            }

# 评分计算函数
def calculate_scores(distribution, recycling, core_accounts, office_score):
    # 分销得分计算
    if distribution >= 1000:
        dist_score = 25
    elif distribution >= 601:
        dist_score = 20
    elif distribution >= 301:
        dist_score = 15
    elif distribution >= 151:
        dist_score = 10
    elif distribution >= 61:
        dist_score = 5
    else:
        dist_score = 0

    # 条盒回收得分计算
    if recycling >= 1000:
        rec_score = 35
    elif recycling >= 801:
        rec_score = 30
    elif recycling >= 601:
        rec_score = 25
    elif recycling >= 401:
        rec_score = 20
    elif recycling >= 301:
        rec_score = 15
    elif recycling >= 201:
        rec_score = 10
    elif recycling >= 181:
        rec_score = 5
    else:
        rec_score = 0

    # 核心户得分计算
    if core_accounts >= 31:
        core_score = 20
    elif core_accounts >= 26:
        core_score = 15
    elif core_accounts >= 21:
        core_score = 10
    elif core_accounts >= 16:
        core_score = 5
    else:
        core_score = 0

    total_score = dist_score + rec_score + core_score + office_score
    
    # 工资档位计算
    if total_score >= 91:
        salary = 6000
        level = 1
    elif total_score >= 81:
        salary = 5500
        level = 2
    elif total_score >= 71:
        salary = 5000
        level = 3
    elif total_score >= 61:
        salary = 4700
        level = 4
    elif total_score >= 51:
        salary = 4400
        level = 5
    elif total_score >= 46:
        salary = 4100
        level = 6
    elif total_score >= 41:
        salary = 3900
        level = 7
    elif total_score >= 36:
        salary = 3700
        level = 8
    elif total_score >= 31:
        salary = 3500
        level = 9
    else:
        salary = 3300
        level = 10

    return {
        '分销得分': dist_score,
        '条盒回收得分': rec_score,
        '核心户得分': core_score,
        '办事处得分': office_score,
        '总分': total_score,
        '工资': salary,
        '档位': level
    }

# 主应用界面
def main():
    st.set_page_config(page_title="广东中烟事务员薪酬管理系统", layout="wide")
    
    # 初始化数据
    init_data()
    
    # 登录系统
    if 'logged_in' not in st.session_state:
        show_login()
    else:
        show_main_interface()

def show_login():
    st.title("广东中烟事务员薪酬管理系统")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            role = st.selectbox("角色", ["事务员", "地市经理", "管理员"])
            
            if st.form_submit_button("登录"):
                # 简化登录验证
                if username and password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.session_state.user_role = role
                    st.rerun()

def show_main_interface():
    st.sidebar.title(f"欢迎, {st.session_state.current_user}")
    st.sidebar.write(f"角色: {st.session_state.user_role}")
    
    # 导航菜单
    if st.session_state.user_role == "事务员":
        menu = ["个人看板", "数据填报", "薪酬计算器"]
    elif st.session_state.user_role == "地市经理":
        menu = ["评分管理", "团队查看"]
    else:
        menu = ["数据管理", "系统设置", "季度重置"]
    
    choice = st.sidebar.selectbox("功能菜单", menu)
    
    # 根据选择显示不同页面
    if choice == "个人看板":
        show_personal_dashboard()
    elif choice == "数据填报":
        show_data_input()
    elif choice == "薪酬计算器":
        show_calculator()
    elif choice == "评分管理":
        show_scoring_management()
    elif choice == "数据管理":
        show_admin_management()

def show_personal_dashboard():
    st.header("个人业绩看板")
    
    user_data = st.session_state.quarter_data[st.session_state.current_user]
    
    # 显示当前季度数据
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("分销数量", user_data['分销数量'])
    with col2:
        st.metric("条盒回收", user_data['条盒回收'])
    with col3:
        st.metric("核心户数", user_data['核心户数'])
    with col4:
        st.metric("办事处评分", user_data['办事处评分'])
    
    # 计算并显示得分
    scores = calculate_scores(
        user_data['分销数量'],
        user_data['条盒回收'],
        user_data['核心户数'],
        user_data['办事处评分']
    )
    
    st.subheader("当前得分情况")
    score_cols = st.columns(4)
    score_cols[0].metric("分销得分", scores['分销得分'])
    score_cols[1].metric("条盒回收得分", scores['条盒回收得分'])
    score_cols[2].metric("核心户得分", scores['核心户得分'])
    score_cols[3].metric("总分", scores['总分'])
    
    # 工资档位显示
    st.success(f"当前工资档位: {scores['档位']}级 - 工资: {scores['工资']}元")

def show_data_input():
    st.header("月度数据填报")
    
    month = st.selectbox("选择月份", ["1月", "2月", "3月", "4月", "5月", "6月", 
                                    "7月", "8月", "9月", "10月", "11月", "12月"])
    
    with st.form("data_input_form"):
        col1, col2 = st.columns(2)
        with col1:
            distribution = st.number_input("分销数量", min_value=0, step=1)
            recycling = st.number_input("条盒回收数量", min_value=0, step=1)
        with col2:
            core_accounts = st.number_input("核心户数", min_value=0, step=1)
        
        if st.form_submit_button("提交数据"):
            # 保存月度数据
            user_data = st.session_state.quarter_data[st.session_state.current_user]
            user_data['月度记录'][month] = {
                '分销': distribution,
                '回收': recycling,
                '核心户': core_accounts
            }
            
            # 更新季度数据（考虑月份折算）
            update_quarter_data()
            st.success("数据提交成功！")

def show_calculator():
    st.header("薪酬计算器")
    
    st.info("使用此计算器估算您的季度薪酬")
    
    col1, col2 = st.columns(2)
    with col1:
        distribution = st.number_input("预计分销数量", min_value=0, step=1)
        recycling = st.number_input("预计条盒回收", min_value=0, step=1)
    with col2:
        core_accounts = st.number_input("预计核心户数", min_value=0, step=1)
        office_score = st.slider("预计办事处评分", 0, 20, 10)
    
    if st.button("计算薪酬"):
        scores = calculate_scores(distribution, recycling, core_accounts, office_score)
        
        st.subheader("计算结果")
        st.write(f"**总分**: {scores['总分']}分")
        st.write(f"**工资档位**: 第{scores['档位']}级")
        st.write(f"**预计工资**: {scores['工资']}元")
        
        # 档位提醒
        if scores['档位'] >= 10:
            st.warning("当前预估档位较低，请关注业绩提升")

def show_scoring_management():
    st.header("地市经理评分管理")
    
    # 显示所辖事务员列表
    subordinates = [user for user in st.session_state.users_data 
                   if user['地区'] == '相关地区']  # 根据经理管辖地区筛选
    
    selected_user = st.selectbox("选择事务员", [user['姓名'] for user in subordinates])
    
    if selected_user:
        with st.form("scoring_form"):
            office_score = st.slider("办事处综合评分", 0, 20, 10)
            
            if st.form_submit_button("提交评分"):
                st.session_state.quarter_data[selected_user]['办事处评分'] = office_score
                st.success(f"已为{selected_user}提交评分")

def show_admin_management():
    st.header("管理员数据管理")
    
    tab1, tab2, tab3 = st.tabs(["数据查看", "数据修改", "季度重置"])
    
    with tab1:
        # 显示所有人员数据表格
        display_data = []
        for user, data in st.session_state.quarter_data.items():
            scores = calculate_scores(data['分销数量'], data['条盒回收'], 
                                   data['核心户数'], data['办事处评分'])
            display_data.append({
                '姓名': user,
                '分销': data['分销数量'],
                '回收': data['条盒回收'],
                '核心户': data['核心户数'],
                '办事处评分': data['办事处评分'],
                '总分': scores['总分'],
                '档位': scores['档位'],
                '工资': scores['工资']
            })
        
        df = pd.DataFrame(display_data)
        st.dataframe(df)
    
    with tab3:
        st.subheader("季度重置")
        st.warning("此操作将清空本季度所有数据，开始新的季度考核")
        
        if st.button("执行季度重置"):
            # 重置所有数据
            for user in st.session_state.quarter_data:
                st.session_state.quarter_data[user] = {
                    '分销数量': 0,
                    '条盒回收': 0,
                    '核心户数': 0,
                    '办事处评分': 0,
                    '月度记录': {}
                }
            st.success("季度重置完成！")

if __name__ == "__main__":
    main()
