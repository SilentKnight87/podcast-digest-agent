# Podcast Digest Agent - UI Specifications

## Status: 🚀 IN PROGRESS

**Start Date**: May 2024
**Priority**: High
**Progress**: ~80% Complete

### Implementation Status
- ✅ Design system defined
- ✅ Core components built
- ✅ Hero section implemented
- ✅ Processing visualizer complete
- ✅ Dark mode support
- 🚀 Audio player refinements
- ⬜ Mobile responsiveness improvements
- ⬜ Accessibility enhancements

---

## Design System

### Color Palette
- **Primary**: `#7C3AED` (Violet 600)
- **Primary Dark**: `#6D28D9` (Violet 700)
- **Secondary**: `#06B6D4` (Cyan 500)
- **Accent**: `#F59E0B` (Amber 500)
- **Success**: `#10B981` (Emerald 500)
- **Error**: `#EF4444` (Red 500)
- **Warning**: `#F59E0B` (Amber 500)
- **Background (Light)**: `#FFFFFF`
- **Background (Dark)**: `#0F172A` (Slate 900)
- **Surface (Light)**: `#F8FAFC` (Slate 50)
- **Surface (Dark)**: `#1E293B` (Slate 800)
- **Text (Light)**: `#1E293B` (Slate 800)
- **Text (Dark)**: `#F1F5F9` (Slate 100)
- **Muted Text (Light)**: `#64748B` (Slate 500)
- **Muted Text (Dark)**: `#94A3B8` (Slate 400)

### Typography
- **Font Family**: 
  - Headings: Inter
  - Body: Inter
- **Font Sizes**:
  - Display: 4rem (64px)
  - H1: 2.5rem (40px)
  - H2: 2rem (32px)
  - H3: 1.5rem (24px)
  - H4: 1.25rem (20px)
  - Body: 1rem (16px)
  - Small: 0.875rem (14px)
  - XSmall: 0.75rem (12px)
- **Line Heights**:
  - Tight: 1
  - Default: 1.5
  - Loose: 1.75

### Spacing
- **Base Unit**: 4px
- **Scale**: 0 (0px), 1 (4px), 2 (8px), 3 (12px), 4 (16px), 5 (20px), 6 (24px), 8 (32px), 10 (40px), 12 (48px), 16 (64px), 20 (80px), 24 (96px)

### Shadows
- **sm**: `0 1px 2px 0 rgb(0 0 0 / 0.05)`
- **md**: `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)`
- **lg**: `0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)`
- **xl**: `0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)`

### Border Radius
- **sm**: 2px
- **md**: 6px
- **lg**: 8px
- **xl**: 12px
- **full**: 9999px

### Transitions
- **Fast**: 150ms ease
- **Normal**: 300ms ease
- **Slow**: 500ms ease

## Component Library (shadcn/ui)

### Core Components

#### Layout Components
- `Container`: Max-width containment with proper padding
- `Card`: For contained content sections
- `Section`: For full-width page sections
- `Separator`: For visual separation of content

#### Navigation Components
- `Navbar`: Top navigation with logo, links, and theme switcher
- `Breadcrumbs`: For deep navigation flows

#### Input Components
- `Input`: For URL entry
- `Button`: Multiple variants (primary, secondary, ghost, outline)
- `Form`: Form validation and organization

#### Feedback Components
- `Toast`: For success/error notifications
- `Alert`: For important messages
- `Dialog`: For confirmations and important information
- `Progress`: For tracking processing progress

#### Display Components
- `Tabs`: For organizing content
- `Accordion`: For expandable sections
- `Avatar`: For user profiles and content creators
- `Badge`: For status indicators
- `Tooltip`: For additional information

### Custom Components

#### Agent Workflow Visualization
- **ProcessTimeline**: Shows the overall process steps when not actively processing
- **ProcessingVisualizer**: Displays the active processing with animations
- **AgentFlowDiagram**: Visual graph showing data flow between agents

#### Results Display
- **AudioPlayer**: Enhanced audio player with timestamps and transcription
- **SummaryCard**: Displays the podcast summary with sections
- **InsightTag**: Highlighted tags for key topics

