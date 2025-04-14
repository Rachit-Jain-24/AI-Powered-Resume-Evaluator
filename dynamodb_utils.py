import boto3
from datetime import datetime
import uuid
from decimal import Decimal, InvalidOperation

def save_evaluation_resumes(aws_key, aws_secret, name, email, job_role, ats_score,
                            present_skills, missing_skills, report_url):
    # Initialize DynamoDB resource
    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
        region_name='us-east-1'
    )
    table = dynamodb.Table('ResumeEvaluations')
    
    # Generate unique Resume ID
    resume_id = str(uuid.uuid4())

    # Safely convert ATS score to Decimal
    try:
        ats_score_decimal = Decimal(str(ats_score))
    except (InvalidOperation, ValueError, TypeError):
        ats_score_decimal = Decimal('-1')  # Default fallback score

    # Convert skills to comma-separated strings if needed
    present_skills_str = ', '.join(present_skills) if isinstance(present_skills, list) else str(present_skills)
    missing_skills_str = ', '.join(missing_skills) if isinstance(missing_skills, list) else str(missing_skills)

    # Construct item to insert into DynamoDB
    item = {
        'ResumeID': resume_id,
        'Name': name,
        'Email': email,
        'JobRole': job_role,
        'ATSScore': ats_score_decimal,
        'PresentSkills': present_skills_str,
        'MissingSkills': missing_skills_str,
        'ReportURL': report_url,
        'UploadedAt': datetime.utcnow().isoformat()
    }

    # Attempt to save to DynamoDB
    try:
        table.put_item(Item=item)
    except Exception as e:
        print("❌ Error saving resume evaluation to DynamoDB:", e)
        return None

    return resume_id
