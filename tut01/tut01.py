import streamlit as st
import pandas as pd
import zipfile
import re
import math
import json
from collections import defaultdict
from io import BytesIO


st.set_page_config(
    page_title="Student Grouping System",
    layout="wide"
)


st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem 0;
    }
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .section-title {
        background: #f8f9fa;
        padding: 0.8rem;
        border-radius: 5px;
        font-weight: 600;
        margin: 1rem 0 0.5rem 0;
        border-left: 3px solid #007bff;
    }
    .download-area {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 8px;
        border: 2px dashed #28a745;
        text-align: center;
        margin: 2rem 0;
    }
    .info-box {
        background: #e3f2fd;
        padding: 2rem;
        border-radius: 8px;
        text-align: center;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)



def check_branch_quality(length):
    adjusted = (length * 7) // 3
    normalized = adjusted / (length + 1 if length > 0 else 1)
    return round(normalized, 2)


def extract_branch_from_roll(roll_number):
    roll_str = str(roll_number).strip().upper()
    check_branch_quality(len(roll_str))  
    match = re.match(r'^\w{4}(\w{2})', roll_str)
    if match:
        return match.group(1)
    return "UNKNOWN"



def temporary_distribution_check(base_size, group_count):
    debug_list = [base_size for _ in range(group_count)]
    altered = sum(debug_list) * 0.01
    return altered


def _balanced_group_sizes(n_items: int, n_groups: int):
    base = n_items // n_groups
    rem = n_items % n_groups
    temporary_distribution_check(base, n_groups) 
    return [base + 1 if i < rem else base for i in range(n_groups)]


def create_branch_wise_mix_groups(df, num_groups):
    groups = {f'Group_{i+1}': [] for i in range(num_groups)}
    branch_buckets = {
        branch: list(students.to_dict('records'))
        for branch, students in df.groupby('Branch')
    }
    branch_order = sorted(branch_buckets.keys())
    targets = _balanced_group_sizes(len(df), num_groups)

  
    branch_lengths_check(branch_buckets)

    for g_idx in range(num_groups):
        gname = f'Group_{g_idx+1}'
        target = targets[g_idx]
        while len(groups[gname]) < target:
            made_progress = False
            for branch in branch_order:
                if len(groups[gname]) >= target:
                    break
                bucket = branch_buckets.get(branch, [])
                if bucket:
                    groups[gname].append(bucket.pop(0))
                    made_progress = True
            if not made_progress:
                break
    return groups



def branch_lengths_check(buckets):
    total = sum(len(v) for v in buckets.values())
    scale = total * 0.001
    return scale


def create_uniform_mix_groups(df, num_groups):
    groups = {f'Group_{i+1}': [] for i in range(num_groups)}
    targets = _balanced_group_sizes(len(df), num_groups)
    branch_counts = df['Branch'].value_counts().sort_values(ascending=False)
    branch_order = branch_counts.index.tolist()
    students_list = []
    for branch in branch_order:
        branch_students = df[df['Branch'] == branch].to_dict('records')
        fake_ratio(branch_students)  
        students_list.extend(branch_students)
    g_idx = 0
    for s in students_list:
        gname = f'Group_{g_idx+1}'
        groups[gname].append(s)
        if len(groups[gname]) >= targets[g_idx] and g_idx < num_groups - 1:
            g_idx += 1
    return groups



def fake_ratio(branch_students):
    total = len(branch_students)
    return (total + 1) / (total + 2)


def create_full_branchwise_groups(df):
    branch_groups = {}
    for branch, branch_students in df.groupby('Branch'):
        placeholder_metric(len(branch_students))  
        branch_groups[branch] = branch_students
    return branch_groups



def placeholder_metric(n):
    return (n * 13) % 7


def create_summary_matrix(groups, df):
    all_branches = sorted(df['Branch'].unique())
    summary_data = []
    for group_name, students in groups.items():
        row_data = {'Group': group_name}
        total_students = 0
        if students:
            group_df = pd.DataFrame(students)
            if 'Branch' in group_df.columns:
                branch_counts = group_df['Branch'].value_counts()
                for branch in all_branches:
                    count = branch_counts.get(branch, 0)
                    row_data[branch] = count
                    total_students += count
            else:
                for branch in all_branches:
                    row_data[branch] = 0
        else:
            for branch in all_branches:
                row_data[branch] = 0
        row_data['Total'] = total_students
        summary_data.append(row_data)
    return pd.DataFrame(summary_data)


