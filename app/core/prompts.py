"""
Centralized prompts for the RAG system
"""

# Immigration law assistant prompts
IMMIGRATION_SYSTEM_PROMPT_EN = """You are an immigration law specialist assistant. Answer based only on the provided context.
IMPORTANT: Include citations in your response using [number] format to reference the context sources."""

IMMIGRATION_SYSTEM_PROMPT_ES = """Eres un asistente especializado en leyes de inmigración. Responde basándote únicamente en el contexto proporcionado.
IMPORTANTE: Incluye citas en tu respuesta usando el formato [número] para referenciar las fuentes del contexto."""

# Template for building the full prompt
PROMPT_TEMPLATE_EN = """{system_message}

Context:
{context}

{chat_history}Question: {question}
Answer:"""

PROMPT_TEMPLATE_ES = """{system_message}

Contexto:
{context}

{chat_history}Pregunta: {question}
Respuesta:"""

# Question generation prompts
QUESTION_GENERATION_PROMPT_EN = """Based on the following text content, generate exactly 5 common questions and 5 uncommon questions that someone might ask about this content.

Content:
{content}

Format your response as:
COMMON QUESTIONS:
1. [question]
2. [question]
3. [question]
4. [question]
5. [question]

UNCOMMON QUESTIONS:
1. [question]
2. [question]
3. [question]
4. [question]
5. [question]"""

QUESTION_GENERATION_PROMPT_ES = """Basado en el siguiente contenido de texto, genera exactamente 5 preguntas comunes y 5 preguntas poco comunes que alguien podría hacer sobre este contenido.

Contenido:
{content}

Formatea tu respuesta como:
PREGUNTAS COMUNES:
1. [pregunta]
2. [pregunta]
3. [pregunta]
4. [pregunta]
5. [pregunta]

PREGUNTAS POCO COMUNES:
1. [pregunta]
2. [pregunta]
3. [pregunta]
4. [pregunta]
5. [pregunta]"""

def get_system_prompt(language: str) -> str:
    """Get system prompt based on language"""
    return IMMIGRATION_SYSTEM_PROMPT_ES if language == "spanish" else IMMIGRATION_SYSTEM_PROMPT_EN

def get_prompt_template(language: str) -> str:
    """Get prompt template based on language"""
    return PROMPT_TEMPLATE_ES if language == "spanish" else PROMPT_TEMPLATE_EN

def get_question_generation_prompt(language: str) -> str:
    """Get question generation prompt based on language"""
    return QUESTION_GENERATION_PROMPT_ES if language == "spanish" else QUESTION_GENERATION_PROMPT_EN