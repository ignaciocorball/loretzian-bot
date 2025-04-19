import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging
from typing import Optional, Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, dbname: str, user: str, password: str, host: str = "localhost", port: str = "5432"):
        """
        Initialize the database connection pool.
        
        Args:
            dbname: Database name
            user: Database user
            password: Database password
            host: Database host (default: localhost)
            port: Database port (default: 5432)
        """
        self.connection_pool = None
        try:
            self.connection_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Error creating database connection pool: {e}")
            raise

    def __del__(self):
        """Close the connection pool when the object is destroyed."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")

    def _get_connection(self):
        """Get a connection from the pool."""
        try:
            return self.connection_pool.getconn()
        except Exception as e:
            logger.error(f"Error getting connection from pool: {e}")
            raise

    def _release_connection(self, conn):
        """Release a connection back to the pool."""
        try:
            self.connection_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Error releasing connection to pool: {e}")
            raise

    def create_session(self, initial_balance: float) -> Optional[int]:
        """
        Create a new trading session.
        
        Args:
            initial_balance: Initial balance for the session
            
        Returns:
            session_id if successful, None otherwise
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sessions (start_time, initial_balance, status)
                    VALUES (%s, %s, %s)
                    RETURNING session_id
                """, (datetime.now(), initial_balance, 'active'))
                session_id = cur.fetchone()[0]
                conn.commit()
                logger.info(f"Created new trading session with ID: {session_id}")
                return session_id
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                self._release_connection(conn)

    def update_session(self, session_id: int, final_balance: Optional[float] = None,
                      profit_loss: Optional[float] = None, status: Optional[str] = None) -> bool:
        """
        Update a trading session.
        
        Args:
            session_id: ID of the session to update
            final_balance: New final balance
            profit_loss: New profit/loss value
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                updates = []
                params = []
                
                if final_balance is not None:
                    updates.append("final_balance = %s")
                    params.append(final_balance)
                
                if profit_loss is not None:
                    updates.append("profit_loss = %s")
                    params.append(profit_loss)
                
                if status is not None:
                    updates.append("status = %s")
                    params.append(status)
                
                if not updates:
                    return False
                
                query = f"""
                    UPDATE sessions
                    SET {', '.join(updates)}
                    WHERE session_id = %s
                """
                params.append(session_id)
                
                cur.execute(query, params)
                conn.commit()
                logger.info(f"Updated session {session_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self._release_connection(conn)

    def create_trade(self, session_id: int, symbol: str, trade_type: str, entry_price: float,
                    quantity: float, stop_loss: Optional[float] = None,
                    take_profit: Optional[float] = None) -> Optional[int]:
        """
        Create a new trade record.
        
        Args:
            session_id: ID of the session this trade belongs to
            symbol: Trading symbol
            trade_type: Type of trade (buy/sell)
            entry_price: Entry price
            quantity: Trade quantity
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            trade_id if successful, None otherwise
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO trades (
                        session_id, symbol, type, entry_price, quantity,
                        stop_loss, take_profit, entry_time, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING trade_id
                """, (
                    session_id, symbol, trade_type, entry_price, quantity,
                    stop_loss, take_profit, datetime.now(), 'open'
                ))
                trade_id = cur.fetchone()[0]
                conn.commit()
                logger.info(f"Created new trade with ID: {trade_id}")
                return trade_id
        except Exception as e:
            logger.error(f"Error creating trade: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                self._release_connection(conn)

    def update_trade(self, trade_id: int, exit_price: Optional[float] = None,
                    profit_loss: Optional[float] = None, status: Optional[str] = None) -> bool:
        """
        Update a trade record.
        
        Args:
            trade_id: ID of the trade to update
            exit_price: Exit price
            profit_loss: Profit/loss value
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                updates = []
                params = []
                
                if exit_price is not None:
                    updates.append("exit_price = %s")
                    params.append(exit_price)
                
                if profit_loss is not None:
                    updates.append("profit_loss = %s")
                    params.append(profit_loss)
                
                if status is not None:
                    updates.append("status = %s")
                    params.append(status)
                
                if not updates:
                    return False
                
                query = f"""
                    UPDATE trades
                    SET {', '.join(updates)}
                    WHERE trade_id = %s
                """
                params.append(trade_id)
                
                cur.execute(query, params)
                conn.commit()
                logger.info(f"Updated trade {trade_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating trade: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self._release_connection(conn)

    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active trading session.
        
        Returns:
            Session data if found, None otherwise
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM sessions
                    WHERE status = 'active'
                    ORDER BY start_time DESC
                    LIMIT 1
                """)
                return cur.fetchone()
        except Exception as e:
            logger.error(f"Error getting active session: {e}")
            return None
        finally:
            if conn:
                self._release_connection(conn)

    def get_session_trades(self, session_id: int) -> List[Dict[str, Any]]:
        """
        Get all trades for a specific session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of trades
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM trades
                    WHERE session_id = %s
                    ORDER BY entry_time
                """, (session_id,))
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting session trades: {e}")
            return []
        finally:
            if conn:
                self._release_connection(conn)

    def get_open_trades(self, session_id: int) -> List[Dict[str, Any]]:
        """
        Get all open trades for a specific session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of open trades
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM trades
                    WHERE session_id = %s AND status = 'open'
                    ORDER BY entry_time
                """, (session_id,))
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting open trades: {e}")
            return []
        finally:
            if conn:
                self._release_connection(conn) 