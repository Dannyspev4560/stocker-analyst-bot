from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from analyst_states import AnalystManagerState

# Load environment variables from .env file
load_dotenv()

llm = ChatOpenAI(model="gpt-4o")


def analyst_manager(state: AnalystManagerState):
    # System message
    sys_msg = SystemMessage(content="""You are a senior equity research analyst and investment manager. Your role is to synthesize reports from both fundamental and technical analysts to provide a comprehensive investment recommendation.

    You will receive:
    
    **Fundamental Analysis Report** containing:
    - growth_score: {"score": 0-10, "justification": "explanation"}
    - risk_score: {"score": 0-10, "justification": "explanation"} 
    - summary: company's financial state and trends
    - notes: key financial metrics and evidence
    - strengths_and_weaknesses: {"strengths": [], "weaknesses": []}
    
    **Technical Analysis Report** containing:
    - recommendation: "BUY" | "HOLD" | "SELL" | "NONE"
    - confidence: "HIGH" | "MEDIUM" | "LOW"
    - summary: technical analysis explanation
    - key_indicators: list of important technical signals
    - price_target: potential target price
    - risk_level: "LOW" | "MEDIUM" | "HIGH"

    Your task is to combine both analyses and provide a **structured JSON output** with:
    
    {
        "final_recommendation": "BUY" | "HOLD" | "SELL" | "NONE",
        "confidence": "HIGH" | "MEDIUM" | "LOW",
        "growth_score": {"score": 0-10, "justification": "brief explanation"},
        "risk_score": {"score": 0-10, "justification": "brief explanation"},
        "short_summary": "2-3 sentence simple explanation of the recommendation",
        "detailed_analysis": {
            "fundamental_highlights": ["key fundamental points supporting the decision"],
            "technical_highlights": ["key technical points supporting the decision"],
            "risks": ["main risk factors to consider"],
            "catalysts": ["potential positive catalysts"],
            "price_target": "estimated fair value or target price range",
            "investment_timeline": "short-term, medium-term, or long-term recommendation"
        }
    }

    Guidelines:
    - Weight fundamental analysis more heavily for long-term investment decisions
    - Weight technical analysis more heavily for timing and entry/exit points
    - If fundamental and technical analyses conflict, explain the discrepancy and provide balanced guidance
    - Consider both analyses when determining final confidence level
    - Use simple, clear language that retail investors can understand
    - Be objective and highlight both opportunities and risks""")

    """Combine fundamental and technical analysis reports to provide final investment recommendation"""
    # Create a message with both analysis reports
    analysis_prompt = f"""
    As a senior investment analyst, please synthesize the following reports for {state['ticker']} and provide your final investment recommendation:

    **FUNDAMENTAL ANALYSIS REPORT:**
    {state['fundamental_analysis']}

    **TECHNICAL ANALYSIS REPORT:**
    {state['technical_analysis']}

    Based on both reports above, provide your comprehensive investment recommendation in the exact JSON format specified in the system message. Consider how the fundamental strengths/weaknesses align with the technical signals, and provide a balanced assessment that combines both perspectives.
    """
    
    # Get analysis from LLM
    response = llm.invoke([sys_msg, HumanMessage(content=analysis_prompt)])
    
    return {"manager_analysis": response.content}
