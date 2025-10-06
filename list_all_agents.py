"""
List all agents in the trained model and compare with mapped agents.
"""
import joblib
from agent_sop_mapping import AGENT_SOP_MAPPING

# Load the label encoder
encoder = joblib.load('ultra_fast_agent_encoder.pkl')

# Get all agent names from the encoder
all_agents = list(encoder.classes_)
mapped_agents = set(AGENT_SOP_MAPPING.keys())

print("=" * 80)
print(f"TOTAL AGENTS IN MODEL: {len(all_agents)}")
print(f"MAPPED AGENTS: {len(mapped_agents)}")
print(f"UNMAPPED AGENTS: {len(all_agents) - len(mapped_agents)}")
print("=" * 80)

# Get unmapped agents
unmapped = sorted([agent for agent in all_agents if agent not in mapped_agents])

print("\n🔴 UNMAPPED AGENTS (Need SOP Mapping):")
print("-" * 80)
for i, agent in enumerate(unmapped, 1):
    print(f"{i:3d}. {agent}")

print("\n" + "=" * 80)
print("✅ MAPPED AGENTS (Already have SOPs):")
print("-" * 80)
for i, agent in enumerate(sorted(mapped_agents), 1):
    print(f"{i:2d}. {agent}")

