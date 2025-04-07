import pandas as pd

# 读取上传的文件为 DataFrame
trip_report_df = pd.read_excel(uploaded_tripreport)      # 行车报告
timecard_df = pd.read_excel(uploaded_timecard)           # 打卡记录

# 如果任何一个 DataFrame 为空，提前退出避免后续处理出错
if trip_report_df.empty or timecard_df.empty:
    st.error("Trip Report 或 Timecard 数据为空，无法处理。")
    st.stop()

# 1. 规范 Driving Duration 格式并转换为 Timedelta
trip_report_df['Driving Duration'] = trip_report_df['Driving Duration'].astype(str).str.strip().str.upper()
trip_report_df['Driving Duration'] = trip_report_df['Driving Duration'].str.replace('H', ' hours ').str.replace('M', ' min', regex=False)
trip_report_df['Drive Time'] = pd.to_timedelta(trip_report_df['Driving Duration'], errors='coerce')
# 跳过无法解析的行
trip_report_df = trip_report_df[~(trip_report_df['Driving Duration'].notna() & trip_report_df['Drive Time'].isna())]

# 2. 格式化 Clock In/Out 时间
timecard_df['Clock In'] = pd.to_datetime(timecard_df['Clock In'], errors='coerce')
timecard_df['Clock Out'] = pd.to_datetime(timecard_df['Clock Out'], errors='coerce')
timecard_df['Clock In'] = timecard_df['Clock In'].dt.strftime('%H:%M:%S').fillna('')
timecard_df['Clock Out'] = timecard_df['Clock Out'].dt.strftime('%H:%M:%S').fillna('')

# 3. 计算 Working Hours (Timedelta)
timecard_df['ClockIn_dt'] = pd.to_datetime(timecard_df['Clock In'], format='%H:%M:%S', errors='coerce')
timecard_df['ClockOut_dt'] = pd.to_datetime(timecard_df['Clock Out'], format='%H:%M:%S', errors='coerce')
timecard_df['Working_td'] = timecard_df['ClockOut_dt'] - timecard_df['ClockIn_dt']

# 4. 合并数据（严格按 Driver 匹配），只保留 timecard_df 中的司机
trip_report_df['Drive_td'] = trip_report_df['Drive Time']  # 重命名方便理解
merged_df = pd.merge(timecard_df, trip_report_df[['Driver','Drive_td']], on='Driver', how='left')  # 左连接&#8203;:contentReference[oaicite:6]{index=6}

# 5. 计算 Idle Time Timedelta
merged_df['Drive_td_filled'] = merged_df['Drive_td'].fillna(pd.Timedelta(0))
merged_df['Idle_td'] = merged_df['Working_td'] - merged_df['Drive_td_filled']

# 定义格式化 Timedelta 的函数
def format_hhmm(td):
    if pd.isna(td):
        return ""
    total_sec = int(td.total_seconds())
    hrs = total_sec // 3600
    mins = (total_sec % 3600) // 60
    return f"{hrs}:{mins:02d}"

# 6. 生成最终显示的字段
merged_df['Working Hours'] = merged_df['Working_td'].apply(format_hhmm)
merged_df['Drive Time']   = merged_df['Drive_td'].apply(format_hhmm)
merged_df['Idle Time']    = merged_df['Idle_td'].apply(format_hhmm)

result_df = merged_df[['Driver', 'Clock In', 'Clock Out', 
                       'Working Hours', 'Drive Time', 'Idle Time']]

# 在 Streamlit 中展示结果
st.dataframe(result_df)
