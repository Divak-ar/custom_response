import json
import os
import streamlit as st

class ConfigHandler:
    """Handles loading and accessing configuration from Streamlit secrets or config.json"""
    
    @staticmethod
    def get_config():
        """
        Load configuration from Streamlit secrets or config.json file
        Returns a dictionary with email_config, contacts, and cc_list
        """
        # First try Streamlit secrets (works both locally and deployed)
        if hasattr(st, "secrets") and "email_config" in st.secrets:
            try:
                config = {
                    "email_config": dict(st.secrets["email_config"]),
                    "contacts": list(st.secrets["contacts"]) if "contacts" in st.secrets else [],
                    "cc_list": list(st.secrets["cc_list"]) if "cc_list" in st.secrets else []
                }
                return config
            except Exception as e:
                st.error(f"Error loading secrets: {e}")
                
                # Fallback to config.json if secrets failed
                if os.path.exists("config.json"):
                    try:
                        with open("config.json", "r") as f:
                            return json.load(f)
                    except Exception as e:
                        st.error(f"Error loading config.json: {e}")
                
                return None
    
    @staticmethod
    def get_email_config():
        """Get email configuration settings"""
        config = ConfigHandler.get_config()
        return config.get("email_config") if config else None
    
    @staticmethod
    def get_contacts():
        """Get list of contacts"""
        config = ConfigHandler.get_config()
        return config.get("contacts") if config else []
    
    @staticmethod
    def get_cc_list():
        """Get CC list"""
        config = ConfigHandler.get_config()
        return config.get("cc_list") if config else []