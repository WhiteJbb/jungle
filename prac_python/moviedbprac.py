from pymongo import MongoClient           # pymongo를 임포트 하기(패키지 인스톨 먼저 해야겠죠?)

# 아래 uri를 복사해둔 uri로 수정하기
uri = "mongodb+srv://donggun465:A99SkJhPq8CtCjNf@cluster0.wvgsuzt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&tlsAllowInvalidCertificates=true"
client = MongoClient(uri, 27017)  # MongoDB는 27017 포트로 돌아갑니다.
db = client.dbjungle    

# target_movie = db.movies.find_one({'title':'포레스트 검프'})
# target_year = target_movie['released_year']

# same_years = list(db.movies.find({'released_year': target_year},{'_id':False}))

# for movie in same_years:
#     print(movie["title"])

db.movies.update_one({'title':'매트릭스'},{'$set':{'released_year': 1998}})
