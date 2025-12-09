from typing import TypedDict, Annotated, List, Dict, Optional, Any

import operator
import logging
import os
import json
from groq import Groq
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END


from src.shared_memory.memory_manager import shared_memory
from .research_agent import ResearchAgent
from .gis_agent import GISAgent
from .iucn_agent import IUCNAgent

logger = logging.getLogger(__name__)

from langgraph.checkpoint.memory import MemorySaver

# --- State Definition ---
class AgentState(TypedDict):
    question: str
    chat_history: Annotated[List[BaseMessage], operator.add]
    plan: List[str]
    current_step_index: int
    research_data: List[Dict] # Removed operator.add to allow resetting
    gis_data: List[Dict]
    iucn_data: List[Dict]
    errors: List[str]
    retry_count: int
    final_answer: str

class SuperAgent:
    def __init__(self):
        self.workers = dict(
            research=ResearchAgent(),
            gis=GISAgent(),
            iucn=IUCNAgent()
        )
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.memory = MemorySaver() # Initialize Checkpointer
        self.app = self._build_graph()


    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Add Nodes
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("router", self._router_node)
        workflow.add_node("research_agent", self._research_node)
        workflow.add_node("gis_agent", self._gis_node)
        workflow.add_node("iucn_agent", self._iucn_node)
        workflow.add_node("query_rewriter", self._query_rewriter_node)
        workflow.add_node("synthesizer", self._synthesizer_node)

        # Add Edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "router")
        
        # Conditional Routing
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "research": "research_agent",
                "gis": "gis_agent",
                "iucn": "iucn_agent",
                "synthesize": "synthesizer",
                "rewrite": "query_rewriter"
            }
        )

        # Return from agents to router to check results
        workflow.add_edge("research_agent", "router")
        workflow.add_edge("gis_agent", "router")
        workflow.add_edge("iucn_agent", "router")
        workflow.add_edge("query_rewriter", "router")
        
        workflow.add_edge("synthesizer", END)

        # Compile with Checkpointer
        return workflow.compile(checkpointer=self.memory)

    # --- Nodes ---

    def _planner_node(self, state: AgentState):
        """Decompose query into steps, considering history."""
        question = state["question"]
        
        # --- FAST PATH ---
        # If query is short and simple, skip LLM planning to reduce latency
        if len(question.split()) < 8 and not any(k in question.lower() for k in ["and", "also", "compare"]):
            logger.info("Fast Path: Skipping LLM planning")
            plan = [question]
            
            # Heuristic: Force GIS step for location queries
            lower_q = question.lower()
            if any(k in lower_q for k in ["where", "location", "map", "grow", "district", "place"]):
                plan.append(f"Find location and habitat data for: {question}")
                
            return {
                "plan": plan,
                "current_step_index": 0, 
                "errors": [],
                "retry_count": 0
            }
        # -----------------

        history = state.get("chat_history", [])
        
        # Format history for LLM - STRICT LIMIT to last 2 turns to save tokens
        history_str = ""
        if history:
            # Keep only last 2 messages (User + AI)
            recent_history = history[-2:]
            history_str = "Previous Context:\n" + "\n".join([f"{m.type}: {m.content[:200]}..." for m in recent_history])
        
        prompt = f"""{history_str}
        
        Current Query: "{question}"
        
        Analyze the query. If it refers to previous context (e.g., "it", "that plant"), resolve it using the conversation history.
        Break it down into a list of simple steps.
        Format: JSON list of strings.
        Example: ["Identify plant", "Find habitat"]
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
            if "[" in content:
                start = content.find("[")
                end = content.rfind("]") + 1
                plan = json.loads(content[start:end])
            else:
                plan = [question]
        except:
            plan = [question]
            
        if not plan:
            plan = [question]
            
            # Heuristic: Force GIS step for location queries
            lower_q = question.lower()
            if any(k in lower_q for k in ["where", "location", "map", "grow", "district", "place"]):
                plan.append(f"Find location and habitat data for: {question}")
                
            return {
                "plan": plan,
                "current_step_index": 0, 
                "errors": [],
                "retry_count": 0
            }

    def _router_node(self, state: AgentState):
        """Decision point."""
        return {}

    def _route_decision(self, state: AgentState):
        idx = state.get("current_step_index", 0)
        if idx >= len(state["plan"]):
            return "synthesize"
            
        current_step = state["plan"][idx]
        
        # Heuristic Override for GIS
        step_lower = current_step.lower()
        if any(k in step_lower for k in ["where", "location", "region", "habitat", "distribution", "grow"]):
            return "gis"
            
        # Semantic Routing using LLM
        prompt = f"""Given the query step: "{current_step}", which agent is best suited?
        Options: [RESEARCH, GIS, IUCN]
        
        - RESEARCH: Medicinal uses, properties, botany, identification.
        - GIS: Habitat, location, geography, distribution.
        - IUCN: Conservation status, endangered, threats.
        
        Return ONLY the option name.
        """
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            choice = response.choices[0].message.content.strip().upper()
            print(f"Router Choice for '{current_step}': {choice}", flush=True)
        except:
            choice = "RESEARCH" # Default
            
        if "GIS" in choice: return "gis"
        if "IUCN" in choice: return "iucn"
        return "research"

    def _research_node(self, state: AgentState):
        idx = state.get("current_step_index", 0)
        query = state["plan"][idx]
        
        # Context injection
        if state["research_data"]:
            last_plant = state["research_data"][-1].get("results", [{}])[0].get("botanical_name")
            if last_plant and last_plant not in query:
                query = f"{query} {last_plant}"

        result = self.workers["research"].process_query(query)
        
        # Self-Correction Logic
        if not result.get("results") and state.get("retry_count", 0) < 1:
            # Rewrite query and try again (simplified: just append 'plant')
            state["plan"][idx] = f"{query} medicinal plant"
            return {"retry_count": state["retry_count"] + 1, "plan": state["plan"]}
            
        return {"research_data": state.get("research_data", []) + [result], "current_step_index": idx + 1, "retry_count": 0}

    def _gis_node(self, state: AgentState):
        idx = state.get("current_step_index", 0)
        query = state["plan"][idx]
        
        if state["research_data"]:
            last_plant = state["research_data"][-1].get("results", [{}])[0].get("botanical_name")
            if last_plant and last_plant not in query:
                query = f"{query} {last_plant}"
                
        result = self.workers["gis"].process_query(query)
        return {"gis_data": state.get("gis_data", []) + [result], "current_step_index": idx + 1, "retry_count": 0}

    def _iucn_node(self, state: AgentState):
        idx = state.get("current_step_index", 0)
        query = state["plan"][idx]
        
        if state["research_data"]:
            last_plant = state["research_data"][-1].get("results", [{}])[0].get("botanical_name")
            if last_plant and last_plant not in query:
                query = f"{query} {last_plant}"

        result = self.workers["iucn"].process_query(query)
        return {"iucn_data": state.get("iucn_data", []) + [result], "current_step_index": idx + 1, "retry_count": 0}

    def _query_rewriter_node(self, state: AgentState):
        """Rewrites the current step query."""
        return {}

    def _synthesizer_node(self, state: AgentState):
        """Final synthesis."""
        all_results = state.get("research_data", []) + state.get("gis_data", []) + state.get("iucn_data", [])
        
        # Debug: Log size
        logger.info(f"Synthesizer Input Items: {len(all_results)}")
        
        context = json.dumps(all_results, default=str)
        
        # Truncate context aggressively (Groq Free Tier)
        # Limit to 8000 chars (~2000 tokens)
        MAX_CONTEXT_CHARS = 8000
        if len(context) > MAX_CONTEXT_CHARS:
            logger.debug(f"Context too large ({len(context)} chars). Truncating to {MAX_CONTEXT_CHARS}.")
            context = context[:MAX_CONTEXT_CHARS] + "... [TRUNCATED]"
            
        # Explicitly inject GIS data if present
        gis_summary_text = ""
        for item in state.get("gis_data", []):
            if item.get("summary"):
                gis_summary_text += f"\nGIS DATA: {item['summary']}\n"
        
        prompt = f"""
        Answer the user's question based on the context.
        Question: {state['question']}
        Context: 
        {context}
        {gis_summary_text}
        
        Instructions:
        1. Answer the question clearly based on the context.
        2. STRUCTURED RESPONSE: If the question is about a plant, structure the answer with Markdown headers like:
           - ## Description
           - ## Medicinal Uses
           - ## Habitat & Distribution
           - ## Conservation Status (if available)
        3. STRICT RULE: Only provide the list of districts/locations if the user explicitly asked for "location", "where it grows", "distribution", or "map".
        4. IMAGE RULE: Only provide an "image_query" if a SPECIFIC PLANT is identified in the context. If the question is generic (e.g. "What is sound?", "Hello"), set "image_query" to null.
        
        Return a JSON object with the following fields:
        - "answer": The detailed answer in Markdown format.
        - "plant_name": The main plant name discussed (if any).
        - "locations": A list of location names mentioned (e.g. ["India", "Kerala"]).
        - "image_query": A short query to find an image of the plant (e.g. "Ocimum sanctum") OR null if no plant is discussed.
        
        Ensure the output is valid JSON.
        """
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            final_data = json.loads(content)
            answer = final_data.get("answer", "No answer generated.")
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            answer = "Failed to synthesize answer."
            final_data = {"answer": answer}
            
        # Ensure answer is a string (fix Pydantic error)
        if answer is None:
            answer = "No answer generated."
        else:
            answer = str(answer)
            
        # Return answer AND update chat history
        return {
            "final_answer": json.dumps(final_data), # Store full JSON string in final_answer for now
            "chat_history": [
                HumanMessage(content=state["question"]),
                SystemMessage(content=answer)
            ]
        }

    def query(self, question: str, session_id: str = "default", limit: int = 5) -> Dict:
        """Entry point for API."""
        from src.tools.image_fetcher import fetch_wikipedia_image
        import re
        
        inputs = {
            "question": question,
            "current_step_index": 0,
            "plan": [],
            "chat_history": [],
            "research_data": [],
            "gis_data": [],
            "iucn_data": [],
            "errors": [],
            "retry_count": 0
        }
        config = {"configurable": {"thread_id": session_id}}
        
        # Invoke with config for memory
        result = self.app.invoke(inputs, config=config)
        
        # Parse the structured output
        raw_answer = result.get("final_answer", "{}")
        try:
            structured_output = json.loads(raw_answer)
        except:
            # Fallback: Try to extract JSON from markdown code blocks or raw text
            try:
                # Look for { ... } pattern
                match = re.search(r'\{.*\}', raw_answer, re.DOTALL)
                if match:
                    structured_output = json.loads(match.group(0))
                else:
                    raise ValueError("No JSON found")
            except:
                # If all else fails, treat raw text as the answer
                structured_output = {"answer": raw_answer}
            
        # Fetch Image if needed
        if structured_output.get("image_query"):
            img_url = fetch_wikipedia_image(structured_output["image_query"])
            if img_url:
                structured_output["image_url"] = img_url
        
        # Extract GIS locations directly from state for map generation
        gis_districts = []
        if result.get("gis_data"):
            # gis_data is a list of strings like "Found 5 districts in Karnataka: Bagalkot, Bellary..."
            # We need to extract the actual district names.
            # OR, better: The GISAgent should have returned a structured list or we rely on the LLM's 'locations' output.
            # Let's rely on the LLM's extracted 'locations' but fallback/augment with regex from gis_data if needed.
            pass

        # Return structured output directly
        return {
            "answer": structured_output.get("answer"),
            "locations": structured_output.get("locations", []), 
            "gis_data": result.get("gis_data", []), # Pass raw GIS data for debugging/advanced parsing
            "image_url": structured_output.get("image_url"),
            "final_answer": raw_answer,
            "plan": result.get("plan")
        }
