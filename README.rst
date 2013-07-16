Minecloud
=========
*Launch an on-demand Minecraft server on Amazon EC2...easily.*

Hosting a private, multiplayer Minecraft server is a fun way for family and friends to play together. But, what if you only play occasionally? Why pay for a Minecraft server running 24/7, if you don't use it a lot?

Wouldn't it be better if you could run an on-demand server that only ran when you wanted to play and still preserved the state of your world from session to session?

The Minecloud project let's you do just that. You can launch a Minecraft server on Amazon EC2 when you are ready to play, and then shut it down when you are done. It automatically backs up the Minecraft game data files to Amazon S3 when it stops, and restores from S3 when it starts. And, you can start and stop the Minecraft server with the click of a button in an easy-to-use Web application that also shows you if other players in your group are already logged in and playing.


How Does it Work?
-----------------
The Minecloud project consists of two parts that work together:

1. `Minecloud-AMI`__ builds a custom Minecraft EC2 AMI that contains the Minecraft server software, as well as various backup and management scripts.

__ https://github.com/toffer/minecloud-ami

2. `Minecloud`__ is a Django web application whose sole purpose is to launch the custom Minecraft EC2 AMI built in the first step.

__ https://github.com/toffer/minecloud


Requirements
------------
In order to use the Minecloud web application to launch a Minecraft server on Amazon EC2, you first need to follow the steps in the `Minecloud-AMI`_ project to create a custom Minecraft EC2 AMI.

* Custom Minecraft AMI

Once you've built the custom AMI, you're ready to install Minecloud. It's a pretty simple Django app, with the following prerequisites for installation:

* Python 2.7 (untested on Python 3)
* PostgreSQL (PostgreSQL's listen/notify feature is used as a message queue for pushing Server-Sent Events.)

.. _Minecloud-AMI: https://github.com/toffer/minecloud-ami


Installation
------------
Minecloud was designed to run on `Heroku's free tier`_, so the installation instructions below will cover that scenario. If this is the first time you are using Heroku's service, make sure to familiarize yourself with their `Getting Started with Django on Heroku`_ in addition to following these instructions.

.. _Heroku's free tier: https://devcenter.heroku.com/articles/usage-and-billing
.. _Getting Started with Django on Heroku: https://devcenter.heroku.com/articles/django

**Note**: *If running the Minecloud web application elsewhere, pay attention to the required environment variables used for Django configuation described in step 5.*


Steps to get up-and-running on Heroku:

1. **Sign up for Heroku account and install the Heroku toolbelt on your computer.**

2. **Git clone Minecloud.** ::

    $ git clone https://github.com/toffer/minecloud

3. **Create app.** ::

    $ heroku create <app-name>

4. **Add free Postgres add-on to your app.** ::

    $ heroku addons:add heroku-postgresql:dev

5. **Add free Memcachier add-on to your app.** ::

    $ heroku addons:add memcachier:dev

6. **Set environment variables.** ::

    # Use the heroku command to set each config variable
    # See: https://devcenter.heroku.com/articles/config-vars

    # Amazon AWS settings. AWS account must be authorized to use EC2 and S3.
    $ heroku config:set AWS_ACCESS_KEY_ID=...
    $ heroku config:set AWS_SECRET_ACCESS_KEY=...

    # Setting for the database connection uses a Heroku-style URL
    # You can "promote" the database to set DATABASE_URL
    # First, you find the name of your Postgres DB.
    # It will be something like "HEROKU_POSTGRES...URL".
    $ heroku config | grep HEROKU_POSTGRESQL

    # Then, you "promote it" to set the DATABASE_URL config var.
    $ heroku pg:promote <HEROKU_POSTGRESQL...URL>

    # Use "Production" Django settings, rather than "Development"
    $ heroku config:set DJANGO_SETTINGS_MODULE=minecloud.settings.production

    # Space-separated list of ALLOWED_HOSTS
    # New security setting in Django 1.5
    # See: https://docs.djangoproject.com/en/dev/releases/1.5/#allowed-hosts-required-in-production
    $ heroku config:set DJANGO_ALLOWED_HOSTS="<app-name>.herokuapp.com <customdomain>.com"

    # Django Secret Key
    # See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-SECRET_KEY
    $ heroku config:set DJANGO_SECRET_KEY=...

    # Required Minecloud settings
    $ heroku config:set MCL_EC2_AMI=<ami-id of custom AMI built by Minecloud-AMI>
    $ heroku config:set MSM_S3_BUCKET=<name of S3 bucket in which to store Minecraft backup files>

    # Optional Minecloud settings
    # If you built your Minecloud-AMI in a different region than 'us-west-2', you need
    # to set the MCL_EC2_REGION variable
    $ heroku config:set MCL_EC2_REGION=<EC2 region name>

    # Review all your settings
    $ heroku config

7. **Deploy.** ::

    $ git push heroku master

8. **Sync database and create superuser.**

   Every user (incuding superusers) should use their Minecraft username as their username for the Minecloud web application. ::

    $ heroku run python manage.py syncdb

9. **Add authorized players.**

   Log in to <app-name>.herokuapp.com/admin/ with the superuser account. Click on 'Users' to add accounts for players who will be white-listed to play on the Minecraft server. Player accounts have two required fields: "Username", which should be the player's Minecraft username, and "Password". 

   * Every user is authorized both to play on and to launch the Minecraft server.

   * Every user who is a Staff member will be authorized as an Operator on the Minecraft server.

10. **Launch Minecraft server.**

    Open <app-name>.herokuapp.com/ and click the "Wake Up Server" button.


License
-------
MIT License. Copyright (c) 2013 Tom Offermann.
