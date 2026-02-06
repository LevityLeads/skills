# Glassmorphism UI Skill

Modern glassmorphism styling with Tailwind CSS. Frosted glass effects, subtle gradients, and depth.

## When to Use

- Dark-themed dashboards and apps
- Cards that need visual depth
- Modern SaaS interfaces
- Data visualization overlays

## Core Patterns

### 1. Base Card

```tsx
<div className="
  rounded-xl 
  border border-white/10 
  bg-zinc-900/80 
  backdrop-blur-md 
  shadow-xl
">
  {/* content */}
</div>
```

### 2. With Accent Color

```tsx
<div 
  className="rounded-xl border-2 backdrop-blur-md"
  style={{
    backgroundColor: `${accentColor}15`,  // 15% opacity
    borderColor: accentColor,
    boxShadow: `0 0 20px ${accentColor}20`  // subtle glow
  }}
>
```

### 3. Gradient Header

```tsx
<div className="rounded-xl overflow-hidden border border-white/10">
  {/* Header with gradient */}
  <div className="px-4 py-3 bg-gradient-to-r from-blue-500/20 to-purple-500/20 border-b border-white/10">
    <h3 className="font-semibold text-white">Title</h3>
  </div>
  
  {/* Body */}
  <div className="p-4 bg-zinc-900/80 backdrop-blur-md">
    {/* content */}
  </div>
</div>
```

### 4. Interactive States

```tsx
<button className="
  px-4 py-2 
  rounded-lg 
  bg-white/10 
  hover:bg-white/20 
  active:bg-white/25
  border border-white/10
  text-white 
  transition-all
">
  Click me
</button>
```

### 5. Color-Coded Cards

```typescript
const COLORS = {
  blue: { bg: 'rgba(59, 130, 246, 0.15)', border: '#3b82f6' },
  green: { bg: 'rgba(34, 197, 94, 0.15)', border: '#22c55e' },
  purple: { bg: 'rgba(168, 85, 247, 0.15)', border: '#a855f7' },
  amber: { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b' },
  rose: { bg: 'rgba(244, 63, 94, 0.15)', border: '#f43f5e' },
};

function Card({ color, children }) {
  const { bg, border } = COLORS[color];
  return (
    <div 
      className="rounded-xl border-2 backdrop-blur-md p-4"
      style={{ backgroundColor: bg, borderColor: border }}
    >
      {children}
    </div>
  );
}
```

### 6. Modal Overlay

```tsx
<div className="fixed inset-0 z-50 flex items-center justify-center">
  {/* Backdrop */}
  <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
  
  {/* Modal */}
  <div className="
    relative z-10
    w-full max-w-lg
    rounded-2xl 
    border border-white/10 
    bg-zinc-900/90 
    backdrop-blur-xl 
    shadow-2xl
    p-6
  ">
    {/* content */}
  </div>
</div>
```

### 7. Input Fields

```tsx
<input
  type="text"
  className="
    w-full px-4 py-2
    rounded-lg
    bg-white/5
    border border-white/10
    text-white
    placeholder-zinc-500
    focus:outline-none
    focus:border-white/30
    focus:bg-white/10
    transition-colors
  "
  placeholder="Enter text..."
/>
```

### 8. Semantic Zoom Scaling

```typescript
// Scale cards based on content importance
function getScale(itemCount: number): number {
  if (itemCount >= 20) return 1.15;
  if (itemCount >= 10) return 1.08;
  if (itemCount >= 5) return 1.03;
  return 1;
}

function getGlowIntensity(itemCount: number): number {
  return Math.min(itemCount / 20, 1);
}

// Usage
<div style={{
  transform: `scale(${getScale(count)})`,
  boxShadow: `0 0 ${20 * glowIntensity}px ${color}40`
}}>
```

## Tailwind Config

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        zinc: {
          950: '#09090b',
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
};
```

## CSS Variables

```css
/* globals.css */
:root {
  --glass-bg: rgba(24, 24, 27, 0.8);
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-blur: 12px;
}

.glass {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(var(--glass-blur));
}
```

## Best Practices

1. **Use zinc-950 for backgrounds** - true black looks harsh
2. **Keep opacity low (10-20%)** - subtlety is key
3. **Add border-white/10** - defines edges without being harsh
4. **Use backdrop-blur-md** - too much blur looks muddy
5. **Add subtle shadows** - creates depth
6. **Animate transitions** - smooth state changes

## Anti-Patterns

❌ Don't use pure white text - use zinc-100 or zinc-200
❌ Don't overdo the blur - backdrop-blur-md is usually enough  
❌ Don't forget borders - glass needs edges to look right
❌ Don't use on light backgrounds - glassmorphism needs dark mode