## Page Layouts

### Home Page
```
┌─────────────────────────────────────────┐
│ Navbar                                   │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ Hero Section                         │ │
│ │ - Title                              │ │
│ │ - Description                        │ │
│ │ - URL Input                          │ │
│ │ - Generate Button                    │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Process Visualization               │ │
│ │ - Timeline or Active Process        │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Results (when available)            │ │
│ │ - Summary                           │ │
│ │ - Audio Player                      │ │
│ │ - Key Points                        │ │
│ └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│ Footer                                   │
└─────────────────────────────────────────┘
```

### Processing Page State
```
┌─────────────────────────────────────────┐
│ Navbar                                   │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ Processing Status                   │ │
│ │ - Video Title & Thumbnail           │ │
│ │ - Overall Progress                  │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Agent Workflow Visualization        │ │
│ │ - Interactive diagram showing each  │ │
│ │   agent's progress and data flow    │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Detailed Process Steps              │ │
│ │ - Each agent with status            │ │
│ │ - Time estimates                    │ │
│ └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│ Footer                                   │
└─────────────────────────────────────────┘
```

## Agent Workflow Visualization Detailed Spec

### Design Goals
- Visually engaging but not distracting
- Clear indication of current processing stage
- Shows data flow between components
- Provides appropriate feedback for progress and errors

### Implementation Details

#### Data Model
```typescript
interface AgentNode {
  id: string;
  name: string;
  description: string;
  type: 'preprocessor' | 'transcriber' | 'summarizer' | 'tts' | 'postprocessor';
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number; // 0-100
  startTime?: Date;
  endTime?: Date;
  logs?: string[];
}

interface DataFlow {
  fromAgentId: string;
  toAgentId: string;
  dataType: string;
  status: 'pending' | 'transferring' | 'completed' | 'error';
}

interface WorkflowState {
  agents: AgentNode[];
  dataFlows: DataFlow[];
  overallProgress: number;
  currentAgentId: string | null;
  startTime: Date;
  estimatedEndTime?: Date;
}
```

#### Visual Elements
- **Agent Nodes**: Cards with icon, name, status indicator, and progress bar
- **Flow Connectors**: Animated lines showing data movement between nodes
- **Progress Indicators**: 
  - Individual: Per agent progress bar
  - Overall: Progress bar showing overall completion percentage

#### Animations
- **Flow Animation**: Data particles moving along connectors
- **Active Agent**: Subtle pulsing effect for the currently active agent
- **Completion**: Success animation when agent completes processing
- **Error**: Visual indicator for failure states

#### Interactivity
- Hover on agent to see detailed description and metrics
- Click on agent to expand and see detailed logs (if available)
- Option to collapse/expand the visualization

## Responsive Design Specs

### Breakpoints
- **Mobile**: < 640px
- **Tablet**: 640px - 1023px
- **Desktop**: ≥ 1024px

### Mobile Adaptations
- Stack all layouts vertically
- Simplify agent workflow visualization into a linear step indicator
- Full-width input fields and buttons
- Collapse detailed information behind expanding sections

### Tablet Adaptations
- Grid-based layouts for certain sections
- Simplified agent workflow with key components visible
- Semi-detailed visualization with option to expand

### Desktop Experience
- Full visualization with all details
- Side-by-side layouts where appropriate
- Richer hover interactions

## Implementation Technologies

### Frontend Framework
- Next.js 14+ with App Router
- React Server Components for improved performance
- TypeScript for type safety

### UI Components
- shadcn/ui component system
- Tailwind CSS for styling
- Lucide Icons for iconography

### Animation
- Framer Motion for complex animations
- CSS transitions for simple animations

### State Management
- React Context for theme and global state
- React Query for API state management
- Zod for data validation

### API Communication
- REST API for basic operations
- WebSockets for real-time process updates

## Accessibility Guidelines

- All interactive elements must be keyboard accessible
- Proper contrast ratios for all text (WCAG AA compliance)
- Semantic HTML structure
- Proper ARIA labels for custom components
- Support for screen readers
- Reduced motion option for animations 