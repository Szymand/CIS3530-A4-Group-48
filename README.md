# 1. Clone the repository
```git clone https://github.com/Szymand/CIS3530-A4-Group-48.git```  
```cd CIS3530-A4-Group-48```

# 2. Create a virtual environment
```python -m venv .venv```

# 3. Activate the virtual environment
Windows PowerShell:
```.\.venv\Scripts\Activate.ps1```
If you get an error about scripts being disabled, run this first:
```Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass```
Then activate again.

# 4. Install dependencies
```pip install -r requirements.txt```

# 5. Create the PostgreSQL database
Open a terminal and run:
```& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres```  
Sign into PostgreSQL then run the following:  
```CREATE DATABASE company_portal_db;```

# 6. Load the SQL file into the database
In PowerShell from the project directory:  
```& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d company_portal_db -f sql\company_v3.02.sql```  
```& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d company_portal_db -f sql\team_setup.sql```  
(Change the version number in the path if needed.)

# 7. Create Dotenv file to hold PostgreSQL credentials
* From the project directory create a new file named .env
    * (in Powershell, you can run ```New-Item -Path .env -ItemType File```)
* inside the .env file, enter the following (replace ```<your postgres password>``` with your postgres password):
    ```
    DB_USER=postgres
    DB_PASSWORD=<your postgres password>
    DB_HOST=localhost
    DB_PORT=5432
    ```
    * replace ```DB_USER```, ```DB_HOST```, and ```DB_PORT``` if your credentials do not match the defaults

# 8 Add the Test Account to the Database
From the main project directory, run the command below, and the one in step 9  
```python insert_user.py``` 
# 9. Run the Flask app
```python app.py```

# 10. Open a browser and go to:
http://127.0.0.1:5000/

You should see the Flask test page with the current date from the database.
If you get a connection error, make sure PostgreSQL is running and the password in app.py matches your local setup.

# 11. Indexes
The first index implemented is idx_employee_name on Employee(Lname, Fname) this index imporves performance on the home page (A2), where employees
are searched and sorted by name. The page orders results using ORDER by full_name also allowing partial name filtering. Since we have built full_name from Lname and Fname, Postgres can use this index to avoid a full table scan and reduce the cost of sorting employees alphabetically. This speeds up both name searches and default page load when the employee list is ordered by name. 

The second index is idx_workson_pno on Works_On(Pno), this index speeds up queries that retrieve project related stats on the Home page. The proj_stats CTE groups by project number and aggregates hours and project counts: 

SELECT Essn, COUNT(DISTINCT Pno), SUM(Hours)
FROM Works_On
GROUP BY Essn;

When we aggregate by project or feth all employees on a specific project, the index on Pno helps it avoid scanning the entire Works_on table. This makes the page's project and hours calculations more efficient. 

Both of these indexes can be found within team_setup.sql like required.
