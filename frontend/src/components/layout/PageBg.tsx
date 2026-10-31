import React, { useEffect, useRef } from 'react';

interface Props {
  /** 'home' uses home color + monochromo home; 'app' uses neon circuit + mono circuit */
  bg?: 'home' | 'app';
  children: React.ReactNode;
  className?: string;
  showCursorRing?: boolean;
}

const BG_SETS = {
  home: {
    color: '/bg-home-color.png',
    mono: '/bg-home-mono.png',
  },
  app: {
    color: '/bg-app-color.png',
    mono: '/bg-app-mono.png',
  },
};

/**
 * Full-page wrapper with layered backgrounds and cursor-reveal effect.
 * Base layer = 100% full vibrant color background (no black dimming overlay).
 * Top layer = monochrome (black & white) image masked so it ONLY appears
 * in a circular spotlight where the cursor is.
 */
export const PageBg: React.FC<Props> = ({
  bg = 'app',
  children,
  className = '',
  showCursorRing = true,
}) => {
  const ringRef = useRef<HTMLDivElement>(null);
  const monoRef = useRef<HTMLDivElement>(null);
  const { color, mono } = BG_SETS[bg];

  useEffect(() => {
    const handlePointerMove = (e: PointerEvent) => {
      const x = e.clientX;
      const y = e.clientY;

      if (monoRef.current) {
        monoRef.current.style.setProperty('--cx', `${x}px`);
        monoRef.current.style.setProperty('--cy', `${y}px`);
      }

      if (ringRef.current) {
        ringRef.current.style.transform = `translate3d(${x - 140}px, ${y - 140}px, 0)`;
        ringRef.current.style.opacity = '1';
      }
    };

    const handlePointerLeave = () => {
      if (ringRef.current) {
        ringRef.current.style.opacity = '0';
      }
    };

    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerleave', handlePointerLeave);

    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerleave', handlePointerLeave);
    };
  }, []);

  return (
    <div className={`relative min-h-screen text-slate-100 ${className}`}>
      {/* Fixed Background Stack */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        {/* 1. Base Color Layer (100% full vibrant image, no dark shadow) */}
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-cover bg-center opacity-100 transition-opacity duration-300"
          style={{ backgroundImage: `url('${color}')` }}
        />

        {/* 2. Monochrome Layer - appears as a circle where the cursor moves */}
        <div
          ref={monoRef}
          aria-hidden="true"
          className="absolute inset-0 bg-cover bg-center opacity-100 pointer-events-none bg-reveal-mono transition-opacity duration-300"
          style={{ backgroundImage: `url('${mono}')` }}
        />

        {/* 3. Cyberpunk Cursor Spotlight Ring */}
        {showCursorRing && (
          <div
            ref={ringRef}
            aria-hidden="true"
            className="pointer-events-none fixed top-0 left-0 w-[280px] h-[280px] rounded-full border border-primary/50 shadow-[0_0_25px_rgba(232,0,120,0.4)] transition-opacity duration-150 opacity-0"
            style={{ willChange: 'transform' }}
          >
            {/* Cyber reticle crosshairs */}
            <div className="absolute top-1/2 left-0 right-0 h-[1px] bg-primary/30 -translate-y-1/2" />
            <div className="absolute left-1/2 top-0 bottom-0 w-[1px] bg-primary/30 -translate-x-1/2" />
            <div className="absolute top-1/2 left-1/2 w-2 h-2 rounded-full bg-primary -translate-x-1/2 -translate-y-1/2 shadow-[0_0_8px_#e80078]" />
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 text-[9px] font-mono text-primary tracking-widest uppercase">
              B&amp;W SENSOR
            </div>
          </div>
        )}
      </div>

      {/* Page Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};
