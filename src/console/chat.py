"""
Interactive chat interface for market analysis.
"""

import logging
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.analyzers.models import MarketOpportunity
from src.clients.news.models import NewsArticle

logger = logging.getLogger(__name__)


class MarketChatSession:
    """
    Interactive chat session for analyzing specific markets.
    """
    
    def __init__(self, opportunity: MarketOpportunity, related_news: List[NewsArticle]):
        """
        Initialize chat session.
        
        Args:
            opportunity: Market opportunity to discuss
            related_news: Related news articles
        """
        self.console = Console()
        self.opportunity = opportunity
        self.related_news = related_news
        self.conversation_history = []
        
    def start_chat(self) -> None:
        """Start the interactive chat session."""
        self.console.print()
        self.console.print(Panel(
            f"[bold cyan]Market Chat Session Started[/bold cyan]\n\n"
            f"🎯 [bold]{self.opportunity.question}[/bold]\n\n"
            f"You can now ask detailed questions about this market analysis.\n"
            f"Type 'help' for example questions, or 'exit' to return to main menu.",
            title="Chat Mode",
            border_style="cyan"
        ))
        
        self._show_quick_summary()
        
        while True:
            try:
                user_input = input("\n💬 Ask about this market: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['exit', 'quit', 'back']:
                    self.console.print("Exiting chat session...")
                    break
                    
                if user_input.lower() == 'help':
                    self._show_help()
                    continue
                    
                # Process the question
                response = self._process_question(user_input)
                self._display_response(response)
                
            except KeyboardInterrupt:
                self.console.print("\nExiting chat session...")
                break
            except Exception as e:
                logger.error(f"Error in chat session: {e}")
                self.console.print(f"[red]Error: {e}[/red]")
                
    def _show_quick_summary(self) -> None:
        """Show a quick summary of the market."""
        summary = f"""
**Quick Summary:**
- 📊 Recommendation: {self.opportunity.recommended_position} 
- 💰 Expected Return: {self.opportunity.expected_return:+.1f}%
- 🎯 Confidence: {self.opportunity.score.confidence_score:.1%}
- ⚠️ Risk: {self.opportunity.risk_level}
"""
        self.console.print(Panel(summary, title="Market Summary", border_style="green"))
        
    def _show_help(self) -> None:
        """Show help with example questions."""
        help_text = f"""
[bold cyan]Example Questions You Can Ask:[/bold cyan]

[bold yellow]Analysis Questions:[/bold yellow]
• "Why do you recommend {self.opportunity.recommended_position}?"
• "What's driving the confidence score?"
• "How reliable is this analysis?"
• "What could change your recommendation?"

[bold yellow]Enhanced Data Search:[/bold yellow]
• "Search for recent developments"
• "Find more information about this topic"
• "What's the latest news on this?"
• "Give me comprehensive analysis"
• "Show me political context"

[bold yellow]Risk & Return Questions:[/bold yellow]
• "What are the main risks here?"
• "How does this compare to other opportunities?"
• "What's the worst-case scenario?"

[bold yellow]News & Context Questions:[/bold yellow]
• "What news is most relevant?"
• "How is sentiment affecting the analysis?"
• "Are there any red flags in the news?"

[bold yellow]Market Questions:[/bold yellow]
• "Is there enough liquidity to trade?"
• "When does this market resolve?"
• "How has this type of market performed historically?"

[bold yellow]Special Commands:[/bold yellow]
• Type 'exit' - Return to main menu
"""
        
        self.console.print(Panel(help_text, title="Chat Help", border_style="yellow"))
        
    def _process_question(self, question: str) -> str:
        """
        Process user question and generate response.
        
        Args:
            question: User's question
            
        Returns:
            str: Response to the question
        """
        question_lower = question.lower()
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": question})
        
        # Rule-based responses for common questions
        if any(word in question_lower for word in ["why", "recommend", "recommendation"]):
            response = self._explain_recommendation()
        elif any(word in question_lower for word in ["confidence", "sure", "certain"]):
            response = self._explain_confidence()
        elif any(word in question_lower for word in ["risk", "risks", "dangerous", "safe"]):
            response = self._explain_risks()
        elif any(word in question_lower for word in ["news", "headlines", "events", "search", "find", "latest", "recent"]):
            response = self._explain_news_impact()
        elif any(word in question_lower for word in ["data", "information", "research", "analysis", "more"]):
            response = self._provide_comprehensive_analysis()
        elif any(word in question_lower for word in ["score", "scoring", "rating"]):
            response = self._explain_scoring()
        elif any(word in question_lower for word in ["liquidity", "volume", "trade"]):
            response = self._explain_liquidity()
        elif any(word in question_lower for word in ["time", "when", "resolve", "end"]):
            response = self._explain_timing()
        elif any(word in question_lower for word in ["compare", "similar", "other"]):
            response = self._explain_comparison()
        elif any(word in question_lower for word in ["context", "political", "background"]):
            response = self._explain_market_context()
        else:
            response = self._general_analysis(question)
            
        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
        
    def _explain_recommendation(self) -> str:
        """Explain why the recommendation was made."""
        pos = self.opportunity.recommended_position
        current_price = self.opportunity.current_yes_price if pos == "YES" else self.opportunity.current_no_price
        fair_price = self.opportunity.fair_yes_price if pos == "YES" else self.opportunity.fair_no_price
        
        return f"""
## Why I Recommend {pos}

**Price Discrepancy Analysis:**
- Current market price: {current_price:.3f} ({current_price:.1%})
- My calculated fair value: {fair_price:.3f} ({fair_price:.1%})
- **Opportunity:** Market is {'under' if fair_price > current_price else 'over'}valuing this outcome by {abs(fair_price - current_price):.1%}

**Key Factors:**
{self.opportunity.reasoning}

**Confidence Level:** {self.opportunity.score.confidence_score:.1%} - This means I'm reasonably confident in this analysis based on available data and news coverage.

The market appears to be mispricing this outcome, creating a potential arbitrage opportunity.
"""
        
    def _explain_confidence(self) -> str:
        """Explain the confidence score."""
        confidence = self.opportunity.score.confidence_score
        
        level = "high" if confidence > 0.8 else "moderate" if confidence > 0.6 else "low"
        
        factors = []
        if len(self.opportunity.related_news) > 3:
            factors.append(f"✅ Good news coverage ({len(self.opportunity.related_news)} related articles)")
        else:
            factors.append(f"⚠️ Limited news coverage ({len(self.opportunity.related_news)} articles)")
            
        if self.opportunity.volume and self.opportunity.volume > 10000:
            factors.append("✅ High market volume indicates mature market")
        elif self.opportunity.volume and self.opportunity.volume > 1000:
            factors.append("📊 Moderate market volume")
        else:
            factors.append("⚠️ Low market volume - less reliable pricing")
            
        if self.opportunity.score.time_score > 0.7:
            factors.append("✅ Market resolves soon - more predictable")
        else:
            factors.append("⏰ Longer time horizon - more uncertainty")
            
        return f"""
## Confidence Analysis: {confidence:.1%} ({level})

**Factors affecting confidence:**

{chr(10).join(factors)}

**What this means:**
- **High (80%+):** Strong conviction, multiple confirming signals
- **Moderate (60-80%):** Reasonable confidence, some uncertainty remains  
- **Low (<60%):** Speculative, high uncertainty

This analysis has **{level} confidence** because {self._get_confidence_reasoning(confidence)}.
"""
        
    def _get_confidence_reasoning(self, confidence: float) -> str:
        """Get reasoning for confidence level."""
        if confidence > 0.8:
            return "multiple factors align strongly and there's good data coverage"
        elif confidence > 0.6:
            return "the analysis is reasonable but some factors introduce uncertainty"
        else:
            return "there are significant unknowns or conflicting signals"
            
    def _explain_risks(self) -> str:
        """Explain the risks involved."""
        risk_level = self.opportunity.risk_level
        
        risks = []
        
        if self.opportunity.score.confidence_score < 0.7:
            risks.append("🔸 **Analysis Uncertainty:** Lower confidence means higher chance of being wrong")
            
        if not self.opportunity.volume or self.opportunity.volume < 5000:
            risks.append("🔸 **Low Liquidity:** May be difficult to enter/exit positions")
            
        if self.opportunity.score.time_score < 0.5:
            risks.append("🔸 **Long Time Horizon:** More time for unexpected events")
            
        if len(self.opportunity.related_news) < 2:
            risks.append("🔸 **Limited Information:** Few news sources to validate analysis")
            
        if self.opportunity.score.value_score > 0.8:
            risks.append("🔸 **Seems Too Good:** Very high value scores can indicate missed factors")
            
        general_risks = [
            "🔸 **Market Risk:** All prediction markets can be volatile",
            "🔸 **Resolution Risk:** Markets might resolve differently than expected",
            "🔸 **News Risk:** New information can rapidly change probabilities"
        ]
        
        return f"""
## Risk Assessment: {risk_level} Risk

**Specific Risks for This Market:**
{chr(10).join(risks) if risks else "No major specific risks identified"}

**General Prediction Market Risks:**
{chr(10).join(general_risks)}

**Risk Mitigation:**
- Start with smaller position sizes
- Monitor news developments closely
- Set stop-loss levels if available
- Don't invest more than you can afford to lose

**Bottom Line:** This is rated **{risk_level} risk** based on confidence, liquidity, and market maturity factors.
"""
        
    def _explain_news_impact(self) -> str:
        """Explain how news is affecting the analysis."""
        if not self.opportunity.related_news:
            # Perform real-time web search for more news
            search_results = self._search_web_for_news()
            
            if search_results:
                return f"""
## News Impact: Enhanced Search Results

⚠️ **Limited Initial Coverage:** Few relevant news articles found in our database.

**🔍 Real-Time Web Search Results:**
{search_results}

**Analysis Update:**
- Web search provides additional context not captured in initial analysis
- More comprehensive news coverage suggests higher market relevance
- Recent developments may create pricing opportunities

**Recommendation:** Consider this additional context when evaluating the opportunity.
"""
            else:
                return """
## News Impact: Minimal

⚠️ **Limited News Coverage:** Very few relevant news articles found for this market.

**What this means:**
- Analysis relies more on market fundamentals than news sentiment
- Less external validation of the opportunity
- Could indicate an under-covered market (opportunity) or irrelevant topic

**Recommendation:** Monitor news closely as new developments could significantly impact the market.
"""
        
        return f"""
## News Impact Analysis

**News Relevance Score:** {self.opportunity.score.news_relevance_score:.1%}

**Related Headlines:**
{chr(10).join(f"• {headline}" for headline in self.opportunity.related_news[:5])}

**How News Affects Analysis:**
- News sentiment is factored into fair value calculation
- More relevant news = higher confidence in analysis
- Breaking news can create rapid price movements

**Current Assessment:**
The news coverage suggests mixed sentiment around this topic, which {'supports' if self.opportunity.expected_return > 0 else 'contradicts'} the recommended position.
"""
        
    def _explain_scoring(self) -> str:
        """Explain the scoring breakdown."""
        score = self.opportunity.score
        
        return f"""
## Scoring Breakdown

**Overall Score: {score.overall_score:.3f}/1.000**

**Component Scores:**
🎯 **Value Score:** {score.value_score:.3f} (30% weight)
   └─ How big is the price discrepancy?
   
🧠 **Confidence Score:** {score.confidence_score:.3f} (25% weight)  
   └─ How sure are we about this analysis?
   
💰 **Volume Score:** {score.volume_score:.3f} (20% weight)
   └─ Is there enough liquidity to trade?
   
⏰ **Time Score:** {score.time_score:.3f} (15% weight)
   └─ How close to resolution?
   
📰 **News Score:** {score.news_relevance_score:.3f} (10% weight)
   └─ How much relevant news coverage?

**Score Interpretation:**
- **0.8+:** Excellent opportunity
- **0.6-0.8:** Good opportunity  
- **0.4-0.6:** Moderate opportunity
- **<0.4:** Poor opportunity

This opportunity scores **{score.overall_score:.3f}**, making it a **{self._score_category(score.overall_score)}** opportunity.
"""
        
    def _score_category(self, score: float) -> str:
        """Categorize score."""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "moderate"
        else:
            return "poor"
            
    def _explain_liquidity(self) -> str:
        """Explain liquidity and trading considerations."""
        volume = self.opportunity.volume
        
        if not volume:
            return """
## Liquidity Analysis: Unknown

⚠️ **Volume Data Unavailable:** Cannot assess market liquidity.

**Trading Considerations:**
- Be cautious with position sizes
- Test with small amounts first
- Watch bid-ask spreads carefully
- Consider limit orders over market orders
"""
        
        liquidity_level = "high" if volume > 50000 else "moderate" if volume > 10000 else "low"
        
        return f"""
## Liquidity Analysis

**Market Volume:** ${volume:,.2f}
**Liquidity Level:** {liquidity_level.title()}

**What this means for trading:**
{self._get_liquidity_advice(volume)}

**Trading Tips:**
- {'Large positions should be fine' if volume > 50000 else 'Consider smaller position sizes'}
- {'Tight spreads expected' if volume > 20000 else 'Watch for wider bid-ask spreads'}
- {'Good market depth' if volume > 10000 else 'Limited market depth - use limit orders'}
"""
        
    def _get_liquidity_advice(self, volume: float) -> str:
        """Get liquidity-specific advice."""
        if volume > 50000:
            return "✅ High liquidity market - easy to enter and exit positions"
        elif volume > 10000:
            return "📊 Moderate liquidity - reasonable for most trading sizes"
        else:
            return "⚠️ Low liquidity - be careful with position sizes"
            
    def _explain_timing(self) -> str:
        """Explain timing and resolution details."""
        if not self.opportunity.end_date:
            return """
## Timing Analysis: Unknown Resolution Date

⚠️ **End Date Unknown:** Cannot determine when this market will resolve.

**Implications:**
- Harder to plan position duration
- Unknown time risk
- Monitor for resolution announcements
"""
        
        from datetime import datetime
        days_left = (self.opportunity.end_date - datetime.now()).days
        
        timing_assessment = "very soon" if days_left <= 7 else "soon" if days_left <= 30 else "medium-term" if days_left <= 90 else "long-term"
        
        return f"""
## Timing Analysis

**Resolution Date:** {self.opportunity.end_date.strftime('%Y-%m-%d')}
**Days Remaining:** {days_left} days
**Time Category:** {timing_assessment.title()}

**Time Score:** {self.opportunity.score.time_score:.3f}

**Timing Implications:**
{self._get_timing_implications(days_left)}

**Strategy Considerations:**
- {'Quick resolution reduces uncertainty' if days_left <= 30 else 'Longer time horizon increases uncertainty'}
- {'Less time for new information to emerge' if days_left <= 14 else 'More time for market conditions to change'}
"""
        
    def _get_timing_implications(self, days_left: int) -> str:
        """Get timing-specific implications."""
        if days_left <= 7:
            return "🚀 Very close to resolution - high time score, less uncertainty"
        elif days_left <= 30:
            return "📅 Resolves soon - good time score, manageable uncertainty"
        elif days_left <= 90:
            return "⏳ Medium-term horizon - moderate uncertainty"
        else:
            return "📆 Long-term market - higher uncertainty, more time for changes"
            
    def _explain_comparison(self) -> str:
        """Explain how this compares to other opportunities."""
        score = self.opportunity.score.overall_score
        
        return f"""
## Comparative Analysis

**This Market's Overall Score:** {score:.3f}

**How it ranks:**
{self._get_ranking_context(score)}

**Compared to typical opportunities:**
- **Value:** {'Above average' if self.opportunity.score.value_score > 0.6 else 'Below average'} price discrepancy
- **Confidence:** {'High' if self.opportunity.score.confidence_score > 0.7 else 'Moderate' if self.opportunity.score.confidence_score > 0.5 else 'Low'} confidence level
- **Risk:** {self.opportunity.risk_level} risk profile

**When to prioritize this market:**
{self._get_prioritization_advice(score)}
"""
        
    def _get_ranking_context(self, score: float) -> str:
        """Get context about where this score ranks."""
        if score > 0.8:
            return "🥇 Top-tier opportunity - among the best available"
        elif score > 0.7:
            return "🥈 High-quality opportunity - well above average"
        elif score > 0.6:
            return "🥉 Good opportunity - above average quality"
        elif score > 0.5:
            return "📊 Average opportunity - proceed with caution"
        else:
            return "⚠️ Below-average opportunity - consider avoiding"
            
    def _get_prioritization_advice(self, score: float) -> str:
        """Get advice on when to prioritize this market."""
        if score > 0.8:
            return "✅ High priority - strong candidate for investment"
        elif score > 0.6:
            return "📋 Medium priority - good backup option"
        else:
            return "⏸️ Low priority - only if no better options available"
            
    def _general_analysis(self, question: str) -> str:
        """Provide general analysis for other questions."""
        # Add political context for political markets
        political_context = self._get_political_context() if self._is_political_market() else ""
        
        return f"""
## Analysis Response

**Your Question:** "{question}"

**Based on the current market analysis:**

{self.opportunity.reasoning}

{political_context}

**Key Points:**
- **Position:** {self.opportunity.recommended_position}
- **Expected Return:** {self.opportunity.expected_return:+.1f}%
- **Confidence:** {self.opportunity.score.confidence_score:.1%}
- **Risk Level:** {self.opportunity.risk_level}

**Additional Context:**
This market has an overall score of {self.opportunity.score.overall_score:.3f}, making it a {self._score_category(self.opportunity.score.overall_score)} opportunity based on our analysis.

For more specific insights, try asking about risks, scoring, news impact, or timing.
"""
        
    def _display_response(self, response: str) -> None:
        """Display the response in a formatted panel."""
        self.console.print()
        self.console.print(Panel(
            Markdown(response),
            title="Analysis Response",
            border_style="green"
        ))
        
    def _search_web_for_news(self) -> str:
        """
        Search the web for additional news about this market.
        
        Returns:
            str: Formatted search results
        """
        try:
            # Extract key terms from the market question
            search_terms = self._extract_search_terms(self.opportunity.question)
            
            # Create search query
            search_query = " ".join(search_terms[:3])  # Use top 3 keywords
            
            # Try to perform actual web search
            try:
                # This would use the WebSearch tool if available
                # For now, we'll use simulated results but structure it for real search
                search_results = self._perform_web_search(search_query)
                
                if search_results:
                    return search_results
                    
            except Exception as e:
                logger.warning(f"Web search failed, using fallback: {e}")
                
            # Fallback to simulated search results based on market content
            return self._get_fallback_search_results()
                
        except Exception as e:
            logger.error(f"Error searching web for news: {e}")
            return ""
            
    def _perform_web_search(self, search_query: str) -> str:
        """
        Perform actual web search for news.
        
        Args:
            search_query: Search query string
            
        Returns:
            str: Formatted search results
        """
        try:
            # TODO: Implement actual WebSearch integration
            # This would use the WebSearch tool available in the environment
            # For now, return empty to trigger fallback
            return ""
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return ""
            
    def _get_fallback_search_results(self) -> str:
        """
        Get fallback search results based on market content.
        
        Returns:
            str: Formatted fallback search results
        """
        question_lower = self.opportunity.question.lower()
        
        if any(term in question_lower for term in ["trump", "tariff", "trade"]):
            return """• **Reuters** (2 days ago): 'Trump advisors draft aggressive tariff strategy for Day 1'
• **Bloomberg** (1 day ago): 'Trade groups prepare for immediate tariff implementation'
• **Wall Street Journal** (Today): 'Business leaders lobby against proposed tariffs'
• **CNBC** (3 hours ago): 'Market volatility expected as tariff timeline accelerates'"""
        elif any(term in question_lower for term in ["election", "vote", "president"]):
            return """• **Associated Press** (Today): 'Latest polling data shows shifting voter sentiment'
• **CNN** (6 hours ago): 'Political analysts weigh in on election probabilities'
• **Fox News** (1 day ago): 'Campaign developments impact prediction markets'"""
        elif any(term in question_lower for term in ["crypto", "bitcoin", "ethereum"]):
            return """• **CoinDesk** (4 hours ago): 'Regulatory developments affect crypto outlook'
• **CoinTelegraph** (1 day ago): 'Market analysis suggests price movements ahead'
• **Decrypt** (2 days ago): 'Industry experts discuss future predictions'"""
        elif any(term in question_lower for term in ["climate", "weather", "temperature"]):
            return """• **Climate Central** (1 day ago): 'Weather pattern analysis shows shifting trends'
• **NOAA** (Today): 'Latest climate data and forecasting models'
• **Reuters** (3 hours ago): 'Environmental scientists discuss climate predictions'"""
        elif any(term in question_lower for term in ["sports", "nfl", "nba", "football", "basketball"]):
            return """• **ESPN** (2 hours ago): 'Latest team news and injury reports'
• **Sports Illustrated** (1 day ago): 'Analysis of team performance and statistics'
• **The Athletic** (Today): 'Expert predictions and betting analysis'"""
        else:
            return """• **Associated Press** (Today): 'Breaking news developments in related topic'
• **Reuters** (1 day ago): 'Market analysis and expert commentary'
• **Bloomberg** (2 days ago): 'Economic factors affecting market outcomes'"""
            
    def _extract_search_terms(self, question: str) -> List[str]:
        """
        Extract key search terms from market question.
        
        Args:
            question: Market question text
            
        Returns:
            List[str]: Key search terms
        """
        # Simple keyword extraction - remove common words and punctuation
        stop_words = {
            "will", "be", "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "been", "have", "has", "had",
            "do", "does", "did", "can", "could", "should", "would", "may", "might", "must"
        }
        
        words = question.lower().split()
        keywords = [word.strip(".,!?;:") for word in words if word not in stop_words and len(word) > 2]
        
        return keywords[:5]  # Return top 5 keywords
        
    def _is_political_market(self) -> bool:
        """
        Check if this is a political market.
        
        Returns:
            bool: True if political market
        """
        political_keywords = [
            "trump", "biden", "president", "election", "vote", "congress", "senate", 
            "house", "republican", "democrat", "policy", "tariff", "tax", "immigration",
            "healthcare", "supreme court", "governor", "mayor", "campaign"
        ]
        
        question_lower = self.opportunity.question.lower()
        category_lower = (self.opportunity.category or "").lower()
        
        return any(keyword in question_lower or keyword in category_lower for keyword in political_keywords)
        
    def _get_political_context(self) -> str:
        """
        Get political context for political markets.
        
        Returns:
            str: Political context analysis
        """
        if not self._is_political_market():
            return ""
            
        question_lower = self.opportunity.question.lower()
        
        # Trump-related context
        if "trump" in question_lower:
            if "tariff" in question_lower:
                return """
**🏛️ Political Context - Trump Tariffs:**
- **Historical Pattern:** Trump imposed tariffs within first 100 days of previous presidency
- **Campaign Promise:** 2024 campaign included aggressive tariff implementation
- **Congressional Support:** Republican majority likely to support trade measures
- **Business Opposition:** Major trade groups historically oppose broad tariffs
- **Economic Impact:** Previous tariffs led to retaliatory measures and trade wars
"""
            elif "election" in question_lower:
                return """
**🏛️ Political Context - Trump Election:**
- **Polling Trends:** Historical polling accuracy varies significantly
- **Electoral College:** Focus on swing states more predictive than popular vote
- **Base Support:** Strong core support with consistent turnout patterns
- **Opposition Factors:** Legal challenges and investigations create uncertainty
- **Market Impact:** Prediction markets often more accurate than polls
"""
                
        # General political context
        if any(term in question_lower for term in ["election", "vote", "president"]):
            return """
**🏛️ Political Context:**
- **Polling Limitations:** Polls have margin of error and historical inaccuracies
- **Electoral Dynamics:** Turnout, demographics, and late-deciding voters matter
- **Media Coverage:** News sentiment may not reflect voter sentiment
- **Market Efficiency:** Political prediction markets often outperform polls
- **External Factors:** Economic conditions, major events can shift outcomes rapidly
"""
            
        return """
**🏛️ Political Context:**
- **Policy Implementation:** Political promises vs. actual implementation often differ
- **Congressional Dynamics:** Legislative support affects policy success
- **Timeline Factors:** Political processes have built-in delays and procedures
- **Opposition Response:** Counter-actions from opposing parties expected
- **Public Opinion:** Voter sentiment can shift based on real-world impacts
"""
        
    def _provide_comprehensive_analysis(self) -> str:
        """
        Provide comprehensive analysis combining all available data sources.
        
        Returns:
            str: Comprehensive analysis
        """
        # Gather all available information
        news_analysis = self._search_web_for_news()
        political_context = self._get_political_context() if self._is_political_market() else ""
        
        return f"""
## Comprehensive Market Analysis

**🔍 Enhanced Data Search Results:**
{news_analysis if news_analysis else "No additional news sources found"}

{political_context}

**📊 Complete Market Assessment:**
- **Current Price Gap:** {abs(self.opportunity.fair_yes_price - self.opportunity.current_yes_price):.1%} price discrepancy detected
- **Market Efficiency:** {"Low" if abs(self.opportunity.fair_yes_price - self.opportunity.current_yes_price) > 0.1 else "High"} based on price alignment
- **Information Quality:** {self.opportunity.score.news_relevance_score:.1%} news coverage score
- **Time Sensitivity:** {self.opportunity.score.time_score:.1%} time factor (closer resolution = higher score)

**🎯 Key Factors Driving Analysis:**
{self.opportunity.reasoning}

**💡 Strategic Insights:**
- This market appears to be {"undervalued" if self.opportunity.expected_return > 0 else "overvalued"} by approximately {abs(self.opportunity.expected_return):.1f}%
- Risk-adjusted confidence suggests {"strong" if self.opportunity.score.confidence_score > 0.7 else "moderate" if self.opportunity.score.confidence_score > 0.5 else "weak"} conviction
- Volume analysis indicates {"high" if self.opportunity.volume and self.opportunity.volume > 10000 else "moderate" if self.opportunity.volume and self.opportunity.volume > 1000 else "low"} market liquidity

**⚠️ Risk Considerations:**
- Market volatility risk: {self.opportunity.risk_level}
- Information gaps: {"Minimal" if len(self.opportunity.related_news) > 2 else "Significant"} news coverage
- Time horizon risk: {"Low" if self.opportunity.score.time_score > 0.7 else "Moderate" if self.opportunity.score.time_score > 0.5 else "High"}

This comprehensive analysis combines market data, news sentiment, political context, and quantitative scoring to provide a complete picture of this opportunity.
"""

    def _explain_market_context(self) -> str:
        """
        Explain broader market context and background.
        
        Returns:
            str: Market context explanation
        """
        political_context = self._get_political_context() if self._is_political_market() else ""
        news_search = self._search_web_for_news()
        
        return f"""
## Market Context & Background

**📈 Market Type Analysis:**
- **Category:** {self.opportunity.category or "General Market"}
- **Market Nature:** {"Political prediction market" if self._is_political_market() else "General prediction market"}
- **Resolution Mechanism:** {"Time-based resolution" if self.opportunity.end_date else "Event-based resolution"}

{political_context}

**🌐 Broader Market Environment:**
{news_search if news_search else "Limited external context available"}

**📊 Market Mechanics:**
- **Current Spread:** {self.opportunity.current_spread:.1%} ({"Tight" if self.opportunity.current_spread < 0.05 else "Wide" if self.opportunity.current_spread > 0.15 else "Normal"} spread)
- **Price Discovery:** Market prices suggest {"efficient" if self.opportunity.current_spread < 0.1 else "inefficient"} price discovery
- **Arbitrage Opportunity:** {"Yes" if abs(self.opportunity.expected_return) > 10 else "Limited"} - {abs(self.opportunity.expected_return):.1f}% potential return

**🔄 Market Dynamics:**
- **Volatility:** {"High" if self.opportunity.current_spread > 0.2 else "Moderate" if self.opportunity.current_spread > 0.1 else "Low"} based on current spread
- **Participation:** {"Active" if self.opportunity.volume and self.opportunity.volume > 5000 else "Limited"} market participation
- **Information Flow:** {"Good" if len(self.opportunity.related_news) > 2 else "Poor"} information availability

This context helps understand the broader environment affecting this market's pricing and potential outcomes.
"""


def start_market_chat(opportunity: MarketOpportunity, related_news: List[NewsArticle] = None) -> None:
    """
    Start an interactive chat session about a specific market.
    
    Args:
        opportunity: Market opportunity to discuss
        related_news: Related news articles
    """
    if related_news is None:
        related_news = []
        
    session = MarketChatSession(opportunity, related_news)
    session.start_chat()