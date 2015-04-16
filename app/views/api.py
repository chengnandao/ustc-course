from flask import Blueprint,jsonify,request
from flask.ext.login import login_required,current_user
from app.models import Review, ReviewComment , User, Course, ImageStore
from app.forms import ReviewCommentForm
from app.utils import rand_str
from app import app

import re
import os

api = Blueprint('api',__name__)


@api.route('/reviews/')
def get_reviews():
    response = {'status':'ok',
            'info':'',
            'data': []
            }
    course_id = request.args.get('course_id',type=int)
    page = request.args.get('page',1,type=int)
    if not course_id:
        response['status'] = 'error'
        response['info'] = 'Need to specify a course id'
        return jsonify(response)
    course = Course.query.get(course_id)
    if not course:
        response['status'] = 'error'
        response['info'] = 'Course can\'t found'
        return jsonify(response)
    reviews = course.reviews.paginate(page)
    for item in reviews.items:
        review = {'id':item.id,
                'rate':item.rate,
                'content':item.content,
                'author':{'name':item.author.username,
                    'id':item.author_id},
                'upvote':item.upvote,
                }
        response['data'].append(review)
    return jsonify(response)


@api.route('/review/upvote/',methods=['GET','POST'])
def review_upvote():
    review_id = request.values.get('review_id')
    if not review_id:
        return jsonify(status=false,message="A id must be given")
    review = Review.query.get(review_id)
    status,message = review.upvote()
    return jsonify(status=status,message=message)

@api.route('/review/cancel_upvote/',methods=['GET','POST'])
def review_cancel_upvote():
    review_id = request.values.get('review_id')
    if not review_id:
        return jsonify(status=False,message="A id must be given")
    review = Review.query.get(review_id)
    if not review:
        return jsonify(status=False,message="The review dosen't exist.")
    if review.author != current_user:
        return jsonify(status=False,message="Forbiden")
    status,message = review.cancel_upvote()
    return jsonify(status=status,message=message)

@api.route('/review/new_comment/',methods=['POST'])
def review_new_comment():
    form = ReviewCommentForm(request.form)
    if form.validate_on_submit():
        review_id = request.form.get('review_id')
        review = Review.query.get(review_id)
        if not review_id:
            return jsonify(status=False,message="The review dosen't exist.")
        comment = ReviewComment()
        content = request.form.get('content')
        status,message = comment.add(review,content)
        return jsonify(status=status,message=message,content=content)
    return jsonify(status=False,message=form.errors)

@api.route('/review/delete_comment/',methods=['GET','POST'])
def review_delete_comment():
    comment_id = request.values.get('id')
    if not comment_id:
        return jsonify(status=False,message="A id must be given")
    comment = ReviewComment.query.filter_by(id=comment_id).first()
    if not comment:
        return jsonify(status=False,message="The comment dosen't exist.")
    if comment.author != current_user:
        return jsonify(status=False,message="Forbiden")
    status,message = comment.delete()
    return jsonify(status=False,message=message)


def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@api.route('/upload/',methods=['POST'])
@login_required
def upload():
    file = request.files['image']
    if file and allowed_file(file.filename):
        old_filename = file.filename
        file_suffix = old_filename.split('.')[-1]
        new_filename = rand_str() + '.' + file_suffix
        try:
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images/')
            file.save(os.path.join(upload_path, new_filename))
        except FileNotFoundError:
            os.makedirs(upload_path)
            file.save(os.path.join(upload_path, new_filename))
        except:
            return jsonify(status=False,message="Something WRONG")
        img = ImageStore(old_filename,new_filename)
        return jsonify(status=True,filename=new_filename)
    return jsonify(status=False,message="Upload failed")




@api.route('/review_comment/',methods=['GET'])
def get_review_comment():
    id = request.args.get('id')
    if not id:
        return jsonify(status='Id not found')

    review = Review.query.get(id)
    if review:
        comments = review.comments
    else:
        return jsonify(status='Id not found',data=None)
    return jsonify(status='OK',data=comments)

@api.route('/reg_verify', methods=['GET'])
def reg_verify():
    name = request.args.get('name')
    value = request.args.get('value')

    if name == 'username':
        if User.query.filter_by(username=value).first():
            return 'Username Exists'
        return 'OK'
    elif name == 'email':
        if User.query.filter_by(email=value).first():
            return 'Email Exists'
        regex = re.compile("[a-zA-Z0-9_]+@(mail\.)?ustc\.edu\.cn")
        if not regex.fullmatch(value):
            return 'Illegal Address'
        return 'OK'
    return 'Invalid Request', 400
