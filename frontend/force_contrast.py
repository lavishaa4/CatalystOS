import os
import glob
import re

directories = ['C:/Users/Ananya/Desktop/AiForBharat/frontend/src/pages', 'C:/Users/Ananya/Desktop/AiForBharat/frontend/src/components']

def apply_global_rules(content, filepath):
    # 1. Global Typography Reset: replace all text-white, text-zinc-50, text-zinc-100, and text-zinc-200 with text-zinc-900.
    content = re.sub(r'text-white\b', 'text-zinc-900', content)
    content = re.sub(r'text-zinc-50\b', 'text-zinc-900', content)
    content = re.sub(r'text-zinc-100\b', 'text-zinc-900', content)
    content = re.sub(r'text-zinc-200\b', 'text-zinc-900', content)
    
    # 4. Dashboard Headers (System Overview, Real-time telemetry) should be 900
    if 'Overview.tsx' in filepath:
        # 5. System Log & Candidates: Force all log entries and candidate names to text-zinc-800.
        content = content.replace('text-zinc-900 shrink-0', 'text-zinc-800 shrink-0') # log time
        content = content.replace('flex gap-3 text-zinc-900', 'flex gap-3 text-zinc-800') # log row
        # candidate names
        content = content.replace('font-mono text-zinc-900 text-sm">{cat.name}', 'font-mono text-zinc-800 text-sm">{cat.name}')
        # Make sure target/condition/catalyst labels are 500
        content = re.sub(r'<div className="font-mono text-xs text-zinc-\d00 space-y-1">', '<div className="font-mono text-xs text-zinc-500 space-y-1">', content)
        # Make sure values are 900
        content = re.sub(r'<span className="text-zinc-\d00">\{stage.product\}</span>', '<span className="text-zinc-900">{stage.product}</span>', content)
        content = re.sub(r'<span className="text-zinc-\d00">\{stage.catalyst\}</span>', '<span className="text-zinc-900">{stage.catalyst}</span>', content)
        content = re.sub(r'<span className="text-zinc-\d00">\{stage.condition\}</span>', '<span className="text-zinc-900">{stage.condition}</span>', content)
        # Progress bar backgrounds
        content = re.sub(r'w-full h-1\.5 bg-zinc-\d00', 'w-full h-1.5 bg-zinc-100', content)
        
    if 'Copilot.tsx' in filepath:
        # Preserve user message white text exception
        content = content.replace('bg-cyan-600 text-zinc-900', 'bg-cyan-600 text-white')

    return content

for d in directories:
    for f in glob.glob(d + '/*.tsx'):
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Don't overwrite AppShell's manual fixes for logo/nav
        if 'AppShell.tsx' not in f:
            content = apply_global_rules(content, f)
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
        else:
            # We already fixed AppShell manually, but let's just make sure text-zinc-200 is replaced
            content = content.replace('text-zinc-200', 'text-zinc-800')
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)

print("Replacement complete")
