"""HydraFusion-inspired multi-model orchestrator for Express'Arte Studio.

Selects the best AI provider (Ollama, Copilot, or Codex) based on task
complexity signals, following three execution patterns:
- Single: Direct answer from one model (fastest).
- Cascade: Ollama drafts -> if low confidence, escalate to Codex/Copilot.
- Critique: One model answers, another reviews for quality.

Uses the existing bridge modules: ollama_bridge, copilot_bridge, codex_bridge.
"""
from __future__ import annotations

import logging
import re
from typing import Any

# Import existing bridges
try:
    import ollama_bridge
except ImportError:
    ollama_bridge = None

try:
    import copilot_bridge
except ImportError:
    copilot_bridge = None

try:
    import codex_bridge
except ImportError:
    codex_bridge = None

# Complexity keywords that suggest a harder task requiring stronger models
COMPLEX_KEYWORDS = [
    "otimizar", "debug", "erro complexo", "análise profunda", "refatorar",
    "arquitetura", "segurança", "performance crítica", "multi-step",
    "dependências cruzadas", "blender python script", "mesh repair advanced"
]

def _estimate_complexity(message: str) -> float:
    """Estimate task complexity from 0.0 (simple) to 1.0 (complex)."""
    lower_msg = message.lower()
    score = 0.0
    
    # Length factor
    if len(message) > 500:
        score += 0.3
    elif len(message) > 200:
        score += 0.1
        
    # Keyword factor
    for kw in COMPLEX_KEYWORDS:
        if kw in lower_msg:
            score += 0.2
            
    # Question mark density (multiple questions often mean complex inquiry)
    q_count = message.count('?')
    if q_count > 2:
        score += 0.2
        
    return min(score, 1.0)

def _get_available_providers() -> list[str]:
    """Check which providers are currently available."""
    available = []
    if ollama_bridge and ollama_bridge.available():
        available.append('ollama')
    if copilot_bridge and copilot_bridge.available():
        available.append('copilot')
    if codex_bridge and codex_bridge.available():
        available.append('codex')
    return available

def _select_provider(complexity: float, available: list[str]) -> str | None:
    """Select the best provider based on complexity and availability."""
    if not available:
        return None
        
    # Simple tasks: prefer local/fastest (Ollama)
    if complexity < 0.3:
        if 'ollama' in available:
            return 'ollama'
        if 'codex' in available:
            return 'codex'
        return 'copilot' if 'copilot' in available else None
        
    # Medium tasks: prefer Codex (balanced)
    if complexity < 0.7:
        if 'codex' in available:
            return 'codex'
        if 'copilot' in available:
            return 'copilot'
        return 'ollama' if 'ollama' in available else None
        
    # Complex tasks: prefer strongest available (Copilot or Codex)
    if 'copilot' in available:
        return 'copilot'
    if 'codex' in available:
        return 'codex'
    return 'ollama' if 'ollama' in available else None

def run_hydra_chat(
    message: str,
    context: str = "",
    history: list[tuple[str, str]] | None = None,
    preferred_model: str | None = None
) -> dict[str, Any]:
    """Execute HydraFusion-inspired orchestration.
    
    Returns a dict with:
    - answer: The final response text
    - provider_used: Which provider actually answered
    - pattern: 'single', 'cascade', or 'critique'
    - complexity_score: Estimated complexity of the request
    """
    complexity = _estimate_complexity(message)
    available = _get_available_providers()
    
    if not available:
        return {
            'answer': 'Nenhum provedor de IA está disponível no momento. Verifique se Ollama, Copilot ou Codex estão configurados.',
            'provider_used': 'none',
            'pattern': 'error',
            'complexity_score': complexity
        }
        
    primary_provider = _select_provider(complexity, available)
    if not primary_provider:
        return {
            'answer': 'Erro interno na seleção do provedor.',
            'provider_used': 'none',
            'pattern': 'error',
            'complexity_score': complexity
        }
        
    # Execute based on pattern
    try:
        if complexity < 0.5:
            # SINGLE pattern: direct answer
            answer = _call_provider(primary_provider, message, context, history, preferred_model)
            return {
                'answer': answer,
                'provider_used': primary_provider,
                'pattern': 'single',
                'complexity_score': complexity
            }
        elif complexity < 0.8:
            # CASCADE pattern: Ollama drafts, escalate if needed
            draft_answer = _call_provider('ollama' if 'ollama' in available else primary_provider, message, context, history, preferred_model)
            
            # Simple quality check: if answer is too short or contains error markers
            if len(draft_answer) < 50 or 'não sei' in draft_answer.lower() or 'erro' in draft_answer.lower():
                # Escalate to stronger model
                final_answer = _call_provider(primary_provider, message, context, history, preferred_model)
                return {
                    'answer': final_answer,
                    'provider_used': primary_provider,
                    'pattern': 'cascade_escalated',
                    'complexity_score': complexity
                }
            else:
                return {
                    'answer': draft_answer,
                    'provider_used': 'ollama' if 'ollama' in available else primary_provider,
                    'pattern': 'cascade_accepted',
                    'complexity_score': complexity
                }
        else:
            # CRITIQUE pattern: One answers, another reviews
            first_provider = primary_provider
            second_provider = [p for p in available if p != first_provider]
            second_provider = second_provider[0] if second_provider else first_provider
            
            initial_answer = _call_provider(first_provider, message, context, history, preferred_model)
            
            # Build critique prompt
            critique_prompt = f"Revise a seguinte resposta técnica sobre modelagem 3D/impressão. Aponte erros factuais, sugestões de melhoria ou confirme se está correta:\n\nPergunta original: {message}\n\nResposta inicial:\n{initial_answer}"
            
            critique_response = _call_provider(second_provider, critique_prompt, "", [], preferred_model)
            
            # Combine results
            final_answer = f"Resposta inicial ({first_provider}):\n{initial_answer}\n\nRevisão crítica ({second_provider}):\n{critique_response}"
            
            return {
                'answer': final_answer,
                'provider_used': f'{first_provider}+{second_provider}',
                'pattern': 'critique',
                'complexity_score': complexity
            }
            
    except Exception as exc:
        logging.exception("Erro no orquestrador Hydra")
        return {
            'answer': f'Erro interno no processamento: {str(exc)[:200]}',
            'provider_used': 'error',
            'pattern': 'error',
            'complexity_score': complexity
        }

def _call_provider(
    provider: str,
    message: str,
    context: str,
    history: list[tuple[str, str]] | None,
    model: str | None
) -> str:
    """Call the specified provider bridge."""
    if provider == 'ollama':
        if not ollama_bridge:
            raise RuntimeError("Ollama bridge não disponível")
        return ollama_bridge.run_prompt(message, context, history, model)
    elif provider == 'copilot':
        if not copilot_bridge:
            raise RuntimeError("Copilot bridge não disponível")
        return copilot_bridge.run_prompt(message, context, history)
    elif provider == 'codex':
        if not codex_bridge:
            raise RuntimeError("Codex bridge não disponível")
        return codex_bridge.run_prompt(message, context, history, model)
    else:
        raise ValueError(f"Provedor desconhecido: {provider}")