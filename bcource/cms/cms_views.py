from collections import OrderedDict
from functools import wraps

from flask import render_template, redirect, url_for, flash, request
from flask_security import current_user
from flask_babel import lazy_gettext as _l

from bcource import menu_structure, db
from bcource.models import Content, TrainingType, Location, Trainer, Policy
from . import cms_bp


CATEGORIES = OrderedDict([
    ('email',        (_l('Email Templates'),  lambda tag: (
        tag.startswith('Email') or 'Reminder' in tag or
        tag.startswith('ENROLL_') or tag.startswith('REMOVE_')
    ))),
    ('trainingtype', (_l('Training Types'),   lambda tag: tag.startswith('TrainingType_'))),
    ('location',     (_l('Locations'),        lambda tag: tag.startswith('Location_'))),
    ('trainer',      (_l('Trainers'),         lambda tag: tag.startswith('Trainer_'))),
    ('policy',       (_l('Policies'),         lambda tag: tag.startswith('Policy_'))),
    ('pages',        (_l('Pages'),            lambda tag: True)),  # catch-all
])


def _tag_category(tag):
    """Return the category key for a given tag."""
    for key, (label, predicate) in CATEGORIES.items():
        if predicate(tag):
            return key
    return 'pages'


def cms_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_anonymous or not current_user.accessible_by_permission('admin-interface'):
            return redirect(url_for('home_bp.home'))
        return f(*args, **kwargs)
    return decorated


# Register in nav menu between Training Administration and Training Scheduler
cms_menu = menu_structure.add_menu(_l('CMS Editor'), role='trainer')
cms_menu.add_menu(_l('CMS Editor'), 'cms_bp.index', role='trainer')


@cms_bp.route('/')
@cms_required
def index():
    return redirect(url_for('cms_bp.list_category', category='email'))


@cms_bp.route('/<category>')
@cms_required
def list_category(category):
    if category not in CATEGORIES:
        return redirect(url_for('cms_bp.list_category', category='email'))

    label, predicate = CATEGORIES[category]

    # Get all distinct tags and their language coverage
    rows = db.session.query(Content.tag, Content.lang, Content.text, Content.subject).all()

    # Group by tag
    tag_data = {}
    for tag, lang, text, subject in rows:
        if tag not in tag_data:
            tag_data[tag] = {'en': False, 'nl': False}
        if text or subject:
            tag_data[tag][lang] = True

    # Filter to this category, but only tags that belong HERE (first matching category wins)
    category_tags = sorted(
        [tag for tag in tag_data if _tag_category(tag) == category]
    )

    # Build a display name map for _N tags
    tag_names = {}
    if category == 'trainingtype':
        for tt in TrainingType.query.all():
            tag_names[f'TrainingType_{tt.id}'] = tt.name
    elif category == 'location':
        for loc in Location.query.all():
            tag_names[f'Location_{loc.id}'] = loc.name
    elif category == 'trainer':
        for tr in Trainer.query.all():
            tag_names[f'Trainer_{tr.id}'] = tr.user.fullname if tr.user else str(tr.id)
    elif category == 'policy':
        for pol in Policy.query.all():
            tag_names[f'Policy_{pol.id}'] = pol.name

    return render_template(
        'cms/list.html',
        categories=CATEGORIES,
        current_category=category,
        current_label=label,
        tags=category_tags,
        tag_data=tag_data,
        tag_names=tag_names,
    )


@cms_bp.route('/edit/<path:tag>', methods=['GET', 'POST'])
@cms_required
def edit(tag):
    category = _tag_category(tag)

    en = db.session.query(Content).filter_by(tag=tag, lang='en').first()
    nl = db.session.query(Content).filter_by(tag=tag, lang='nl').first()

    if request.method == 'POST':
        # Upsert EN
        if en is None:
            en = Content(tag=tag, lang='en')
            db.session.add(en)
        en.subject = request.form.get('en_subject', '') or None
        en.text = request.form.get('en_text', '') or None

        # Upsert NL
        if nl is None:
            nl = Content(tag=tag, lang='nl')
            db.session.add(nl)
        nl.subject = request.form.get('nl_subject', '') or None
        nl.text = request.form.get('nl_text', '') or None

        db.session.commit()
        flash(_l('Saved.'), 'success')
        return redirect(url_for('cms_bp.list_category', category=category))

    return render_template(
        'cms/edit.html',
        categories=CATEGORIES,
        current_category=category,
        tag=tag,
        en=en,
        nl=nl,
    )
