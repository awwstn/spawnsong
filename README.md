Tom's Django Template
=====================

This is a template for my own use for quick apps to stick on Heroku.

It almost certainly isn't the best for whatever you want, and I don't use it myself for larger projects.

Setup process
=============


Read these commands before you run them, don't be an idiot :)

```
export APPNAME=realappname
git clone git@github.com:thomasparslowltd/django-heroku-template.git $APPNAME
cd $APPNAME
git checkout -b master
find . -iname '*.py' | xargs gsed -i "s/MYAPPNAME/$APPNAME/"
git mv MYAPPNAME $APPNAME
git commit -am "Replace placeholder name with actual project name"
mkvirtualenv ~/envs/$APPNAME
workon $APPNAME
pip install -r requirements.txt
heroku apps:create $APPNAME
git push heroku master
heroku run 'python manage.py syncdb --migrate'
git remote rename origin template
```

If you add AWS credentials to the settings.py and set up the correct bucket names etc you can run `python manage collectstatic` to upload your static files to S3.

