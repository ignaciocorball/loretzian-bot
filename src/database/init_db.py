import psycopg2
from psycopg2 import sql
import logging
from .config import DB_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database():
    """Create the trading bot database if it doesn't exist."""
    try:
        # Connect to the default postgres database to create our database
        conn = psycopg2.connect(
            dbname='postgres',
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port']
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (DB_CONFIG['dbname'],))
        exists = cur.fetchone()
        
        if not exists:
            # Create the database
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_CONFIG['dbname'])))
            logger.info(f"Database {DB_CONFIG['dbname']} created successfully")
        else:
            logger.info(f"Database {DB_CONFIG['dbname']} already exists")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise

def create_tables():
    """Create the required tables in the database."""
    try:
        # Connect to our database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Read and execute the schema file
        with open('src/database/schema.sql', 'r') as f:
            schema_sql = f.read()
            cur.execute(schema_sql)
            
        conn.commit()
        logger.info("Tables created successfully")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

def initialize_database():
    """Initialize the database and create all required tables."""
    try:
        create_database()
        create_tables()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    initialize_database() 