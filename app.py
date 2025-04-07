import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Arial']  # 避免乱码
matplotlib.rcParams['axes.unicode_minus'] = False   # 修复负号乱码

# 分析后保持结果（不被刷新清除）
if st.session_state.get("output_df") is not None:
    st.subheader("📋 分析结果")
    st.dataframe(st.session_state.output_df)
    csv = st.session_state.output_df.to_csv(index=False)
    st.download_button('下载分析结果 CSV', data=csv, file_name='driver_analysis.csv')


# 保存分析数据
if uploaded_timecard and uploaded_tripreport:
    if st.button("📊 分析数据"):
        # [你已有的分析代码，此处略]

        st.session_state.output_df = output_df  # 存入 session

# 显示分析结果（若存在）
if st.session_state.output_df is not None:
    st.subheader("📋 分析结果")
    st.dataframe(st.session_state.output_df)
    csv = st.session_state.output_df.to_csv(index=False)
    st.download_button('下载分析结果 CSV', data=csv, file_name='driver_analysis.csv')

# 历史图表
st.markdown("---")
st.header("📈 查看历史趋势图")

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
                ax.plot(group_sorted['Date'], y, label=driver, marker='o')
            ax.set_title(f"{metric} 趋势")
            ax.set_ylabel("小时")
            ax.set_xlabel("日期")
            ax.legend(title="Driver")
            plt.xticks(rotation=45)
            st.pyplot(fig)
    else:
        st.warning("暂无历史记录可供分析。")
