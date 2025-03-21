Alright yall need to install psql:
https://www.postgresql.org/download/
(yall gotta get its path and put that shit in the environment variable) 
(the path should be sumn like this: C:\Program Files\PostgreSQL\17\bin )


Install git
use these commands to get pull the code from the repo ive created:
To make repo:
git clone https://github.com/3astW1nd/se_proj.git
cd se_proj

to get all requirements:
pip install -r requirements.txt

to pull code:
git pull origin main

to push code:
git add .
git commit -m "Implemented feature XYZ"
git push origin main 
(we will be pushing all the shit in main because why the fuck not)


To run the Django server:
python manage.py migrate (to get new changes if needed)
python manage.py runserver

To run neon PostgreSQL / connect to db:
python manage.py dbshell


