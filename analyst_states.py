from langgraph.graph import MessagesState


class FundamentalAnalysisState(MessagesState):
    summary: str = ""
    growth_score: dict = {"score": 0, "justification": ""}
    risk_score: dict = {"score": 0, "justification": ""}
    notes: str = ""
    strengths_and_weaknesses: dict = {"strengths": [], "weaknesses": []}


class TechnicalAnalysisState(MessagesState):
    recommendation: str = ""
    confidence: str = ""
    summary: str = ""
    key_indicators: list[str] = []
    price_target: str = ""
    risk_level: str = ""


class AnalystManagerState(MessagesState):
    ticker: str = ""
    fundamental_analysis: str
    technical_analysis: str
    manager_analysis: str
