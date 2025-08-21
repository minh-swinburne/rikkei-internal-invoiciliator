"""
LLM-based data extraction for invoice and purchase order processing.
Uses provider-agnostic configuration with structured output support.
"""

import json
from typing import Any, Optional

from openai import OpenAI
from pydantic import ValidationError

from ..models import Invoice, PurchaseOrder, Item
from ...settings import settings
from ...logging_config import get_module_logger


class LLMExtractor:
    """Handles LLM-based extraction of invoice and purchase order data."""
    
    def __init__(self):
        """Initialize the LLM extractor with provider-agnostic configuration."""
        self.logger = get_module_logger('llm_extractor')
        
        # Use provider-agnostic settings
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url
        )
        self.model = settings.llm_model
        self.max_retries = settings.llm_max_retries
        self.timeout = settings.llm_timeout_sec
        
        self.logger.info(f"LLM Extractor initialized with model: {self.model}")
        self.logger.info(f"Base URL: {settings.llm_base_url}")
        self.logger.info(f"API Key present: {'Yes' if settings.llm_api_key else 'No'}")

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
                                                "description": "Stock Keeping Unit (SKU). If not found, try finding item number and consider it as SKU. Sometimes it may be mixed into the description."
                                            },
                                            "vpn": {
                                                "type": ["string", "null"],
                                                "description": "Vendor Part Number (VPN). Sometimes it may be mixed into the description."
                                            },
                                            "is_fee": {
                                                "type": "boolean",
                                                "description": "Indicates if the item is a fee (e.g., shipping fee), false if it is a product."
                                            },
                                            "description": {
                                                "type": "string",
                                                "description": "Item description."
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
                                        "required": ["description", "unit_price", "quantity_ordered", "total"],
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
                                                "description": "Stock Keeping Unit (SKU). If not found, try finding item number and consider it as SKU. Sometimes it may be mixed into the description."
                                            },
                                            "vpn": {
                                                "type": ["string", "null"],
                                                "description": "Vendor Part Number (VPN). Sometimes it may be mixed into the description."
                                            },
                                            "is_fee": {
                                                "type": "boolean",
                                                "description": "Indicates if the item is a fee (e.g., shipping fee), false if it is a product."
                                            },
                                            "description": {
                                                "type": "string",
                                                "description": "Description of the item."
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
                                        "required": ["description", "unit_price", "quantity_ordered", "total"],
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
            self.logger.debug(f"Raw structured response: {content[:500]}{'...' if len(content) > 500 else ''}")

            result = json.loads(content)
            self.logger.info("✅ Used structured output successfully")
            return result
            
        except Exception as e:
            # Log the exact error for debugging
            self.logger.warning(f"Structured output failed with error: {type(e).__name__}: {str(e)}")
            
            # Fallback to plain text with explicit JSON instruction
            self.logger.debug("Falling back to plain text mode...")
            
            fallback_prompt = system_prompt + "\n\n" + \
                "You MUST return a JSON object following this exact schema (with NO code block wrappers):\n" + \
                json.dumps(response_format["json_schema"]["schema"], indent=2) + "\n\n" + \
                "Return ONLY the JSON object, no additional text or formatting."
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": fallback_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.0,
                    max_tokens=4000
                )
                
                content = response.choices[0].message.content
                self.logger.debug(f"Fallback response length: {len(content)} characters")
                self.logger.debug(f"Raw fallback response: {content[:500]}..." if len(content) > 500 else f"Raw fallback response: {content}")
                
                # Remove Markdown code block wrappers if present
                cleaned_content = self._clean_json_response(content)
                self.logger.debug(f"Cleaned response: {cleaned_content[:500]}{'...' if len(cleaned_content) > 500 else ''}")
                
                result = json.loads(cleaned_content)
                self.logger.info("✅ Used fallback plain text mode successfully")
                return result
                
            except Exception as e2:
                self.logger.error(f"Both structured output and fallback failed!")
                self.logger.error(f"Structured error: {type(e).__name__}: {str(e)}")
                self.logger.error(f"Fallback error: {type(e2).__name__}: {str(e2)}")
                if 'content' in locals():
                    self.logger.error(f"Final response content: {content}")
                return None

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
