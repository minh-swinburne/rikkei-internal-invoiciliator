import os
import json
import logging
from typing import Any
from openai import OpenAI
from .models import Invoice, PurchaseOrder, Item

logger = logging.getLogger(__name__)

class LLMExtractor:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        logger.info(f"LLM Extractor initialized with model: {self.model}")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"API Key present: {'Yes' if self.api_key else 'No'}")

    def extract_invoice_data(self, text: str) -> dict[str, Any] | None:
        """Extract invoice and PO data using structured outputs with fallback"""
        logger.debug(f"Starting extraction for text length: {len(text)} characters")
        
        system_prompt = """You are an expert at extracting structured invoice and purchase order data from merged PDF text.
        
        Extract invoice and PO information from the provided text. The text may contain both an invoice and a purchase order.
        
        For items in invoices: include both quantity_ordered and quantity_shipped (may be different for partial shipments)
        For items in purchase orders: only include quantity_ordered (quantity_shipped should be null)
        
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
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "sku": {"type": ["string", "null"]},
                                            "vpn": {"type": ["string", "null"]},
                                            "description": {"type": "string"},
                                            "unit_price": {"type": "number"},
                                            "quantity_ordered": {"type": "integer"},
                                            "quantity_shipped": {"type": ["integer", "null"]},
                                            "total": {"type": "number"}
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
                                            "sku": {"type": ["string", "null"]},
                                            "vpn": {"type": ["string", "null"]},
                                            "description": {"type": "string"},
                                            "unit_price": {"type": "number"},
                                            "quantity_ordered": {"type": "integer"},
                                            "quantity_shipped": {"type": ["integer", "null"]},
                                            "total": {"type": "number"}
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
            logger.debug("Attempting structured output extraction...")
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
            logger.debug(f"Structured output response length: {len(content)} characters")
            logger.debug(f"Raw structured response: {content[:500]}..." if len(content) > 500 else f"Raw structured response: {content}")
            
            result = json.loads(content)
            logger.info("✅ Used structured output successfully")
            return result
            
        except Exception as e:
            # Log the exact error for debugging
            logger.warning(f"Structured output failed with error: {type(e).__name__}: {str(e)}")
            
            # Fallback to plain text with explicit JSON instruction
            logger.debug("Falling back to plain text mode...")
            
            fallback_prompt = system_prompt + "\n\n" + \
                "You MUST return a JSON object following this exact schema (with NO code block wrappers like ```json):\n" + \
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
                logger.debug(f"Fallback response length: {len(content)} characters")
                logger.debug(f"Raw fallback response: {content[:500]}..." if len(content) > 500 else f"Raw fallback response: {content}")
                
                # Remove Markdown code block wrappers if present
                cleaned_content = self._clean_json_response(content)
                logger.debug(f"Cleaned response: {cleaned_content[:500]}..." if len(cleaned_content) > 500 else f"Cleaned response: {cleaned_content}")
                
                result = json.loads(cleaned_content)
                logger.info("✅ Used fallback plain text mode successfully")
                return result
                
            except Exception as e2:
                logger.error(f"Both structured output and fallback failed!")
                logger.error(f"Structured error: {type(e).__name__}: {str(e)}")
                logger.error(f"Fallback error: {type(e2).__name__}: {str(e2)}")
                if 'content' in locals():
                    logger.error(f"Final response content: {content}")
                return None

    def _clean_json_response(self, content: str) -> str:
        """Remove markdown code block wrappers and clean up response"""
        original_content = content
        content = content.strip()
        
        # Remove ```json wrapper
        if content.startswith("```json"):
            content = content[7:]
            logger.debug("Removed ```json wrapper")
        elif content.startswith("```"):
            content = content[3:]
            logger.debug("Removed ``` wrapper")
            
        # Remove ending ```
        if content.endswith("```"):
            content = content[:-3]
            logger.debug("Removed ending ``` wrapper")
            
        cleaned = content.strip()
        
        if cleaned != original_content:
            logger.debug(f"Content cleaning changed length from {len(original_content)} to {len(cleaned)}")
            
        return cleaned

    def test_structured_output_support(self) -> bool:
        """Test if the current model supports structured output"""
        logger.info("Testing structured output support...")
        
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
            logger.debug(f"Structured test response: {content}")
            
            data = json.loads(content)
            supports_structured = "test" in data
            
            logger.info(f"Structured output test result: {supports_structured}")
            if supports_structured:
                logger.info(f"Test response data: {data}")
            
            return supports_structured
            
        except Exception as e:
            logger.warning(f"Structured output test failed: {type(e).__name__}: {str(e)}")
            return False

    def extract_invoice_data(self, text: str) -> dict[str, Any] | None:
        """Extract invoice and PO data using structured outputs with fallback"""
        system_prompt = """You are an expert at extracting structured invoice and purchase order data from merged PDF text.
        
        Extract invoice and PO information from the provided text. The text may contain both an invoice and a purchase order.
        
        For items in invoices: include both quantity_ordered and quantity_shipped (may be different for partial shipments)
        For items in purchase orders: only include quantity_ordered (quantity_shipped should be null)
        
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
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "sku": {"type": ["string", "null"]},
                                            "vpn": {"type": ["string", "null"]},
                                            "description": {"type": "string"},
                                            "unit_price": {"type": "number"},
                                            "quantity_ordered": {"type": "integer"},
                                            "quantity_shipped": {"type": ["integer", "null"]},
                                            "total": {"type": "number"}
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
                                            "sku": {"type": ["string", "null"]},
                                            "vpn": {"type": ["string", "null"]},
                                            "description": {"type": "string"},
                                            "unit_price": {"type": "number"},
                                            "quantity_ordered": {"type": "integer"},
                                            "quantity_shipped": {"type": ["integer", "null"]},
                                            "total": {"type": "number"}
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
            logger.info("Used structured output successfully")
            return json.loads(content)
            
        except Exception as e:
            # Fallback to plain text with explicit JSON instruction
            logger.warning(f"Structured output failed, falling back to plain text: {e}")
            
            fallback_prompt = system_prompt + "\n\n" + \
                "You MUST return a JSON object following this exact schema (with NO code block wrappers like ```json):\n" + \
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
                
                # Remove Markdown code block wrappers if present
                content = self._clean_json_response(content)
                
                logger.info("Used fallback plain text mode")
                return json.loads(content)
                
            except Exception as e2:
                logger.error(f"Both structured output and fallback failed: {e2}")
                return None

    def _clean_json_response(self, content: str) -> str:
        """Remove markdown code block wrappers and clean up response"""
        content = content.strip()
        
        # Remove ```json wrapper
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
            
        # Remove ending ```
        if content.endswith("```"):
            content = content[:-3]
            
        return content.strip()

    def test_structured_output_support(self) -> bool:
        """Test if the current model supports structured output"""
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
                    {"role": "system", "content": "Return a simple test JSON object with a 'test' field."},
                    {"role": "user", "content": "Please return test JSON."}
                ],
                response_format=test_schema,
                temperature=0.0,
                max_tokens=100
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            return "test" in data
            
        except Exception as e:
            logger.info(f"Model does not support structured output: {e}")
            return False
