import streamlit as st
from utils.s3_manager import get_s3_client, list_s3_files, download_s3_file, delete_s3_file

def run_admin_dashboard(aws_key, aws_secret, bucket_name):
    st.title("🛠️ Admin Dashboard")

    s3_client = get_s3_client(aws_key, aws_secret)

    st.sidebar.header("Navigation")
    view = st.sidebar.radio("Go to", ["Overview", "View Resumes", "View Reports", "S3 Info"])

    if view == "Overview":
        st.subheader("📊 Resume Insights")
        resume_files = list_s3_files(bucket_name, "resumes/", s3_client)
        report_files = list_s3_files(bucket_name, "reports/", s3_client)

        st.metric("📄 Total Resumes", len(resume_files))
        st.metric("📝 Total Reports", len(report_files))

    elif view == "View Resumes":
        st.subheader("📂 Uploaded Resumes")
        resumes = list_s3_files(bucket_name, "resumes/", s3_client)

        for file in resumes:
            st.write(file)
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Download {file}", key=file+"dl"):
                    data = download_s3_file(bucket_name, file, s3_client)
                    st.download_button("Download", data, file_name=file)
            with col2:
                if st.button(f"Delete {file}", key=file+"del"):
                    delete_s3_file(bucket_name, file, s3_client)
                    st.success(f"{file} deleted!")

    elif view == "View Reports":
        st.subheader("📄 ATS Reports")
        reports = list_s3_files(bucket_name, "reports/", s3_client)
        for file in reports:
            st.write(file)
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Download {file}", key=file+"rdl"):
                    data = download_s3_file(bucket_name, file, s3_client)
                    st.download_button("Download", data, file_name=file)
            with col2:
                if st.button(f"Delete {file}", key=file+"rdel"):
                    delete_s3_file(bucket_name, file, s3_client)
                    st.success(f"{file} deleted!")

    elif view == "S3 Info":
        st.subheader("📦 S3 Configuration")
        st.code(f"Bucket: {bucket_name}")
        st.code(f"AWS Access Key: {aws_key[:4]}****")
