"""
LLM-based data extraction for invoice and purchase order processing.
Uses provider-agnostic configuration with structured output support.
"""

import json
import os
import ssl
from typing import Any, Optional
from pathlib import Path

from openai import OpenAI
import httpx
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from pydantic import ValidationError

from ..models import Invoice, PurchaseOrder, Item
from ...settings import settings
from ...logging_config import get_module_logger


class LLMExtractor:
    """Handles LLM-based extraction of invoice and purchase order data."""
    
    def __init__(self):
        """Initialize the LLM extractor with provider-agnostic configuration."""
        self.logger = get_module_logger('llm_extractor')
        
        # Get API configuration
        api_key = settings.llm_api_key
        base_url = settings.llm_base_url
        model = settings.llm_model
        
        if not api_key:
            raise ValueError("LLM API key not configured")
        
        # Clean API key
        api_key = api_key.strip()
        
        # Configure SSL settings
        self._configure_ssl_environment()
        
        # Create HTTP client with SSL configuration
        http_client = self._create_http_client()
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=settings.llm_timeout_sec,
            max_retries=settings.llm_max_retries,
            http_client=http_client
        )
        
        self.model = model
        self.base_url = base_url
        
        self.logger.info(f"LLM Extractor initialized with model: {model}")
        self.logger.info(f"Base URL: {base_url}")
        self.logger.info(f"API Key present: {'Yes' if api_key else 'No'}")
        self.logger.info(f"SSL Verification: {'Enabled' if settings.ssl_verify else 'Disabled'}")
        self.logger.info(f"Using certifi: {'Yes' if settings.use_certifi else 'No'}")
        
        if not settings.ssl_verify:
            self.logger.warning("⚠️ SSL verification is DISABLED - only use in corporate environments")
    
    def _configure_ssl_environment(self) -> None:
        """Configure SSL environment variables based on settings."""
        try:
            # Configure SSL certificate file using certifi (recommended approach)
            if settings.use_certifi and settings.ssl_verify:
                try:
                    import certifi
                    cert_file = certifi.where()
                    os.environ['SSL_CERT_FILE'] = cert_file
                    os.environ['REQUESTS_CA_BUNDLE'] = cert_file
                    os.environ['CURL_CA_BUNDLE'] = cert_file
                    self.logger.info(f"✅ Using certifi SSL certificates: {cert_file}")
                except ImportError:
                    self.logger.warning("⚠️ certifi package not available, using system certificates")
            
            # Use custom SSL certificate file if specified
            elif settings.ssl_cert_file and Path(settings.ssl_cert_file).exists():
                cert_file = settings.ssl_cert_file
                os.environ['SSL_CERT_FILE'] = cert_file
                os.environ['REQUESTS_CA_BUNDLE'] = cert_file
                os.environ['CURL_CA_BUNDLE'] = cert_file
                self.logger.info(f"✅ Using custom SSL certificate file: {cert_file}")
            
            # Disable SSL warnings if requested
            if settings.disable_ssl_warnings:
                urllib3.disable_warnings(InsecureRequestWarning)
                self.logger.info("SSL warnings disabled")
                
        except Exception as e:
            self.logger.warning(f"Failed to configure SSL environment: {e}")
    
    def _create_http_client(self) -> httpx.Client:
        """Create httpx client with appropriate SSL and proxy configuration."""
        # Base client configuration
        client_kwargs = {
            'timeout': httpx.Timeout(settings.llm_timeout_sec),
            'follow_redirects': True,
            'limits': httpx.Limits(max_keepalive_connections=5, max_connections=10)
        }
        
        # Configure SSL verification
        if not settings.ssl_verify:
            # Disable SSL verification for corporate networks
            client_kwargs['verify'] = False
            self.logger.info("🔓 SSL verification disabled for corporate network compatibility")
            
        elif settings.ssl_cert_file and Path(settings.ssl_cert_file).exists():
            # Use custom certificate file
            client_kwargs['verify'] = settings.ssl_cert_file
            self.logger.info(f"🔒 Using custom SSL certificate: {settings.ssl_cert_file}")
            
        elif settings.use_certifi:
            # Use certifi certificates (recommended)
            try:
                import certifi
                client_kwargs['verify'] = certifi.where()
                self.logger.info(f"🔒 Using certifi SSL certificates: {certifi.where()}")
            except ImportError:
                self.logger.warning("⚠️ certifi not available, using default SSL verification")
        
        # Configure proxy settings
        proxies = {}
        if settings.http_proxy:
            proxies['http://'] = settings.http_proxy
            self.logger.info(f"🌐 HTTP proxy configured: {settings.http_proxy}")
            
        if settings.https_proxy:
            proxies['https://'] = settings.https_proxy
            self.logger.info(f"🌐 HTTPS proxy configured: {settings.https_proxy}")
            
        if proxies:
            client_kwargs['proxies'] = proxies
        
        try:
            return httpx.Client(**client_kwargs)
        except Exception as e:
            self.logger.error(f"Failed to create HTTP client: {e}")
            # Fallback to basic client
            self.logger.info("Creating fallback HTTP client...")
            return httpx.Client(timeout=httpx.Timeout(settings.llm_timeout_sec))

    def extract_invoice_data(self, text: str) -> tuple[Optional[Invoice], Optional[PurchaseOrder]]:
        """Extract invoice and PO data using structured outputs with fallback"""
        self.logger.debug(f"Starting extraction for text length: {len(text)} characters")

        # DEBUG: Return empty results (for debugging only)
        # self.logger.debug(f"Returning empty results for debugging...")
        # return None, None

        # Get raw data from LLM
        raw_data = self._extract_raw_data(text)
        if not raw_data:
            return None, None
            
        # Convert to Pydantic models
        try:
            invoice_data = raw_data.get('invoice', {})
            po_data = raw_data.get('purchase_order', {})
            
            # Create Invoice object
            invoice = Invoice(**invoice_data)
            # Create PurchaseOrder object  
            purchase_order = PurchaseOrder(**po_data)

            # Check invoice items' shipped quantity
            for item in invoice.items:
                if item.quantity_shipped is None or item.quantity_shipped == 0:
                    # Fallback to ordered quantity
                    item.quantity_shipped = item.quantity_ordered

            self.logger.info(f"✅ Successfully created Invoice {invoice.invoice_number} and PO {purchase_order.po_number}")
            return invoice, purchase_order
            
        except ValidationError as e:
            self.logger.error(f"Failed to create Pydantic models: {str(e)}")
            return None, None

    def _extract_raw_data(self, text: str) -> Optional[dict[str, Any]]:

        system_prompt = """You are an expert at extracting structured invoice and purchase order data from merged PDF text.

        Extract invoice and PO information from the provided text. The text contain both an invoice and a purchase order. The invoice will always come first, and may consist of multiple pages, followed by the purchase order.

        For items in invoices: include both quantity_ordered and quantity_shipped (may be different for partial shipments)
        For items in purchase orders: only include quantity_ordered (quantity_shipped should not be included)
        
        Return valid JSON with the specified schema."""
        
        # Define the structured output schema
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "invoice_po_data",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "invoice": {
                            "type": "object",
                            "properties": {
                                "invoice_number": {"type": "string"},
                                "po_number": {"type": "string"},
                                "vendor": {
                                    "type": "string",
                                    "description": "The name of the vendor, e.g. Ingram, TD SYNNEX, Scansource..."
                                },
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "description": "This schema defines an item in the invoice. Sometimes, it is not an actual product but a fee (e.g., shipping fee)",
                                        "properties": {
                                            "sku": {
                                                "type": ["string", "null"],
                                                "description": "Stock Keeping Unit (SKU), an alphanumeric string, often a six-character long, e.g. \"Q96284\" or \"6YV960\". It usually stands alone in a separate line in front of the item description. If not found, try finding item number and consider it as SKU. Sometimes it may be mixed into the description, so make sure to extract only the SKU part."
                                            },
                                            "vpn": {
                                                "type": ["string", "null"],
                                                "description": "Vendor Part Number (VPN), an alphanumeric string with possible hyphens, e.g. \"D2CIM-DVUSB\". Sometimes it may be mixed into the description, so make sure to extract only the VPN part (no line-break)."
                                            },
                                            "is_fee": {
                                                "type": "boolean",
                                                "description": "Indicates if the item is a fee (e.g., shipping fee), false if it is a product."
                                            },
                                            "name": {
                                                "type": "string",
                                                "description": "Clean product/item name extracted from the description, without shipping info, addresses, contact details, or other metadata. Should be the core product name only, e.g. 'FOXIT PDF EDITOR' instead of the full description with shipping details."
                                            },
                                            "description": {
                                                "type": "string",
                                                "description": "Complete item description exactly as it appears in the document, including all details, shipping info, addresses, contact details, etc."
                                            },
                                            "unit_price": {
                                                "type": "number",
                                                "description": "Price per unit"
                                            },
                                            "quantity_ordered": {
                                                "type": "integer",
                                                "description": "Number of units ordered"
                                            },
                                            "quantity_shipped": {
                                                "type": "integer",
                                                "description": "Number of units shipped. If not explicitly provided, defaults to found quantity."
                                            },
                                            "total": {
                                                "type": "number", 
                                                "description": "Total price for the item"
                                            }
                                        },
                                        "required": ["name", "description", "unit_price", "quantity_ordered", "total"],
                                        "additionalProperties": False
                                    }
                                },
                                "extra_fees": {
                                    "type": "object",
                                    "additionalProperties": {"type": "number"}
                                },
                                "is_credit_memo": {"type": "boolean"}
                            },
                            "required": ["invoice_number", "po_number", "items"],
                            "additionalProperties": False
                        },
                        "purchase_order": {
                            "type": "object",
                            "properties": {
                                "po_number": {"type": "string"},
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "sku": {
                                                "type": ["string", "null"],
                                                "description": "Stock Keeping Unit (SKU), an alphanumeric string, often a six-character long, e.g. \"Q96284\" or \"6YV960\". It usually stands alone in a separate line in front of the item description. If not found, try finding item number and consider it as SKU. Sometimes it may be mixed into the description, so make sure to extract only the SKU part."
                                            },
                                            "vpn": {
                                                "type": ["string", "null"],
                                                "description": "Vendor Part Number (VPN), an alphanumeric string with possible hyphens, e.g. \"D2CIM-DVUSB\". Sometimes it may be mixed into the description, so make sure to extract only the VPN part (no line-break)."
                                            },
                                            "is_fee": {
                                                "type": "boolean",
                                                "description": "Indicates if the item is a fee (e.g., shipping fee), false if it is a product."
                                            },
                                            "name": {
                                                "type": "string",
                                                "description": "Clean product/item name extracted from the description, without shipping info, addresses, contact details, or other metadata. Should be the core product name only."
                                            },
                                            "description": {
                                                "type": "string",
                                                "description": "Complete item description exactly as it appears in the document, including all details."
                                            },
                                            "unit_price": {
                                                "type": "number",
                                                "description": "Unit price of the item."
                                            },
                                            "quantity_ordered": {
                                                "type": "integer",
                                                "description": "Quantity ordered."
                                            },
                                            "total": {
                                                "type": "number",
                                                "description": "Total price of the item."
                                            }
                                        },
                                        "required": ["name", "description", "unit_price", "quantity_ordered", "total"],
                                        "additionalProperties": False
                                    }
                                },
                                "extra_fees": {
                                    "type": "object",
                                    "additionalProperties": {"type": "number"}
                                }
                            },
                            "required": ["po_number", "items"],
                            "additionalProperties": False
                        }
                    },
                    "required": ["invoice", "purchase_order"],
                    "additionalProperties": False
                }
            }
        }
        
        try:
            # Try structured output first
            self.logger.debug("Attempting structured output extraction...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                response_format=response_format,
                temperature=0.0,
                max_tokens=4000
            )
            content = response.choices[0].message.content
            self.logger.debug(f"Structured output response length: {len(content)} characters")
            self.logger.debug(f"Raw structured response: {content[:100]}{'...' if len(content) > 100 else ''}")

            result = json.loads(content)
            self.logger.info("✅ Used structured output successfully")
            return result
            
        except Exception as e:
            # Log the exact error for debugging
            self.logger.warning(f"Structured output failed with error: {type(e).__name__}: {str(e)}")
            
            # Fallback to plain text with explicit JSON instruction
            self.logger.debug("Falling back to plain text mode...")
            
            fallback_prompt = system_prompt + "\n\n" + \
                "You MUST return a JSON object following this JSON Schema definition:\n" + \
                json.dumps(response_format["json_schema"]["schema"], indent=2) + "\n\n" + \
                "IMPORTANT NOTE: Return ONLY plain text of the JSON object, NO additional text or formatting."
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": fallback_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.0,
                    max_tokens=4096
                )
                
                content = response.choices[0].message.content
                self.logger.debug(f"Fallback response length: {len(content)} characters")
                self.logger.debug(f"Raw fallback response: {content[:100]}..." if len(content) > 100 else f"Raw fallback response: {content}")
                
                # Remove Markdown code block wrappers if present
                cleaned_content = self._clean_json_response(content)
                self.logger.debug(f"Cleaned response: {cleaned_content[:100]}{'...' if len(cleaned_content) > 100 else ''}")
                
                result = json.loads(cleaned_content)
                self.logger.info("✅ Used fallback plain text mode successfully")
                return result
                
            except Exception as e2:
                self.logger.error(f"Both structured output and fallback failed!")
                self.logger.error(f"Structured error: {type(e).__name__}: {str(e)}")
                self.logger.error(f"Fallback error: {type(e2).__name__}: {str(e2)}")
                
                # Enhanced error reporting for SSL and network issues
                self._handle_api_errors(e2)
                
                if 'content' in locals():
                    self.logger.error(f"Final response content: {content}")
                return None
    
    def _handle_api_errors(self, error: Exception) -> None:
        """Provide concise guidance for common API errors."""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Create a consolidated error message
        if "ssl" in error_str or "certificate" in error_str:
            self.logger.error(
                f"🔒 SSL Certificate Error ({error_type}): Corporate network detected. "
                f"Quick fix: Add 'SSL_VERIFY=false' and 'DISABLE_SSL_WARNINGS=true' to your .env file. "
                f"For proper fix, contact IT for corporate SSL certificates."
            )
            
        elif "connection" in error_str or "connect" in error_str:
            self.logger.error(
                f"🌐 Network Connection Error ({error_type}): Check firewall settings, "
                f"configure proxy if needed, or try different network (mobile hotspot)."
            )
            
        elif "timeout" in error_str:
            self.logger.error(
                f"⏰ Request Timeout ({error_type}): Increase LLM_TIMEOUT_SECONDS in .env "
                f"or check network stability."
            )
            
        elif "401" in error_str or "unauthorized" in error_str:
            self.logger.error(
                f"🔑 Authentication Failed ({error_type}): Verify API key is correct "
                f"and has sufficient credits."
            )
            
        elif "rate" in error_str and ("limit" in error_str or "429" in error_str):
            self.logger.error(
                f"📈 Rate Limit Exceeded ({error_type}): Wait and retry later, "
                f"or reduce processing frequency."
            )
        else:
            self.logger.error(f"❓ API Error ({error_type}): {error}")
        
        # Add a single help line
        self.logger.info("🔍 For detailed troubleshooting, check Settings → Network Configuration")

    def _clean_json_response(self, content: str) -> str:
        """Remove markdown code block wrappers and clean up response"""
        original_content = content
        content = content.strip()
        
        # Remove ```json wrapper
        if content.startswith("```json"):
            content = content[7:]
            self.logger.debug("Removed ```json wrapper")
        elif content.startswith("```"):
            content = content[3:]
            self.logger.debug("Removed ``` wrapper")
            
        # Remove ending ```
        if content.endswith("```"):
            content = content[:-3]
            self.logger.debug("Removed ending ``` wrapper")
            
        cleaned = content.strip()
        
        if cleaned != original_content:
            self.logger.debug(f"Content cleaning changed length from {len(original_content)} to {len(cleaned)}")
            
        return cleaned

    def test_structured_output_support(self) -> bool:
        """Test if the current model supports structured output"""
        self.logger.info("Testing structured output support...")
        
        test_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "test",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "test": {"type": "string"}
                    },
                    "required": ["test"],
                    "additionalProperties": False
                }
            }
        }
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Return a simple test JSON object with a 'test' field containing the value 'success'."},
                    {"role": "user", "content": "Please return test JSON."}
                ],
                response_format=test_schema,
                temperature=0.0,
                max_tokens=100
            )
            
            content = response.choices[0].message.content
            self.logger.debug(f"Structured test response: {content}")
            
            data = json.loads(content)
            supports_structured = "test" in data
            
            self.logger.info(f"Structured output test result: {supports_structured}")
            if supports_structured:
                self.logger.info(f"Test response data: {data}")
            
            return supports_structured
            
        except Exception as e:
            self.logger.warning(f"Structured output test failed: {type(e).__name__}: {str(e)}")
            return False
