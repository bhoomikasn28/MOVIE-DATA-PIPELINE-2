1.Project Overview 
Implemented an ETL data pipeline that integrates the MovieLens dataset with the OMDb API. The objective is to extract movie and rating data, perform data cleaning and transformation, enrich the dataset with additional movie metadata, and load the processed data into an SQLite database for analytical querying and insights. 

2.Project Structure
movie-data-pipeline/
├── etl.py
├── schema.sql
├── queries.sql
├── README.md
└── data/
├── movies.csv
└── ratings.csv

3.Setup Instructions
1. Create Virtual Environment
python -m venv venv

2. Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

3. Install Requirements
pip install pandas requests python-dotenv

4. Create .env file
Create a file named .env in the project folder and add:
OMDB_API_KEY=your_api_key_here

5. Add Dataset
Download MovieLens “latest-small” from Grouplens and place:
movies.csv ratings.csv
inside the data/ folder.

4.Running the ETL Pipeline
python etl.py
output:
ETL Completed Successfully! movies.db is ready.
Running SQL Queries
Use DB Browser for SQLite:

5.Open movies.db
Go to Execute SQL
Copy & paste queries from queries.sql
Run and view results

6.Design Choices

1.SQLite was selected as the database to keep the project lightweight and avoid the overhead of setting up a dedicated database server.

2.Only the first 15 movies were enriched using the OMDb API to stay within the limits of the free API tier.

3.A title-cleaning and fallback search mechanism was implemented to handle inconsistencies between MovieLens titles and OMDb records, improving metadata matching accuracy.

4.The database schema was intentionally kept simple, focusing on readability and ease of understanding for educational and demonstration purposes.

7.Key Challenges and Implemented Solutions

1.Several MovieLens titles did not exactly match the OMDb database.
  Solution: Implemented multiple title-cleaning and normalization techniques to improve matching accuracy.
2.The OMDb API imposed strict request limits during data enrichment.
  Solution: Restricted enrichment to the first 15 movie records to prevent API blocking and maintain workflow continuity.
3.The .env file was not being recognized during initial runs.
  Solution: Ensured the .env file was correctly placed in the project root directory for proper configuration loading.
4.The SQLite3 command-line tool was not recognized or failed to run initially.
  Solution: Verified SQLite installation and PATH configuration, ensuring that sqlite3.exe was properly extracted and accessible from the command line.




  
