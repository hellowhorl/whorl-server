# Setting up the API Endpoints

This README provides instructions for setting up the database, configuring users, and connecting the client and server in development mode.

First, clone the repository and navigate to the project directory.

```bash
git clone org-184059057@github.com:hellowhorl/whorl-server.git
```

## Setup a Virtual Environment

Here you will utilize `venv`, which is short for virtual environment, specific for your client.

1. **Create a Virtual Environment**  
    - In the root of the `whorl-server` repository, run the following command:

      ```bash
      python -m venv .venv
      ```

2. **Activate the Virtual Environment**  
    - Activate your virtual environment with the command:

      ```bash
      source .venv/bin/activate
      ```

## Development Install

Once your virtual environment is set up, perform a development install by running the following command:

```bash
python -m pip install -e .
```

## PostgreSQL Setup

1. **Install PostgreSQL**  
   - Make sure PostgreSQL is installed on your machine.  
   - If not installed, you can download it from [PostgreSQL Downloads](https://www.postgresql.org/download/) and follow the installation instructions for your operating system.

2. **Access the PostgreSQL Shell**  
   - Open a terminal and log into the PostgreSQL shell:  

     ```bash
     psql postgres
     ```

3. **Start the services**
    - Start the PostgreSQL service:

      ```bash
        brew services start postgresql
      ```

## Database Setup

1. **Create the Database**  
   - Run the following SQL command to create the `<database>` database:

     ```sql
     CREATE DATABASE "<database>";
     ```

2. **Create the User**
    - Run the following SQL command to create the user with password (reference the `.env file` for the password):

        ```sql
        CREATE USER 'user' WITH PASSWORD '<password>';
        ```

    PS: 'user' doesn't need quotes, but 'password' does.

3. **Grant User Permissions**  
   - Grant all privileges on the `<database>` database to the user:  

    ```sql
    GRANT ALL PRIVILEGES ON DATABASE "<database>" TO <user>;
    ```

4. **Verify Ownership**  
   - Use the `\l` command to list databases and check if user owns the `<database>` database.  
   - If not, update the owner with this command:

     ```sql
     ALTER DATABASE "<database>" OWNER TO <user>;
     ```

5. **Exit the PostgreSQL Shell**  
   - Type `\q` to exit.

## Test if client and server are connected

1. **Client Configuration**  
   - Open the `.env` file in the client directory.  
   - Set the `API_URL` to:  

     ```plaintext
     http://localhost
     ```

2. **Start the Server**  
   - Navigate to the server directory.

     ```bash
     cd src
     ```

   - Run the following command to start the server:

     ```bash
     python manage.py runserver
     ```

3. **Run the Client**  
   - In the client directory, run the command to see if output is displayed:

     ```bash
     climate
     ```


