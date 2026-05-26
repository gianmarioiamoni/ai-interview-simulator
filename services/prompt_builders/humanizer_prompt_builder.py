# services/prompt_builders/humanizer_prompt_builder.py 

from app.prompts.prompt_loader import PromptLoader 
from app.prompts.prompt_renderer import PromptRenderer 
from domain.contracts.question.question import Question 

def build_humanizer_prompt( 
    question: Question, 
    language: str, 
    chat_history: list[str], 
) -> str: 
    
    template = PromptLoader.load("transformation/humanizer.txt") 
    history_snippet = "\n".join(chat_history[-5:]) if chat_history else "" 
    context = { 
        "question": question.prompt, 
        "language": language, 
        "history": history_snippet, } 
        
    return PromptRenderer.render(template, context)
