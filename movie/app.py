from bson import ObjectId
from pymongo import MongoClient

from flask import Flask, render_template, jsonify, request
from flask.json.provider import JSONProvider

import json
import sys


app = Flask(__name__)

# 아래 uri를 복사해둔 uri로 수정하기
uri = "mongodb+srv://donggun465:A99SkJhPq8CtCjNf@cluster0.wvgsuzt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&tlsAllowInvalidCertificates=true"
client = MongoClient(uri, 27017)  # MongoDB는 27017 포트로 돌아갑니다.
db = client.dbjungle


#####################################################################################
# 이 부분은 코드를 건드리지 말고 그냥 두세요. 코드를 이해하지 못해도 상관없는 부분입니다.
#
# ObjectId 타입으로 되어있는 _id 필드는 Flask의 jsonify 호출 시 문제가 된다.
# 이를 처리하기 위해서 기본 JsonEncoder 가 아닌 custom encoder를 사용한다.
# Custom encoder는 다른 부분은 모두 기본 encoder에 동작을 위임하고 ObjectId 타입만 직접 처리한다.
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)


# 위에 정의된 custom encoder를 사용하게끔 설정한다.
app.json = CustomJSONProvider(app)

# 여기까지 이해 못 해도 그냥 넘어갈 코드입니다.
# #####################################################################################



#####
# 아래의 각각의 @app.route 은 RESTful API 하나에 대응됩니다.
# @app.route()의 첫 번째 인자는 API 경로,
# 생략 가능한 두 번째 인자는 해당 경로에 적용 가능한 HTTP method 목록을 의미합니다.

# API #1: HTML 틀(template) 전달
#         틀 안에 데이터를 채워 넣어야 하는데 이는 아래 이어지는 /api/list를 통해 이루어집니다.
@app.route('/')
def home():
    return render_template('index.html')


# API #2: 휴지통에 버려지지 않은 영화 목록을 반환합니다.
@app.route('/api/list', methods=['GET'])
def show_movies():
    # client에서 요청한 정렬 방식이 있는지를 확인합니다. 없다면 기본으로 좋아요 순으로 정렬합니다.
    sortMode = request.args.get('sortMode', 'likes')

    # 1. db에서 trashed가 False인 movies 목록을 검색합니다. 주어진 정렬 방식으로 정렬합니다.
    # 참고) find({},{}), sort()를 활용하면 됨.
    #      개봉일 순서 정렬처럼 여러 기준으로 순서대로 정렬해야 되는 경우 sort([('A', 1), ('B', 1)])처럼 줄 수 있음.
    #    TODO: 다음 코드에서 likes로 정렬이 정상 동작하도록 직접 수정해 보세요!!!
    if sortMode == 'likes':
        movies = list(db.movies.find({'trashed': False}, {}).sort({'likes' : -1}))
    elif sortMode == 'running_time':
        movies = list(db.movies.find({'trashed': False}, {}).sort({'running_time' : -1}))
    elif sortMode == 'released_year':
        movies = list(db.movies.find({'trashed': False}, {}).sort({'released_year' : -1}))
    else:
        return jsonify({'result': 'failure'})

    # 2. 성공하면 success 메시지와 함께 movies_list 목록을 클라이언트에 전달합니다.
    return jsonify({'result': 'success', 'movies_list': movies})

# API #3: 휴지통에 버려진 영화 목록을 반환합니다.
@app.route('/api/list/trash', methods=['GET'])
def show_trash_movies():
    # client에서 요청한 정렬 방식이 있는지를 확인합니다. 없다면 기본으로 좋아요 순으로 정렬합니다.
    sortMode = request.args.get('sortMode', 'likes')

    if sortMode == 'likes':
        movies = list(db.movies.find({'trashed': True}, {}).sort({'likes' : -1}))
    elif sortMode == 'running_time':
        movies = list(db.movies.find({'trashed': True}, {}).sort({'running_time' : -1}))
    elif sortMode == 'released_year':
        movies = list(db.movies.find({'trashed': True}, {}).sort({'released_year' : -1}))
    else:
        return jsonify({'result': 'failure'})

    # 2. 성공하면 success 메시지와 함께 movies_list 목록을 클라이언트에 전달합니다.
    return jsonify({'result': 'success', 'movies_trash_list': movies})

# API #4: 영화에 좋아요 숫자를 하나 올립니다.
@app.route('/api/like', methods=['POST'])
def like_movie():
    # 1. movies 목록에서 find_one으로 영화 하나를 찾습니다.
    #    TODO: 영화 하나만 찾도록 다음 코드를 직접 수정해 보세요!!!
    movie_title = request.form['movie_title']
    movie = db.movies.find_one({'title' : movie_title})

    # 2. movie의 like에 1을 더해준 new_like 변수를 만듭니다.
    new_likes = movie['likes'] + 1

    # 3. movies 목록에서 id 가 매칭되는 영화의 like를 new_like로 변경합니다.
    #    참고: '$set' 활용하기!
    #    TODO: 영화 하나의 likes 값이 변경되도록 다음 코드를 직접 수정해 보세요!!!
    result = db.movies.update_one({'title' : movie_title}, {'$set': {'likes': new_likes}})

    # 4. 하나의 영화만 영향을 받아야 하므로 result.updated_count 가 1이면  result = success를 보냄
    if result.modified_count == 1:
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'failure'})

# API #5: 휴지통으로 이동
@app.route('/api/trash', methods=['POST'])
def trash_movie():
    movie_title = request.form['movie_title']
    movie = db.movies.find_one({'title' : movie_title})

    result = db.movies.update_one({'title' : movie_title}, {'$set': {'trashed': True}})

    # 4. 하나의 영화만 영향을 받아야 하므로 result.updated_count 가 1이면  result = success를 보냄
    if result.modified_count == 1:
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'failure'})
    
# API #6: 휴지통에서 복구
@app.route('/api/trash/restore', methods=['POST'])
def trash_movie_restore():
    movie_title = request.form['movie_title']
    movie = db.movies.find_one({'title' : movie_title})

    result = db.movies.update_one({'title' : movie_title}, {'$set': {'trashed': False}})

    # 4. 하나의 영화만 영향을 받아야 하므로 result.updated_count 가 1이면  result = success를 보냄
    if result.modified_count == 1:
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'failure'})
    
# API #7: 휴지통에서 완전 삭제
@app.route('/api/trash/delete', methods=['POST'])
def trash_movie_delete():
    movie_title = request.form['movie_title']
    movie = db.movies.find_one({'title' : movie_title})


    if movie['trashed'] == True:
        result = db.movies.delete_one({'title' : movie_title})
    else:
        return jsonify({'result': 'failure'})

    # 2. 성공하면 success 메시지와 함께 movies_list 목록을 클라이언트에 전달합니다.
    return jsonify({'result': 'success'})

if __name__ == '__main__':
    print(sys.executable)
    app.run('0.0.0.0', port=5000, debug=True)