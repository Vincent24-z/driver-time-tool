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

    # 计算工作时长
    timecard_df['Clock In'] = pd.to_datetime(timecard_df['Time In'], format='%H:%M:%S', errors='coerce')
    timecard_df['Clock Out'] = pd.to_datetime(timecard_df['Time Out'], format='%H:%M:%S', errors='coerce')
    timecard_df['Working Hours Float'] = (timecard_df['Clock Out'] - timecard_df['Clock In']).dt.total_seconds() / 3600

    # Drive Time 转 HH:MM
    trip_df['Drive Time'] = pd.to_timedelta(trip_df['Driving Duration'].astype(str), errors='coerce')
    trip_df['Drive Time HHMM'] = trip_df['Drive Time'].apply(
        lambda x: f"{int(x.total_seconds() // 3600)}:{int((x.total_seconds() % 3600) // 60):02d}" if pd.notnull(x) else ''
    )

    # 合并并计算空闲时间
    merged = pd.merge(timecard_df, trip_df[['Driver', 'Drive Time HHMM']], on='Driver', how='left')
    merged['Drive Time Float'] = merged['Drive Time HHMM'].apply(
        lambda x: int(x.split(':')[0]) + int(x.split(':')[1]) / 60 if x else 0
    )
    merged['Idle Time Float'] = merged['Working Hours Float'] - merged['Drive Time Float']

    # 转换为 HH:MM 字符串
    def to_hhmm(hours_float):
        hours = int(hours_float)
        minutes = int((hours_float - hours) * 60)
        return f"{hours}:{minutes:02d}"

    merged['Clock In'] = merged['Clock In'].dt.strftime('%H:%M:%S')
    merged['Clock Out'] = merged['Clock Out'].dt.strftime('%H:%M:%S')
    merged['Working Hours'] = merged['Working Hours Float'].apply(to_hhmm)
    merged['Idle Time'] = merged['Idle Time Float'].apply(to_hhmm)

    # 展示结果
    display_df = merged[['Driver', 'Clock In', 'Clock Out', 'Working Hours', 'Drive Time HHMM', 'Idle Time']].rename(
        columns={'Drive Time HHMM': 'Drive Time'}
    )
    st.dataframe(display_df)

    # 导出按钮
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button('下载分析结果 CSV', data=csv, file_name='driver_analysis.csv', mime='text/csv')
