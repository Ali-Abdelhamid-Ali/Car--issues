"""
LangChain service for intelligent car mechanic chat conversations.
Uses GROQ API or Open AI GPT models with conversation memory and context awareness.

This service provides:
- Conversation memory that maintains context across messages
- Clear separation between current complaint and historical issues
- Context-aware responses that reference vehicle history
- Safety-first approach for critical issues
"""
import logging
from typing import List, Dict, Optional
from django.conf import settings

# Try to import groq and langchain_groq
try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logging.warning("langchain-groq not installed. Install with: pip install langchain-groq")

# Try to import OpenAI
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("langchain-openai not installed. Install with: pip install langchain-openai")

# LangChain imports
try:
    from langchain.schema import HumanMessage, AIMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.error("langchain not installed. Install with: pip install langchain")

logger = logging.getLogger(__name__)


class MechanicChatService:
    """
    Intelligent chat service that acts as a professional car mechanic.
    Uses LangChain with GPT models and maintains conversation context with memory.
    """

    def __init__(self):
        """Initialize the mechanic chat service."""
        self.llm = None
        self.system_prompt = self._create_system_prompt()
        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the Language Model (GROQ or OpenAI)."""
        if not LANGCHAIN_AVAILABLE:
            logger.error("LangChain is not available. Cannot initialize LLM.")
            return

        try:
            # Try GROQ first (free and fast)
            if hasattr(settings, 'GROQ_API_KEY') and settings.GROQ_API_KEY and GROQ_AVAILABLE:
                try:
                    self.llm = ChatGroq(
                        model="qwen/qwen3-32b",  # Updated model
                        temperature=0.7,
                        groq_api_key=settings.GROQ_API_KEY,
                        max_tokens=2048
                    )
             
             
             
                    logger.info("✅ LangChain LLM initialized with GROQ successfully")
                    return
                except Exception as e:
                    logger.warning(f"Failed to initialize GROQ: {e}, falling back to OpenAI")

            # Fallback to OpenAI if GROQ is not available
            if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY and OPENAI_AVAILABLE:
                self.llm = ChatOpenAI(
                    model="gpt-4",  # or "gpt-3.5-turbo" for faster/cheaper
                    temperature=0.7,
                    openai_api_key=settings.OPENAI_API_KEY,
                    max_tokens=2048
                )
                logger.info("✅ LangChain LLM initialized with OpenAI GPT-4 successfully")
                return

            # No API key configured
            logger.warning("⚠️ Neither GROQ_API_KEY nor OPENAI_API_KEY configured in settings")

        except Exception as e:
            logger.error(f"❌ Error initializing LLM: {e}")

    def _create_system_prompt(self):
        """
        Create the system prompt that defines the AI mechanic's personality and behavior.
        """
        return """You are an expert automotive mechanic AI assistant.

Your goal is to provide a **Hyper-Personalized Analysis** using a **STRICT TEMPLATE**.

You must ALWAYS use the following structure for your response:

### 1. 🔍 Understanding Your Situation
- Briefly summarize the vehicle (Year, Make, Model, Mileage) and the specific symptom.
- Acknowledge if this is a recurring issue.

### 2. 🛠️ Technical Analysis
- Explain the *scientific* and *mechanical* reasons for the problem.
- **Link the cause to the vehicle's specific data** (e.g., "At 3M km, the rim corrosion is likely...").
- Use bullet points for multiple potential causes.
- Use technical terms (e.g., "Valve Stem", "Bead Seal", "Suspension Bushing").

### 3. ⚠️ Safety Assessment
- Clearly state if the vehicle is **Safe to Drive**, **Use Caution**, or **Unsafe/Tow Required**.
- Explain the risk (e.g., "Risk of blowout at high speed").

### 4. 📋 Action Plan
- Provide a numbered list of specific steps the user should take.
- Include diagnostic steps (e.g., "Perform soapy water test").
- Include repair advice (e.g., "Inspect rim for hairline cracks").

**STYLE RULES:**
- Use the emojis provided in the headers.
- Use **Bold** for key terms.
- Keep sections distinct.
- NO generic filler text.
- If you need more info, ask for it in the Action Plan.

