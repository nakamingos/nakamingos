import os
import re
import json
import sys
from collections import defaultdict

# Interactive file input with smart path resolution
raw_input_path = input("Enter path to metadata JSON file: ").strip()
expanded_path = os.path.expanduser(raw_input_path)
abs_path = os.path.abspath(expanded_path)

base_dir = os.path.dirname(os.path.realpath(__file__))

# Smart path resolution - try multiple locations
if not os.path.isfile(abs_path):
    project_root = os.path.normpath(os.path.join(base_dir, '..'))
    candidate = os.path.normpath(os.path.join(project_root, raw_input_path))
    if os.path.isfile(candidate):
        input_meta = candidate
    else:
        print(f"Error: File not found: {abs_path}")
        sys.exit(1)
else:
    input_meta = abs_path

# File management setup
input_meta = os.path.normpath(input_meta)
metadata_dir = os.path.dirname(input_meta)
base_name = os.path.splitext(os.path.basename(input_meta))[0]
rarity_dir = os.path.normpath(os.path.join(base_dir, '..', 'rarity'))

# Ensure directories exist
os.makedirs(metadata_dir, exist_ok=True)
os.makedirs(rarity_dir, exist_ok=True)

# Versioning system function
def next_version(dir_path, pattern):
    max_ver = 0
    for fname in os.listdir(dir_path):
        match = re.match(pattern, fname)
        if match:
            try:
                ver = int(match.group(1))
                if ver > max_ver:
                    max_ver = ver
            except ValueError:
                continue
    return max_ver + 1

# File patterns and paths (Nakamingos-specific naming)
json_pattern = rf"^{re.escape(base_name)}-new(\d+)\.json$"
rank_static = os.path.join(rarity_dir, f"{base_name}-rarity-rankings.txt")
stats_static = os.path.join(rarity_dir, f"{base_name}-rarity-statistics.txt")

new_json_ver = next_version(metadata_dir, json_pattern)
new_rank_ver = next_version(rarity_dir, rf"^{re.escape(base_name)}-rarity-rankings-new(\d+)\.txt$") if os.path.exists(rank_static) else None
new_stats_ver = next_version(rarity_dir, rf"^{re.escape(base_name)}-rarity-statistics-new(\d+)\.txt$") if os.path.exists(stats_static) else None

# Define output file paths
output_meta = os.path.join(metadata_dir, f"{base_name}-new{new_json_ver}.json")
output_rank = os.path.join(rarity_dir, f"{base_name}-rarity-rankings-new{new_rank_ver}.txt") if new_rank_ver else rank_static
output_stats = os.path.join(rarity_dir, f"{base_name}-rarity-statistics-new{new_stats_ver}.txt") if new_stats_ver else stats_static

# Load and validate data
with open(input_meta, 'r', encoding='utf-8') as f:
    nft_data = json.load(f)

# Flexible data extraction but prefer Nakamingos structure
if isinstance(nft_data, list):
    items = nft_data
elif 'collection_items' in nft_data:
    items = nft_data['collection_items']
elif 'items' in nft_data:
    items = nft_data['items']
else:
    items = []

if not items:
    print("No items found in metadata.")
    sys.exit(1)

total_retrieved = len(items)

# Collection size validation
if total_retrieved > 0:
    print(f"Retrieved {total_retrieved} items. Version: new{new_json_ver}\nCalculating rarity...")

# Step 3: Calculate Trait Value Frequencies (excluding Featured Artist traits)
trait_value_counts = defaultdict(int)
total_items = len(items)

# Traits to filter out from the rarity calculations
traits_to_exclude = {"Wisdom/Magic", "Power/Strength", "Speed/Agility", "Origin"}

for item in items:
    for attr in item.get('item_attributes', []):
        trait_type = attr.get('trait_type')  # Ensure 'trait_type' exists
        trait_value = attr.get('value')      # Ensure 'value' exists
        # Skip Featured Artist trait type and metadata traits to avoid inflating rarity scores
        if (trait_type and trait_value and 
            trait_type not in traits_to_exclude and 
            trait_type.lower() not in ['rarity', 'rank'] and 
            trait_type != 'Featured Artist'):
            trait_value_counts[(trait_type, trait_value)] += 1

# Step 4: Calculate Rarity Score for Each Trait
def calculate_rarity_score(trait_type, trait_value):
    frequency = trait_value_counts[(trait_type, trait_value)]
    return total_items / frequency  # Rarity Score formula

# Step 5: Calculate Total Rarity Scores and Rankings
# Dynamically identify Featured Artists by their trait
def is_featured_artist(item):
    """Check if an item is a Featured Artist based on its traits"""
    for attr in item.get('item_attributes', []):
        if attr.get('trait_type') == 'Featured Artist':
            return True
    return False

nft_rankings = []

for nft in items:
    nft_traits = nft.get('item_attributes', [])
    total_rarity_score = 0  # Initialize total rarity score for the NFT
    rarity_scores = []  # Store rarity scores for each trait for later retrieval

    for trait in nft_traits:
        trait_type = trait.get('trait_type')  # Ensure 'trait_type' exists
        trait_value = trait.get('value')      # Ensure 'value' exists
        # Skip excluded traits, metadata traits and Featured Artist traits in scoring
        if (trait_type in traits_to_exclude or 
            trait_type.lower() in ['rarity', 'rank'] or 
            trait_type == 'Featured Artist'):  
            continue
        
        rarity_score = calculate_rarity_score(trait_type, trait_value)
        total_rarity_score += rarity_score  # Sum all trait rarity scores for the NFT
        rarity_scores.append((trait_type, trait_value, rarity_score))  # Store for later

    if rarity_scores:
        # Find the rarest trait based on the highest rarity score
        rarest_trait = max(rarity_scores, key=lambda x: x[2])
        nft_rankings.append((nft.get('name', ''), total_rarity_score, rarest_trait, nft))
    elif is_featured_artist(nft):
        # Featured Artists get added with special handling (they have no calculated rarity scores)
        # Find their Featured Artist trait to display as "rarest"
        featured_trait = None
        for trait in nft_traits:
            if trait.get('trait_type') == 'Featured Artist':
                featured_trait = ('Featured Artist', trait.get('value'), 999999)  # High dummy score for sorting
                break
        if featured_trait:
            nft_rankings.append((nft.get('name', ''), 999999, featured_trait, nft))  # High score to rank at top

# Step 6: Order NFTs by Total Rarity Score (Descending)
nft_rankings.sort(key=lambda x: x[1], reverse=True)

# Step 7: Save Rarity Rankings to a File

# First, identify Featured Artists and assign them rank 1
featured_artist_ids = set()
for item in items:
    if is_featured_artist(item):
        featured_artist_ids.add(item.get('ethscription_id', item.get('id', '')))

# Assign ranks based on whether Featured Artists exist
ranked_nfts = []
ranks = {}
has_featured_artists = len(featured_artist_ids) > 0
regular_rank_counter = 2 if has_featured_artists else 1  # Start from 1 if no Featured Artists

# First assign rank 1 to Featured Artists if they exist
for item_id in featured_artist_ids:
    ranks[item_id] = 1

for rank, (nft_name, total_rarity_score, rarest_trait, nft_item) in enumerate(nft_rankings, start=1):
    # Calculate the number of digits needed based on collection size
    num_digits = len(str(total_items))
    
    # Check if the current NFT is a Featured Artist
    if is_featured_artist(nft_item):
        formatted_rank = 1
        rank_str = "1".zfill(num_digits)  # Pad with correct number of zeros
    else:
        if has_featured_artists:
            # If we have Featured Artists, start regular items at 2
            formatted_rank = regular_rank_counter
            rank_str = str(regular_rank_counter).zfill(num_digits)
            regular_rank_counter += 1
        else:
            # If no Featured Artists, use sequential ranking starting at 1
            formatted_rank = rank
            rank_str = str(rank).zfill(num_digits)

    # Store rank for metadata updating (Featured Artists already have rank 1)
    ethscription_id = nft_item.get('ethscription_id', nft_item.get('id', ''))
    if ethscription_id not in featured_artist_ids:
        ranks[ethscription_id] = formatted_rank

    # Calculate the number of digits needed based on collection size
    num_digits = len(str(total_items))
    
    # Extract the base name and number from the NFT name (e.g., "Nakamingo #1234" or "DarkNezz #123")
    name_parts = nft_name.split("#")
    if len(name_parts) == 2:
        base_name = name_parts[0].strip()
        try:
            number = int(name_parts[1])
            formatted_nft_name = f"{base_name} #{number:0{num_digits}d}"
        except ValueError:
            # If we can't parse the number, use the original name
            formatted_nft_name = nft_name
    else:
        # If the name doesn't follow the "#" format, use it as is
        formatted_nft_name = nft_name

    link = f"https://ethscriptions.com/ethscriptions/{ethscription_id}"

    # Extract the rarest trait and its value
    rarest_trait_type, rarest_trait_value, _ = rarest_trait

    # Output the rarest trait (as requested)
    ranked_nfts.append((rank_str, formatted_nft_name, rarest_trait_type, rarest_trait_value, link))

# Sort NFTs by rank to ensure "00001" is at the top
ranked_nfts.sort(key=lambda x: x[0])

# Update metadata with rarity values
for item in items:
    eid = item.get('ethscription_id', item.get('id'))
    
    # Get rank - Featured Artists get rank 1, others get their calculated rank
    if is_featured_artist(item):
        rank_val = 1
    else:
        rank_val = ranks.get(eid)
    
    if rank_val is None:
        continue
    
    # Remove any existing rank or rarity traits
    item['item_attributes'] = [attr for attr in item.get('item_attributes', []) 
                             if attr.get('trait_type', '').lower() not in ['rank', 'rarity']]
    
    # Add new rank trait
    item.setdefault('item_attributes', []).append({'trait_type': 'Rank', 'value': rank_val})

# Write updated metadata
with open(output_meta, 'w', encoding='utf-8') as f:
    json.dump(nft_data, f, ensure_ascii=False, indent=4)
print(f"Wrote updated metadata to {output_meta}")

# Write the rankings to file
with open(output_rank, 'w', encoding='utf-8') as txt_file:
    for formatted_rank, formatted_nft_name, rarest_trait_type, rarest_trait_value, link in ranked_nfts:
        text = f"Rank {formatted_rank} - {formatted_nft_name} | Rarest trait = {rarest_trait_type} - {rarest_trait_value} | Link: {link}\n"
        txt_file.write(text)
print(f"Wrote rankings to {output_rank}")

# Step 8: Calculate and Print Rarity Scores for Traits
# Collect Featured Artist traits separately (for display purposes only)
featured_artist_traits = defaultdict(int)

for item in items:
    for attr in item.get('item_attributes', []):
        trait_type = attr.get('trait_type')
        trait_value = attr.get('value')
        
        if trait_type == 'Featured Artist':
            # Count Featured Artist traits for display only
            featured_artist_traits[(trait_type, trait_value)] += 1

# Prepare regular trait entries
regular_trait_entries = []
for (trait_type, trait_value), count in trait_value_counts.items():
    entry = ((trait_type, trait_value), count)
    regular_trait_entries.append(entry)

# Sort regular traits by rarity score descending
regular_trait_entries.sort(key=lambda x: (total_items / x[1] if x[1] else 0), reverse=True)

# Prepare Featured Artist entries for display
featured_entries = []
for (trait_type, trait_value), count in featured_artist_traits.items():
    entry = ((trait_type, trait_value), count)
    featured_entries.append(entry)

# Sort Featured Artist entries by rarity score descending
featured_entries.sort(key=lambda x: (total_items / x[1] if x[1] else 0), reverse=True)

with open(output_stats, 'w', encoding='utf-8') as f:
    if featured_entries:
        f.write("-------------------------------------------------------------\n")
        f.write("Rarity Scores for Traits (Featured Artist traits shown separately):\n")
        f.write("-------------------------------------------------------------\n")
        f.write("NOTE: Featured Artist traits are excluded from rarity calculations\n")
        f.write("to prevent inflation of common trait rarity scores.\n\n")
        f.write("FEATURED ARTIST TRAITS (not included in rarity calculations):\n")
        for (trait_type, trait_value), count in featured_entries:
            f.write(f"{trait_type} - {trait_value} | frequency = {count} / {total_items} (excluded from scoring)\n")
        f.write("\nREGULAR TRAITS (used in rarity calculations):\n")
    else:
        f.write("-------------------------------------------------------------\n")
        f.write("Rarity Scores for Traits:\n")
        f.write("-------------------------------------------------------------\n")
    
    # Then regular traits (these are actually used in calculations)
    for (trait_type, trait_value), count in regular_trait_entries:
        rarity_score = calculate_rarity_score(trait_type, trait_value)
        f.write(f"{trait_type} - {trait_value} | rarity score = {rarity_score:.2f} | frequency = {count} / {total_items}\n")

print(f"Wrote statistics to {output_stats}")

print("\n-------------------------------------------------------------\nRarity Scores for Traits (sorted by most rare to least rare):\n-------------------------------------------------------------")
if featured_entries:
    print("NOTE: Featured Artist traits are excluded from calculations")
for trait, count in sorted(trait_value_counts.items(), key=lambda x: (x[1] / total_items)):
    trait_type, trait_value = trait
    
    rarity_score = calculate_rarity_score(trait_type, trait_value)
    frequency = count
    
    print(f"{trait_type} - {trait_value} | rarity score = {rarity_score:.2f} | frequency = {frequency} / {total_items}")
    
print("\nThe terminal output of this script is tracked as a text file here: https://github.com/nakamingos/nakamingos/blob/main/rarity/nakamingos-rarity-statistics.txt")
print("\nThe full rankings text file that this script produces is tracked here: https://github.com/nakamingos/nakamingos/blob/main/rarity/nakamingos-rarity-rankings.txt")
print("\ns/o to VirtualAlaska: https://github.com/VirtualAlaska and mfpurrs: https://x.com/mfpurrs")