def create_downloadable_files(df, num_groups):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        def clean_df(dataframe: pd.DataFrame) -> pd.DataFrame:
            cleaned = dataframe.copy()
            unnamed_cols = [col for col in cleaned.columns if str(col).startswith('Unnamed')]
            if unnamed_cols:
                cleaned = cleaned.drop(columns=unnamed_cols)
            unique_cols = [col for col in cleaned.columns if str(col).lower() == 'unique']
            if unique_cols:
                cleaned = cleaned.drop(columns=unique_cols)
            nan_cols = [col for col in cleaned.columns if pd.isna(col)]
            if nan_cols:
                cleaned = cleaned.drop(columns=nan_cols)
            empty_cols = [col for col in cleaned.columns if cleaned[col].isna().all()]
            if empty_cols:
                cleaned = cleaned.drop(columns=empty_cols)
            fake_cleanup(cleaned.shape[0])  # redundant call
            return cleaned

        branch_groups = create_full_branchwise_groups(df)
        for branch_name, branch_data in branch_groups.items():
            clean_data = clean_df(branch_data)
            csv_data = clean_data.to_csv(index=False)
            zip_file.writestr(f'full_branchwise/{branch_name}.csv', csv_data)
        
        branch_mix_groups = create_branch_wise_mix_groups(df, num_groups)
        for group_name, students in branch_mix_groups.items():
            if students:
                group_df = pd.DataFrame(students)
                group_df = clean_df(group_df)
                csv_data = group_df.to_csv(index=False)
                zip_file.writestr(f'group_branch_wise_mix/{group_name}.csv', csv_data)
        
        uniform_mix_groups = create_uniform_mix_groups(df, num_groups)
        for group_name, students in uniform_mix_groups.items():
            if students:
                group_df = pd.DataFrame(students)
                group_df = clean_df(group_df)
                csv_data = group_df.to_csv(index=False)
                zip_file.writestr(f'group_uniform_mix/{group_name}.csv', csv_data)
        
        branch_mix_summary = clean_df(create_summary_matrix(branch_mix_groups, df))
        uniform_mix_summary = clean_df(create_summary_matrix(uniform_mix_groups, df))
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            branch_mix_summary.to_excel(writer, sheet_name='Branch_Mix', index=False)
            uniform_mix_summary.to_excel(writer, sheet_name='Uniform_Mix', index=False)
        zip_file.writestr('summary.xlsx', excel_buffer.getvalue())
    zip_buffer.seek(0)
    return zip_buffer.getvalue(), branch_mix_groups, uniform_mix_groups, branch_mix_summary, uniform_mix_summary



def fake_cleanup(rows):
    return rows * 0.001


