import streamlit as st
import pandas as pd

st.title('🚚 司机每日工作/行车/空闲时间分析')

uploaded_timecard = st.file_uploader('上传员工打卡记录', type=['xlsx'])
uploaded_tripreport = st.file_uploader('上传行车报告 Trip Report', type=['xlsx'])

if uploaded_timecard and uploaded_tripreport:
    timecard_df = pd.read_excel(uploaded_timecard)
    trip_df = pd.read_excel(uploaded_tripreport)

    timecard_df = timecard_df[['Employee', 'Time In', 'Time Out']].dropna()
    trip_df['Driver'] = trip_df['Name'].str.split('@').str[0].str.lower().str.strip()

    # 名称映射
    name_mapping = {
        'angel r': 'angel.r', 'daniel': 'daniel.wang', 'daury': 'daury.fabian',
        'david': 'david.chen', 'jarlin': 'jarlin.reyes', 'jorjan': 'jordan.hernandez',
        'jose a': 'jose.alberto', 'kevin d': 'kevin.lei', 'leonardo': 'leonardo.perez',
        'marco': 'marco.brito', 'wei chen': 'chen.wei', 'wir': 'wir.wirawan',
        'qi': 'kejian.qi', 'quan': 'weiquan.luo', 'rommel': 'rommel.jaime'
    }

    timecard_df['Driver'] = timecard_df['Employee'].str.lower().str.strip().replace(name_mapping)

    # 计算时长（修正）
    timecard_df['Clock In'] = pd.to_datetime(timecard_df['Time In'], format='%H:%M:%S', errors='coerce')
    timecard_df['Clock Out'] = pd.to_datetime(timecard_df['Time Out'], format='%H:%M:%S', errors='coerce')
    timecard_df['Working Hours'] = (timecard_df['Clock Out'] - timecard_df['Clock In']).dt.total_seconds() / 3600

    trip_df['Drive Time'] = pd.to_timedelta(trip_df['Driving Duration'], errors='coerce').dt.total_seconds() / 3600

    merged = pd.merge(timecard_df, trip_df[['Driver', 'Drive Time']], on='Driver', how='left')
    merged['Idle Time'] = merged['Working Hours'] - merged['Drive Time']

    st.dataframe(merged[['Driver', 'Clock In', 'Clock Out', 'Working Hours', 'Drive Time', 'Idle Time']])

    # 导出结果
    csv = merged.to_csv(index=False)
    st.download_button('下载分析结果 CSV', data=csv, file_name='driver_analysis.csv')
