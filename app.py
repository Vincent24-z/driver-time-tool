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

    # 转换 Clock In / Clock Out 为 datetime
    timecard_df['Clock In DT'] = pd.to_datetime(timecard_df['Time In'], errors='coerce')
    timecard_df['Clock Out DT'] = pd.to_datetime(timecard_df['Time Out'], errors='coerce')

    # 仅保留有完整 Clock In 和 Out 的记录
    timecard_df = timecard_df.dropna(subset=['Clock In DT', 'Clock Out DT'])

    # 每位司机仅保留第一次完整打卡记录
    timecard_df = timecard_df.sort_values('Clock In DT').drop_duplicates(subset='Driver', keep='first')

    # 计算工作时长（float 小时）
    timecard_df['Working Hours Float'] = (timecard_df['Clock Out DT'] - timecard_df['Clock In DT']).dt.total_seconds() / 3600

    # 格式化 Clock In / Out 为 HH:MM
    timecard_df['Clock In'] = timecard_df['Clock In DT'].dt.strftime('%H:%M')
    timecard_df['Clock Out'] = timecard_df['Clock Out DT'].dt.strftime('%H:%M')

    # Trip Report 处理
    trip_df = trip_df.dropna(subset=['Driving Duration'])
    trip_df['Drive Time'] = pd.to_timedelta(trip_df['Driving Duration'].astype(str), errors='coerce')
    trip_df = trip_df.dropna(subset=['Drive Time'])
    trip_df = trip_df.drop_duplicates(subset='Driver', keep='first')

    # 格式化 Drive Time
    trip_df['Drive Time HHMM'] = trip_df['Drive Time'].apply(
        lambda x: f"{int(x.total_seconds() // 3600)}:{int((x.total_seconds() % 3600) // 60):02d}"
    )

    # 合并
    merged = pd.merge(timecard_df, trip_df[['Driver', 'Drive Time HHMM']], on='Driver', how='left')

    # Drive Time 转 float 小时
    merged['Drive Time Float'] = merged['Drive Time HHMM'].apply(
        lambda x: int(x.split(':')[0]) + int(x.split(':')[1])/60 if pd.notnull(x) and x != '' else 0
    )

    # Idle Time = 工作 - 行车
    merged['Idle Time Float'] = merged['Working Hours Float'] - merged['Drive Time Float']

    # 转换成 H:MM 格式的函数
    def to_hhmm(hours_float):
        try:
            if pd.isnull(hours_float) or hours_float < 0:
                return ''
            hours = int(hours_float)
            minutes = int(round((hours_float - hours) * 60))
            return f"{hours}:{minutes:02d}"
        except:
            return ''

    # 应用转换
    merged['Working Hours'] = merged['Working Hours Float'].apply(to_hhmm)
    merged['Idle Time'] = merged['Idle Time Float'].apply(to_hhmm)

    # 最终展示字段
    display_df = merged[['Driver', 'Clock In', 'Clock Out', 'Working Hours', 'Drive Time HHMM', 'Idle Time']].rename(
        columns={'Drive Time HHMM': 'Drive Time'}
    )

    st.dataframe(display_df)

    # 导出按钮
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button('📄 下载分析结果 CSV', data=csv, file_name='driver_analysis.csv', mime='text/csv')
