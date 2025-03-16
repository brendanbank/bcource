from sqlalchemy import  String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .. import db, table_admin
from bcource.admin.admin_views import AuthModelView

class Content(db.Model):
    tag: Mapped[str] = mapped_column(String(256), primary_key=True)
    lang: Mapped[str] = mapped_column(String(16), default="en", primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=True)

    @classmethod
    def get_tag(cls,tag,lang="en"):
        content = db.session.query(cls).filter(cls.tag==tag, lang==lang).first()
        if not content:
            content=cls(tag=tag,text="")
            db.session.add(content)
            db.session.commit()
        return(content.text)
    
from wtforms import TextAreaField
from wtforms.widgets import TextArea

class CKTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] += ' ckeditor'
        else:
            kwargs.setdefault('class', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)

class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()

class ContentModelView(AuthModelView):
    column_display_pk = True
    form_columns = ('tag', 'text', 'lang')
    edit_template = 'admin/cms.html'
    column_list = ['tag', 'lang']
    permission = "cms-admin"

    extra_js = ['//cdn.ckeditor.com/ckeditor5/44.3.0/ckeditor5.umd.js',
                '//cdn.ckeditor.com/ckeditor5-premium-features/44.3.0/ckeditor5-premium-features.umd.js',
                '//cdn.ckbox.io/ckbox/2.6.1/ckbox.js',
                '/static/ckeditor.js' ]
    #
    # form_overrides = {
    #     'text': CKTextAreaField
    # }

table_admin.add_view(ContentModelView(Content, db.session)) #@UndefinedVariable
