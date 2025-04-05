import streamlit as st
import pandas as pd
import numpy as np

st.title('🚚 司机每日工作/行车/空闲时间分析')

uploaded_timecard = st.file_uploader('上传员工打卡记录', type=['xlsx'])
uploaded_tripreport = st.file_uploader('上传行车报告 Trip Report', type=['xlsx'])

def to_hhmm(hours_float):
    if pd.isnull(hours_float):
        return ""
    hours = int(hours_float)
    minutes = int(round((hours_float - hours) * 60))
    return f"{hours}:{minutes:02d}"

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

    # 转换时间并保留完整打卡记录
    timecard_df['Clock In'] = pd.to_datetime(timecard_df['Time In'], format='%H:%M:%S', errors='coerce')
    timecard_df['Clock Out'] = pd.to_datetime(timecard_df['Time Out'], format='%H:%M:%S', errors='coerce')
    valid_timecard_df = timecard_df.dropna(subset=['Clock In', 'Clock Out'])

    # 按 Driver 和 Clock In 排序后，保留每位司机第一条完整记录
    valid_timecard_df = valid_timecard_df.sort_values(by=['Driver', 'Clock In'])
    valid_timecard_df = valid_timecard_df.drop_duplicates(subset='Driver', keep='first')

    # 计算工时
    valid_timecard_df['Working Hours Float'] = (valid_timecard_df['Clock Out'] - valid_timecard_df['Clock In']).dt.total_seconds() / 3600
    valid_timecard_df['Working Hours'] = valid_timecard_df['Working Hours Float'].apply(to_hhmm)

    # 处理 Drive Time（转为 HH:MM）
    trip_df['Drive Time'] = pd.to_timedelta(trip_df['Driving Duration'], errors='coerce')
    trip_df = trip_df.dropna(subset=['Drive Time'])
    trip_df = trip_df.drop_duplicates(subset='Driver')
    trip_df['Drive Time HHMM'] = trip_df['Drive Time'].apply(lambda x: f"{int(x.total_seconds() // 3600)}:{int((x.total_seconds() % 3600) // 60):02d}")

    # 合并数据
    merged = pd.merge(valid_timecard_df, trip_df[['Driver', 'Drive Time', 'Drive Time HHMM']], on='Driver', how='left')
    merged['Idle Time Float'] = merged['Working Hours Float'] - merged['Drive Time'].dt.total_seconds() / 3600
    merged['Idle Time'] = merged['Idle Time Float'].apply(to_hhmm)

    # 清理展示字段
    merged['Clock In'] = merged['Clock In'].dt.strftime('%H:%M:%S')
    merged['Clock Out'] = merged['Clock Out'].dt.strftime('%H:%M:%S')

    st.dataframe(merged[['Driver', 'Clock In', 'Clock Out', 'Working Hours', 'Drive Time HHMM', 'Idle Time']])

    # 导出结果
    output_df = merged[['Driver', 'Clock In', 'Clock Out', 'Working Hours', 'Drive Time HHMM', 'Idle Time']].copy()
    output_df.columns = ['Driver', 'Clock In', 'Clock Out', 'Working Hours', 'Drive Time', 'Idle Time']
    csv = output_df.to_csv(index=False)
    st.download_button('下载分析结果 CSV', data=csv, file_name='driver_analysis.csv')
