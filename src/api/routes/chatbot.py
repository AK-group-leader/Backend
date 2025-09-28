"""
AI Chatbot API endpoints using Google Gemini
Provides urban planning and environmental analysis assistance
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import google.generativeai as genai
import os

from src.utils.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Configure Gemini AI
api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
if api_key:
    genai.configure(api_key=api_key)
else:
    logger.warning("Neither GEMINI_API_KEY nor GOOGLE_API_KEY found in settings")

# Initialize Gemini model
model = genai.GenerativeModel('models/gemini-2.5-flash')

class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(default=None, description="Message timestamp")

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=[],
        description="Previous conversation messages"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Current map context (location, layers, analysis data)"
    )

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="AI assistant response")
    conversation_id: str = Field(..., description="Conversation identifier")
    timestamp: str = Field(..., description="Response timestamp")
    suggestions: Optional[List[str]] = Field(
        default=None,
        description="Suggested follow-up questions"
    )

# System prompt for urban planning context
SYSTEM_PROMPT = """
You are an AI assistant specialized in sustainable urban planning and environmental analysis. You help users understand:

1. **Environmental Data Analysis**:
   - Urban Heat Island (UHI) effects and mitigation strategies
   - Vegetation indices (NDVI) and green space optimization
   - Water absorption, drainage, and flood risk management
   - Air quality impacts and improvement recommendations
   - Building density and sustainable development

2. **Urban Planning Expertise**:
   - Sustainable city design principles
   - Green infrastructure planning
   - Climate-resilient urban development
   - Smart city technologies and IoT integration
   - Zoning and land use optimization

3. **Data Interpretation**:
   - Satellite imagery analysis
   - Environmental sensor data
   - Predictive modeling results
   - Sustainability metrics and scoring

4. **Actionable Recommendations**:
   - Specific improvement strategies
   - Cost-effective solutions
   - Policy recommendations
   - Implementation timelines

Always provide:
- Clear, actionable advice
- Specific examples when possible
- Consideration of environmental and economic factors
- References to best practices in urban planning

