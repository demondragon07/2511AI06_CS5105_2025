import pandas as pd
import logging
import streamlit as st
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)
logger = logging.getLogger("guide_allocation")


def _find_cgpa_index(df: pd.DataFrame) -> int:
    cols = list(df.columns)
    if 'CGPA' not in cols:
        logger.error("Missing 'CGPA' column in input file.")
        raise ValueError("Input CSV must contain a column named 'CGPA' (case-sensitive).")
    return cols.index('CGPA')


def allocate_students(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Starting student allocation process.")
    df = df.copy()
    cgpa_idx = _find_cgpa_index(df)
    pref_cols = list(df.columns)[cgpa_idx + 1:]
    n = len(pref_cols)
    num_students = len(df)
    logger.info(f"Detected {n} faculty columns and {num_students} students.")

    df['__CGPA_numeric'] = pd.to_numeric(df['CGPA'], errors='coerce').fillna(-1e9)
    df_sorted = df.sort_values(by='__CGPA_numeric', ascending=False).reset_index(drop=True)

    roll_to_faculty = {}
    total_allocations = 0

    for group_start in range(0, num_students, n):
        group_end = min(group_start + n, num_students)
        group_df = df_sorted.iloc[group_start:group_end]
        taken = set()
        logger.debug(f"Allocating group from row {group_start} to {group_end - 1}")

        for _, row in group_df.iterrows():
            roll = row.get('Roll', f"row_{_}")
            prefs = []
            for fac in pref_cols:
                val = pd.to_numeric(row[fac], errors='coerce')
                if pd.notna(val):
                    prefs.append((fac, int(val)))

            prefs.sort(key=lambda x: x[1])
            allocated_fac = None
            for fac, _ in prefs:
                if fac not in taken:
                    allocated_fac = fac
                    taken.add(fac)
                    break

            roll_to_faculty[roll] = allocated_fac if allocated_fac else 'UNALLOCATED'
            total_allocations += 1

    logger.info(f"Allocation completed for {total_allocations} students.")
    df['AllocatedFaculty'] = df['Roll'].map(roll_to_faculty)
    output_cols = ['Roll', 'Name', 'Email', 'CGPA', 'AllocatedFaculty']
    return df[output_cols]


def prepare_fac_pref_stats(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Preparing faculty preference statistics.")
    cgpa_idx = _find_cgpa_index(df)
    pref_cols = list(df.columns)[cgpa_idx + 1:]

    max_pref = int(df[pref_cols].max().max())
    fac_pref_counts = defaultdict(lambda: [0] * max_pref)

    for _, row in df.iterrows():
        for fac in pref_cols:
            val = pd.to_numeric(row[fac], errors='coerce')
            if pd.notna(val) and 1 <= int(val) <= max_pref:
                fac_pref_counts[fac][int(val) - 1] += 1

    data = []
    for fac, counts in sorted(fac_pref_counts.items()):
        entry = {'Faculty': fac}
        for i, c in enumerate(counts, start=1):
            entry[f'Pref {i}'] = c
        data.append(entry)

    logger.info("Faculty preference statistics generated successfully.")
    return pd.DataFrame(data)


st.title("Faculty Allocation System")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        logger.info(f"CSV file uploaded successfully: {uploaded_file.name}")

        st.subheader("Uploaded Data Preview")
        st.dataframe(df.head())

        result_df = allocate_students(df)
        stats_df = prepare_fac_pref_stats(df)

        st.subheader("Allocation Results")
        st.dataframe(result_df)

        st.subheader("Faculty Preference Count")
        st.dataframe(stats_df)

        st.download_button(
            label="Download Allocation CSV",
            data=result_df.to_csv(index=False).encode('utf-8'),
            file_name='allocation_results.csv',
            mime='text/csv'
        )

        st.download_button(
            label="Download Faculty Preference Count CSV",
            data=stats_df.to_csv(index=False).encode('utf-8'),
            file_name='faculty_preference_count.csv',
            mime='text/csv'
        )

    except Exception as e:
        st.error(f"Error: {e}")
        logger.exception("An error occurred during allocation.")
else:
    st.info("Please upload a CSV file to begin allocation.")
