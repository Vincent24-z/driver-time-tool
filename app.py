import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import matplotlib.pyplot as plt

st.title('🚚 司机每日工作/行车/空闲时间分析')

uploaded_timecard = st.file_uploader('上传员工打卡记录', type=['xlsx'])
uploaded_tripreport = st.file_uploader('上传行车报告 Trip Report', type=['xlsx'])

# 存储数据的文件夹路径
data_dir = "driver_history"
os.makedirs(data_dir, exist_ok=True)

def to_hhmm(hours_float):
    if pd.isnull(hours_float):
        return ""
    hours = int(hours_float)
    minutes = int(round((hours_float - hours) * 60))
    return f"{hours}:{minutes:02d}"

if uploaded_timecard and uploaded_tripreport:
    if st.button("📊 分析数据"):
        timecard_df = pd.read_excel(uploaded_timecard)
        trip_df = pd.read_excel(uploaded_tripreport)

        timecard_df = timecard_df[['Employee', 'Time In', 'Time Out']].dropna(subset=['Time In', 'Time Out'])
        timecard_df['Driver'] = timecard_df['Employee'].str.lower().str.strip()

        name_mapping = {
            'angel r': 'angel.r', 'daniel': 'daniel.wang', 'daury': 'daury.fabian',
            'david': 'david.chen', 'jarlin': 'jarlin.reyes', 'jorjan': 'jordan.hernandez',
            'jose a': 'jose.alberto', 'kevin d': 'kevin.lei', 'leonardo': 'leonardo.perez',
            'marco': 'marco.brito', 'wei chen': 'chen.wei', 'wir': 'wir.wirawan',
            'qi': 'kejian.qi', 'quan': 'weiquan.luo', 'rommel': 'rommel.jaime'
        }
        timecard_df['Driver'] = timecard_df['Driver'].replace(name_mapping)

        timecard_df['Clock In'] = pd.to_datetime(timecard_df['Time In'], format='%H:%M:%S', errors='coerce')
        timecard_df['Clock Out'] = pd.to_datetime(timecard_df['Time Out'], format='%H:%M:%S', errors='coerce')
        timecard_df = timecard_df.dropna(subset=['Clock In', 'Clock Out'])
        timecard_df = timecard_df.drop_duplicates(subset='Driver', keep='first')

        timecard_df['Working Hours Float'] = (timecard_df['Clock Out'] - timecard_df['Clock In']).dt.total_seconds() / 3600
        timecard_df['Working Hours'] = timecard_df['Working Hours Float'].apply(to_hhmm)
        timecard_df['Clock In'] = timecard_df['Clock In'].dt.strftime('%H:%M:%S')
        timecard_df['Clock Out'] = timecard_df['Clock Out'].dt.strftime('%H:%M:%S')

        # 自动匹配含名称的列
        potential_cols = [col for col in trip_df.columns if any(key in col.lower() for key in ['name', 'email', 'driver'])]
        if not potential_cols:
            st.error("❌ 无法识别司机名称列（应包含关键词 'name'、'email' 或 'driver'），请检查行车报告文件格式。")
            st.stop()
        email_col = potential_cols[0]
        trip_df['Driver'] = trip_df[email_col].astype(str).str.split('@').str[0].str.lower().str.strip()
        trip_df = trip_df[trip_df['Driver'].isin(timecard_df['Driver'])]

        duration_cols = [col for col in trip_df.columns if 'duration' in col.lower()]
        if not duration_cols:
            st.error("❌ 无法识别行车时间列（应包含关键词 'duration'），请检查行车报告文件格式。")
            st.stop()
        duration_col = duration_cols[0]

        def extract_duration(duration):
            if pd.isnull(duration):
                return pd.NaT
            match = re.search(r'(\d+):(\d+)', str(duration))
            if match:
                h, m = int(match.group(1)), int(match.group(2))
                return pd.to_timedelta(f"{h}:{m}:00")
            return pd.NaT

        trip_df['Drive Time'] = trip_df[duration_col].apply(extract_duration)
        trip_df = trip_df.dropna(subset=['Drive Time'])
        trip_df['Drive Time HHMM'] = trip_df['Drive Time'].apply(lambda x: f"{int(x.total_seconds() // 3600)}:{int((x.total_seconds() % 3600) // 60):02d}")

        # 计算每位司机的总 Driving Duration
        total_drive = trip_df.groupby('Driver')['Drive Time'].sum().reset_index()

        # 提取 Actual Out 时间（Home zone 后一行的 Start Date）
        actual_out_list = []
        for driver in trip_df['Driver'].unique():
            df_driver = trip_df[trip_df['Driver'] == driver].reset_index(drop=True)
            idx_list = df_driver[df_driver['Stop Zone Types'].str.lower().str.contains('home', na=False)].index.tolist()
            if idx_list:
                idx = idx_list[0] + 1
                if idx < len(df_driver):
                    actual_out = df_driver.loc[idx, 'Start Date']
                    actual_out_list.append({'Driver': driver, 'Actual Out': actual_out})
        actual_out_df = pd.DataFrame(actual_out_list)

        trip_df = trip_df.drop_duplicates(subset='Driver')
        trip_df = pd.merge(trip_df, total_drive, on='Driver', suffixes=('', '_Total'))
        trip_df = pd.merge(trip_df, actual_out_df, on='Driver', how='left')

        merged = pd.merge(timecard_df, trip_df[['Driver', 'Drive Time_Total', 'Drive Time HHMM', 'Actual Out']], on='Driver', how='left')
        merged['Idle Time Float'] = merged['Working Hours Float'] - merged['Drive Time_Total'].dt.total_seconds() / 3600
        merged['Idle Time'] = merged['Idle Time Float'].apply(to_hhmm)

        output_df = merged[['Driver', 'Clock In', 'Clock Out', 'Working Hours', 'Drive Time HHMM', 'Idle Time', 'Actual Out']].copy()
        output_df.columns = ['Driver', 'Clock In', 'Clock Out', 'Working Hours', 'Drive Time', 'Idle Time', 'Actual Out']

        today_str = datetime.today().strftime('%Y-%m-%d')
        output_path = os.path.join(data_dir, f"{today_str}_driver_analysis.csv")
        if not os.path.exists(output_path):
            output_df.to_csv(output_path, index=False)

        st.success(f"分析结果已保存为：{output_path}")
        st.dataframe(output_df)
        csv = output_df.to_csv(index=False)
        st.download_button('下载分析结果 CSV', data=csv, file_name='driver_analysis.csv')
