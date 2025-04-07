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

        trip_df['Driver'] = trip_df['Name'].str.split('@').str[0].str.lower().str.strip()
        trip_df = trip_df[trip_df['Driver'].isin(timecard_df['Driver'])]

        def extract_duration(duration):
            if pd.isnull(duration):
                return pd.NaT
            match = re.search(r'(\d+):(\d+)', str(duration))
            if match:
                h, m = int(match.group(1)), int(match.group(2))
                return pd.to_timedelta(f"{h}:{m}:00")
            return pd.NaT

        trip_df['Drive Time'] = trip_df['Driving Duration'].apply(extract_duration)
        trip_df = trip_df.dropna(subset=['Drive Time'])
        trip_df = trip_df.drop_duplicates(subset='Driver')
        trip_df['Drive Time HHMM'] = trip_df['Drive Time'].apply(lambda x: f"{int(x.total_seconds() // 3600)}:{int((x.total_seconds() % 3600) // 60):02d}")

        merged = pd.merge(timecard_df, trip_df[['Driver', 'Drive Time', 'Drive Time HHMM']], on='Driver', how='left')
        merged['Idle Time Float'] = merged['Working Hours Float'] - merged['Drive Time'].dt.total_seconds() / 3600
        merged['Idle Time'] = merged['Idle Time Float'].apply(to_hhmm)

        output_df = merged[['Driver', 'Clock In', 'Clock Out', 'Working Hours', 'Drive Time HHMM', 'Idle Time']].copy()
        output_df.columns = ['Driver', 'Clock In', 'Clock Out', 'Working Hours', 'Drive Time', 'Idle Time']

        today_str = datetime.today().strftime('%Y-%m-%d')
        output_path = os.path.join(data_dir, f"{today_str}_driver_analysis.csv")
        if not os.path.exists(output_path):
            output_df.to_csv(output_path, index=False)

        st.success(f"分析结果已保存为：{output_path}")
        st.dataframe(output_df)
        csv = output_df.to_csv(index=False)
        st.download_button('下载分析结果 CSV', data=csv, file_name='driver_analysis.csv')

# 图表按钮（不依赖上传文件）
st.markdown("---")
st.header("📊 查看历史趋势图")
if st.button("展示司机时间趋势图"):
    all_files = [f for f in os.listdir(data_dir) if f.endswith("_driver_analysis.csv")]
    dfs = []
    for f in all_files:
        df = pd.read_csv(os.path.join(data_dir, f))
        df['Date'] = f.split('_')[0]
        dfs.append(df)

    if dfs:
        history_df = pd.concat(dfs)
        for metric in ['Working Hours', 'Drive Time', 'Idle Time']:
            fig, ax = plt.subplots(figsize=(10, 5))
            for driver, group in history_df.groupby("Driver"):
                group_sorted = group.sort_values('Date')
                y = group_sorted[metric].apply(lambda x: int(x.split(":")[0]) + int(x.split(":")[1])/60 if pd.notnull(x) else None)
                ax.plot(group_sorted['Date'], y, label=driver)
            ax.set_title(f"各司机每日 {metric} 趋势")
            ax.set_ylabel(f"{metric} (小时)")
            ax.set_xlabel("日期")
            ax.legend()
            st.pyplot(fig)
    else:
        st.warning("暂无历史记录可供分析。")
