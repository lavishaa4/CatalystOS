import React, { useEffect, useRef } from 'react';
import * as $3Dmol from '3dmol';

interface MoleculeViewerProps {
  pdbUrl?: string;
}

export function MoleculeViewer({ pdbUrl = 'https://files.rcsb.org/download/1HTB.pdb' }: MoleculeViewerProps) {
  const viewerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!viewerRef.current) return;

    // Initialize 3Dmol viewer
    const viewer = $3Dmol.createViewer(viewerRef.current, {
      backgroundColor: '#09090b' // Zinc-950
    });

    fetch(pdbUrl)
      .then(res => res.text())
      .then(data => {
        viewer.addModel(data, "pdb");
        viewer.setStyle({}, { stick: { colorscheme: 'Jmol', radius: 0.15 }, sphere: { radius: 0.3 } });
        viewer.zoomTo();
        viewer.render();
      })
      .catch(err => console.error("Error loading molecule:", err));

    return () => {
      viewer.clear();
    };
  }, [pdbUrl]);

  return (
    <div className="relative w-full h-full min-h-[300px]">
      <div 
        ref={viewerRef} 
        className="absolute inset-0 rounded-lg bg-white ring-1 ring-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.3)] overflow-hidden"
      ></div>
      <div className="absolute bottom-2 right-2 text-[10px] text-cyan-500/50 font-mono z-10 pointer-events-none uppercase tracking-wider">
        3Dmol.js Renderer Active
      </div>
    </div>
  );
}
