from bcource.training.training_views import training_bp, request, redirect, url_for
from bcource.helpers import get_url
from flask import render_template
from flask_babel import _
from flask_babel import lazy_gettext as _l
from bcource.models import Training

@training_bp.route('/training-detail/<int:id>',methods=['GET', 'POST'])
def training_detail(id):
    clear = request.args.getlist('submit_id')
    if clear and clear[0]=='back':
        return redirect(get_url())
    
    training = Training().query.get(id)
    url = get_url()
    
    return render_template("training/training_detail.html", 
                           return_url=url,
                           page_name=_("Training Overview for %(training_name)s", training_name=training.name),
                           training=training)
