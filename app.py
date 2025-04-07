import streamlit as st
import pandas as pd

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

    # 清洗打卡数据
    timecard_df = timecard_df[['Employee', 'Time In', 'Time Out']].dropna()
    timecard_df['Driver'] = timecard_df['Employee'].str.lower().str.strip()

    # 名称映射
    name_mapping = {
        'angel r': 'angel.r', 'daniel': 'daniel.wang', 'daury': 'daury.fabian',
        'david': 'david.chen', 'jarlin': 'jarlin.reyes', 'jorjan': 'jordan.hernandez',
        'jose a': 'jose.alberto', 'kevin d': 'kevin.lei', 'leonardo': 'leonardo.perez',
        'marco': 'marco.brito', 'wei chen': 'chen.wei', 'wir': 'wir.wirawan',
        'qi': 'kejian.qi', 'quan': 'weiquan.luo', 'rommel': 'rommel.jaime'
    }
    timecard_df['Driver'] = timecard_df['Driver'].replace(name_mapping)

    # 去除无效时间
    timecard_df['Clock In'] = pd.to_datetime(timecard_df['Time In'], errors='coerce')
    timecard_df['Clock Out'] = pd.to_datetime(timecard_df['Time Out'], errors='coerce')
    timecard_df = timecard_df.dropna(subset=['Clock In', 'Clock Out'])

    # 只保留每位司机一条记录（已预处理）

    # 计算 Working Hours
    timecard_df['Working Hours Float'] = (timecard_df['Clock Out'] - timecard_df['Clock In']).dt.total_seconds() / 3600
    timecard_df['Working Hours'] = timecard_df['Working Hours Float'].apply(to_hhmm)

    # 格式化时间为 HH:MM:SS
    timecard_df['Clock In'] = timecard_df['Clock In'].dt.strftime('%H:%M:%S')
    timecard_df['Clock Out'] = timecard_df['Clock Out'].dt.strftime('%H:%M:%S')

    # 处理行车报告
    trip_df['Driver'] = trip_df['Name'].str.split('@').str[0].str.lower().str.strip()
    trip_df = trip_df[trip_df['Driver'].isin(timecard_df['Driver'])]  # 只保留打卡表中有的司机
    trip_df['Drive Time'] = pd.to_timedelta(trip_df['Driving Duration'], errors='coerce')
    trip_df = trip_df.dropna(subset=['Drive Time'])
    trip_df = trip_df.drop_duplicates(subset='Driver')
    trip_df['Drive Time HHMM'] = trip_df['Drive Time'].apply(lambda x: f"{int(x.total_seconds() // 3600)}:{int((x.total_seconds() % 3600) // 60):02d}")

    # 合并数据
    merged = pd.merge(timecard_df, trip_df[['Driver', 'Drive Time', 'Drive Time HHMM']], on='Driver', how='left')
    merged['Idle Time Float'] = merged['Working Hours Float'] - merged['Drive Time'].dt.total_seconds() / 3600
    merged['Idle Time'] = merged['Idle Time Float'].apply(to_hhmm)

    # 最终输出列
    output_df = merged[['Driver', 'Clock In', 'Clock Out', 'Working Hours', 'Drive Time HHMM', 'Idle Time']].copy()
    output_df.columns = ['Driver', 'Clock In', 'Clock Out', 'Working Hours', 'Drive Time', 'Idle Time']

    st.dataframe(output_df)
    csv = output_df.to_csv(index=False)
    st.download_button('下载分析结果 CSV', data=csv, file_name='driver_analysis.csv')