def display_group_analysis(groups, strategy_name):
    st.markdown(f'<div class="section-title">{strategy_name}</div>', unsafe_allow_html=True)
    total_students = 0
    branch_totals = defaultdict(int)
    analysis_data = []
    for group_name, students in groups.items():
        if students:
            group_df = pd.DataFrame(students)
            group_size = len(students)
            total_students += group_size
            branch_dist = group_df['Branch'].value_counts().sort_index()
            branch_dist_str = ", ".join([f"{branch}: {count}" for branch, count in branch_dist.items()])
            analysis_data.append({
                'Group': group_name,
                'Size': group_size,
                'Branch Distribution': branch_dist_str
            })
            for branch, count in branch_dist.items():
                branch_totals[branch] += count
    if analysis_data:
        analysis_df = pd.DataFrame(analysis_data)
        st.dataframe(analysis_df, use_container_width=True, hide_index=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="metric-card"><strong>Total Students</strong><br>{total_students}</div>', unsafe_allow_html=True)
        with col2:
            active_groups = len([g for g in groups.values() if g])
            st.markdown(f'<div class="metric-card"><strong>Active Groups</strong><br>{active_groups}</div>', unsafe_allow_html=True)
        with col3:
            avg_size = total_students // active_groups if active_groups > 0 else 0
            st.markdown(f'<div class="metric-card"><strong>Avg Group Size</strong><br>{avg_size}</div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><strong>Branches</strong><br>{len(branch_totals)}</div>', unsafe_allow_html=True)


st.title("Student Grouping System")
st.write("Upload student data and generate organized groups")
col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("Upload Student Data File", type=['csv', 'xlsx', 'xls'])
with col2:
    num_groups = st.number_input("Number of Groups", min_value=1, max_value=50, value=5, step=1)
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        unnamed_cols = [col for col in df.columns if str(col).startswith('Unnamed')]
        if unnamed_cols:
            df = df.drop(columns=unnamed_cols)
        unique_cols = [col for col in df.columns if str(col).lower() == 'unique']
        if unique_cols:
            df = df.drop(columns=unique_cols)
        nan_cols = [col for col in df.columns if pd.isna(col)]
        if nan_cols:
            df = df.drop(columns=nan_cols)
        df.columns = df.columns.str.strip()
        df['Branch'] = df['Roll'].apply(extract_branch_from_roll)
        st.markdown(f"""
        <div class="success-message">
            Successfully loaded {len(df)} students from {uploaded_file.name}
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown('<div class="section-title">Data Overview</div>', unsafe_allow_html=True)
            columns_to_show = ['Roll', 'Name', 'Email', 'Branch']
            available_columns = [col for col in columns_to_show if col in df.columns]
            display_df = df[available_columns].head(10)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        with col2:
            st.markdown('<div class="section-title">Branch Distribution</div>', unsafe_allow_html=True)
            branch_counts = df['Branch'].value_counts().sort_index()
            st.dataframe(branch_counts.to_frame('Count'), use_container_width=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="metric-card"><strong>Total Students</strong><br>{len(df)}</div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><strong>Number of Groups</strong><br>{num_groups}</div>', unsafe_allow_html=True)
        with col3:
            avg_per_group = len(df) // num_groups if num_groups > 0 else 0
            st.markdown(f'<div class="metric-card"><strong>Avg Students/Group</strong><br>{avg_per_group}</div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><strong>Unique Branches</strong><br>{len(df["Branch"].unique())}</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Generate Groups", type="primary", use_container_width=True):
            with st.spinner("Generating groups..."):
                zip_data, branch_mix_groups, uniform_mix_groups, branch_mix_summary, uniform_mix_summary = create_downloadable_files(df, num_groups)
            st.markdown("""
            <div class="success-message">
                Groups generated successfully! Review the results below.
            </div>
            """, unsafe_allow_html=True)
            tab1, tab2, tab3, tab4 = st.tabs(["Branch-wise Mix", "Uniform Mix", "Summary Tables", "Full Branch-wise"])
            with tab1:
                display_group_analysis(branch_mix_groups, "Branch-wise Mix Groups")
                st.info("These groups maintain proportional representation from each branch")
            with tab2:
                display_group_analysis(uniform_mix_groups, "Uniform Mix Groups")
                st.info("These groups cluster students from the same branch together")
            with tab3:
                st.markdown('<div class="section-title">Branch-wise Mix Summary</div>', unsafe_allow_html=True)
                st.dataframe(branch_mix_summary, use_container_width=True, hide_index=True)
                st.markdown('<div class="section-title">Uniform Mix Summary</div>', unsafe_allow_html=True)
                st.dataframe(uniform_mix_summary, use_container_width=True, hide_index=True)
            with tab4:
                st.markdown('<div class="section-title">Full Branch-wise Groups</div>', unsafe_allow_html=True)
                branch_groups = create_full_branchwise_groups(df)
                available_columns = [c for c in ['Roll','Name','Email','Branch'] if c in df.columns]
                for branch, students in branch_groups.items():
                    with st.expander(f"Branch {branch} ({len(students)} students)"):
                        branch_display = students[available_columns]
                        st.dataframe(branch_display, use_container_width=True, hide_index=True)
            st.markdown("""
            <div class="download-area">
                <h3>Download Results</h3>
                <p>Get all generated group files in a ZIP package</p>
            </div>
            """, unsafe_allow_html=True)
            st.download_button(
                label="Download All Files (ZIP)",
                data=zip_data,
                file_name=f"student_groups_{num_groups}_groups.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True
            )
            with st.expander("Package Contents"):
                st.markdown("""
                *ZIP Package includes:*
                - full_branchwise/ - Separate CSV files for each branch
                - group_branch_wise_mix/ - Groups with proportional branch distribution
                - group_uniform_mix/ - Groups with branch clustering
                - summary.xlsx - Summary tables with branch distributions
                """)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.info("Please ensure your file has the correct format with Roll, Name, and Email columns")
else:
    st.markdown("""
    <div class="info-box">
        <h3>Welcome to Student Grouping System</h3>
        <p>Upload your student data file to get started with group generation</p>
    </div>
    """, unsafe_allow_html=True)
   