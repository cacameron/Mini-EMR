
Mini-EMR

We decided to do a Mini-EMR because we wanted to help gear something towards smaller companies that couldn't exactly afford the more expensive and big databases. 

## Authors

- [@cacameron](https://www.github.com/cacameron)

- [@kbcameron](https://www.github.com/kbcameron)

- [@luminiousleslie](https://www.github.com/luminiousleslie)


## Tech Stack

Front End: HTML, CSS and Java scritpt

Back end: python, Java script

Database: Mongodb





## Installation

Install Visual studio

    For all Computers:
        https://code.visualstudio.com/download
        click the link that is correct for your Computer
Setting up Monogodb

    For Monogdb 
        https://www.mongodb.com
        Create a free account
## Deployment

To Run Mongodb in visual studio

For mac computers: 

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
For Windows computer:
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
  Install the packages from the requirements.txt: pip install <package_name>
```
```bash
  Test the connection: py test_connection.py
```
Than we ran the test_connection.py file to pull up the python database


## Screenshots

![App Screenshot](<img width="332" height="650" alt="Image" src="https://github.com/user-attachments/assets/275debf5-f5ea-4200-bf43-ac067509e9e9" />
            )

