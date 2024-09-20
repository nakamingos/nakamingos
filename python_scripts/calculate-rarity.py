import json
from collections import defaultdict

# Step 1: Read the JSON File
with open(r"nakamingos_metadata_v1.4a_W_artdrop_Ordex.json", 'r') as json_file:
    nft_data = json.load(json_file)
    total_retrieved = len(nft_data['collection_items'])

# Step 2: Print Status
if total_retrieved == 20000:
    print("Retrieved 20,000 Nakamingos.\nCalculating rarity...")
else:
    print(f"Retrieved the wrong number of Nakamingos. Expected 20,000 but retrieved {total_retrieved}.")

# Step 3: Calculate Trait Value Frequencies
trait_value_counts = defaultdict(int)
total_items = len(nft_data['collection_items'])

# Traits to filter out from the rarity calculations
traits_to_exclude = {"Wisdom/Magic", "Power/Strength", "Speed/Agility"}

for item in nft_data['collection_items']:
    for attr in item['item_attributes']:
        trait_type = attr.get('trait_type')  # Ensure 'trait_type' exists
        trait_value = attr.get('value')      # Ensure 'value' exists
        if trait_type and trait_value and trait_type not in traits_to_exclude:
            trait_value_counts[(trait_type, trait_value)] += 1

# Step 4: Calculate Trait Frequencies
for (trait_type, trait_value), count in sorted(trait_value_counts.items(), key=lambda x: x[1]):
    frequency_percentage = (count / total_items) * 100

# Step 5: Calculate Rarity Scores and Rankings
nft_rankings = []

for nft in nft_data['collection_items']:
    nft_traits = nft['item_attributes']
    rarity_scores = []

    for trait in nft_traits:
        trait_type = trait.get('trait_type')  # Ensure 'trait_type' exists
        trait_value = trait.get('value')      # Ensure 'value' exists
        if not trait_type or not trait_value or trait_type in traits_to_exclude or trait_type == 'rarity':
            continue
        
        count = trait_value_counts[(trait_type, trait_value)]
        rarity_score = 1 / (count / total_items)
        rarity_scores.append((trait_type, trait_value, rarity_score))

    if rarity_scores:
        rarity_scores.sort(key=lambda x: x[2], reverse=True)
        nft_rankings.append((nft['name'], rarity_scores[0]))

# Step 6: Order Rarity Rankings by Rarest to Least Rare
nft_rankings.sort(key=lambda x: x[1][2], reverse=True)

# Step 7: Save Rarity Rankings to a File
txt_filename = r"nakamingosRarity.txt"

# List of specific Nakamingos considered 'Featured Artist'
featured_artist_list = [
    "Nakamingo #369",
    "Nakamingo #420",
    "Nakamingo #6666",
    "Nakamingo #6969",
    "Nakamingo #13413",
    "Nakamingo #14234",
    "Nakamingo #14341",
    "Nakamingo #14432"
]

with open(txt_filename, 'w') as txt_file:
    ranked_nfts = []
    regular_rank_counter = 2  # Start regular rankings from 2 (after '00001')
    
    for rank, (nft_name, (trait_type, trait_value, _)) in enumerate(nft_rankings, start=1):
        # Default to regular rank
        formatted_rank = f"{regular_rank_counter:05d}"

        # Check if the current NFT is in the 'Featured Artist' list
        if nft_name in featured_artist_list:
            formatted_rank = "00001"
        else:
            regular_rank_counter += 1  # Increment for regular ranks

        ethscription_id = next(
            (item['ethscription_id'] for item in nft_data['collection_items'] if item['name'] == nft_name),
            ''
        )
        link = f"https://ordex.io/ethscription/{ethscription_id}"
        ranked_nfts.append((formatted_rank, nft_name, trait_type, trait_value, link))
    
    # Sort NFTs by rank to ensure "00001" is at the top
    ranked_nfts.sort(key=lambda x: x[0])

    # Write the sorted NFTs to the file
    for formatted_rank, nft_name, trait_type, trait_value, link in ranked_nfts:
        text = f"Rank {formatted_rank} - {nft_name} | Rarest trait = {trait_type} - {trait_value} | Link: {link}\n"
        txt_file.write(text)

# Step 8: Calculate and Print Rarity Scores for Traits
print("\n-------------------------------------------------------------\nRarity Scores for Traits (sorted by most rare to least rare):\n-------------------------------------------------------------")
for trait, count in sorted(trait_value_counts.items(), key=lambda x: (x[1] / total_items)):
    trait_type, trait_value = trait
    
    # Skip the 'rarity' trait_type and excluded traits
    if trait_type == 'rarity' or trait_type in traits_to_exclude:
        continue
    
    rarity_score = 1 / (count / total_items)
    frequency = count
    
    print(f"{trait_type} - {trait_value} | rarity score = {rarity_score:.2f} | frequency = {frequency} / 20,000")
    
print("\nThe terminal output of this script is tracked as a text file here: https://github.com/nakamingos/nakamingos/blob/main/rarity/rarity-statistics.txt")
print("\nThe full rankings text file that this script produces is tracked here: https://github.com/nakamingos/nakamingos/blob/main/rarity/rarity-rankings.txt")
print("\ns/o to VirtualAlaska: https://github.com/VirtualAlaska and mfpurrs: https://x.com/mfpurrs")
