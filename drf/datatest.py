import boto3

session = boto3.Session(profile_name="test")
s3 = session.client("s3")
bucket_name = "simkim-s3-bucket"

# 파일 목록 조회
response = s3.list_objects_v2(Bucket=bucket_name)

file_list = [obj["Key"] for obj in response.get("Contents", [])]

print(file_list)