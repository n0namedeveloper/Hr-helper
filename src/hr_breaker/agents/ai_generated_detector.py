from datetime import date

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from hr_breaker.agents.perplexity_client import create_perplexity_agent
from hr_breaker.config import get_settings, logger
from hr_breaker.models import FilterResult, OptimizedResume


class AIGeneratedResult(BaseModel):
    is_ai_generated: bool = Field(
        default=False,
        description="True if resume appears AI-generated"
    )
    ai_probability: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Probability that content is AI-generated (0-1)"
    )
    indicators: list[str] = Field(
        default_factory=list,
        description="Specific indicators of AI generation found",
    )
    
    model_config = {
        "extra": "ignore",  # Ignore extra fields from Perplexity
    }


SYSTEM_PROMPT = """You detect AI-generated content in resumes.

CRITICAL: Resumes are INTENTIONALLY formulaic. Every resume guide teaches:
- Action Verb + Task + Result pattern
- Consistent bullet structure and length
- Quantified metrics
- Industry keywords
This is GOOD resume writing, NOT AI tells.

=== NEVER FLAG (expected in professional resumes) ===
- Uniform bullet structure (Action Verb + Task + Metric)
- Consistent bullet lengths
- Action verbs: led, developed, managed, implemented, optimized
- Industry jargon and recent buzzwords (AI, ML, cloud, agile)
- Quantified achievements with ranges ("improved by 15-20%")
- Formal/professional tone throughout
- Perfect grammar and spelling
- Standard phrases: "responsible for", "collaborated with", "spearheaded"

=== FLAG ONLY (actual AI tells) ===
- FABRICATED/IMPOSSIBLE claims:
  - "5 years at [company founded 2 years ago]"
  - Metrics that don't make sense ("reduced latency by 500%")
  - Claimed seniority that contradicts timeline
- INTERNAL CONTRADICTIONS:
  - Different job titles for same role in different sections
  - Dates that overlap impossibly
- BUZZWORD SOUP with ZERO specifics:
  - "Leveraged synergies to drive paradigm shifts" (what did they actually DO?)
  - Multiple bullets with no concrete deliverables
- GENERIC FILLER repeated verbatim:
  - "Passionate about excellence" appearing 3+ times
  - Same vague phrase copy-pasted across roles
- HALLUCINATED DETAILS:
  - Technologies that didn't exist during claimed timeframe
  - Products/features the company never had

=== SCORING ===
ai_probability:
- 0.0-0.3 = Normal professional resume, no concerns
- 0.3-0.5 = Minor issues, possibly over-polished
- 0.5-0.7 = Multiple genuine AI tells found
- 0.7-1.0 = Clearly fabricated or AI-generated content

Set is_ai_generated=true ONLY if ai_probability > 0.5

When listing indicators, quote specific problematic text.
"""


def get_ai_generated_agent() -> Agent:
    settings = get_settings()
    
    # Include current date in system prompt
    today = date.today().strftime('%B %Y')
    full_prompt = f"{SYSTEM_PROMPT}\n\nToday's date: {today}"
    
    agent = create_perplexity_agent(
        model=settings.perplexity_flash_model,
        result_type=AIGeneratedResult,
        system_prompt=full_prompt,
    )
    
    return agent


async def detect_ai_generated(optimized: OptimizedResume) -> FilterResult:
    """Detect AI-generated content in optimized resume."""
    # Use pdf_text (extracted from rendered PDF) for analysis
    if optimized.pdf_text:
        content = optimized.pdf_text
    elif optimized.html:
        content = optimized.html
    elif optimized.data:
        content = optimized.data.model_dump_json(indent=2)
    else:
        content = "(no content)"

    prompt = f"""Analyze this resume text for signs of AI generation.

=== RESUME TEXT ===
{content}
=== END ===

Return a JSON object with:
- is_ai_generated: true/false - whether the resume appears AI-generated
- ai_probability: A number from 0.0 to 1.0 for the probability of AI generation
- indicators: A list of specific AI indicators found

Example JSON format:
{{"is_ai_generated": false, "ai_probability": 0.2, "indicators": []}}

IMPORTANT: Return ONLY the JSON object, no other text.
Remember: Professional resumes naturally use action verbs and consistent structure - this is NOT an AI tell."""

    agent = get_ai_generated_agent()
    try:
        result = await agent.run(prompt)
        r = result.output
    except Exception as e:
        # If parsing fails, return conservative default
        logger.warning(f"AI generation detection failed: {e}, using conservative default")
        return FilterResult(
            filter_name="AIGeneratedChecker",
            passed=True,  # Conservative: assume not AI-generated
            score=0.2,
            threshold=0.4,
            issues=["Could not parse AI response"],
            suggestions=["Retry or check AI response format"],
        )

    issues = []
    suggestions = []

    if r.indicators:
        # Each indicator is specific - list them individually for the optimizer
        for indicator in r.indicators:
            issues.append(f"AI giveaway: {indicator}")
        suggestions.append(
            "Fix AI tells: vary bullet lengths/structure, add specific details "
            "instead of generic claims, introduce minor style variations"
        )

    return FilterResult(
        filter_name="AIGeneratedChecker",
        passed=not r.is_ai_generated,
        score=1.0 - r.ai_probability,
        issues=issues,
        suggestions=suggestions,
    )
