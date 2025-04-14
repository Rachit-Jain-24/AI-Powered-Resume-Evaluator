import streamlit as st
import boto3
import os
import json
from datetime import datetime
from decimal import Decimal
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from resume_parser import extract_text_from_pdf, extract_details, upload_to_s3
from dynamodb_utils import save_evaluation_resumes

# -------------------- Streamlit Config --------------------
st.set_page_config(page_title="Smart Resume Evaluator", page_icon="🧠")
st.title("🧠 Smart Resume Evaluator")
st.write("Upload your resume and enter the job role you're targeting.")

# -------------------- AWS Credentials --------------------
aws_key = st.text_input("AWS Access Key ID", type="password")
aws_secret = st.text_input("AWS Secret Access Key", type="password")

# -------------------- Admin Mode --------------------
if st.sidebar.checkbox("🛡️ Admin Mode"):
    from admin_dashboard import run_admin_dashboard
    bucket_name = st.sidebar.text_input("S3 Bucket Name")
    if aws_key and aws_secret and bucket_name:
        run_admin_dashboard(aws_key, aws_secret, bucket_name)

# -------------------- File Upload & Inputs --------------------
uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
job_role = st.text_input("Enter Job Role (e.g. Data Scientist)")

# -------------------- Load Job Role Skill DB --------------------
with open("job_roles.json") as f:
    job_skills = json.load(f)

def calculate_ats_score(resume_text, jd_text):
    tfidf = TfidfVectorizer().fit_transform([resume_text, jd_text])
    score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return round(score * 100, 2)

def generate_report(details, skills_found, missing_skills, ats_score, report_path="resume_report.txt"):
    with open(report_path, "w") as f:
        f.write(f"Name: {details['Name']}\n")
        f.write(f"Email: {details['Email']}\n")
        f.write("Projects:\n" + "\n".join(details['Projects']) + "\n\n")
        f.write("Skills Found:\n" + ", ".join(skills_found) + "\n")
        f.write("Missing Skills:\n" + ", ".join(missing_skills) + "\n")
        f.write(f"\nATS Score: {ats_score if isinstance(ats_score, (int, float)) else 'Not Available'}\n")

def send_sns_email(aws_key, aws_secret, subject, message):
    sns = boto3.client(
        'sns',
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
        region_name='us-east-1'
    )
    topic_arn = 'arn:aws:sns:us-east-1:213448609223:ResumeNotifications'
    sns.publish(TopicArn=topic_arn, Subject=subject, Message=message)


# -------------------- Main Evaluation --------------------


if uploaded_file and job_role and aws_key and aws_secret:

    with open("temp_resume.pdf", "wb") as f:
        f.write(uploaded_file.read())

    st.info("⏳ Extracting text from resume using AWS Textract...")
    resume_text = extract_text_from_pdf("temp_resume.pdf", aws_key, aws_secret)

    details = extract_details(resume_text)
    st.subheader("📌 Resume Details")
    st.write(f"**Name:** {details['Name']}")
    st.write(f"**Email:** {details['Email']}")

    required_skills = job_skills.get(job_role, [])
    present_skills = [skill for skill in required_skills if skill.lower() in resume_text.lower()]
    missing_skills = [skill for skill in required_skills if skill.lower() not in resume_text.lower()]

    st.success("✅ Resume Evaluated Successfully!")
    st.subheader("✅ Skills Found in Resume")
    st.write(present_skills)

    st.subheader("❌ Missing Skills (Recommended to Learn)")
    st.write(missing_skills)

    st.subheader("📚 Learning Suggestions")
    for skill in missing_skills:
        st.markdown(f"- **{skill}** → [YouTube](https://www.youtube.com/results?search_query={skill}+tutorial) | [Coursera](https://www.coursera.org/search?query={skill})")

    # Initialize ATS Score
score = "N/A"

# JD-based ATS Score (if uploaded)
jd_file = st.file_uploader("Upload Job Description (PDF or TXT)", type=["pdf", "txt"])

if jd_file:
    jd_text = ""

    if jd_file.type == 'text/plain':
        jd_text = jd_file.read().decode("utf-8")

    elif jd_file.type == 'application/pdf':
        with open("temp_jd.pdf", "wb") as f:
            f.write(jd_file.getbuffer())
        try:
            jd_text = extract_text_from_pdf("temp_jd.pdf", aws_key, aws_secret)
        except Exception as e:
            st.error(f"❌ Error reading JD PDF: {str(e)}")

    if jd_text.strip() != "":
        st.subheader("📄 ATS Score (Resume vs Job Description)")
        try:
            numeric_score = calculate_ats_score(resume_text, jd_text)
            score = round(numeric_score, 2)
            st.metric("Match Percentage", f"{score}%")

            if score < 80:
                st.warning("❗ Your resume matches less than 80% with the Job Description.")
                st.markdown("### Suggestions:")
                st.markdown("""
                - Add more relevant keywords from the JD
                - Mention specific tools or technologies
                - Quantify your achievements
                - Highlight certifications or recent projects
                """)
            else:
                st.success("🎯 Your resume aligns well with the job description!")
        except Exception as e:
            st.error(f"⚠️ Could not calculate ATS score: {str(e)}")
            score = "N/A"

    # Report generation and storage
    report_filename = f"report_{details['Name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report_path = os.path.join(".", report_filename)
    generate_report(details, present_skills, missing_skills, score, report_path)

    bucket_name = "smart-resume-evaluator-bucket"
    resume_s3_key = f"resumes/{uploaded_file.name}"
    report_s3_key = f"reports/{report_filename}"

    resume_url = upload_to_s3("temp_resume.pdf", bucket_name, resume_s3_key, aws_key, aws_secret)
    report_url = upload_to_s3(report_path, bucket_name, report_s3_key, aws_key, aws_secret)

    resume_id = save_evaluation_resumes(
        aws_key, aws_secret, details['Name'], details['Email'], job_role,
        score, present_skills, missing_skills, report_url
    )

    st.success("🗂️ Files uploaded to S3!")
    st.markdown(f"📄 [View Resume on S3]({resume_url})")
    st.markdown(f"📊 [View Report on S3]({report_url})")
    st.success(f"✅ Evaluation saved with ID: `{resume_id}`")

    send_sns_email(
    aws_key,
    aws_secret,
    subject=f"📄 Resume Evaluated for {details['Name']}",
    message=f"""
        Dear Admin,

        A new resume has been successfully evaluated. Please find the summary below:

        👤 Student Name: {details['Name']}
        📧 Email: {details['Email']}
        📝 Job Role: {job_role}
        📊 Match Score: {str(score) + '%' if isinstance(score, (int, float)) else 'Not Available'}
        ✅ Present Skills: {', '.join(present_skills) if present_skills else 'None'}
        ❌ Missing Skills:{', '.join(missing_skills) if missing_skills else 'None'}

        📎 Resume File: {resume_url}
        📑 Evaluation Report: {report_url}

        Kindly review the evaluation and take appropriate action if needed.

        Regards,  
        Smart Resume Evaluator System
    """
)


    st.success("📨 Email sent to Admin!")