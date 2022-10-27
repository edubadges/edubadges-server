
#from django.utils import unittest
from django.db import connection

from test_project.models import *

from django.core.cache import cache
from django.test import TestCase

from django.contrib.auth.models import User


class CacheModelTestCase(TestCase):
    def setUp(self):
        """called before each test case method"""
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Author.objects.all().delete()
        User.objects.all().delete()
        Category.objects.all().delete()
        cache.clear()

    def test_auto_publish_by_pk(self):
        """Tests whether or not a CacheModel will automatically publish_by pk"""
        orig = Author(first_name='joe', last_name='blow')
        orig.save()

        with self.assertNumQueries(0):
            Author.cached.get(pk=orig.pk)

    def test_manual_publish_by_fields(self):
        """Verify that Author's publish_by('first_name','last_name') works"""
        kwargs = {
            'first_name': "joe",
            'last_name': "blow",
        }
        orig = Author(**kwargs)
        orig.save()

        with self.assertNumQueries(0):
            Author.cached.get(**kwargs)

    def test_denormalized_field(self):
        """Verify that a @denormalized_field gets updated on save"""
        author = Author(first_name='joe', last_name='blow')
        author.save()

        # create our post with popularity -1
        post = Post(title='Test Post', author=author, body="lipsum", popularity=-1)
        post.save() 

        # denormalize_field of Post._popularity should set popularity == 0
        self.assertEqual(post.popularity, 0)


    def test_cached_method(self):
        """Verify that a auto_publish=False @cached_method retrieves from the cache"""
        author = Author(first_name='joe', last_name='blow')
        author.save()
        post = Post(title='Test Post', author=author, body="lipsum", popularity=-1)
        post.save() 
        post.last_comments() # run the cached method once first

        with self.assertNumQueries(0):
            post.last_comments()


    def test_auto_published_cached_method(self):
        """Verify that auto_publish=True @cached_method fetches from cache the first time"""
        author = Author(first_name='joe', last_name='blow')
        author.save()

        with self.assertNumQueries(0):
            author.num_posts()


    def test_cached_method_with_no_parems(self):
        """Verify that using @cached_method with no parens works"""
        author = Author(first_name='joe', last_name='blow')
        author.save()
        post = Post(title='Test Post', author=author, body="lipsum", popularity=-1)
        post.save() 
        user = User(username='troll')
        user.save()
        first_post = Comment(post=post, user=user, comment="First!")
        first_post.save()
        second_post = Comment(post=post, user=user, comment="Second!", parent=first_post)
        second_post.save()

        # it returned successfully
        self.assertTrue(second_post in first_post.replies())

        # it cached correctly
        with self.assertNumQueries(0):
            first_post.replies()


    def test_publish_triggers(self):
        """Verify that calling publish on a foreignkey member trickles up"""
        author = Author(first_name='joe', last_name='blow')
        author.save()
        post = Post(title='Test Post', author=author, body="lipsum", popularity=-1)
        post.save() 

        with self.assertNumQueries(0):
            self.assertEqual(1, author.num_posts())

    def test_cached_table(self):
        """Verify that a CachedTable does not generate any queries on .get() lookups"""
        for name in ('Foo', 'Bar', 'Baz', 'Quuz'):
            Category(name=name, slug=name.lower()).save()

        with self.assertNumQueries(0):
            cats = Category.cached.all()
            foo = Category.cached.get(slug='foo')
            bar = Category.cached.get(id=2)
            baz = Category.cached.get(pk=3)


    def test_cached_table_save_updates_indices(self):
        """Ensure that a save on a CachedTable updates the indexes"""
        for name in ('Foo', 'Bar', 'Baz', 'Quuz'):
            Category(name=name, slug=name.lower()).save()
        Category.cached.all()

        foo = Category.cached.get(slug='foo')
        new_name = 'Foobar'
        foo.name = new_name
        foo.save()
        with self.assertNumQueries(0):
            new_foo = Category.cached.get(slug='foo')
            self.assertEqual(new_foo.name, new_name)





