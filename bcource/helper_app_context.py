from bcource import db
from flask import request, current_app

def b_pagination(select_query, per_page=current_app.config['POSTS_PER_PAGE']):
    page = request.args.get('page', 1, type=int)
    pagination = db.paginate(select_query, page=page,per_page=per_page, error_out=False)

    if pagination.last == 0:
        pagination = db.paginate(select_query, page=1, per_page=per_page, error_out=False)

    return pagination