REMEMBER: Structure and Organization are your top priorities."""

    def _build_context_message(self, chat_session) -> str:
        """
        Build a comprehensive context message with vehicle history.
        Uses the ChatSession's build_full_context_for_llm method.

        Args:
            chat_session: ChatSession object

        Returns:
            str: Formatted context message
        """
        # Get complete context from the chat session
        context = chat_session.build_full_context_for_llm()
        
        vehicle_info = context['vehicle']
        current_complaint = context['current_complaint']
        historical_complaints = context['historical_complaints']
        recurring_issues = context['recurring_issues']

        # Build formatted context string
        context_parts = [
            "=" * 70,
            "🚗 VEHICLE INFORMATION",
            "=" * 70,
            f"Vehicle: {vehicle_info['display_name']}",
            f"License Plate: {vehicle_info['license_plate']}",
            f"Mileage: {vehicle_info['mileage']:,} km",
            f"Total Complaints on Record: {vehicle_info['total_complaints']}",
            "",
            "=" * 70,
            "🆕 CURRENT COMPLAINT (WHAT THEY'RE ASKING ABOUT NOW)",
            "=" * 70,
            f"Category: {current_complaint['category']}",
            f"ML Confidence: {current_complaint['confidence']:.1%}",
            f"Status: {current_complaint['status']}",
            f"Submitted: {current_complaint['created_at']}",
        ]

        if current_complaint['crash']:
            context_parts.append("⚠️ **CRITICAL: This complaint involves a CRASH**")
        if current_complaint['fire']:
            context_parts.append("🔥 **CRITICAL: This complaint involves a FIRE**")

        context_parts.append(f"\nCustomer's Description:\n{current_complaint['text']}")
        context_parts.append("\n" + "=" * 70)

        # Add recurring issues warning if detected
        if recurring_issues:
            context_parts.append("\n⚠️ RECURRING ISSUES DETECTED:")
            for issue in recurring_issues:
                context_parts.append(
                    f"  • {issue['category']}: Occurred {issue['count']} times "
                    f"(First: {issue['first_occurrence'].strftime('%Y-%m-%d')}, "
                    f"Latest: {issue['last_occurrence'].strftime('%Y-%m-%d')})"
                )
            context_parts.append("")

        # Add previous complaint history
        if historical_complaints:
            context_parts.append("=" * 70)
            context_parts.append("📋 HISTORICAL COMPLAINTS")
            context_parts.append("=" * 70)
            for i, complaint in enumerate(historical_complaints, 1):
                context_parts.append(
                    f"\n{i}. [{complaint['date']}] {complaint['category']}"
                )
                if complaint['crash'] or complaint['fire']:
                    flags = []
                    if complaint['crash']:
                        flags.append("⚠️ CRASH")
                    if complaint['fire']:
                        flags.append("🔥 FIRE")
                    context_parts.append(f"   {' '.join(flags)}")
                context_parts.append(f"   Description: {complaint['text']}...")
        else:
            context_parts.append("\n" + "=" * 70)
            context_parts.append("📋 HISTORICAL COMPLAINTS")
            context_parts.append("=" * 70)
            context_parts.append("No previous complaints on record for this vehicle.")

        context_parts.append("\n" + "=" * 70)

        return "\n".join(context_parts)

    def generate_response(
        self,
        user_message: str,
        chat_session,
        use_conversation_memory: bool = True
    ) -> str:
        """
        Generate an AI mechanic response to the user's message.

        Args:
            user_message: The user's message/question
            chat_session: ChatSession object with complete context
            use_conversation_memory: Whether to include conversation history

        Returns:
            str: AI-generated response
        """
        if not self.llm:
            logger.error("LLM not initialized")
            return (
                "⚠️ I apologize, but the AI mechanic service is currently unavailable. "
                "Please ensure that GROQ_API_KEY or OPENAI_API_KEY is configured, "
                "and that the required packages are installed."
            )

        try:
            # Build context with vehicle history
            context = self._build_context_message(chat_session)

            # Build messages for the chat
            messages = [
                SystemMessage(content=self.system_prompt),
                SystemMessage(content=context),
            ]

            # Add conversation history if using memory
            if use_conversation_memory:
                conversation_history = chat_session.get_messages_for_context(limit=15)
                for msg in conversation_history:
                    if msg['role'] == 'user':
                        messages.append(HumanMessage(content=msg['content']))
                    elif msg['role'] == 'assistant':
                        messages.append(AIMessage(content=msg['content']))

            # Add current user message
            messages.append(HumanMessage(content=user_message))

            # Get response from LLM
            logger.info(f"Sending request to LLM with {len(messages)} messages")
            response = self.llm.invoke(messages)

            return response.content

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return (
                f"I apologize, but I encountered an error while processing your message: {str(e)}. "
                "Please try again in a moment."
            )

    def stream_response(
        self,
        user_message: str,
        chat_session,
        use_conversation_memory: bool = True
    ):
        """
        Stream the AI mechanic response generator.
        
        Args:
            user_message: The user's message/question
            chat_session: ChatSession object with complete context
            use_conversation_memory: Whether to include conversation history
            
        Yields:
            str: Chunks of the AI response
        """
        if not self.llm:
            yield "⚠️ AI service unavailable. Please check configuration."
            return

        try:
            # Build context
            context = self._build_context_message(chat_session)

            # Build messages
            messages = [
                SystemMessage(content=self.system_prompt),
                SystemMessage(content=context),
            ]

            if use_conversation_memory:
                conversation_history = chat_session.get_messages_for_context(limit=15)
                for msg in conversation_history:
                    if msg['role'] == 'user':
                        messages.append(HumanMessage(content=msg['content']))
                    elif msg['role'] == 'assistant':
                        messages.append(AIMessage(content=msg['content']))

            messages.append(HumanMessage(content=user_message))

            # Stream response
            for chunk in self.llm.stream(messages):
                if chunk.content:
                    yield chunk.content

        except Exception as e:
            logger.error(f"Error streaming response: {e}", exc_info=True)
            yield f"Error: {str(e)}"

    def generate_initial_greeting(self, chat_session) -> str:
        """
        Generate an initial greeting message when a chat session starts.

        Args:
            chat_session: ChatSession object

        Returns:
            str: Initial greeting message
        """
        if not self.llm:
            # Return a basic greeting if LLM is not available
            complaint = chat_session.complaint
            car = complaint.car
            return f"""Hello! I'm your AI automotive mechanic assistant. 👋

