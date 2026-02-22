#!/usr/bin/env python3
"""
EXTREME Oblique Multi-Hop Generator
Combines knowledge graph traversal with highly esoteric, cross-domain descriptions.
"""

import json
import os
import argparse
from typing import Dict, List
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_BASE_URL")
)

CHAINS = [
    {
        "answer": "Nicolas Cage",
        "category": "cross-domain",
        "hops": [
            {"entity": "Truffaut's 400 Blows", "role": "French New Wave film that inspired a famous poster"},
            {"entity": "Raising Arizona", "role": "Film featuring the protagonist stealing diapers, directed by Coens, inspired by the above poster"},
            {"entity": "H.I. McDunnough", "role": "Character played by Nicolas Cage in Raising Arizona"}
        ]
    }
]

def generate_oblique_clue(entity: str, context: str) -> str:
    prompt = f"""
You are an expert riddle writer. Describe the following entity in an EXTREMELY esoteric, abstract, lateral-thinking way.
DO NOT use the entity's name, direct synonyms, popular buzzwords, or obvious primary associations.
Instead, focus on obscure structural mechanisms, hidden secondary works, structural metaphors, or bizarre trivia.

Entity: {entity}
Context/Role in the riddle: {context}

Requirements:
1. No names, titles, or obvious keywords.
2. Must require deep niche knowledge to decode.
3. Short (8-15 words).
4. Sounds like an ancient cryptic text or abstract system description.

Return your response as a JSON object with a single key 'clue' containing the text.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You write incredibly hard, esoteric riddle clues."},
            {"role": "user", "content": prompt}
        ],
        response_format={ "type": "json_object" },
        temperature=0.9,
        max_tokens=100
    )
    return json.loads(response.choices[0].message.content)["clue"]

def synthesize_riddle(answer: str, hops: List[Dict], clues: List[str]) -> str:
    hops_str = "\n".join([f"- Entity {i+1}: {hops[i]['entity']} (Clue: '{clues[i]}')" for i in range(len(hops))])
    
    prompt = f"""
You are an expert synthesizer of the hardest riddles on Earth. 
I have a chain of entities leading to a final answer, and an incredibly obscure clue for each intermediate entity.

Final Answer: {answer}
Intermediate Entities & Clues:
{hops_str}

Task: Write a single, flowing riddle that connects these clues in sequence and asks for the Final Answer.
The final answer itself MUST NOT be named or hinted at directly. 
Do NOT mention the intermediate entity names either.
The riddle MUST require the solver to resolve the first clue, trace the relationship to the second, and so on, until the final answer is reached.

Requirements:
1. One or two long, flowing sentences maximum.
2. Seamlessly weave the provided clues together. Add connective tissue that describes the relationships between them abstractly.
3. End by asking for the final answer obliquely (e.g., "What vessel...", "Whose voice...").
4. The difficulty should be excruciating, aiming for only the top 5% of AIs to solve it.

Return your response as a JSON object with a single key 'riddle' containing the final text.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You write seamless, excruciatingly difficult multi-hop riddles."},
            {"role": "user", "content": prompt}
        ],
        response_format={ "type": "json_object" },
        temperature=0.8,
        max_tokens=200
    )
    return json.loads(response.choices[0].message.content)["riddle"]

def generate_dataset(num_items: int = 5, output_file: str = "data/benchmark_oblique_multihop_hard.jsonl"):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    print(f"Generating {num_items} EXTREME multi-hop oblique riddles...")
    
    chain_prompt = f"""Generate {num_items} incredibly obscure, cross-domain multi-hop relationship chains for an extreme AI riddle benchmark.
Each chain should have a final answer (a specific person, object, or location) and 3-4 intermediate entities.
The hops MUST cross domains (e.g., from Biology to 19th-century Poetry to 1980s Pop Culture to Geography).
Format as JSON list of objects:
{{
  "chains": [
    {{
      "answer": "Final Answer Name",
      "category": "cross-domain",
      "hops": [
        {{"entity": "Entity 1", "role": "How it connects to Entity 2"}},
        {{"entity": "Entity 2", "role": "How it connects to Entity 3"}},
        {{"entity": "Entity 3", "role": "How it connects to the Final Answer"}}
      ]
    }}
  ]
}}
IMPORTANT: The connections MUST be highly non-obvious but factual and verifiable. 
Do NOT use standard trivia like 'Lord of the Rings' -> 'C.S. Lewis'. Use weird, esoteric links.
"""
    print("Generating extreme chain structures...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a savant of bizarre, esoteric knowledge graph connections."},
            {"role": "user", "content": chain_prompt}
        ],
        response_format={ "type": "json_object" },
        temperature=1.0
    )
    
    try:
        new_chains = json.loads(response.choices[0].message.content)
        chains_list = new_chains.get("chains", [])
    except Exception as e:
        print(f"Error parsing chains: {e}")
        chains_list = []
        
    valid_chains = [c for c in chains_list if isinstance(c, dict) and "answer" in c and "hops" in c]
    all_chains = (CHAINS + valid_chains)[:num_items]
    
    results = []
    
    for i, chain in enumerate(all_chains):
        print(f"[{i+1}/{len(all_chains)}] Processing chain ending in '{chain['answer']}'...")
        
        clues = []
        for hop in chain["hops"]:
            clue = generate_oblique_clue(hop["entity"], hop["role"])
            clues.append(clue)
            
        riddle = synthesize_riddle(chain["answer"], chain["hops"], clues)
        
        item = {
            "id": f"mh_hard_{i+1}",
            "question": riddle,
            "answer": chain["answer"],
            "aliases": [],
            "category": chain.get("category", "cross-domain"),
            "chain": [h["entity"] for h in chain["hops"]] + [chain["answer"]],
            "oblique_clues": clues,
            "num_hops": len(chain["hops"])
        }
        
        results.append(item)
        print(f"  -> {riddle}")
        
    with open(output_file, "w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item) + "\n")
            
    print(f"Done! Saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=30, help="Number of questions to generate")
    parser.add_argument("--out", type=str, default="data/benchmark_oblique_multihop_hard.jsonl")
    args = parser.parse_args()
    
    generate_dataset(args.count, args.out)
