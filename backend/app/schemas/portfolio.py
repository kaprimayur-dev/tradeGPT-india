from pydantic import BaseModel, Field

class PortfolioRequest(BaseModel):
    portfolio: str = Field(
        ...,
        description="Multi-line string containing stock symbols and their integer allocations (percentage or share count). E.g. 'TCS 60\\nInfosys 40'",
        examples=["TCS 60\nInfosys 40"]
    )

class PortfolioResponse(BaseModel):
    success: bool = Field(..., description="Indicates whether the orchestration succeeded.")
    report: str = Field(..., description="The unified master financial intelligence report.")
    timestamp: str = Field(..., description="ISO formatted timestamp of when the report was compiled.")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Detailed explanation of the error that occurred.")
