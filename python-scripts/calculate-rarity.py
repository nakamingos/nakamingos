import json
from collections import defaultdict

# Step 1: Read the JSON File
with open(r"<ENTER FILE PATH HERE FOR NAKAMINGOS METADATA>", 'r') as json_file:
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

# Step 4: Calculate Rarity Score for Each Trait
def calculate_rarity_score(trait_type, trait_value):
    frequency = trait_value_counts[(trait_type, trait_value)]
    return total_items / frequency  # Rarity Score formula

# Step 5: Calculate Total Rarity Scores and Rankings
nft_rankings = []

for nft in nft_data['collection_items']:
    nft_traits = nft['item_attributes']
    total_rarity_score = 0  # Initialize total rarity score for the NFT
    rarity_scores = []  # Store rarity scores for each trait for later retrieval

    for trait in nft_traits:
        trait_type = trait.get('trait_type')  # Ensure 'trait_type' exists
        trait_value = trait.get('value')      # Ensure 'value' exists
        if trait_type in traits_to_exclude or trait_type == 'rarity':  # Skip excluded traits
            continue
        
        rarity_score = calculate_rarity_score(trait_type, trait_value)
        total_rarity_score += rarity_score  # Sum all trait rarity scores for the NFT
        rarity_scores.append((trait_type, trait_value, rarity_score))  # Store for later

    if rarity_scores:
        # Find the rarest trait based on the highest rarity score
        rarest_trait = max(rarity_scores, key=lambda x: x[2])
        nft_rankings.append((nft['name'], total_rarity_score, rarest_trait))

# Step 6: Order NFTs by Total Rarity Score (Descending)
nft_rankings.sort(key=lambda x: x[1], reverse=True)

# Step 7: Save Rarity Rankings to a File
txt_filename = r"<ENTER FILE PATH HERE FOR TEXT FILE LOCATION>"

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
    
    for rank, (nft_name, total_rarity_score, rarest_trait) in enumerate(nft_rankings, start=1):
        # Default to regular rank
        formatted_rank = f"{regular_rank_counter:05d}"

        # Extract Nakamingo number from the NFT name (e.g., Nakamingo #1234)
        nakamingo_number = int(nft_name.split("#")[1])  # Get the number part
        formatted_nft_name = f"Nakamingo #{nakamingo_number:05d}"  # Add leading zeros

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

        # Extract the rarest trait and its value
        rarest_trait_type, rarest_trait_value, _ = rarest_trait

        # Output the rarest trait (as requested)
        ranked_nfts.append((formatted_rank, formatted_nft_name, rarest_trait_type, rarest_trait_value, link))
    
    # Sort NFTs by rank to ensure "00001" is at the top
    ranked_nfts.sort(key=lambda x: x[0])

    # Write the sorted NFTs to the file
    for formatted_rank, formatted_nft_name, rarest_trait_type, rarest_trait_value, link in ranked_nfts:
        text = f"Rank {formatted_rank} - {formatted_nft_name} | Rarest trait = {rarest_trait_type} - {rarest_trait_value} | Link: {link}\n"
        txt_file.write(text)

# Step 8: Calculate and Print Rarity Scores for Traits
print("\n-------------------------------------------------------------\nRarity Scores for Traits (sorted by most rare to least rare):\n-------------------------------------------------------------")
for trait, count in sorted(trait_value_counts.items(), key=lambda x: (x[1] / total_items)):
    trait_type, trait_value = trait
    
    # Skip the 'rarity' trait_type and excluded traits
    if trait_type == 'rarity' or trait_type in traits_to_exclude:
        continue
    
    rarity_score = calculate_rarity_score(trait_type, trait_value)
    frequency = count
    
    print(f"{trait_type} - {trait_value} | rarity score = {rarity_score:.2f} | frequency = {frequency} / 20,000")
    
print("\nThe terminal output of this script is tracked as a text file here: https://github.com/nakamingos/nakamingos/blob/main/rarity/rarity-statistics.txt")
print("\nThe full rankings text file that this script produces is tracked here: https://github.com/nakamingos/nakamingos/blob/main/rarity/rarity-rankings.txt")
print("\ns/o to VirtualAlaska: https://github.com/VirtualAlaska and mfpurrs: https://x.com/mfpurrs")
