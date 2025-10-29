
## Mini EMR

We decided to do a Mini-EMR because we wanted to help gear something towards smaller companies that couldn't exactly afford the more expensive and big databases.

## Authors:

- [@cacameron](https://www.github.com/cacameron)
- [@kbcameron](https://www.github.com/kbcameron)
- [@luminiousleslie](https://www.github.com/luminiousleslie)


## Tech Stack:

Front End: HTML, CSS and Java scritpt

Back end: python, Java script

Database: Mongodb

## Installation:

Install Visual Studio Code
```bash
  For all Computers:
    https://code.visualstudio.com/download
    click the link that is correct for your Computer
```
Setting up Monogodb
```bash
 For Monogdb 
    https://www.mongodb.com
    Create a free account
```
## Deployment:

To Run Mongodb in visual studio

## For Mac Computers:
```bash
   python3 -m venv venv 
```
```bash
   source venv/bin/activate
```
```bash
   #connection string for python backend
            MONGO_URI=mongodb+srv://<db_username>:<db_password>@cluster0.yexocbd.mongodb.net/
```
```bash
    Rename file .env.example => .env
```
```bash
     Then, replace fields with our own MongoDB user credentials so it would look like:
                  MONGO_URI=mongodb+srv://username:password@cluster0.yexcdb.mongodb.net/
```
```bash
       Run to install libraries: pip install -r requirements.txt
```
```bash
        Once we have those installed, run the script: python test_connection.py 
```
## For Windows Computers:
```bash
      Open new terminal and choose command prompt (Defauly is powershell) 
```
```bash
      py -m venv venv 
```
```bash
      .\venv\Scripts\activate
    you will know when you're in if you see (venv)
```
```bash
      Open the .env.exmaple file and remame it as .env
```
```bash
        Then, replace fields with our own MongoDB user credentials so it would look like:
    MONGO_URI=mongodb+srv://username:password@cluster0.yexcdb.mongodb.net/
```
```bash
      Install the packages from the requirements.txt: pip install -r requirements.txt
```
```bash
      Test the connection: py test_connection.py
```

Than we ran the test_connection.py file to pull up the python database

## Running Tests Locally:

To get the program to pull up in the window:

```bash
 Run the app.py file
```
```bash
  Then you will click on the link that it gives you, should be something like this: 
  http://127.0.0.1:5000
```
```bash
Once you click that it will take you into a webrowser on your computer
```
```bash
  You will see the Patient and Dr login screen
```
```bash
  Sign in to the according one and view the records
```





![Logo](https://github.com/cacameron/Mini-EMR)

