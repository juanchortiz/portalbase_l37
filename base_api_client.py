"""
Base.gov.pt API Client

A Python client for interacting with the Portuguese public procurement API.
Provides access to contracts, announcements, modifications, and entity data.
"""

import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode


class BaseAPIClient:
    """
    Client for the Base.gov.pt API REST.
    
    This client provides methods to query Portuguese public procurement data
    including contracts, announcements, contract modifications, and entities.
    """
    
    BASE_URL = "https://www.base.gov.pt/APIBase2"
    
    def __init__(self, access_token: str):
        """
        Initialize the Base API client.
        
        Args:
            access_token: Your API access token
        """
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            "_AcessToken": self.access_token
        })
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            ValueError: If no parameters are provided or response indicates error
            requests.exceptions.RequestException: For network/HTTP errors
        """
        if not params:
            raise ValueError("At least one parameter must be provided")
        
        # Remove None values from params
        clean_params = {k: v for k, v in params.items() if v is not None}
        
        if not clean_params:
            raise ValueError("At least one parameter must be provided")
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=clean_params)
            response.raise_for_status()
            
            # Check for API-specific errors in response
            data = response.json()
            
            # Handle error messages from API
            if isinstance(data, str):
                if "Error no Params submited" in data:
                    raise ValueError("Missing or invalid parameters")
                elif "The Token is required" in data:
                    raise ValueError("Missing access token")
                elif "Invalid Token" in data:
                    raise ValueError("Invalid access token")
                else:
                    raise ValueError(f"API Error: {data}")
            
            return data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 500:
                raise Exception("Internal server error") from e
            raise
    
    def get_contract_info(
        self,
        id_contrato: Optional[str] = None,
        id_procedimento: Optional[str] = None,
        nif_entidade: Optional[str] = None,
        n_anuncio: Optional[str] = None,
        ano: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve contract information.
        
        At least one parameter must be provided.
        
        Args:
            id_contrato: Contract ID
            id_procedimento: Procedure ID
            nif_entidade: Entity NIF (tax identification number)
            n_anuncio: Announcement number
            ano: Year
            
        Returns:
            Contract information dictionary
            
        Example:
            >>> client = BaseAPIClient("your_token")
            >>> contract = client.get_contract_info(id_contrato="12345")
        """
        params = {
            "idContrato": id_contrato,
            "IdProcedimento": id_procedimento,
            "nifEntidade": nif_entidade,
            "nAnuncio": n_anuncio,
            "Ano": ano
        }
        return self._make_request("GetInfoContrato", params)
    
    def get_announcement_info(
        self,
        n_anuncio: Optional[str] = None,
        nif_entidade: Optional[str] = None,
        id_incm: Optional[str] = None,
        ano: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve announcement information.
        
        At least one parameter must be provided.
        
        Args:
            n_anuncio: Announcement number
            nif_entidade: Entity NIF (tax identification number)
            id_incm: INCM ID
            ano: Year
            
        Returns:
            Announcement information dictionary
            
        Example:
            >>> client = BaseAPIClient("your_token")
            >>> announcement = client.get_announcement_info(n_anuncio="1234/2015")
        """
        params = {
            "nAnuncio": n_anuncio,
            "nifEntidade": nif_entidade,
            "IdIncm": id_incm,
            "Ano": ano
        }
        return self._make_request("GetInfoAnuncio", params)
    
    def get_contract_modification_info(
        self,
        id_contrato: Optional[str] = None,
        ano: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve contract modification information.
        
        At least one parameter must be provided.
        
        Args:
            id_contrato: Contract ID
            ano: Year
            
        Returns:
            Contract modification information dictionary
            
        Example:
            >>> client = BaseAPIClient("your_token")
            >>> modification = client.get_contract_modification_info(id_contrato="12345")
        """
        params = {
            "idContrato": id_contrato,
            "Ano": ano
        }
        return self._make_request("GetInfoModContrat", params)
    
    def get_entity_info(self, nif_entidade: str) -> Dict[str, Any]:
        """
        Retrieve entity information.
        
        Args:
            nif_entidade: Entity NIF (tax identification number)
            
        Returns:
            Entity information dictionary
            
        Example:
            >>> client = BaseAPIClient("your_token")
            >>> entity = client.get_entity_info(nif_entidade="654123987")
        """
        params = {
            "nifEntidade": nif_entidade
        }
        return self._make_request("GetInfoEntidades", params)
    
    def search_contracts_by_year(self, year: str) -> List[Dict[str, Any]]:
        """
        Search all contracts for a given year.
        
        Args:
            year: Year to search (e.g., "2015")
            
        Returns:
            List of contract dictionaries
            
        Example:
            >>> client = BaseAPIClient("your_token")
            >>> contracts_2015 = client.search_contracts_by_year("2015")
        """
        result = self.get_contract_info(ano=year)
        # Ensure result is a list
        return result if isinstance(result, list) else [result]
    
    def search_contracts_by_entity(self, nif: str, year: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search contracts for a specific entity.
        
        Args:
            nif: Entity NIF (tax identification number)
            year: Optional year filter
            
        Returns:
            List of contract dictionaries
            
        Example:
            >>> client = BaseAPIClient("your_token")
            >>> entity_contracts = client.search_contracts_by_entity("654123987", "2015")
        """
        result = self.get_contract_info(nif_entidade=nif, ano=year)
        return result if isinstance(result, list) else [result]
