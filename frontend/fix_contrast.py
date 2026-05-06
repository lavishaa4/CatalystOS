import os
import glob
import re

directories = ['C:/Users/Ananya/Desktop/AiForBharat/frontend/src/pages', 'C:/Users/Ananya/Desktop/AiForBharat/frontend/src/components']

def apply_rules(content, filepath):
    if 'AppShell.tsx' in filepath:
        # Already manually handled AppShell, just do icons
        content = re.sub(r'text-cyan-400\b', 'text-cyan-700', content)
        content = re.sub(r'text-cyan-500\b', 'text-cyan-700', content)
        return content

    # Rule 1: Global Text Swap
    content = re.sub(r'text-white', 'text-zinc-900', content)
    content = re.sub(r'text-zinc-50\b', 'text-zinc-900', content)
    content = re.sub(r'text-zinc-100\b', 'text-zinc-900', content)
    content = re.sub(r'text-zinc-200\b', 'text-zinc-800', content)
    content = re.sub(r'text-zinc-300\b', 'text-zinc-800', content)
    
    # Rule 3: Card & Dashboard Content (Discovery and Overview)
    content = re.sub(r'text-zinc-400\b', 'text-zinc-700', content)
    
    # Rule 4: Icon Visibility (Update Lucide icons)
    content = re.sub(r'text-cyan-400\b', 'text-cyan-700', content)
    
    # Backgrounds and borders (optional but good for light mode)
    # The user didn't ask to change backgrounds globally, only text contrast!
    # "Perform a global text contrast overhaul to support the new Light Mode theme."
    # So I will strictly stick to text colors.

    # Rule 5: Copilot Refinement
    if 'Copilot.tsx' in filepath:
        # Fix user bubble text to stay white (bg-cyan-600 text-white)
        # Because global rule might have changed it to text-zinc-900
        content = content.replace('bg-cyan-600 text-zinc-900', 'bg-cyan-600 text-white')
        content = content.replace('bg-cyan-600 text-zinc-800', 'bg-cyan-600 text-white')
        
        # Bot's response text is strictly text-zinc-800
        content = content.replace('bg-white border border-zinc-200 text-zinc-900 shadow-sm', 'bg-white border border-zinc-200 text-zinc-800 shadow-sm')
        
        # 'Sources Referenced' label is text-zinc-500
        content = content.replace('text-[10px] uppercase font-bold tracking-wider text-zinc-700 font-mono">Sources referenced', 'text-[10px] uppercase font-bold tracking-wider text-zinc-500 font-mono">Sources referenced')
        
        # Link texts
        content = content.replace('text-cyan-700 font-mono hover:border-cyan-500', 'text-cyan-700 font-mono hover:border-cyan-700')

    return content

for d in directories:
    for f in glob.glob(d + '/*.tsx'):
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        new_content = apply_rules(content, f)
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
print("Done")
