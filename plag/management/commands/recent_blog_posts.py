import feedparser

from time import mktime
from datetime import datetime

from django.core.management.base import BaseCommand

from plag.models import RecentBlogPosts


class Command(BaseCommand):
    args = '<number_blog_posts>'
    help = 'Gets N recent blog posts. Better than parsing the list every page load.'

    def handle(self, arg, **options):
        num_blog_posts = int(arg)

        feed = feedparser.parse('https://www.plagiarismguard.com/blog/feed')

        for blog in RecentBlogPosts.objects.all():
            blog.delete()

        loop_max = num_blog_posts if len(feed['entries']) > num_blog_posts else len(feed['entries'])

        for i in range(0, loop_max):
            if feed['entries'][i]:
                blog_post = RecentBlogPosts()
                blog_post.title = feed['entries'][i].title
                blog_post.link = feed['entries'][i].link
                blog_post.desc = feed['entries'][i].description
                blog_post.date = datetime.fromtimestamp(mktime(feed['entries'][i].published_parsed))
                blog_post.save()

