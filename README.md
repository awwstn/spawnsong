Tom's Django Template
=====================

This is a template for my own use for quick apps to stick on Heroku.

It almost certainly isn't the best for whatever you want, and I don't use it myself for larger projects.

Setup process
=============


```
export APPNAME=realappname
find . -iname '*.py' | xargs gsed -i "s/MYAPPNAME/$APPNAME/"
mv MYAPPNAME $APPNAME
mkvirtualenv ~/envs/$APPNAME
workon $APPNAME
pip install -r requirements.txt
python manage.py syncdb --migrate
heroku pps:create $APPNAME
```