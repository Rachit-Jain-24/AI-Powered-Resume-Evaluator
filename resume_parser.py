import boto3
import re

def extract_text_from_pdf(file_path, aws_key, aws_secret):
    textract = boto3.client(
        'textract',
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
        region_name='us-east-1'
    )
    with open(file_path, 'rb') as document:
        image_bytes = document.read()
    response = textract.detect_document_text(Document={'Bytes': image_bytes})
    lines = [item["Text"] for item in response["Blocks"] if item["BlockType"] == "LINE"]
    return '\n'.join(lines)

def extract_details(resume_text):
    name = resume_text.split('\n')[0]
    email = re.findall(r'[\w\.-]+@[\w\.-]+', resume_text)
    projects = re.findall(r'(?i)(?:project[s]?\s*[:\-–]?\s*)(.*)', resume_text)

    return {
        'Name': name.strip(),
        'Email': email[0] if email else "Not found",
        'Projects': projects if projects else ["No projects found"]
    }
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_ats_score(resume_text, jd_text):
    # Clean both texts by making them lowercase and removing special characters
    resume_text = resume_text.lower()
    jd_text = jd_text.lower()

    # Using TfidfVectorizer with ngram range and stopwords removal
    tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform([resume_text, jd_text])
    
    # Cosine similarity calculation  davinchi and vectorembedd
    score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]  
    
    # Multiply by 100 to get a percentage
    return round(score * 100, 2)

# Clean & extract keywords from text
def clean_and_tokenize(text):
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
    tokens = text.split()
    stopwords = set([
        'and', 'or', 'the', 'a', 'an', 'of', 'to', 'in', 'on', 'for', 'with',
        'by', 'is', 'are', 'was', 'were', 'this', 'that', 'at', 'from', 'as',
        'be', 'have', 'has', 'will', 'shall', 'we', 'you', 'your', 'it'
    ])
    return [word for word in tokens if word not in stopwords and len(word) > 1]

# def calculate_ats_score(resume_text, jd_text):
#     resume_keywords = set(clean_and_tokenize(resume_text))
#     jd_keywords = set(clean_and_tokenize(jd_text))

#     if not jd_keywords:
#         return 0.0

#     matched_keywords = resume_keywords.intersection(jd_keywords)
#     score = (len(matched_keywords) / len(jd_keywords)) * 100
#     return round(score, 2)



def upload_to_s3(local_path, bucket_name, s3_key, aws_key, aws_secret):
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
        region_name='us-east-1'
    )
    s3.upload_file(local_path, bucket_name, s3_key)
    url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
    return url


