#!/usr/bin/env python3
"""
Oblique Multi-Hop Generator
Combines knowledge graph traversal with highly oblique, riddle-like descriptions.
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
        "answer": "Trent Reznor",
        "category": "music/film",
        "hops": [
            {"entity": "Fight Club", "role": "film directed by Fincher"},
            {"entity": "David Fincher", "role": "director of Fight Club and The Social Network"},
            {"entity": "The Social Network", "role": "film scored by Trent Reznor"}
        ]
    },
    {
        "answer": "The Eagle and Child",
        "category": "places",
        "hops": [
            {"entity": "J.R.R. Tolkien", "role": "author of Lord of the Rings"},
            {"entity": "C.S. Lewis", "role": "author of Chronicles of Narnia"},
            {"entity": "Inklings", "role": "literary group they belonged to"}
        ]
    }
]

def generate_oblique_clue(entity: str, context: str) -> str:
    prompt = f"""
You are an expert riddle writer. Describe the following entity in a highly oblique, lateral-thinking, poetic way.
DO NOT use the entity's name or direct synonyms. Focus on iconic traits, concepts, plot points, or structural elements.

Entity: {entity}
Context/Role in the riddle: {context}

Requirements:
1. No names or direct titles.
2. Short (5-12 words).
3. Sound like a poetic, abstract clue.

Examples of good oblique clues:
- The Matrix -> "where bullets take suggestions and reality is a demo"
- J.R.R. Tolkien -> "the chronicler of walking jewelry"
- Fight Club -> "soap-funded therapy where names are withheld"

Return your response as a JSON object with a single key 'clue' containing the text.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You write highly oblique, riddle-like clues."},
            {"role": "user", "content": prompt}
        ],
        response_format={ "type": "json_object" },
        temperature=0.8,
        max_tokens=100
    )
    return json.loads(response.choices[0].message.content)["clue"]

def synthesize_riddle(answer: str, hops: List[Dict], clues: List[str]) -> str:
    hops_str = "\n".join([f"- Entity {i+1}: {hops[i]['entity']} (Clue: '{clues[i]}')" for i in range(len(hops))])
    
    prompt = f"""
You are an expert riddle synthesizer. I have a chain of entities leading to a final answer, and an oblique clue for each intermediate entity.

Final Answer: {answer}
Intermediate Entities & Clues:
{hops_str}

Task: Write a single, flowing riddle that connects these clues and asks for the Final Answer.
The final answer itself MUST NOT be named - it is what the riddle asks for.
Use the exact oblique clues provided (or very slight grammatical variations to make them flow).
Do NOT mention the intermediate entity names either.

Requirements:
1. One or two sentences maximum.
2. Seamlessly weave the provided clues together.
3. End by asking for the final answer obliquely (e.g., "What [profession/type]...", "Which [object]...").
4. Maintain a mysterious, convoluted, but logically sound tone.

Return your response as a JSON object with a single key 'riddle' containing the final text.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You write seamless, multi-hop riddles."},
            {"role": "user", "content": prompt}
        ],
        response_format={ "type": "json_object" },
        temperature=0.7,
        max_tokens=150
    )
    return json.loads(response.choices[0].message.content)["riddle"]

def generate_dataset(num_items: int = 5, output_file: str = "data/benchmark_oblique_multihop.jsonl"):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    print(f"Generating {num_items} multi-hop oblique riddles...")
    
    chain_prompt = f"""Generate {num_items} complex multi-hop relationship chains for a riddle benchmark.
Each chain should have a final answer (a well-known person, place, or thing) and 2-3 intermediate entities.
Format as JSON list of objects:
{{
  "chains": [
    {{
      "answer": "Final Answer Name",
      "category": "Domain (e.g. science, film, history)",
      "hops": [
        {{"entity": "Entity 1", "role": "How it connects"}},
        {{"entity": "Entity 2", "role": "How it connects"}}
      ]
    }}
  ]
}}
IMPORTANT: The connections MUST be factual and widely verifiable.
"""
    print("Generating chain structures...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a knowledge graph expert."},
            {"role": "user", "content": chain_prompt}
        ],
        response_format={ "type": "json_object" },
        temperature=0.8
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
            "id": f"mh_{i+1}",
            "question": riddle,
            "answer": chain["answer"],
            "aliases": [],
            "category": chain.get("category", "general"),
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
    parser.add_argument("--count", type=int, default=5, help="Number of questions to generate")
    parser.add_argument("--out", type=str, default="data/benchmark_oblique_multihop.jsonl")
    args = parser.parse_args()
    
    generate_dataset(args.count, args.out)
