# Infinite Canvas Skill

Build nested, navigable canvas UIs with React Flow. Users can zoom into nodes to reveal child canvases - infinite depth.

## When to Use

- Mind maps, knowledge graphs, visual databases
- Nested folder/category systems
- Any UI where items can contain other items
- Visual organization tools

## Architecture

```
React Flow (canvas) + Zustand (state) + Redis/DB (persistence)
```

## Core Concepts

### 1. Data Model

```typescript
interface CanvasNode {
  id: string;
  parentId: string | null;  // null = root level
  type: 'category' | 'container' | 'item';
  title: string;
  position: { x: number; y: number };
  childCount: number;  // cached for badges
  // Type-specific fields
  color?: string;
  icon?: string;
  content?: string;
  url?: string;
}

interface NavigationState {
  path: PathItem[];           // breadcrumb trail
  currentParentId: string | null;
  viewport: Viewport;         // saved per level
}
```

### 2. State Management (Zustand)

```typescript
import { create } from 'zustand';

interface CanvasStore {
  nodes: CanvasNode[];
  path: PathItem[];
  currentParentId: string | null;
  viewport: Viewport;
  loading: boolean;
  
  // Navigation
  navigateInto: (nodeId: string) => void;
  navigateBack: () => void;
  loadLevel: (parentId: string | null) => Promise<void>;
  
  // CRUD
  createNode: (data: Partial<CanvasNode>) => Promise<void>;
  updateNode: (id: string, data: Partial<CanvasNode>) => Promise<void>;
  deleteNode: (id: string) => Promise<void>;
  updatePositions: (updates: PositionUpdate[]) => Promise<void>;
}

export const useCanvasStore = create<CanvasStore>((set, get) => ({
  nodes: [],
  path: [{ id: 'root', title: 'Home' }],
  currentParentId: null,
  viewport: { x: 0, y: 0, zoom: 0.75 },
  loading: false,

  navigateInto: async (nodeId) => {
    const node = get().nodes.find(n => n.id === nodeId);
    if (!node) return;
    
    set(state => ({
      path: [...state.path, { id: node.id, title: node.title }],
      currentParentId: node.id,
    }));
    
    await get().loadLevel(nodeId);
  },

  navigateBack: async () => {
    const { path } = get();
    if (path.length <= 1) return;
    
    const newPath = path.slice(0, -1);
    const newParentId = newPath.length > 1 ? newPath[newPath.length - 1].id : null;
    
    set({ path: newPath, currentParentId: newParentId });
    await get().loadLevel(newParentId);
  },

  loadLevel: async (parentId) => {
    set({ loading: true });
    const res = await fetch(`/api/nodes?parentId=${parentId || 'root'}`);
    const { nodes, viewport } = await res.json();
    set({ nodes, viewport, loading: false });
  },
}));
```

### 3. Canvas Component

```tsx
import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react';
import { useCanvasStore } from '../lib/store';

export default function Canvas() {
  const { nodes, currentParentId, updatePositions } = useCanvasStore();
  
  const flowNodes = nodes.map(node => ({
    id: node.id,
    type: node.type,
    position: node.position,
    data: { node },
  }));

  const handleNodeDragStop = (event, node) => {
    // Debounce save positions to API
    updatePositions([{ id: node.id, position: node.position }]);
  };

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={[]}
      nodeTypes={nodeTypes}
      onNodeDragStop={handleNodeDragStop}
      minZoom={0.1}
      maxZoom={2}
    >
      <Background />
      <Controls />
      <MiniMap />
    </ReactFlow>
  );
}
```

### 4. Custom Node Components

```tsx
function CategoryNode({ data, selected }) {
  const { navigateInto } = useCanvasStore();
  const node = data.node;

  const handleDoubleClick = () => {
    if (node.childCount > 0) {
      navigateInto(node.id);
    }
  };

  return (
    <div
      onDoubleClick={handleDoubleClick}
      className={`p-4 rounded-xl border-2 cursor-pointer ${
        selected ? 'ring-2 ring-white/30' : ''
      }`}
      style={{ borderColor: node.color }}
    >
      <span className="text-2xl">{node.icon}</span>
      <h3 className="font-bold">{node.title}</h3>
      {node.childCount > 0 && (
        <span className="text-xs opacity-60">{node.childCount} items</span>
      )}
    </div>
  );
}
```

### 5. Breadcrumb Navigation

```tsx
function Breadcrumb() {
  const { path, loadLevel } = useCanvasStore();

  return (
    <nav className="flex items-center gap-2">
      {path.map((item, index) => (
        <Fragment key={item.id}>
          {index > 0 && <ChevronRight className="w-4 h-4" />}
          <button
            onClick={() => {
              const newPath = path.slice(0, index + 1);
              const parentId = index === 0 ? null : item.id;
              loadLevel(parentId);
            }}
            className={index === path.length - 1 ? 'font-bold' : 'opacity-60'}
          >
            {item.title}
          </button>
        </Fragment>
      ))}
    </nav>
  );
}
```

### 6. API Routes (Next.js)

```typescript
// /api/nodes/route.ts
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const parentId = searchParams.get('parentId');
  
  const nodes = await redis.getChildren(parentId === 'root' ? null : parentId);
  const viewport = await redis.getViewport(parentId);
  
  return Response.json({ nodes, viewport });
}

export async function POST(request: Request) {
  const body = await request.json();
  const node = await redis.createNode(body);
  return Response.json({ node });
}
```

## Keyboard Shortcuts

```typescript
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape' && path.length > 1) {
      navigateBack();
    }
  };
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [path.length, navigateBack]);
```

## Dependencies

```json
{
  "@xyflow/react": "^12.0.0",
  "zustand": "^4.5.0",
  "framer-motion": "^11.0.0"
}
```

## Best Practices

1. **Save viewport per level** - restore when navigating back
2. **Cache childCount** - show badges without loading children
3. **Debounce position saves** - don't spam API on every drag
4. **Use Framer Motion** - smooth transitions between levels
5. **Lazy load** - only fetch nodes for current level

## Files

- `examples/store.ts` - Full Zustand store
- `examples/Canvas.tsx` - Canvas component
- `examples/nodes/` - Custom node components
- `templates/` - Starter template