Keep responses concise but comprehensive, and ask clarifying questions when needed.
"""

def get_context_prompt(context: Optional[Dict[str, Any]]) -> str:
    """Generate context-aware prompt based on current map state"""
    if not context:
        return ""
    
    context_parts = []
    
    if context.get("location"):
        loc = context["location"]
        context_parts.append(f"Current map location: {loc.get('city', 'Unknown')}, coordinates ({loc.get('lat', 'N/A')}, {loc.get('lng', 'N/A')})")
    
    if context.get("visible_layers"):
        layers = ", ".join(context["visible_layers"])
        context_parts.append(f"Currently viewing layers: {layers}")
    
    if context.get("analysis_data"):
        data = context["analysis_data"]
        if data.get("temperature"):
            context_parts.append(f"Current temperature analysis: {data['temperature']}°C")
        if data.get("uhi_intensity"):
            context_parts.append(f"UHI intensity: {data['uhi_intensity']}")
        if data.get("vegetation_index"):
            context_parts.append(f"Vegetation index (NDVI): {data['vegetation_index']}")
        if data.get("water_absorption"):
            context_parts.append(f"Water absorption rate: {data['water_absorption']}%")
    
    if context.get("user_actions"):
        actions = context["user_actions"]
        if actions.get("added_elements"):
            elements = actions["added_elements"]
            green_count = len([e for e in elements if e.get("type") == "green"])
            building_count = len([e for e in elements if e.get("type") == "building"])
            if green_count > 0:
                context_parts.append(f"User has added {green_count} green spaces")
            if building_count > 0:
                context_parts.append(f"User has added {building_count} buildings")
    
    if context_parts:
        return f"\n\nCurrent Context:\n" + "\n".join(f"- {part}" for part in context_parts)
    
    return ""

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """
    Chat with AI assistant about urban planning and environmental analysis
    """
    try:
        # Build conversation history
        conversation_text = SYSTEM_PROMPT
        
        # Add context if provided
        context_prompt = get_context_prompt(request.context)
        if context_prompt:
            conversation_text += context_prompt
        
        # Add conversation history
        if request.conversation_history:
            conversation_text += "\n\nConversation History:\n"
            for msg in request.conversation_history[-10:]:  # Keep last 10 messages
                role = "Human" if msg.role == "user" else "Assistant"
                conversation_text += f"{role}: {msg.content}\n"
        
        # Add current user message
        conversation_text += f"\nHuman: {request.message}\nAssistant: "
        
        # Generate response using Gemini
        response = model.generate_content(conversation_text)
        
        if not response.text:
            raise HTTPException(status_code=500, detail="Failed to generate response")
        
        # Generate conversation ID
        conversation_id = f"chat_{hash(str(request.conversation_history))}"
        
        # Generate follow-up suggestions based on the response
        suggestions = await generate_suggestions(request.message, response.text, request.context)
        
        return ChatResponse(
            response=response.text,
            conversation_id=conversation_id,
            timestamp=datetime.now().isoformat(),
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Chat request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )

async def generate_suggestions(user_message: str, ai_response: str, context: Optional[Dict[str, Any]]) -> List[str]:
    """Generate contextual follow-up suggestions"""
    suggestions = []
    
    # Topic-based suggestions
    if any(keyword in user_message.lower() for keyword in ["heat", "temperature", "uhi"]):
        suggestions.extend([
            "How can I reduce urban heat island effects?",
            "What are the best cooling strategies for cities?",
            "How does vegetation help with temperature control?"
        ])
    
    if any(keyword in user_message.lower() for keyword in ["water", "flood", "drainage"]):
        suggestions.extend([
            "What are sustainable drainage solutions?",
            "How can I improve water absorption in urban areas?",
            "What is the risk of flooding in this area?"
        ])
    
    if any(keyword in user_message.lower() for keyword in ["green", "vegetation", "park"]):
        suggestions.extend([
            "Where should I place green spaces for maximum impact?",
            "What types of vegetation work best in urban environments?",
            "How much green space does a sustainable city need?"
        ])
    
    if any(keyword in user_message.lower() for keyword in ["building", "development", "construction"]):
        suggestions.extend([
            "What are sustainable building practices?",
            "How does building density affect the environment?",
            "What materials are best for eco-friendly construction?"
        ])
    
    # Context-based suggestions
    if context:
        if context.get("visible_layers"):
            if "heatmap" in context["visible_layers"]:
                suggestions.append("How can I interpret this heat map data?")
            if "vegetation" in context["visible_layers"]:
                suggestions.append("What does the vegetation index tell me?")
            if "water" in context["visible_layers"]:
                suggestions.append("How can I improve water management here?")
    
    # General urban planning suggestions
    general_suggestions = [
        "What are the key principles of sustainable urban planning?",
        "How can I make this area more climate-resilient?",
        "What environmental factors should I consider?",
        "Can you analyze the current environmental conditions?",
        "What are some quick wins for sustainability?"
    ]
    
    # Add general suggestions if we don't have enough specific ones
    while len(suggestions) < 3 and general_suggestions:
        suggestion = general_suggestions.pop(0)
        if suggestion not in suggestions:
            suggestions.append(suggestion)
    
    return suggestions[:3]  # Return max 3 suggestions

@router.get("/chat/suggestions")
async def get_chat_suggestions(
    context: Optional[str] = None,
    topic: Optional[str] = None
):
    """
    Get suggested questions for starting a conversation
    """
    try:
        suggestions = []
        
        if topic == "heat":
            suggestions = [
                "How can I reduce urban heat island effects in this area?",
                "What's causing the high temperatures I'm seeing?",
                "What are the best cooling strategies for cities?"
            ]
        elif topic == "water":
            suggestions = [
                "How can I improve water absorption and drainage?",
                "What's the flood risk in this area?",
                "What are sustainable stormwater management solutions?"
            ]
        elif topic == "vegetation":
            suggestions = [
                "Where should I add green spaces for maximum impact?",
                "How much vegetation does this area need?",
                "What types of plants work best in urban environments?"
            ]
        elif topic == "buildings":
            suggestions = [
                "How does building density affect the environment?",
                "What are sustainable building practices?",
                "How can I optimize development in this area?"
            ]
        else:
            # General suggestions
            suggestions = [
                "How can I make this area more sustainable?",
                "What environmental issues should I be concerned about?",
                "Can you analyze the current conditions and suggest improvements?",
                "What are the key factors for sustainable urban planning?",
                "How can I reduce the environmental impact of development?"
            ]
        
        return {
            "suggestions": suggestions,
            "topic": topic or "general",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get chat suggestions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get suggestions: {str(e)}"
        )

@router.get("/health")
async def chatbot_health_check():
    """Health check for chatbot service"""
    try:
        # List available models
        available_models = []
        try:
            for model_info in genai.list_models():
                if 'generateContent' in model_info.supported_generation_methods:
                    available_models.append(model_info.name)
        except Exception as list_error:
            logger.warning(f"Could not list models: {str(list_error)}")
        
        # Test Gemini API connection
        test_response = model.generate_content("Hello")
        
        return {
            "status": "healthy",
            "service": "AI Chatbot (Gemini)",
            "model": "models/gemini-2.5-flash",
            "api_available": bool(test_response.text),
            "available_models": available_models[:5],  # Show first 5 models
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Chatbot health check failed: {str(e)}")
        
        # Try to list models even if main test fails
        available_models = []
        try:
            for model_info in genai.list_models():
                if 'generateContent' in model_info.supported_generation_methods:
                    available_models.append(model_info.name)
        except Exception as list_error:
            logger.warning(f"Could not list models: {str(list_error)}")
        
        return {
            "status": "unhealthy",
            "service": "AI Chatbot (Gemini)",
            "error": str(e),
            "available_models": available_models[:5],  # Show first 5 models
            "timestamp": datetime.now().isoformat()
        }
