import logging
import datetime
from typing import Dict, Any
from langchain_community.vectorstores import Chroma
from features.master_copilot import generate_master_report_data

logger = logging.getLogger("uvicorn.error")

class PortfolioService:
    @staticmethod
    def generate_report(portfolio_str: str, db: Chroma) -> Dict[str, Any]:
        """Orchestrates the portfolio doctor, stock analyzers, macro analyzers, and realtime
        intelligence layers via the Master Copilot.
        
        Args:
            portfolio_str (str): The portfolio allocation string.
            db (Chroma): The loaded vector store database.
            
        Returns:
            Dict[str, Any]: A dictionary containing success status, report text, structured
                            data (holdings, sector_weights, health_score, hhi), and timestamp.
        """
        logger.info("PortfolioService.generate_report invoked.")
        timestamp = datetime.datetime.now().isoformat()
        
        data = generate_master_report_data(portfolio_str, db, logger)
        
        if not data["success"]:
            logger.error(f"Master Copilot execution failed: {data.get('error')}")
            return {
                "success": False,
                "report": f"An error occurred while compiling the report: {data.get('error')}",
                "timestamp": timestamp,
                "health_score": None,
                "holdings": None,
                "sector_weights": None,
                "hhi": None,
            }
            
        # Format and append combined source attribution to the report
        report_text = data["report"]
        
        sources_str = "\n\nSource Attribution:\n"
        sources_str += "1. Real-Time Market Data & Sectors: Yahoo Finance API\n"
        
        news_list = data.get("news", [])
        if news_list:
            sources_str += "2. News Sources:\n"
            for art in news_list[:6]:
                sources_str += f"   * {art['title']} (Published by {art['publisher']} on {art['date']})\n"
                
        rag_list = data.get("rag_sources", [])
        if rag_list:
            sources_str += "3. Historical Disclosures (RAG Annual Report):\n"
            for src in rag_list:
                sources_str += f"   * Page {src['page']} (from {src['filename']})\n"
                
        full_report = report_text + sources_str
        
        logger.info("PortfolioService.generate_report execution completed successfully.")
        return {
            "success": True,
            "report": full_report,
            "timestamp": timestamp,
            # Structured data for frontend dynamic panels
            "health_score": data.get("health_score"),
            "holdings": data.get("holdings"),
            "sector_weights": data.get("sector_weights"),
            "hhi": data.get("hhi"),
        }
