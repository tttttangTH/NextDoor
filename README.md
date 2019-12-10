# NextDoor

Clone this project

```$ git clone https://github.com/tttttangTH/NextDoor.git ```

Go to this directory and create a virtual environment and activate it:

```
$ virtualenv env
$ source env/bin/activate
```

Install the dependencies:

```$ pip3 install -r requirements.txt```

Modify database config in config.py, your should create an empty database first and do the following each time you change the database in your code

```
flask db migrate
flask db upgrade
```

Finally, to run the app, start the server:

```$ python dbweb.py```
