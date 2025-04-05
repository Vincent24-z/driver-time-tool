import streamlit as st
import pandas as pd

st.title('🚚 司机每日工作/行车/空闲时间分析')

uploaded_timecard = st.file_uploader('上传员工打卡记录', type=['xlsx'])
uploaded_tripreport = st.file_uploader('上传行车报告 Trip Report', type=['xlsx'])

if uploaded_timecard and uploaded_tripreport:
    timecard_df = pd.read_excel(uploaded_timecard)
    trip_df = pd.read_excel(uploaded_tripreport)

    timecard_df = timecard_df[['Employee', 'Time In', 'Time Out']]
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

    # 转换时间字段
    timecard_df['Clock In DT'] = pd.to_datetime(timecard_df['Time In'], errors='coerce')
    timecard_df['Clock Out DT'] = pd.to_datetime(timecard_df['Time Out'], errors='coerce')

    # 保留每位司机最早一条“完整”记录（含clock in 和 clock out）
    complete_logs = timecard_df.dropna(subset=['Clock In DT', 'Clock Out DT']).copy()
    complete_logs = complete_logs.sort_values(['Driver', 'Clock In DT'])
    timecard_df = complete_logs.drop_duplicates(subset=['Driver'], keep='first').copy()

    # 格式化时间
    timecard_df['Clock In'] = timecard_df['Clock In DT'].dt.strftime('%H:%M')
    timecard_df['Clock Out'] = timecard_df['Clock Out DT'].dt.strftime('%H:%M')

    # 计算工作时长（float小时数）
    timecard_df['Working Hours Float'] = (timecard_df['Clock Out DT'] - timecard_df['Clock In DT']).dt.total_seconds() / 3600

    # Trip Report drive time 转为 timedelta
    trip_df['Drive Time'] = pd.to_timedelta(trip_df['Driving Duration'].astype(str), errors='coerce')
    trip_df = trip_df.dropna(subset=['Drive Time'])  # 去掉无效的行
    trip_df = trip_df.drop_duplicates(subset=['Driver'], keep='first').copy()

    # Drive Time 转 float 小时
    trip_df['Drive Time Float'] = trip_df['Drive Time'].dt.total_seconds() / 3600

    # 合并
    merged = pd.merge(timecard_df, trip_df[['Driver', 'Drive Time Float']], on='Driver', how='left')
    merged['Drive Time Float'] = merged['Drive Time Float'].fillna(0)

    merged['Idle Time Float'] = merged['Working Hours Float'] - merged['Drive Time Float']

    def float_to_hhmm(hours_float):
        try:
            if pd.isnull(hours_float):
                return ''
            hours = int(hours_float)
            minutes = int(round((hours_float - hours) * 60))
            return f"{hours}:{minutes:02d}"
        except:
            return ''

    merged['Working Hours'] = merged['Working Hours Float'].apply(float_to_hhmm)
    merged['Drive Time'] = merged['Drive Time Float'].apply(float_to_hhmm)
    merged['Idle Time'] = merged['Idle Time Float'].apply(float_to_hhmm)

    display_df = merged[['Driver', 'Clock In', 'Clock Out', 'Working Hours', 'Drive Time', 'Idle Time']]

    st.dataframe(display_df)

    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button('下载分析结果 CSV', data=csv, file_name='driver_analysis.csv', mime='text/csv')
