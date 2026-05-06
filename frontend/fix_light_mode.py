import os
import glob
import re

directories = ['C:/Users/Ananya/Desktop/AiForBharat/frontend/src/pages', 'C:/Users/Ananya/Desktop/AiForBharat/frontend/src/components']

def apply_global_rules(content, filepath):
    # 5. Global Clean-up
    content = content.replace('bg-zinc-950', 'bg-white')
    content = content.replace('bg-zinc-900', 'bg-zinc-50')
    
    # 1. Hardcoded Light-to-Dark Swap
    content = re.sub(r'text-white\b', 'text-zinc-950', content)
    content = re.sub(r'text-zinc-50\b', 'text-zinc-950', content)
    content = re.sub(r'text-zinc-100\b', 'text-zinc-950', content)
    
    content = re.sub(r'text-zinc-200\b', 'text-zinc-700', content)
    content = re.sub(r'text-zinc-300\b', 'text-zinc-700', content)
    content = re.sub(r'text-zinc-400\b', 'text-zinc-700', content)

    # 2. Sidebar & Logo Fix
    if 'AppShell.tsx' in filepath:
        # Change the 'OS' part of the logo to text-cyan-600
        content = content.replace('<span className="text-zinc-950">OS</span>', '<span className="text-cyan-600">OS</span>')
        # Also, because I replaced text-white with text-zinc-950 above, if it was text-white before, it's now text-zinc-950.
        
        # Navigation links use text-zinc-950
        content = re.sub(r'text-zinc-\d00 hover:text-zinc-\d00 hover:bg-zinc-\d0', 'text-zinc-950 hover:text-zinc-950 hover:bg-zinc-100', content)
        content = content.replace('text-zinc-700 hover:text-zinc-950', 'text-zinc-950 hover:text-zinc-950')
        content = content.replace('text-zinc-600 hover:text-zinc-950', 'text-zinc-950 hover:text-zinc-950')

    # 3 & 4. Pipeline Cards Fix & Top Candidates
    if 'Overview.tsx' in filepath:
        # Pipeline Cards
        content = re.sub(r'<div className="font-mono text-xs text-zinc-\d00 space-y-1">', '<div className="font-mono text-xs text-zinc-600 space-y-1">', content)
        content = re.sub(r'<span className="text-zinc-\d00">\{stage.product\}</span>', '<span className="text-zinc-900">{stage.product}</span>', content)
        content = re.sub(r'<span className="text-zinc-\d00">\{stage.condition\}</span>', '<span className="text-zinc-900">{stage.condition}</span>', content)
        
        # Top Candidates progress bar backgrounds
        content = re.sub(r'w-full h-1\.5 bg-zinc-\d00', 'w-full h-1.5 bg-zinc-100', content)

    # Copilot user message fix
    if 'Copilot.tsx' in filepath:
        content = content.replace('bg-cyan-600 text-zinc-950', 'bg-cyan-600 text-white')

    return content

for d in directories:
    for f in glob.glob(d + '/*.tsx'):
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        content = apply_global_rules(content, f)
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)

print("Replacement complete")
