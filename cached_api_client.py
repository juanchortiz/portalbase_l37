"""
Cached Base.gov.pt API Client with SQLite database

This client caches API results locally to avoid repeatedly fetching
all contracts from the API. It intelligently updates only new data.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from base_api_client import BaseAPIClient


class CachedBaseAPIClient:
    """
    Cached client for Base.gov.pt API that stores results in SQLite database.
    """
    
    def __init__(self, access_token: str, db_path: str = "base_cache.db"):
        """
        Initialize the cached API client.
        
        Args:
            access_token: Your API access token
            db_path: Path to SQLite database file
        """
        self.client = BaseAPIClient(access_token)
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with necessary tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create contracts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contracts (
                id_contrato TEXT PRIMARY KEY,
                data_publicacao TEXT,
                data_celebracao TEXT,
                ano TEXT,
                n_anuncio TEXT,
                objeto_contrato TEXT,
                preco_contratual TEXT,
                tipo_contrato TEXT,
                adjudicante TEXT,
                adjudicatarios TEXT,
                cpv TEXT,
                local_execucao TEXT,
                raw_data TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(id_contrato)
            )
        """)
        
        # Create announcements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                n_anuncio TEXT PRIMARY KEY,
                data_publicacao TEXT,
                ano TEXT,
                tipo_anuncio TEXT,
                nif_entidade TEXT,
                raw_data TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(n_anuncio)
            )
        """)
        
        # Create cache metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_metadata (
                year TEXT PRIMARY KEY,
                last_fetched TIMESTAMP,
                record_count INTEGER
            )
        """)
        
        # Create saved searches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                filters TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP
            )
        """)
        
        # Create index on publication dates for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_contract_pub_date 
            ON contracts(data_publicacao)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_announcement_pub_date 
            ON announcements(data_publicacao)
        """)
        
        conn.commit()
        conn.close()
    
    def _should_refresh_cache(self, year: str) -> bool:
        """
        Check if cache for a year should be refreshed.
        
        Uses date-based refresh logic: cache refreshes if last fetch was on
        a different calendar day, regardless of the time of day.
        
        Args:
            year: Year to check
            
        Returns:
            True if cache should be refreshed, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT last_fetched FROM cache_metadata WHERE year = ?",
            (year,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return True  # Never cached
        
        last_fetched = datetime.fromisoformat(result[0]).date()
        today = datetime.now().date()
        
        # Refresh if last fetch was on a different day
        return last_fetched < today
    
    def sync_year(self, year: str, force: bool = False):
        """
        Sync contracts and announcements for a specific year.
        
        Args:
            year: Year to sync (e.g., "2025")
            force: Force refresh even if cache is recent
        """
        if not force and not self._should_refresh_cache(year):
            print(f"Cache for {year} is up to date. Use force=True to refresh.")
            return
        
        print(f"Syncing data for year {year}...")
        
        # Fetch contracts
        try:
            contracts = self.client.search_contracts_by_year(year)
            self._store_contracts(contracts, year)
            print(f"✅ Synced {len(contracts)} contracts for {year}")
        except Exception as e:
            print(f"❌ Error syncing contracts: {e}")
        
        # Fetch announcements
        try:
            announcements = self.client.get_announcement_info(ano=year)
            if not isinstance(announcements, list):
                announcements = [announcements] if announcements else []
            self._store_announcements(announcements, year)
            print(f"✅ Synced {len(announcements)} announcements for {year}")
        except Exception as e:
            print(f"❌ Error syncing announcements: {e}")
    
    def _store_contracts(self, contracts: List[Dict[str, Any]], year: str):
        """Store contracts in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for contract in contracts:
            cursor.execute("""
                INSERT OR REPLACE INTO contracts 
                (id_contrato, data_publicacao, data_celebracao, ano, n_anuncio,
                 objeto_contrato, preco_contratual, tipo_contrato, adjudicante,
                 adjudicatarios, cpv, local_execucao, raw_data, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contract.get('idContrato'),
                contract.get('dataPublicacao'),
                contract.get('dataCelebracaoContrato'),
                contract.get('Ano'),
                contract.get('nAnuncio'),
                contract.get('objectoContrato'),
                contract.get('precoContratual'),
                json.dumps(contract.get('tipoContrato', [])),
                json.dumps(contract.get('adjudicante', [])),
                json.dumps(contract.get('adjudicatarios', [])),
                json.dumps(contract.get('cpv', [])),
                json.dumps(contract.get('localExecucao', [])),
                json.dumps(contract),
                datetime.now().isoformat()
            ))
        
        # Update metadata
        cursor.execute("""
            INSERT OR REPLACE INTO cache_metadata (year, last_fetched, record_count)
            VALUES (?, ?, ?)
        """, (year, datetime.now().isoformat(), len(contracts)))
        
        conn.commit()
        conn.close()
    
    def _store_announcements(self, announcements: List[Dict[str, Any]], year: str):
        """Store announcements in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for announcement in announcements:
            cursor.execute("""
                INSERT OR REPLACE INTO announcements 
                (n_anuncio, data_publicacao, ano, tipo_anuncio, nif_entidade, 
                 raw_data, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                announcement.get('nAnuncio'),
                announcement.get('dataPublicacao'),
                announcement.get('Ano'),
                announcement.get('TipoAnuncio'),
                announcement.get('nifEntidade'),
                json.dumps(announcement),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def get_contracts_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """
        Get all contracts published on a specific date.
        
        Args:
            date_str: Date in format "DD/MM/YYYY"
            
        Returns:
            List of contract dictionaries
        """
        # Extract year and ensure it's synced
        year = date_str.split("/")[2]
        if self._should_refresh_cache(year):
            self.sync_year(year)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT raw_data FROM contracts WHERE data_publicacao = ?",
            (date_str,)
        )
        results = cursor.fetchall()
        conn.close()
        
        return [json.loads(row[0]) for row in results]
    
    def get_announcements_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """
        Get all announcements published on a specific date.
        
        Args:
            date_str: Date in format "DD/MM/YYYY"
            
        Returns:
            List of announcement dictionaries
        """
        # Extract year and ensure it's synced
        year = date_str.split("/")[2]
        if self._should_refresh_cache(year):
            self.sync_year(year)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT raw_data FROM announcements WHERE data_publicacao = ?",
            (date_str,)
        )
        results = cursor.fetchall()
        conn.close()
        
        return [json.loads(row[0]) for row in results]
    
    def get_contracts_by_date_range(
        self, 
        start_date: str, 
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Get all contracts published within a date range.
        
        Args:
            start_date: Start date in format "DD/MM/YYYY"
            end_date: End date in format "DD/MM/YYYY"
            
        Returns:
            List of contract dictionaries
        """
        # Ensure relevant years are synced
        start_year = start_date.split("/")[2]
        end_year = end_date.split("/")[2]
        
        for year in range(int(start_year), int(end_year) + 1):
            if self._should_refresh_cache(str(year)):
                self.sync_year(str(year))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert DD/MM/YYYY to comparable format YYYY-MM-DD for proper date comparison
        def convert_date(date_str):
            """Convert DD/MM/YYYY to YYYY-MM-DD"""
            parts = date_str.split('/')
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
        
        start_comparable = convert_date(start_date)
        end_comparable = convert_date(end_date)
        
        # Get all contracts and filter by date
        cursor.execute("""
            SELECT raw_data, data_publicacao FROM contracts 
            WHERE data_publicacao LIKE ?
        """, (f"%/{start_year}",))
        
        results = []
        for row in cursor.fetchall():
            date_pub = row[1]
            if date_pub:
                comparable_date = convert_date(date_pub)
                if start_comparable <= comparable_date <= end_comparable:
                    results.append(row[0])
        
        conn.close()
        
        return [json.loads(data) for data in results]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cached data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM contracts")
        total_contracts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM announcements")
        total_announcements = cursor.fetchone()[0]
        
        cursor.execute("SELECT year, last_fetched, record_count FROM cache_metadata")
        years_cached = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_contracts": total_contracts,
            "total_announcements": total_announcements,
            "years_cached": [
                {
                    "year": year,
                    "last_fetched": last_fetched,
                    "record_count": count
                }
                for year, last_fetched, count in years_cached
            ]
        }
    
    def save_search(self, name: str, filters: Dict[str, Any]) -> bool:
        """
        Save a search with a name.
        
        Args:
            name: Name for the saved search
            filters: Dictionary of filter settings
            
        Returns:
            True if successful, False if name already exists
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO saved_searches (name, filters)
                VALUES (?, ?)
            """, (name, json.dumps(filters)))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Name already exists
            return False
    
    def get_saved_searches(self) -> List[Dict[str, Any]]:
        """
        Get all saved searches.
        
        Returns:
            List of saved searches with their metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, filters, created_at, last_used
            FROM saved_searches
            ORDER BY name
        """)
        
        searches = []
        for row in cursor.fetchall():
            searches.append({
                'id': row[0],
                'name': row[1],
                'filters': json.loads(row[2]),
                'created_at': row[3],
                'last_used': row[4]
            })
        
        conn.close()
        return searches
    
    def load_search(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a saved search by name.
        
        Args:
            name: Name of the saved search
            
        Returns:
            Dictionary of filters or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT filters FROM saved_searches
            WHERE name = ?
        """, (name,))
        
        result = cursor.fetchone()
        
        if result:
            # Update last_used timestamp
            cursor.execute("""
                UPDATE saved_searches
                SET last_used = CURRENT_TIMESTAMP
                WHERE name = ?
            """, (name,))
            conn.commit()
        
        conn.close()
        
        return json.loads(result[0]) if result else None
    
    def delete_search(self, name: str) -> bool:
        """
        Delete a saved search.
        
        Args:
            name: Name of the saved search to delete
            
        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM saved_searches
            WHERE name = ?
        """, (name,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted

