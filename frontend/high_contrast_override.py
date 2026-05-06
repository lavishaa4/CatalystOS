import os
import glob
import re

directories = ['C:/Users/Ananya/Desktop/AiForBharat/frontend/src/pages', 'C:/Users/Ananya/Desktop/AiForBharat/frontend/src/components']

def apply_global_rules(content, filepath):
    filename = os.path.basename(filepath)
    
    # We will preserve some specific things if needed, but the prompt says "Global Text Override"
    # To avoid breaking the user's recent manual edits in Overview and AppShell, we might want to be careful.
    # Actually, the user specifically gave instructions for AppShell and Overview in the prompt:
    
    if filename == 'AppShell.tsx':
        # 3. Sidebar (AppShell.tsx)
        # Set navigation links to text-zinc-600 with a hover state of text-zinc-950.
        content = re.sub(r'text-zinc-\d00 hover:text-zinc-\d00', 'text-zinc-600 hover:text-zinc-950', content)
        
        # Set the active link state to bg-cyan-50 text-cyan-800 border-cyan-200.
        # The user's manual edit currently has: "bg-cyan-100 text-cyan-900 border border-cyan-200 shadow-sm"
        content = content.replace('bg-cyan-100 text-cyan-900 border border-cyan-200', 'bg-cyan-50 text-cyan-800 border border-cyan-200')
        
        # Logo is already text-zinc-950 in user's manual edit
        
    elif filename == 'Overview.tsx':
        # 4. Dashboard Cards (Overview.tsx)
        # Change all card backgrounds from bg-zinc-900 or bg-zinc-800 to bg-white.
        # Add a border border-zinc-200 and a shadow-sm to every card.
        # (User already did most of this, but let's ensure it)
        
        # In the Reaction Pipeline, change the data labels (Target, Catalyst, Condition) to text-zinc-500 and values to text-zinc-900.
        # User manual edit has: <span className="text-zinc-400">Target:</span>
        content = content.replace('"text-zinc-400">Target:', '"text-zinc-500">Target:')
        content = content.replace('"text-zinc-400">Catalyst:', '"text-zinc-500">Catalyst:')
        content = content.replace('"text-zinc-400">Condition:', '"text-zinc-500">Condition:')
        
        # Values are text-zinc-900 already.
        
        # 5. Progress Bars: bg-zinc-100 container, bg-cyan-600 fill
        # User manual edit has: className="w-full h-2 bg-zinc-200 rounded-full overflow-hidden"
        content = content.replace('w-full h-2 bg-zinc-200 rounded-full overflow-hidden', 'w-full h-2 bg-zinc-100 rounded-full overflow-hidden')
        
        # 6. System Log: terminal background bg-zinc-900, text text-zinc-300, AI mentions text-cyan-400
        # User manual edit already has this.
        
    else:
        # For all other files (Discovery, Prediction, GapIntelligence, Copilot)
        
        # 4. Dashboard Cards generally: bg-zinc-900/800 to bg-white border border-zinc-200 shadow-sm
        content = re.sub(r'bg-zinc-900/50 border border-zinc-800', 'bg-white border border-zinc-200 shadow-sm', content)
        content = re.sub(r'bg-zinc-900 border border-zinc-800', 'bg-white border border-zinc-200 shadow-sm', content)
        content = re.sub(r'bg-zinc-800 border border-zinc-700', 'bg-white border border-zinc-200 shadow-sm', content)
        content = re.sub(r'bg-zinc-950', 'bg-white', content)
        content = re.sub(r'bg-zinc-900', 'bg-zinc-50', content)
        
        # Preserve Copilot user message text-white exception if it's there
        # We will temporarily hide it
        content = content.replace('bg-cyan-600 text-white', 'TEMP_CYAN_WHITE')
        
        # 1. Global Text Override
        content = re.sub(r'text-white\b', 'text-zinc-950', content)
        content = re.sub(r'text-zinc-50\b', 'text-zinc-950', content)
        content = re.sub(r'text-zinc-100\b', 'text-zinc-950', content)
        content = re.sub(r'text-zinc-200\b', 'text-zinc-950', content)
        
        # 2. Muted Text Fix
        content = re.sub(r'text-zinc-300\b', 'text-zinc-600', content)
        content = re.sub(r'text-zinc-400\b', 'text-zinc-600', content)
        
        # Restore Copilot user message exception
        content = content.replace('TEMP_CYAN_WHITE', 'bg-cyan-600 text-white')
        
    return content

for d in directories:
    for f in glob.glob(d + '/*.tsx'):
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        content = apply_global_rules(content, f)
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)

print("High-contrast Light Mode override complete.")
