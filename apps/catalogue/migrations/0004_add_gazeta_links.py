# -*- coding: utf-8 -*-
from south.db import db
from django.db import models


class Migration:    
    def forwards(self):
        db.add_column('catalogue_tag', 'gazeta_link', models.CharField(blank=True,  max_length=240))
        db.add_column('catalogue_book', 'gazeta_link', models.CharField(blank=True,  max_length=240))
    
    def backwards(self):
        db.delete_column('catalogue_tag', 'gazeta_link')
        db.delete_column('catalogue_book', 'gazeta_link')
