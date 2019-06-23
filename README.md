# Plagiarism detection with Python 3 and Django

In 2014-2015 I developed a side-project called Plagiarism Guard which was a plagiarism detection service. I mainly did this to teach myself Python (kudos to [Learn Python the Hard Way](https://learnpythonthehardway.org/) and also implement some (very!) basic [NLP](https://en.wikipedia.org/wiki/Natural_language_processing). This was developed in Python 3 and the Django framework.

The basic premise for this plagiarism detection is to accept resources in a few different formats (URL being the most popular, but also text files and Office-type documents). The resources can then be periodically scanned (via custom management commands triggered via a crontab), and a few fairly unique phrases are pulled out of them. These phrases are then searched online (using Bing's search engine API), and the results are the 'plagiarism-detected' candidates. Finally these candidates are scanned to rule out any false positives, and discover an approximate duplication score. 

The files for this project are organised into three main folders:

 * /plag/ - this is the bulk of the Django application, hence it contains the models, forms, routes, services etc.
   * The /plag/templates/ folder contains the HTML pages covering both the public (unauthenticated) website pages such as the order form and legal documents (under static/), and the account (authenticated) pages (under dynamic/)
   * */plag/templatetags/custom_tags.py* contains the Django [custom template tags](https://docs.djangoproject.com/en/1.7/howto/custom-template-tags/) used in various parts of the HTML frontend
   * /plag/management/commands contains the [custom management commands](https://docs.djangoproject.com/en/1.7/howto/custom-management-commands/):
     * *scan_resources.py* chooses *ProtectedResource* entries which are due to be scanned, and then calls the relevant 'utility' methods in /util/getqueriespertype/ to get a few (hopefully distinct) queries from the document/resource. Bing's search engine API is then called in */util/handlequeries.py* to get any potential plagiarism matches for each query. These results are saved back to the DB.
     * *post_processing.py* then looks at each potential plagiarism match URL, loads up the URL and parses the text content to see whether this is a false positive or not. If it's a real match, a duplication percentage score is calculcated. This then appears on the user's account.
     * *recent_blog_posts.py* this [parses a blog's RSS feed](https://www.tristanperry.com/how-to/2014/10/05/add-django-rss-feed.html) and saves the latest results to the database, so that the blog results can be shown in a cached/efficient way.
 * /PlagiarismGuard/ - these are the standard Django files used to configure and power the application.
 * /util/ - as covered a little above, these are a set of 'utilities' which perform the bulk of the plagiarism detection work.

A further write-up of this project is available [on my personal site](https://www.tristanperry.com/python3/2017/12/21/plagiarism-guard-source-code.html).

## Installing/running

Since this was a project from 5+ years ago (and I only came across the code again a couple of years ago), I unfortunately don't have the full install/running instructions for this anymore. However you will see that this project is built around Django and has the relevant models and migrations folders to get the DB side of things setup.

Equally I recently found the `requirements.txt` file which has now been committed, and this project was developed and ran against Python 3.4.

This project can extract text (to check for plagiarism) from many file types, including .pdf and the old (non XML) Word .doc format. For these two formats, the following utilities were used:

 * `pdftotext` which can be installed by `yum install poppler-utils` on Unix systems, whilst the .exe called `xpdfbin-win-3.04.zip` can be found online and installed for Windows.
 * `antiword` which can be installed [from winfield](http://www.winfield.demon.nl/#Programmer){:target="_blank"} for Unix based systems (the Windows source for it worked in 2014 but it now returns a 404).
 
Once the relevant dependencies are installed and Django is running, you will be able to add resources to protect/scan via the Django admin panel (or manually via SQL commands, of course) - and then the management commands can be triggered (manually or via a cron) to scan them and get the results.
 