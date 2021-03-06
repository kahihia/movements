# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MarketItemActions'
        db.create_table(u'market_marketitemactions', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('market_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['market.MarketItem'])),
            ('action', self.gf('django.db.models.fields.TextField')()),
            ('date_of_action', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('market', ['MarketItemActions'])


    def backwards(self, orm):
        # Deleting model 'MarketItemActions'
        db.delete_table(u'market_marketitemactions')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'market.comment': {
            'Meta': {'ordering': "['-pub_date']", 'object_name': 'Comment'},
            'contents': ('tinymce.models.HTMLField', [], {}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'comments'", 'null': 'True', 'to': "orm['market.MarketItem']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'blank': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'market.emailrecommendation': {
            'Meta': {'object_name': 'EmailRecommendation'},
            'email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '75', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'market_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.MarketItem']", 'null': 'True'}),
            'recommendation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        'market.file': {
            'Meta': {'object_name': 'File'},
            'afile': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'files'", 'to': "orm['market.MarketItem']"})
        },
        'market.itemrate': {
            'Meta': {'object_name': 'ItemRate'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'rates'", 'null': 'True', 'to': "orm['market.MarketItem']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'blank': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'market.marketitem': {
            'Meta': {'object_name': 'MarketItem'},
            'closed_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'commentcount': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'countries': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['users.Countries']", 'symmetrical': 'False'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'details': ('tinymce.models.HTMLField', [], {}),
            'exp_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issues': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['users.Issues']", 'symmetrical': 'False'}),
            'item_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'never_exp': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'blank': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'ratecount': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'reportcount': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'score': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'skills': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['users.Skills']", 'symmetrical': 'False'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'max_length': '1'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'})
        },
        'market.marketitemactions': {
            'Meta': {'object_name': 'MarketItemActions'},
            'action': ('django.db.models.fields.TextField', [], {}),
            'date_of_action': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'market_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.MarketItem']"})
        },
        'market.marketitemhidden': {
            'Meta': {'object_name': 'MarketItemHidden'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.MarketItem']"}),
            'viewer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'market.marketitempostreport': {
            'Meta': {'ordering': "['-resolved', '-pub_date']", 'object_name': 'MarketItemPostReport'},
            'contents': ('tinymce.models.HTMLField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'repots'", 'null': 'True', 'to': "orm['market.MarketItem']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'blank': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'resolved': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'market.marketitemstick': {
            'Meta': {'object_name': 'MarketItemStick'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.MarketItem']"}),
            'viewer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'market.marketitemviewconter': {
            'Meta': {'object_name': 'MarketItemViewConter'},
            'counter': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.MarketItem']"}),
            'viewer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'market.messageext': {
            'Meta': {'ordering': "('-sent_at', '-id')", 'object_name': 'MessageExt', '_ormbases': [u'postman.Message']},
            'is_post_recommendation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_user_recommendation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'market_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.MarketItem']", 'null': 'True', 'blank': 'True'}),
            u'message_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['postman.Message']", 'unique': 'True', 'primary_key': 'True'})
        },
        'market.notification': {
            'Meta': {'ordering': "['-pub_date']", 'object_name': 'Notification'},
            'avatar_user': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.Comment']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['market.MarketItem']", 'null': 'True', 'blank': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'read': ('django.db.models.fields.BooleanField', [], {}),
            'seen': ('django.db.models.fields.BooleanField', [], {}),
            'text': ('json_field.fields.JSONField', [], {'default': "u'null'"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'market.userreport': {
            'Meta': {'ordering': "['-resolved', '-pub_date']", 'object_name': 'UserReport'},
            'contents': ('tinymce.models.HTMLField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'resolved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_repots'", 'to': u"orm['auth.User']"})
        },
        u'postman.message': {
            'Meta': {'ordering': "[u'-sent_at', u'-id']", 'object_name': 'Message'},
            'body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderation_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'moderated_messages'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'moderation_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'moderation_reason': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            'moderation_status': ('django.db.models.fields.CharField', [], {'default': "u'p'", 'max_length': '1'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'next_messages'", 'null': 'True', 'to': u"orm['postman.Message']"}),
            'read_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'received_messages'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'recipient_archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient_deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'replied_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'sent_messages'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'sender_archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sender_deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'child_messages'", 'null': 'True', 'to': u"orm['postman.Message']"})
        },
        u'users.countries': {
            'Meta': {'ordering': "['countries']", 'object_name': 'Countries'},
            'countries': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'countries_ar': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'countries_en': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'countries_ru': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'users.issues': {
            'Meta': {'ordering': "['issues']", 'object_name': 'Issues'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issues': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'issues_ar': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'issues_en': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'issues_ru': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'users.skills': {
            'Meta': {'ordering': "['skills']", 'object_name': 'Skills'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'skills': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'skills_ar': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'skills_en': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'skills_ru': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['market']