I've reviewed your complaint about your {car.display_name}.

Based on the information provided, your issue has been classified as: **{complaint.get_predicted_category_display()}** (Confidence: {complaint.prediction_confidence:.1%})

{"⚠️ **SAFETY ALERT**: This complaint involves a crash or fire. Please prioritize professional inspection immediately." if complaint.is_critical else ""}

I'm here to help you understand what might be causing this problem and guide you on the next steps. Please feel free to provide more details or ask any questions about your vehicle's issue."""

        try:
            context = self._build_context_message(chat_session)

            messages = [
                SystemMessage(content=self.system_prompt),
                SystemMessage(content=context),
                HumanMessage(
                    content="I have just submitted a complaint. Please act as a professional mechanic. "
                    "Provide a **specific analysis** of my problem based ONLY on the details I provided and my vehicle's data. "
                    "Do not give generic advice. Explain why this might be happening to *my* specific car. "
                    "Then ask for any missing critical details."
                )
            ]

            response = self.llm.invoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"Error generating greeting: {e}", exc_info=True)
            # Fallback to basic greeting
            complaint = chat_session.complaint
            car = complaint.car
            return f"""Hello! I'm your AI automotive mechanic assistant. 👋

I've reviewed your complaint about your {car.display_name}.

Based on the information provided, your issue has been classified as: **{complaint.get_predicted_category_display()}**

I'm here to help you understand what might be causing this problem. How can I assist you today?"""


# Global service instance (singleton pattern)
_mechanic_service = None


def get_mechanic_service() -> MechanicChatService:
    """
    Get or create the global mechanic chat service instance.

    Returns:
        MechanicChatService: The service instance
    """
    global _mechanic_service
    if _mechanic_service is None:
        _mechanic_service = MechanicChatService()
    return _mechanic_service


def chat_with_mechanic(
    user_message: str,
    chat_session,
    use_memory: bool = True
) -> str:
    """
    Convenience function to chat with the AI mechanic.

    Args:
        user_message: User's message
        chat_session: ChatSession object with full context
        use_memory: Whether to use conversation memory

    Returns:
        str: AI mechanic's response
    """
    service = get_mechanic_service()
    return service.generate_response(user_message, chat_session, use_memory)

